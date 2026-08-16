"""Run commands: everything you can type while you are inside somebody else.

Every verb here that does work routes through `_act`, which applies noise and
residue and then spends ticks. That is deliberate centralisation: the D5
triangle is the game, and a command that advances time by hand is a command
that will eventually forget to make noise.

The costs are declared at the top rather than scattered through the handlers,
so the whole economy of the run can be read in one place and balanced without
a search.
"""

from __future__ import annotations

from ..content import cyberspace
from ..content import factions as fac_content
from ..content import ice as ice_content
from ..content import nodes as node_content
from ..content import origins as origin_content
from ..content import programs
from ..content import shifts
from ..run import network as net_mod
from ..run import session as session_mod
from ..run.checks import Check
from ..run.session import RunState, crack_check
from .. import anim, ui
from ..shell import CommandError, command
from ..world import market as market_mod
from ..world.contracts import OBJECTIVE_PROGRAM

#: verb -> (ticks, noise, residue). The whole run economy, in one table.
COST = {
    'scan': (1, 4, 1),
    'probe': (1, 3, 1),
    'connect': (1, 3, 2),
    'crack': (1, 6, 3),
    'pretext': (1, 2, 2),
    'pull': (2, 5, 4),
    'push': (2, 6, 6),
    'wipe': (2, 7, 5),
    'scrub': (2, 2, 0),
    'strike': (1, 7, 2),
    'overload': (1, 22, 6),
    'mask': (1, 0, 0),
    'sidechannel': (3, 0, 1),
    'jack out': (1, 2, 1),
}


# --------------------------------------------------------------------------
# entering and leaving
# --------------------------------------------------------------------------


@command('jack in', 'Start the run.',
         group='city', contexts=('city',), usage='jack in [--speculative]',
         detail='Generates the target network from the contract and puts you '
                'on the entry node. The loadout is fixed from this point, so '
                'check `deck` first.')
def cmd_jack_in(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if sess.run is not None:
        raise CommandError('you are already in.')
    contract = game.city.current
    if contract is None:
        raise CommandError('no contract accepted. `board` to see what is on '
                           'offer, `take <id>` to accept one.')
    if game.city.where != contract.district:
        from ..content import districts
        # The whole walk, not the destination. Naming a district you cannot
        # reach in one shift and putting `travel` in front of it produces a
        # line that the travel command itself refuses, which is a worse place
        # to leave somebody than saying nothing.
        hops = game.city.shifts_to(contract.district)
        raise CommandError(
            f'the job is in {districts.BY_KEY[contract.district].name}, '
            f'{hops} shift{"s" if hops != 1 else ""} away. '
            f'`{game.city.walk_to(contract.district)}`')

    # Nothing in the city kills you, per D6, so a bad comedown on top of an
    # unhealed run can leave somebody standing in the street at zero
    # integrity, which is survivable out here and is the first damage taken
    # in there. The number is on `char` and on `status` and it is exactly the
    # kind of number a player reads past on the way to the interesting part.
    if game.char.integrity <= 0 and not args.has('force'):
        raise CommandError(
            'you have nothing left to absorb a hit with. The first thing '
            'that touches you in there ends the run and possibly you. '
            '`rest`, or wait out whatever is in your bloodstream, or '
            '`jack in --force` and mean it.')

    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need) and not args.has('force'):
        owned = [programs.BY_KEY[k] for k in game.char.library
                 if k in programs.BY_KEY
                 and programs.BY_KEY[k].category == need]
        fix = (f'`load {owned[0].name.lower()}`' if owned
               else f'you do not own one either, so `market program` first')
        raise CommandError(
            f'a {contract.objective} contract needs a {need} program loaded '
            f'and you have none: {fix}. `jack in --force` goes in without '
            f'one, and the job cannot be finished that way.')

    stream = game.rng.fork('network', contract.cid)
    net = net_mod.generate(stream, contract.target, int(contract.posture),
                           contract.objective, contract.size_mod)
    state = RunState.begin(net, game.char, game.rng('combat'), c,
                           contract=contract.to_dict(),
                           phase=game.city.phase)

    if 'credential' in contract.intel:
        state.tier = max(state.tier, 1)

    # An escort job puts a named runner in the network with you, and their
    # noise is not your decision. See RunState._escort_tick.
    if contract.objective == 'escort':
        from ..world import rivals as rival_world
        who = rival_world.pick_escort(game.rng('rivals'), game.city.rivals,
                                      contract.patron)
        if who is not None:
            data = who.data
            state.escort = {
                'key': who.key, 'name': data.name, 'node': net.entry,
                'integrity': 14 + data.skill, 'state': 'working',
                'skill': data.skill, 'done': False, 'progress': 0,
                'panic': (game.rng('rivals').pick(data.panic)
                          if data.panic else ''),
            }
    # A hired runner comes in with you and takes their cut on the way out.
    if game.city.hired:
        who = game.city.rival(game.city.hired)
        if who is not None and who.alive:
            from ..world import rivals as rival_world
            data = who.data
            state.ally = {
                'key': who.key, 'name': data.name, 'node': net.entry,
                'integrity': 12 + data.skill * 2, 'state': 'with you',
                'skill': data.skill, 'style': data.style,
                'cut': rival_world.HIRE_CUT,
            }
        # Deliberately NOT cleared here. `city.hired` is what keeps them out
        # of the shift-tick rival turn, so it has to survive until the run
        # resolves or they can be sent off to die on somebody else's job while
        # standing next to you.

    sess.run = state

    # The threshold. Everything before this line is the city and everything
    # after it is the other place, and that deserves a moment.
    anim.connect(c, contract.target_data.name)

    c.rule('connected')
    c.say(f'[dim]Target: [/][err]{contract.target_data.name}[/][dim], posture '
          f'{int(contract.posture)}. Objective: {contract.objective}.[/]')
    c.blank()
    # Whose network this is, as a shape before it is a sentence. After five
    # runs a player knows the mark without reading the name under it.
    _sigil(c, contract.target)
    # What their cyberspace is made of. Printed once, because it is the visual
    # key for the whole run and players learn to read it.
    c.say(f'[ice]{cyberspace.signature(contract.target).arrival}[/]')
    c.blank()
    c.say(f'[dim]You come up on [/][accent]{net.entry}[/][dim]: '
          f'{cyberspace.look(net.node(net.entry).type, 0, contract.target)}.[/]')
    if 'topology' in contract.intel:
        _reveal_topology(state)
        c.info('Your legwork holds. The shape of it is already in front of you.')
    if 'ice' in contract.intel:
        for node in net.nodes.values():
            for construct in node.ice:
                construct.known = True
        c.info('You know what they are running.')
    if 'assets' in contract.intel:
        for node in net.nodes.values():
            if node.data:
                node.known = True
    if state.ally:
        from ..content import rivals as rival_content
        style, detail = rival_content.ALLY_SPECIALTY[state.ally['style']]
        c.blank()
        c.say(f'[ok]{state.ally["name"]} comes up beside you and says '
              f'nothing.[/] [dim]{detail}[/]')
    if state.escort:
        c.blank()
        c.say(f'[info]{state.escort["name"]} comes up on the same entry node '
              f'a half-second after you do.[/]')
        c.say('[dim]They are not yours to command. `signal hold|move|out` is '
              'advice, and they take it when they feel like it.[/]')
    # What this run is for, said at the door in the words the player will use
    # to do it. The objective used to arrive as one word in the header line
    # above, which names a category of job and not this one.
    brief = state.brief()
    c.blank()
    c.rule('the job')
    c.say(f'[accent2]{brief.aim}[/]')
    if brief.where:
        c.say(f'[dim]{brief.where}[/]')
    c.blank()
    c.say('[dim]`job` at any point for this and the next move. `scan` to look '
          'around. `status` for where you stand. `jack out` to leave.[/]')


#: Above this much trace, leaving with nothing is a decision rather than a
#: mistake, and the game stops asking about it. Somebody bailing at 70 knows
#: exactly what they are giving up; somebody bailing at 15 has usually lost
#: track of what the job was.
ARGUE_BELOW = 55.0


@command('jack out', 'Leave the run and settle up.',
         group='defence', contexts=('run',), ticks=1, usage='jack out',
         detail='Ends the run. If the contract is not finished and the trace '
                'is still low, this says so once and makes you type it again, '
                'because leaving early is a real move and leaving early by '
                'accident is not.')
def cmd_jack_out(sess, args) -> None:
    state = sess.require_run()
    c = sess.console

    # Said once, on the way out, while it can still be acted on. The summary
    # already reports a burned run, and by then the only thing the player can
    # do about it is read it.
    brief = state.brief()
    if (not brief.done and not args.has('anyway')
            and not state.warned_incomplete
            and state.trace < ARGUE_BELOW):
        state.warned_incomplete = True
        c.blank()
        c.warn('You have not done the job yet.')
        c.say(f'[dim]{brief.aim}[/]')
        if brief.where:
            c.say(f'[dim]{brief.where}[/]')
        c.blank()
        c.say(f'[dim]Leaving now pays nothing for the contract. The trace is '
              f'at {int(state.trace)} and you have room. `job` for the whole '
              f'brief, or `jack out --anyway` to go.[/]')
        return
    # The Grave Governor holds a session open, and does not distinguish
    # between one you want held and one you are trying to leave.
    riders = state.char.riders()
    slow = 'slow_exit' in riders
    if slow:
        c.say('[warn]The Governor does not want to let go. It takes a moment '
              'to convince it.[/]')
    # Greedy: you have never left a node with anything still on it, and you
    # are not about to start.
    if ('cannot_leave' in riders
            and any(not a.taken for a in state.node.data)):
        slow = True
        c.say('[warn]There is still something on this node. You spend a '
              'moment not leaving.[/]')
    _act(sess, 'jack out', ticks=2 if slow else None)
    if sess.run is None:
        # Leaving cost you the last tick you had. `_act` has already settled.
        return
    state.finish('clean' if state.objective_met() else 'burned')
    _resolve(sess)


def _resolve(sess) -> None:
    """Close out a run and hand the summary to the city layer."""
    game, c = sess.game, sess.console
    state = sess.run
    summary = state.summary()
    sess.run = None
    game.char.runs += 1

    c.blank()
    c.rule('disconnected')
    verdict = {
        'clean': ('[ok]You are out.[/] The room comes back one sense at a '
                  'time and your hands have gone cold on the arms of the '
                  'chair. Nothing outside has noticed anything.'),
        'burned': ('[warn]You are out, with nothing.[/] The same room, the '
                   'same cold hands, and the specific hollow feeling of '
                   'having spent a night making somebody else\'s security '
                   'team better at their jobs.'),
        'severed': ('[err]They cut you loose from the far end.[/] You come '
                    'back badly, tasting copper, with the deck fans screaming '
                    'and a nosebleed you did not feel start.'),
        'flatline': '[err][bold]FLATLINE.[/][/]',
    }.get(summary['outcome'], '')
    c.say(verdict)

    c.blank()
    c.kv([('ticks', str(summary['ticks'])),
          ('trace', f'{summary["trace"]}/100'),
          ('alert', summary['alert']),
          ('residue', f'[residue]{summary["residue"]}[/]'),
          ('haul', f'{len(summary["haul"])} assets, '
                   f'[credit]{summary["haul_value"]:,}c[/] nominal')])

    if summary['outcome'] == 'flatline':
        game.over = 'flatlined'
        from .. import save as save_mod
        save_mod.bump_meta(flatlines=1)
        c.blank()
        c.say('[err]It held on long enough. There is no disconnection, no '
              'room coming back, no cold hands: the feed simply stops being a '
              'feed and becomes the last thing.[/]')
        c.blank()
        c.say('[dim]Somebody will find the deck still warm and the chair '
              'still occupied. The building will bill the estate for the '
              'cleaning. Nobody will run this address again for a year, out '
              'of superstition rather than respect.[/]')
        c.blank()
        c.kv([('handle', game.char.handle),
              ('ran as', game.alias.name),
              ('runs', str(game.char.runs)),
              ('earned', f'{game.earned:,}c'),
              ('killed by', 'black ICE')])
        # Everything else this character had is gone. The shell is not theirs
        # and never was, and this is the one moment where saying so out loud
        # is the point rather than an interruption.
        # The game is named after this moment and it has always ended into a
        # scoreboard. Something of them reaches whoever gets made next.
        from .core import _bequeath
        _bequeath(sess, 'flatlined')
        sess.record_progress()
        sess.autosave()
        return

    # The story layer reads what you have actually done.
    game.story.flags.add(f'ran:{summary["faction"]}')

    for line in game.city.apply_run(game.alias, summary, game.rng,
                                    game.char.memorable):
        c.say(line)

    contract = game.city.current
    if contract is not None:
        pay, told = game.city.pay_out(game.alias, contract, summary,
                                      game.char.mult('pay_mult'),
                                      game.char.memorable)
        game.char.credits += pay
        game.earned += pay
        for line in told:
            c.say(line)
        if summary.get('objective'):
            game.city.board = [x for x in game.city.board
                               if x.cid != contract.cid]
            game.city.accepted = ''
            # Work somebody handed you personally comes off the tab when you
            # finish it. That is the whole loop: they trust you with a job,
            # the job buys favours, and the favours were what you wanted.
            if contract.from_npc:
                from ..content import npcs as npc_content
                who = npc_content.BY_KEY.get(contract.from_npc)
                owed = game.story.owed.get(contract.from_npc, 0)
                if who is not None:
                    if owed:
                        game.story.owed[contract.from_npc] = owed - 1
                        c.say(f'[ok]{who.name} has one fewer reason to say '
                              f'no to you.[/]')
                    else:
                        game.story.flags.add(f'delivered:{contract.from_npc}')
                        c.say(f'[ok]{who.name} will remember that you did '
                              f'this one properly.[/]')

    # Selling the haul is a city action, but crediting it here keeps the run
    # readable: what you carried out is worth what it is worth.
    # What you carried out is worth what somebody will pay for it today, and
    # who that somebody is depends on who you know. A trusted runner clears
    # nearly three quarters of nominal; a stranger clears under half.
    extra = int(summary.get('haul_value') or 0)
    ally = summary.get('ally')
    if extra:
        buyer = contract.patron if contract is not None else 'fixers'
        take, rate = market_mod.data_price(game.rng('market'), extra,
                                           game.alias, buyer)
        if ally and ally['state'] != 'dead':
            cut = int(take * ally['cut'])
            take -= cut
            c.say(f'[dim]{ally["name"]} takes {cut:,}c off the top, counts it '
                  f'once, and leaves.[/]')
        game.char.credits += take
        game.earned += take
        c.say(f'[credit]{take:,}c[/] for the haul, at '
              f'[dim]{rate * 100:.0f}% of nominal through '
              f'{fac_content.BY_KEY[buyer].short}.[/]')

    # An escort job is the game's relationship engine: you spent a night
    # keeping somebody alive, or you did not, and either way they remember.
    # Without this there is no route up from a cold start to a favour.
    escort = summary.get('escort')
    if escort:
        who = game.city.rival(escort['key'])
        if who is not None:
            if escort['state'] == 'dead':
                who.alive = False
                who.died = game.city.shift
                for other in game.city.rivals:
                    if other.key != who.key and other.alive:
                        other.adjust_disposition(-10)
                c.blank()
                c.say('[err]Everybody is going to hear whose job that was.[/]')
                game.city.news.append(f'{escort["name"]} died on your watch.')
            elif escort['done']:
                who.adjust_disposition(18)
                c.say(f'[ok]{escort["name"]} got out with what they went in '
                      f'for, and knows who covered them.[/]')
            else:
                who.adjust_disposition(-6)
                c.say(f'[warn]{escort["name"]} came out with nothing. They '
                      f'are not blaming you out loud.[/]')

    game.city.hired = ''
    if ally:
        who = game.city.rival(ally['key'])
        if who is not None:
            if ally['state'] == 'dead':
                who.alive = False
                who.died = game.city.shift
                c.blank()
                c.say(f'[err]You are going to have to tell somebody about '
                      f'{ally["name"]}.[/]')
                # The street knows who they went in with.
                for other in game.city.rivals:
                    if other.key != who.key and other.alive:
                        other.adjust_disposition(-6)
                game.city.news.append(f'{ally["name"]} died on a job with you.')
            else:
                who.adjust_disposition(6 if summary.get('objective') else 2)

    if 'creeping_dissonance' in game.char.riders():
        game.char.dissonance += 1
        c.say('[accent2]Something you are wearing has settled another '
              'millimetre closer in.[/] [dim]Dissonance '
              f'{game.char.dissonance}.[/]')

    gained = 2 + summary['ticks'] // 12 + (2 if summary.get('objective') else 0)
    game.char.xp += gained
    c.say(f'[dim]{gained} experience.[/]')

    # Meta, which outlives the character. A run counts as run whatever
    # happened in it; a run counts as clean only if nobody ever knew.
    from .. import save as save_mod
    save_mod.bump_meta(runs_completed=1,
                       clean_runs=1 if summary['outcome'] == 'clean' else 0)

    from ..commands.city import _advance
    _advance(sess, 1)
    sess.record_progress()


# --------------------------------------------------------------------------
# reconnaissance
# --------------------------------------------------------------------------


@command('scan', 'Look at what this node is connected to.',
         group='recon', contexts=('run',), ticks=1, usage='scan [--quiet]')
def cmd_scan(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    depth = 1 + state.char.bonus('scan_depth')
    hunter = programs.best(state.char.deck.loaded, 'hunter')
    if hunter:
        depth += max(0, hunter.rating // 3)
    quiet = args.has('quiet')

    found = _reveal(state, state.here, depth)
    state.scanned.add(state.here)
    noise_scale = 0.4 if quiet else 1.0
    if hunter:
        noise_scale *= hunter.signature
    _act(sess, 'scan', noise_scale=noise_scale,
         ticks=2 if quiet else 1)

    if not found:
        c.info('Nothing new.')
        return
    c.blank()
    rows = []
    for uid in found:
        node = state.net.nodes[uid]
        rows.append((uid, node.display_type, node.zone,
                     'open' if node.open else f'tier {node.tier}'))
    c.table(('host', 'type', 'zone', 'access'), rows,
            roles=('accent', 'dim', 'info', 'warn'))


@command('probe', 'Enumerate a node: services, data, and what is watching.',
         group='recon', contexts=('run',), ticks=1, usage='probe [host]',
         complete=lambda sess, prefix: _known_hosts(sess))
def cmd_probe(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    uid = args.get(0) or state.here
    node = _node(state, uid)
    if not node.known:
        raise CommandError(f'{uid} has not been found yet. `scan` first.')

    hunter = programs.best(state.char.deck.loaded, 'hunter')
    node.mapped = True
    # A honeypot gives itself up to a good enough look, and only then.
    if node.type == 'honeypot' and node.disguised:
        check = Check(name='spot the honeypot', resistance=10)
        check.add('logic', state.char.attr('logic'))
        check.add('forensics', state.char.skill('forensics') * 2)
        if hunter:
            check.add(hunter.name, hunter.rating)
        if state.char.origin == 'defector':
            check.add('you have read the standard', 3)
        check.resolve(state.rng)
        if check.success:
            node.disguised = False
    for construct in node.ice:
        if hunter and hunter.key == 'auspex':
            construct.known = True
        elif state.char.origin == 'expolice':
            construct.known = True

    _act(sess, 'probe', node=node,
         noise_scale=hunter.signature if hunter else 1.0)
    if not state.running:
        # The tick this probe cost was the one that finished the run, and
        # there is nobody left to show the node to.
        return
    _show_node(sess, node, detail=True)


@command('map', 'The shape of where you are: the city, or the network.',
         group='recon', usage='map [--flat]',
         detail='In the city: the nine districts, how they join, and the walk '
                'from here to each of them. In a run: every host you have '
                'found and what connects to what, with `--flat` for the same '
                'thing listed by zone. The same picture either way, because it '
                'is the same question.')
def cmd_map(sess, args) -> None:
    if sess.run is None:
        from .city import city_map
        city_map(sess)
        return
    state, c = sess.require_run(), sess.console
    net = state.net
    visible = {n.uid for n in net.nodes.values() if n.known}
    c.header('Known hosts', f'{len(visible)} of {len(net.nodes)}')

    if args.has('flat') or state.here not in visible:
        _map_flat(sess, visible)
        return

    ascii_only = c.caps.glyphs is ui.GlyphLevel.ASCII
    # Drawn from the entry rather than from where you are standing, so the
    # picture does not reshuffle every time you move. A map that redraws
    # itself as you walk is a compass, not a map.
    root = net.entry if net.entry in visible else state.here
    rows = net_mod.tree_rows(net, root, visible, ascii_only)
    _, extra = net_mod.spanning_tree(net, root, visible)
    drawn = {uid for _, uid in rows}

    c.blank()
    for prefix, uid in ui.tree_leads(rows):
        node = net.node(uid)
        if node is None:
            continue
        c.raw(f'[dim]{prefix}[/]{_map_label(state, node)}')

    # Hosts the scan found but that nothing known connects to yet. They are
    # real and they are not reachable, and hiding them would be a lie.
    orphans = sorted(visible - drawn)
    if orphans:
        c.blank()
        c.say('[dim]Seen, with no route from anywhere you have opened:[/]')
        for uid in orphans:
            node = net.node(uid)
            if node is not None:
                c.raw(f'  {_map_label(state, node)}')

    # One line per pair. `extra` reports both ends of every back edge, and
    # printing both makes a network with four crossings look like it has
    # eight.
    pairs = sorted({tuple(sorted((a, b)))
                    for a, others in extra.items() for b in others})
    if pairs:
        c.blank()
        c.say('[dim]Also connected, which the shape above cannot show:[/]')
        for a, b in pairs:
            c.raw(f'  [accent]{a}[/][dim] to [/][accent]{b}[/]')

    c.blank()
    c.say('[dim]`map --flat` for the list by zone. '
          '`scan` to reach further.[/]')


def _sigil(c, faction: str) -> None:
    """The faction's mark, beside their name."""
    rows = cyberspace.sigil(faction,
                            c.caps.glyphs is ui.GlyphLevel.ASCII)
    if not rows:
        return
    role = cyberspace.sigil_role(faction)
    name = fac_content.BY_KEY[faction].name
    # Name on the second row so the block reads as a mark with a caption
    # rather than as a heading with a picture under it.
    for i, row in enumerate(rows):
        tail = f'   [dim]{name}[/]' if i == 1 else ''
        c.raw(f'  [{role}]{row}[/]{tail}')
    c.blank()


def _map_label(state, node) -> str:
    """One host, with everything currently known about it."""
    marks = []
    if node.uid == state.here:
        marks.append('[accent]you[/]')
    if node.open:
        marks.append('[ok]open[/]')
    if node.uid == state.net.objective_node:
        marks.append('[accent2]objective[/]')
    live = [i for i in node.live_ice if i.known]
    if live:
        marks.append(f'[ice]{len(live)} ice[/]')
    if node.data and node.mapped:
        marks.append(f'[credit]{len(node.data)} assets[/]')
    if node.residue:
        marks.append(f'[residue]residue {node.residue}[/]')
    role = 'accent' if node.open else 'fg'
    head = f'[{role}]{node.uid:<12}[/] [dim]{node.zone[:4]:<5}[/]'
    # The type is only padded when something follows it. Padding it
    # unconditionally leaves trailing spaces on most rows, which nobody sees
    # in a terminal and everybody sees in a bug report.
    if not marks:
        return f'{head}[dim]{node.display_type}[/]'
    return f'{head}[dim]{node.display_type:<12}[/] {"  ".join(marks)}'


def _map_flat(sess, visible: set[str]) -> None:
    """The list by zone. Still here because it sorts by depth, which the
    tree does not, and depth is the number that matters when you are
    deciding how far in you are willing to go."""
    state, c = sess.run, sess.console
    for zone in node_content.ZONES:
        group = [n for n in state.net.nodes.values()
                 if n.uid in visible and n.zone == zone]
        if not group:
            continue
        c.blank()
        c.raw(f'[info]{zone}[/] [dim]{node_content.ZONE_BLURB[zone]}[/]')
        for node in group:
            c.raw(f'  {_map_label(state, node)}')


@command('here', 'What is in front of you right now.',
         group='recon', contexts=('run',), usage='here')
def cmd_here(sess, args) -> None:
    state = sess.require_run()
    _show_node(sess, state.node, detail=state.node.mapped)


# --------------------------------------------------------------------------
# access
# --------------------------------------------------------------------------


@command('connect', 'Move to an adjacent node you have opened.',
         group='access', contexts=('run',), aliases=('cd',), ticks=1,
         usage='connect <host> [--ghost] [--present]',
         complete=lambda sess, prefix: _known_hosts(sess))
def cmd_connect(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    uid = args.require(0, 'a host to connect to')
    node = _node(state, uid)
    if uid == state.here:
        raise CommandError('you are already there')
    if uid not in state.node.edges:
        raise CommandError(f'{uid} is not reachable from {state.here}')
    if not node.open:
        raise CommandError(f'{uid} is not open. `crack` a service on it first.')

    wardens = [i for i in node.live_ice
               if i.behaviour == 'warden' and i.state != 'dead']
    if wardens:
        warden = wardens[0]
        challenge = state.credential_challenge(warden)
        if challenge is None:
            # Named counters rather than "break it". Nothing you can type from
            # out here reaches a construct standing on another node, so a
            # player told to break it and left to work out how spends the rest
            # of the run rattling the same handle.
            warden.known = True
            raise CommandError(
                f'{warden.data.name} holds {uid} and does not take '
                f'credentials. Nothing you can do from here touches it: '
                f'`pivot` goes past one at Intrusion 4, and otherwise there '
                f'is another way in. `map` will show you where.')
        if not args.has('present'):
            # It has just been named and its odds printed. Anything that asks
            # what the player knows has to count that.
            warden.known = True
            c.blank()
            c.say(f'[ice]{warden.data.name} holds {uid}, and it is the kind '
                  f'that asks rather than the kind that refuses.[/]')
            c.say(f'{challenge.summary()}')
            c.say(challenge.explain(), indent='  ')
            c.blank()
            c.say(f'[dim]`connect {uid} --present` to show it something. '
                  f'A failure escalates.[/]')
            return
        challenge.resolve(state.rng)
        _act(sess, 'pretext', node=node, noise_scale=0.3)
        if not state.running:
            return
        if not challenge.success:
            c.blank()
            c.err(f'{warden.data.name} does not accept it.')
            c.say(challenge.explain())
            state.escalate(1, 'A credential was presented and refused.')
            return
        c.blank()
        c.ok(f'{warden.data.name} reads what you are carrying and stands '
             f'aside.')
        warden.state = 'dead'

    ghost = args.has('ghost')
    if ghost and not state.char.has_technique('ghost'):
        raise CommandError('you have not learned to ghost. Stealth rank 2.')

    crossing = node.tier > state.net.nodes[state.here].tier
    state.here = uid
    # Native: the network is a room and you are walking across it.
    free = state.native > 0
    _act(sess, 'connect', node=node,
         noise_scale=0.0 if (ghost or free) else 1.0,
         ticks=0 if free else (2 if ghost else 1))
    if state.running and crossing:
        # Depth has to feel like depth rather than a counter going up.
        line = cyberspace.descent(node.zone, state.tick)
        if line:
            c.blank()
            c.say(f'[ice]{line}[/]')
    if state.running:
        state.check_traps(node)
    if state.running:
        c.blank()
        _show_node(sess, node, detail=node.mapped)


@command('crack', 'Break a service open.',
         group='access', contexts=('run',), ticks=1,
         usage='crack <host> <service> [--quiet] [--key] [--chain]',
         detail='Uses your best loaded breaker. `--quiet` swaps to the '
                'lowest-signature one and takes a penalty. `--key` uses the '
                'Keygrind technique: Focus instead of ticks, and no noise. '
                '`--chain` uses the Chain technique: two services on one node '
                'for one action, at 1.6x the noise of the louder half.')
def cmd_crack(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if args.has('chain'):
        _crack_chain(sess, args)
        return
    node, svc = _target_service(state, args)
    if svc.cracked:
        raise CommandError(f'{svc.key} on {node.uid} is already open')

    skill_key, category = node_content.FAMILIES[svc.family]
    quiet = args.has('quiet')
    keygrind = args.has('key')

    if keygrind:
        if not state.char.has_technique('keygrind'):
            raise CommandError('Keygrind is Cryptography rank 2.')
        if svc.family != 'crypto':
            raise CommandError('Keygrind only works on encrypted services.')
        if state.focus < 2:
            raise CommandError(f'Keygrind costs 2 Focus and you have '
                               f'{state.focus}.')

    program = (programs.quietest(state.char.deck.loaded, category) if quiet
               else programs.best(state.char.deck.loaded, category))
    check = crack_check(state, node, svc, program, quiet=quiet)
    check.resolve(state.rng)

    if keygrind:
        state.focus -= 2
        _act(sess, 'crack', node=node, ticks=0, noise_scale=0.0)
    else:
        signature = program.signature if program else 1.5
        _act(sess, 'crack', node=node,
             noise_scale=signature * svc.data.noise * (0.5 if quiet else 1.0),
             ticks=2 if (program and program.key == 'lattice') else 1)

    if not state.running:
        return
    c.blank()
    if check.success:
        svc.cracked = True
        was_open = node.open
        node.open = True
        c.ok(f'{svc.data.name} on [accent]{node.uid}[/] is open.')
        if not was_open:
            c.info(f'{node.uid} will take a connection now.')
        if check.critical:
            state.tier = max(state.tier, node.tier)
            c.say('[ok]Clean enough that you came out of it holding a '
                  'credential.[/]')
        if node.type == 'auth' and node.cracked_all:
            state.tier = max(state.tier, node.tier + 1)
            c.say(f'[ok]This is where the badges come from. Access tier '
                  f'{state.tier}.[/]')
    else:
        c.err(f'{svc.data.name} holds.')
        state.last_failure = (node.uid, svc.key)
        c.say(check.explain())
        culprit = check.culprit()
        if culprit and culprit.value < 0:
            c.say(f'[dim]What sank it: {culprit.label}.[/]')
        if check.fumble:
            state.escalate(1, 'A failed attempt was logged loudly.')
    state.check_traps(node)


def _crack_chain(sess, args) -> None:
    """Intrusion rank 2: two services on one node for the price of one action.

    The maths favours it when the trace is your problem and the ICE is not:
    you pay one action's ticks instead of two, and 1.6x the noise of the
    *louder* half rather than the sum. On a quiet node that is a bargain. On
    one with something dormant listening it is how you wake it.
    """
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('chain'):
        raise CommandError('Chain is Intrusion rank 2.')

    host = args.get(0)
    if not host:
        raise CommandError('chain what? `crack <host> --chain`')
    node = _node(state, host)
    if not node.mapped:
        raise CommandError(f'{node.uid} has not been probed. '
                           f'`probe {node.uid}` first.')

    closed = [s for s in node.services if not s.cracked]
    if len(closed) < 2:
        raise CommandError(f'{node.uid} has {len(closed)} service'
                           f'{"s" if len(closed) != 1 else ""} left to break. '
                           f'Chain needs two.')

    named = [a for a in args.positional[1:]]
    if named:
        picked = []
        for key in named[:2]:
            match = [s for s in closed if s.key.startswith(key.lower())]
            if not match:
                raise CommandError(f'{node.uid} has no uncracked service '
                                   f'matching {key!r}')
            if match[0] not in picked:
                picked.append(match[0])
        if len(picked) < 2:
            raise CommandError('name two different services, or none and I '
                               'will take the two easiest')
    else:
        picked = sorted(closed, key=lambda s: s.difficulty)[:2]

    quiet = args.has('quiet')
    checks = []
    loudest = 0.0
    for svc in picked:
        _, category = node_content.FAMILIES[svc.family]
        program = (programs.quietest(state.char.deck.loaded, category) if quiet
                   else programs.best(state.char.deck.loaded, category))
        check = crack_check(state, node, svc, program, quiet=quiet)
        check.resolve(state.rng)
        checks.append((svc, check))
        signature = program.signature if program else 1.5
        loudest = max(loudest, signature * svc.data.noise)

    # One action, and 1.6x the louder half rather than the sum of both.
    _act(sess, 'crack', node=node,
         noise_scale=loudest * 1.6 * (0.5 if quiet else 1.0),
         ticks=1)
    if not state.running:
        return

    c.blank()
    opened = 0
    for svc, check in checks:
        if check.success:
            svc.cracked = True
            node.open = True
            opened += 1
            c.ok(f'{svc.data.name} on [accent]{node.uid}[/] is open.')
        else:
            c.err(f'{svc.data.name} holds.')
            c.say(check.explain(), indent='  ')
    if opened == 2:
        c.say('[dim]Both, in one pass. Everything within earshot knows.[/]')
    if node.type == 'auth' and node.cracked_all:
        state.tier = max(state.tier, node.tier + 1)
        c.say(f'[ok]This is where the badges come from. Access tier '
              f'{state.tier}.[/]')
    if any(check.fumble for _, check in checks):
        state.escalate(1, 'A failed attempt was logged loudly.')
    state.check_traps(node)


@command('pretext', 'Talk a service into letting you in.',
         group='access', contexts=('run',), ticks=1,
         usage='pretext <host> <service>',
         detail='Subterfuge rank 2. A Guile check instead of a Logic one, at a '
                'quarter of the noise. Fails badly: a blown pretext escalates '
                'the alert rather than merely making noise.')
def cmd_pretext(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('pretext'):
        raise CommandError('Pretext is Subterfuge rank 2.')
    if 'no_social' in state.char.riders():
        raise CommandError('you are rendering as a scheduled job. Processes '
                           'do not talk, and trying would drop the disguise.')
    node, svc = _target_service(state, args)
    if svc.cracked:
        raise CommandError('that is already open')

    forger = programs.best(state.char.deck.loaded, 'forger')
    check = Check(name='pretext', resistance=svc.difficulty * 2 + 2)
    check.add('subterfuge', state.char.skill('subterfuge') * 2)
    check.add('guile', state.char.attr('guile'))
    check.add('gear', state.char.bonus('pretext_bonus'))
    if forger:
        check.add(forger.name, forger.rating * 2)
    if node.tier > state.tier:
        check.add('you have no business here', -3 * (node.tier - state.tier))
    check.resolve(state.rng)

    _act(sess, 'pretext', node=node,
         noise_scale=0.25 * (forger.signature if forger else 1.0))
    if not state.running:
        return
    c.blank()
    if check.success:
        svc.cracked = True
        node.open = True
        c.ok(f'They let you in. {svc.data.name} on '
             f'[accent]{node.uid}[/] is open.')
    else:
        c.err('It does not land.')
        c.say(check.explain())
        state.escalate(1, 'Somebody checked, and you were not who you said.')


@command('pivot', 'Enter a neighbour on this node\'s trust.',
         group='access', contexts=('run',), ticks=1, usage='pivot <host>',
         detail='Intrusion rank 4. Skips the access check on any node that '
                'trusts the one you are standing in. Silent.')
def cmd_pivot(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('pivot'):
        raise CommandError('Pivot is Intrusion rank 4.')
    uid = args.require(0, 'a host to pivot to')
    node = _node(state, uid)
    if uid not in state.node.edges:
        raise CommandError(f'{uid} does not touch {state.here}')
    if not state.node.open:
        raise CommandError('you do not hold this node firmly enough to trade '
                           'on its trust')
    node.open = True
    node.known = True
    state.here = uid
    _act(sess, 'connect', node=node, noise_scale=0.0)
    if state.running:
        c.ok(f'{uid} took the connection without asking.')
        state.check_traps(node)
        if state.running:
            _show_node(sess, node, detail=node.mapped)


@command('sidechannel', 'Derive a key from traffic you can already see.',
         group='access', contexts=('run',), ticks=3, usage='sidechannel',
         detail='Cryptography rank 4. Free, silent, and slow: three ticks of '
                'residency. Opens every crypto service on this node.')
def cmd_sidechannel(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('sidechannel'):
        raise CommandError('Sidechannel is Cryptography rank 4.')
    node = state.node
    crypto = [s for s in node.services if s.family == 'crypto' and not s.cracked]
    if not crypto:
        raise CommandError('nothing here is encrypted enough to leak.')
    _act(sess, 'sidechannel', ticks=3)
    if not state.running:
        return
    for svc in crypto:
        svc.cracked = True
    node.open = True
    c.ok(f'{len(crypto)} encrypted service'
         f'{"s" if len(crypto) != 1 else ""} on {node.uid} gave up a key.')


@command('impersonate', 'Become the owner of a credential you hold.',
         group='access', contexts=('run',), ticks=1, usage='impersonate',
         detail='Subterfuge rank 4. ICE ignores you for a number of ticks '
                'equal to your Guile. You are not hidden; you are authorised.')
def cmd_impersonate(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('impersonate'):
        raise CommandError('Impersonate is Subterfuge rank 4.')
    if 'no_social' in state.char.riders():
        raise CommandError('a process cannot claim to be a person.')
    if 'impersonate' in state.spent:
        raise CommandError('you have already used that name once tonight')
    if state.tier < 1:
        raise CommandError('you have no credential worth wearing yet')
    state.spent.add('impersonate')
    state.impersonating = state.char.attr('guile')
    for construct in state.locked:
        construct.state = 'dormant'
        construct.telegraphed = False
    state.locked.clear()
    _act(sess, 'pretext', noise_scale=0.0)
    c.ok(f'You are somebody else for {state.impersonating} ticks. Everything '
         f'that was chasing you has lost interest.')


# --------------------------------------------------------------------------
# action
# --------------------------------------------------------------------------


@command('pull', 'Take data out.',
         group='action', contexts=('run',), ticks=2, usage='pull [asset|--all]')
def cmd_pull(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    node = state.node
    if not node.open:
        raise CommandError('you are not standing anywhere you can read from')
    available = [a for a in node.data if not a.taken]
    if not available:
        raise CommandError('nothing here to take')

    payload = programs.best(state.char.deck.loaded, 'payload')
    if payload is None:
        raise CommandError('you have no payload program loaded. Nothing can '
                           'carry it out.')

    if args.has('all'):
        targets = available
    else:
        query = (args.get(0) or '').lower()
        targets = [a for a in available
                   if not query or query in a.name.lower() or query == a.uid]
        if not targets:
            raise CommandError(f'nothing here matches {query!r}')
        targets = targets[:1]

    # A wipe contract is satisfied by destroying one specific record, and
    # `wipe` can only reach a record that is still on the node. Taking it puts
    # it in your hands and out of reach of the only verb that finishes the
    # job, which is a soft lock reached by typing an obviously sensible thing.
    kind = (state.contract or {}).get('objective', '')
    if kind == 'wipe' and not args.has('anyway'):
        doomed = [a for a in targets if a.uid == state.net.objective_asset]
        if doomed:
            raise CommandError(
                f'{doomed[0].name} is the record you were paid to destroy, '
                f'and taking it puts it somewhere `wipe` cannot reach. '
                f'`wipe` it instead, or `pull {doomed[0].uid} --anyway` and '
                f'give up the fee.')

    for asset in targets:
        if asset.encrypted:
            check = Check(name='decrypt', resistance=state.net.posture // 4 + 6)
            check.add('cryptography', state.char.skill('cryptography') * 2)
            check.add('logic', state.char.attr('logic'))
            check.add('gear', state.char.bonus('crypto_bonus'))
            if state.char.origin == 'academic':
                check.add('first principles', 3)
            check.resolve(state.rng)
            if not check.success:
                c.err(f'{asset.name} is sealed and stays sealed.')
                c.say(check.explain())
                _act(sess, 'pull', node=node, noise_scale=payload.signature)
                continue
        asset.taken = True
        state.haul.append(asset.uid)
        mark = ' [accent2](the job)[/]' if asset.objective else ''
        c.ok(f'{asset.name} pulled, [credit]{asset.value:,}c[/] nominal.{mark}')
        _act(sess, 'pull', node=node, noise_scale=payload.signature)
        if not state.running:
            return
    if state.contract and state.contract.get('objective') == 'exfiltrate':
        if state.net.objective_asset in state.haul:
            c.blank()
            c.say('[ok][bold]That is what you came for. Get out.[/][/]')


@command('push', 'Leave something behind: an implant or an edit.',
         group='action', contexts=('run',), ticks=2, usage='push [asset]')
def cmd_push(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    node = state.node
    if not node.open:
        raise CommandError('you do not hold this node')
    payload = programs.best(state.char.deck.loaded, 'payload')
    if payload is None:
        raise CommandError('no payload program loaded')

    kind = (state.contract or {}).get('objective', 'implant')
    if kind not in ('implant', 'corrupt'):
        kind = 'implant'

    check = Check(name=kind, resistance=state.net.posture // 5 + 6)
    check.add('intrusion', state.char.skill('intrusion') * 2)
    check.add('logic', state.char.attr('logic'))
    check.add(payload.name, payload.rating * 2)
    check.resolve(state.rng)

    _act(sess, 'push', node=node, noise_scale=payload.signature)
    if not state.running:
        return
    c.blank()
    if check.success:
        state.done[kind] = node.uid
        c.ok(f'Done. It is on [accent]{node.uid}[/] and it will still be '
             f'there next quarter.')
        if node.uid == state.net.objective_node:
            c.say('[ok][bold]That is the job. Get out.[/][/]')
    else:
        c.err('It will not take.')
        c.say(check.explain())


@command('wipe', 'Destroy an asset.',
         group='action', contexts=('run',), ticks=2, usage='wipe [asset]')
def cmd_wipe(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    node = state.node
    available = [a for a in node.data if not a.taken]
    if not available:
        raise CommandError('nothing here to destroy')
    query = (args.get(0) or '').lower()
    targets = [a for a in available
               if not query or query in a.name.lower() or query == a.uid]
    if not targets:
        raise CommandError(f'nothing matches {query!r}')
    asset = targets[0]
    asset.taken = True
    state.done['wipe'] = asset.uid
    _act(sess, 'wipe', node=node)
    if state.running:
        c.ok(f'{asset.name} is gone. Loudly.')


@command('scrub', 'Reduce the evidence you have left on this node.',
         group='defence', contexts=('run',), ticks=2, usage='scrub',
         detail='Forensics rank 2. The purest expression of the D5 trade: you '
                'spend the trace, right now, to buy down heat you will not '
                'feel for another two shifts.')
def cmd_scrub(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('scrub'):
        raise CommandError('Scrub is Forensics rank 2.')
    node = state.node
    if not node.residue:
        raise CommandError('there is nothing on this node to clean')

    wiper = programs.best(state.char.deck.loaded, 'wiper')
    check = Check(name='scrub', resistance=8 + state.net.posture // 6)
    check.add('forensics', state.char.skill('forensics') * 2)
    check.add('logic', state.char.attr('logic'))
    if wiper:
        check.add(wiper.name, wiper.rating * 2)
    else:
        check.add('no wiper loaded', -4)
    check.resolve(state.rng)

    before = node.residue
    removed = int(before * (0.75 if check.success else 0.3))
    node.residue = max(0, before - removed)
    _act(sess, 'scrub', node=node, noise_scale=wiper.signature if wiper else 1.0)
    if state.running:
        c.ok(f'Residue on {node.uid}: {before} -> {node.residue}.'
             if check.success else
             f'A partial job. Residue {before} -> {node.residue}.')


# --------------------------------------------------------------------------
# defence
# --------------------------------------------------------------------------


@command('strike', 'Attack a countermeasure directly.',
         group='defence', contexts=('run',), ticks=1, usage='strike [ice]',
         detail='Warfare rank 2. Damage scales on rank and Nerve. Cheaper than '
                'evasion once the thing is already locked on to you.')
def cmd_strike(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('strike'):
        raise CommandError('Strike is Warfare rank 2.')
    target = _pick_ice(state, args.get(0))
    weapon = programs.best(state.char.deck.loaded, 'weapon')

    check = Check(name='strike', resistance=target.rating * 2)
    check.add('warfare', state.char.skill('warfare') * 2)
    check.add('nerve', state.char.attr('nerve'))
    if weapon:
        check.add(weapon.name, weapon.rating * 2)
    else:
        check.add('bare hands', -5)
    check.add('gear', state.char.bonus('ice_damage'))
    check.resolve(state.rng)

    _act(sess, 'strike', noise_scale=weapon.signature if weapon else 1.2)
    if not state.running:
        return
    c.blank()
    if check.success:
        damage = 4 + state.char.skill('warfare') + state.char.bonus('ice_damage')
        if check.critical:
            damage *= 2
        target.damage_taken += damage
        if target.damage_taken >= target.hp:
            target.state = 'dead'
            if target in state.locked:
                state.locked.remove(target)
            c.ok(f'{target.data.name} stops.')
        else:
            pct = 1 - target.damage_taken / target.hp
            c.say(f'[ok]You hurt it.[/] [dim]{target.data.name} at '
                  f'{int(pct * 100)}%.[/]')
            if weapon and weapon.key == 'scalpel' and target in state.locked:
                state.locked.remove(target)
                target.state = 'awake'
                c.say('[ok]The lock breaks.[/]')
    else:
        c.err(f'{target.data.name} is not where you hit.')
        c.say(check.explain())


@command('overload', 'Destroy a countermeasure outright. Once per run.',
         group='defence', contexts=('run',), ticks=1, usage='overload [ice]',
         detail='Warfare rank 4. Kills any non-black construct regardless of '
                'rating, for the largest single trace spike you will see all '
                'session.')
def cmd_overload(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('overload'):
        raise CommandError('Overload is Warfare rank 4.')
    if 'overload' in state.spent:
        raise CommandError('you only get one of those a run')
    target = _pick_ice(state, args.get(0))
    if target.behaviour == 'black':
        raise CommandError('black ICE does not overload. It is not that kind '
                           'of thing.')
    state.spent.add('overload')
    target.state = 'dead'
    if target in state.locked:
        state.locked.remove(target)
    _act(sess, 'overload')
    if state.running:
        c.ok(f'{target.data.name} comes apart.')
        c.warn('Everything on this network now knows the shape of you.')
        state.escalate(1, 'An overload is not subtle.')


@command('observe', 'Sit still and listen. The surveil verb.',
         group='action', contexts=('run',), ticks=2, usage='observe',
         detail='A surveil contract wants residency, not theft. Stand on the '
                'objective node with the alert below red and bank ticks. '
                'Observing is nearly silent, and every other thing you might '
                'do while you are in there is not.')
def cmd_observe(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    kind = (state.contract or {}).get('objective', '')
    if kind != 'surveil':
        raise CommandError('this is not a surveil job. Nobody is paying you '
                           'to sit there.')
    if state.here != state.net.objective_node:
        raise CommandError(f'the job is on {state.net.objective_node}, and '
                           f'you are not standing in it.')
    if state.observed_enough:
        raise CommandError('you already have what they wanted. Get out.')

    _act(sess, 'scrub', noise_scale=0.35, ticks=2)
    if not state.running:
        return
    if state.observed_enough:
        return
    left = max(0, state.SURVEIL_TICKS - state.observed)
    c.ok(f'You hold still and let it come to you. '
         f'[dim]{state.observed}/{state.SURVEIL_TICKS} banked'
         + (f', {left} to go.' if left else '.') + '[/]')


@command('signal', 'Tell the runner you are covering what to do.',
         group='defence', contexts=('run',), usage='signal <hold|move|out>',
         detail='On an escort job you do not control them, you advise them. '
                '`hold` keeps them still and quiet, `move` sends them back to '
                'work, `out` sends them for the door. They will ignore you if '
                'they are hurt enough to have stopped listening.')
def cmd_signal(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    escort = state.escort
    if not escort:
        raise CommandError('you are running this one alone.')
    if escort['state'] == 'dead':
        raise CommandError(f'{escort["name"]} is not going to answer.')
    if escort['state'] == 'out':
        raise CommandError(f'{escort["name"]} is already clear.')

    what = (args.get(0) or '').lower()
    if what.startswith('h'):
        escort['state'] = 'hold'
        c.ok(f'{escort["name"]} stops where they are.')
    elif what.startswith('m'):
        if escort['done']:
            raise CommandError(f'{escort["name"]} has what they came for. '
                               f'There is nothing left to send them at.')
        escort['state'] = 'working'
        c.ok(f'{escort["name"]} moves off toward the job.')
    elif what.startswith('o'):
        escort['state'] = 'leaving'
        c.ok(f'{escort["name"]} turns for the door.')
        if not escort['done']:
            c.warn('They have not finished. Nobody is paying for half of it.')
    else:
        raise CommandError('signal hold|move|out')


@command('daemon', 'Deploy an autonomous process.',
         group='action', contexts=('run',), ticks=1,
         usage='daemon <hold|grind|noise|script> [name|host] [service]',
         detail='Daemonology rank 4. A daemon acts every tick without you. '
                '`hold` keeps a node quiet, `grind` works a service open while '
                'you are elsewhere, `noise` is a diversion loud enough to pull '
                'a Probe off your trail. It has its own signature and it is '
                'not clever. Two of them will get you caught. Two of them will '
                'also get you out with the data.')
def cmd_daemon(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('daemon'):
        raise CommandError('Daemon is Daemonology rank 4.')
    prog = programs.best(state.char.deck.loaded, 'daemon')
    if prog is None:
        raise CommandError('no daemon program loaded')

    limit = 1 + state.char.skill('daemonology') // 3
    if len(state.daemons) >= limit:
        raise CommandError(f'you can hold {limit} daemon'
                           f'{"s" if limit != 1 else ""} at your rank')

    task = (args.get(0) or 'hold').lower()
    if task not in ('hold', 'grind', 'noise', 'script'):
        raise CommandError('daemon hold|grind|noise|script')

    lines: list[str] = []
    if task == 'script':
        if not state.char.has_technique('script'):
            raise CommandError('a scripted daemon needs Daemonology rank 2 as '
                               'well, for the script itself.')
        name = args.get(1)
        if not name:
            raise CommandError('which script? `daemon script <name> [host]`')
        script = sess.scripts.get(name)
        if script is None:
            raise CommandError(f'no script called {name!r}')
        from .. import script as script_mod
        try:
            steps = script.steps
        except script_mod.ScriptError as e:
            raise CommandError(f'{name}: {e}') from None
        usable = [st for st in steps
                  if st.kind == 'stop'
                  or st.command.split()[0].lower() in state.DAEMON_TASKS]
        if not usable:
            raise CommandError(
                f'{name} tells a daemon nothing it can do. A daemon script '
                f'names tasks from: ' + ', '.join(state.DAEMON_TASKS))
        lines = list(script.lines)

    host = args.get(2 if task == 'script' else 1) or state.here
    node = _node(state, host)
    if not node.known:
        raise CommandError(f'{host} has not been found yet')

    arg = ''
    if task == 'grind':
        key = args.get(2)
        if not key:
            raise CommandError('grind which service?')
        if not node.mapped:
            raise CommandError(f'probe {node.uid} first')
        matches = [s for s in node.services
                   if s.key.startswith(key.lower()) and not s.cracked]
        if not matches:
            raise CommandError(f'{node.uid} has no uncracked service '
                               f'matching {key!r}')
        arg = matches[0].key

    uid = f'{prog.key}-{len(state.daemons) + 1}'
    state.daemons.append({
        'uid': uid, 'program': prog.key, 'node': node.uid,
        'task': task, 'arg': arg, 'lines': lines,
        'life': 4 + state.char.skill('daemonology') * 2,
    })
    _act(sess, 'strike', node=node, noise_scale=prog.signature * 0.5)
    if state.running:
        label = f'{task} {args.get(1)}' if task == 'script' else task
        c.ok(f'{uid} is running on [accent]{node.uid}[/]: {label}'
             + (f' {arg}' if arg and task != 'script' else '') + '.')
        if task == 'script':
            c.say('[dim]It re-reads the script every tick and does whatever '
                  'the first passing condition tells it to.[/]')


@command('hotswap', 'Change a deck component mid-run.',
         group='defence', contexts=('run',), ticks=3,
         usage='hotswap <component>',
         detail='Hardware rank 4. Three ticks and a spike of noise to trade '
                'masking for memory, or cooling for speed, once you know what '
                'the network actually is. Legwork guesses; hotswap corrects.')
def cmd_hotswap(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('hotswap'):
        raise CommandError('Hotswap is Hardware rank 4.')
    from ..content import hardware
    query = (args.get(0) or '').lower()
    if not query:
        spares = [hardware.BY_KEY[k].name for k in state.char.library
                  if k in hardware.BY_KEY]
        raise CommandError('swap in what? You are carrying: '
                           + (', '.join(spares) or 'no spare components'))

    key = next((k for k in state.char.library
                if k in hardware.BY_KEY
                and (query == k or query in hardware.BY_KEY[k].name.lower())),
               None)
    if key is None:
        raise CommandError(f'you are not carrying anything called {query!r}')

    comp = hardware.BY_KEY[key]
    old = state.char.deck.parts.get(comp.slot)
    state.char.deck.fit(key)
    state.char.library.remove(key)
    if old:
        state.char.library.append(old)
    _act(sess, 'strike', noise_scale=1.4, ticks=3)
    if state.running:
        c.ok(f'{comp.name} is in. '
             + (f'[dim]{hardware.BY_KEY[old].name} came out.[/]' if old else ''))
        c.info(f'Memory {state.char.deck.memory_used}/'
               f'{state.char.deck.memory}, heat {state.char.deck.heat}/'
               f'{state.char.deck.heat_cap}.')
        if state.char.deck.memory_used > state.char.deck.memory:
            over = state.char.deck.memory_used - state.char.deck.memory
            dropped = []
            while state.char.deck.memory_used > state.char.deck.memory:
                dropped.append(state.char.deck.loaded.pop())
            c.warn(f'{over} memory short. Dropped: '
                   + ', '.join(programs.BY_KEY[d].name for d in dropped
                               if d in programs.BY_KEY))


@command('falsify', 'Plant evidence pointing at somebody else.',
         group='defence', contexts=('run',), ticks=2,
         usage='falsify <faction>',
         detail='Forensics rank 4. Does not reduce your residue. Redirects it, '
                'so the forensics team comes up with a name that is not yours. '
                'The most powerful city-layer verb in the game, because the '
                'faction you name reacts to being named.')
def cmd_falsify(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    has_palimpsest = 'palimpsest' in state.char.deck.loaded
    if not state.char.has_technique('falsify') and not has_palimpsest:
        raise CommandError('Falsify is Forensics rank 4, or a loaded '
                           'Palimpsest.')
    if state.framed:
        raise CommandError(f'you have already dressed this up as '
                           f'{fac_content.BY_KEY[state.framed].short}')
    if not state.residue_total:
        raise CommandError('there is nothing to misattribute yet')

    query = (args.get(0) or '').lower()
    if not query:
        raise CommandError('blame whom? ' + ', '.join(
            k for k in fac_content.FACTION_KEYS if k != state.net.faction))
    key = next((k for k in fac_content.FACTION_KEYS
                if k.startswith(query)
                or query in fac_content.BY_KEY[k].short.lower()), None)
    if key is None:
        raise CommandError(f'no faction called {query!r}')
    if key == state.net.faction:
        raise CommandError('you cannot frame them for robbing themselves')

    other = fac_content.BY_KEY[key]
    check = Check(name='falsify', resistance=10 + state.net.posture // 5)
    check.add('forensics', state.char.skill('forensics') * 2)
    check.add('logic', state.char.attr('logic'))
    wiper = programs.best(state.char.deck.loaded, 'wiper')
    if wiper:
        check.add(wiper.name, wiper.rating * 2)
    else:
        check.add('no wiper loaded', -5)
    rel = fac_content.relation(state.net.faction, key)
    if rel < 0:
        check.add('they already suspect them', int(abs(rel) * 6))
    check.resolve(state.rng)

    _act(sess, 'scrub', noise_scale=wiper.signature if wiper else 1.0,
         ticks=2)
    if not state.running:
        return
    c.blank()
    if check.success:
        state.framed = key
        c.ok(f'The logs now describe {other.short} doing this.')
        c.say('[dim]It will hold up exactly as long as nobody cares enough to '
              'look twice.[/]')
    else:
        c.err('The story does not hang together.')
        c.say(check.explain())
        state.leave_residue(4)


@command('mask', 'Spend a tick making yourself harder to follow.',
         group='defence', contexts=('run',), ticks=1, usage='mask')
def cmd_mask(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    mask = programs.best(state.char.deck.loaded, 'mask')
    if mask is None:
        raise CommandError('no masking program loaded')
    check = Check(name='mask', resistance=10)
    check.add('stealth', state.char.skill('stealth') * 2)
    check.add('reflex', state.char.attr('reflex'))
    check.add(mask.name, mask.rating * 2)
    check.resolve(state.rng)
    reduction = (mask.rating * 2.5 + state.char.skill('stealth') * 1.5)
    if not check.success:
        reduction *= 0.4
    before = state.trace
    state.trace = max(0.0, state.trace - reduction)
    _act(sess, 'mask')
    if state.running:
        c.ok(f'Trace {int(before)} -> {int(state.trace)}.')


@command('nullsig', 'Stop the trace entirely, briefly. Once per run.',
         group='defence', contexts=('run',), usage='nullsig',
         detail='Stealth rank 4. Trace does not advance at all while it holds. '
                'Every action you take inside the window shortens it.')
def cmd_nullsig(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('nullsig'):
        raise CommandError('Nullsig is Stealth rank 4.')
    if 'nullsig' in state.spent:
        raise CommandError('once a run')
    state.spent.add('nullsig')
    state.nullsig = 3 + state.char.skill('stealth')
    c.ok(f'You go quiet. {state.nullsig} points of silence, and no trace at '
         f'all while they last.')
    c.say('[dim]A tick spends one. Acting spends another on top of it, so '
          'the window is twice as long if you spend it holding still.[/]')


@command('overclock', 'Push the deck past its rating.',
         group='defence', contexts=('run',), usage='overclock [steps]',
         detail='Hardware rank 2. Each step is one extra action per tick and '
                'four units of heat. Heat above the cooling budget damages '
                'components and feeds the trace.')
def cmd_overclock(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('overclock'):
        raise CommandError('Overclock is Hardware rank 2.')
    steps = args.int_at(0, 1, 'a number of steps')
    limit = 1 + state.char.skill('hardware') // 2
    if steps < 0 or steps > limit:
        raise CommandError(f'you can hold {limit} step'
                           f'{"s" if limit != 1 else ""} at your Hardware rank')
    state.overclock = steps
    headroom = state.char.deck.heat_headroom
    load = steps * 4
    if steps == 0:
        c.ok('Back to rated speed.')
    elif load <= headroom:
        c.ok(f'{steps} step{"s" if steps != 1 else ""}. '
             f'Heat {load}/{headroom}, within budget.')
    else:
        c.warn(f'{steps} steps. Heat {load}/{headroom}: over budget by '
               f'{load - headroom}. This will cost you.')


@command('focus', 'Spend Focus to retry the last thing that failed.',
         group='defence', contexts=('run',), usage='focus',
         detail='Focus is the precision resource and it does not come back '
                'inside a run.')
def cmd_focus(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if state.focus <= 0:
        raise CommandError('no Focus left')
    state.focus -= 1
    state.trace = max(0.0, state.trace - 4)
    c.ok(f'You take a breath and find the thread again. '
         f'[dim]Focus {state.focus} left.[/]')


# --------------------------------------------------------------------------
# information
# --------------------------------------------------------------------------


@command('status', 'Where you stand.',
         group='info', usage='status')
def cmd_status(sess, args) -> None:
    c = sess.console
    if sess.run is None:
        game = sess.require_game()
        char = game.char
        c.header(char.handle, game.city.when)
        c.kv([('as', f'[accent]{game.alias.name}[/]'),
              ('where', game.city.district.name),
              ('credits', f'[credit]{char.credits:,}c[/]'),
              ('integrity', f'{char.integrity}/{char.integrity_max}'),
              ('deck', f'memory {char.deck.memory_used}/{char.deck.memory}, '
                       f'heat {char.deck.heat}/{char.deck.heat_cap}'),
              ('contract', game.city.current.title if game.city.current
                           else '[dim]none[/]')])
        hot, heat = game.alias.hottest
        if hot:
            from ..content import factions
            c.kv([('heat', f'[heat]{factions.BY_KEY[hot].short} {heat}[/]')])
        if game.debt.owed:
            c.kv([('owed', f'[err]{game.debt.amount:,}c[/] '
                           f'[dim]to {fac_content.BY_KEY[game.debt.lender].short}'
                           f'[/]')])
        return

    state = sess.run
    node = state.node
    c.header(state.here, f'tick {state.tick}')
    c.raw('  ' + c.bar(state.trace_pct, 'trace', 24,
                       f'trace {state.trace_label()}'))
    c.raw('  ' + c.bar(min(1.0, node.noise / 20), 'noise', 24,
                       f'noise {node.noise} here'))
    # How fast it got here, which the bar cannot say. Two runs at 40% are
    # different runs if one of them was at 8% four ticks ago.
    if len(state.trace_history) > 3 and not state.blind_trace:
        history = state.trace_history
        # Scaled to the window rather than to 100, because the bar directly
        # above already says where you are. This row says how you got here,
        # and a shape flattened against a ceiling you are nowhere near says
        # nothing at all. The endpoints are labelled so it cannot mislead.
        spark = ui.sparkline(history, 24, c.caps,
                             lo=min(history), hi=max(history))
        rate = (history[-1] - history[0]) / max(1, len(history) - 1)
        c.raw(f'  [trace]{spark}[/] [dim]{history[0]:.0f} to {history[-1]:.0f} '
              f'over {len(history)} ticks, {rate:+.1f}/tick[/]')
    c.blank()
    when = shifts.phase(state.phase)
    # The job, first, above every number. `status` has always been the screen
    # a player checks when they are unsure, and it answered "how much trouble
    # am I in" without ever answering "what am I doing here", which left the
    # tutorial telling people to read an objective off a screen that did not
    # print one.
    brief = state.brief()
    c.kv([('job', ('[ok]done, get out[/]' if brief.done
                   else f'[accent2]{brief.progress}[/]')
           + f' [dim]{"`job` for the whole of it" if not brief.done else ""}'
             f'[/]')])
    c.kv([
        ('alert', f'[warn]{state.alert}[/] [dim]'
                  f'{ice_content.ALERT_BLURB[state.alert]}[/]'),
        ('shift', f'{when.name.lower()} [dim]trace at '
                  f'{when.trace * 100:.0f}% of nominal[/]'),
        ('zone', f'{node.zone} [dim](tier {node.tier}, you hold '
                 f'{state.tier})[/]'),
        ('integrity', f'{state.char.integrity_max - state.char.hurt - state.hurt}'
                      f'/{state.char.integrity_max}'),
        ('focus', str(state.focus)),
        ('residue', f'[residue]{state.residue_total} across the network[/]'),
        ('haul', f'{len(state.haul)} assets'),
    ])
    kind = (state.contract or {}).get('objective', '')
    if kind == 'surveil':
        c.blank()
        c.raw('  ' + c.bar(min(1.0, state.observed / state.SURVEIL_TICKS),
                           'accent', 24,
                           f'observed {state.observed}/{state.SURVEIL_TICKS}'))
    if state.escort:
        e = state.escort
        role = {'dead': 'err', 'out': 'ok'}.get(e['state'], 'info')
        c.blank()
        c.kv([('escort', f'[{role}]{e["name"]}[/] [dim]on {e["node"]}, '
                         f'{e["state"]}, integrity {max(0, e["integrity"])}'
                         + (', has the goods' if e['done'] else '') + '[/]')])
    if state.daemons:
        c.blank()
        for d in state.daemons:
            c.raw(f'  [accent]{d["uid"]}[/] [dim]{d["task"]} on {d["node"]}, '
                  f'{d["life"]} ticks left[/]')
    if state.locked:
        c.blank()
        for construct in state.locked:
            c.raw(f'  [err]{construct.data.name} is locked on to you.[/]')
    if state.nullsig:
        c.info(f'Nullsig holding, {state.nullsig} ticks.')
    if state.overclock:
        c.info(f'Overclocked {state.overclock} steps.')


@command('job', 'What you are here to do, and the next move.',
         group='info', aliases=('brief',), usage='job',
         detail='The one screen that answers "what am I trying to achieve". '
                'In the city: the contract, the walk to it, and what is still '
                'missing from the deck. In a run: what finishing looks like '
                'for this specific host and record, how far along you are, and '
                'the next thing to type. It costs no time and it is always '
                'safe to ask.')
def cmd_job(sess, args) -> None:
    if sess.run is None:
        from .city import city_job
        city_job(sess)
        return
    state, c = sess.require_run(), sess.console
    brief = state.brief()
    contract = state.contract or {}
    c.header(contract.get('title') or 'Speculative',
             contract.get('objective') or 'no contract')
    c.say(f'[accent2]{brief.aim}[/]')
    if brief.where:
        c.say(f'[dim]{brief.where}[/]')
    c.blank()
    if brief.done:
        c.ok(f'Done: {brief.progress}. Everything from here is spending time '
             f'you have already been paid for.')
    else:
        c.say(f'[dim]Progress: {brief.progress}.[/]')
    if brief.steps:
        c.blank()
        c.say('[dim]Next:[/]')
        for step in brief.steps:
            c.raw(f'  [fg]{step}[/]')
    c.blank()
    c.say(f'[dim]`status` for the numbers. `map` for the shape. '
          f'`odds <action>` for any of the maths.[/]')


@command('odds', 'Show the maths before you commit.',
         group='info', contexts=('run',),
         usage='odds crack <host> <service>',
         detail='D14: no hidden dice. Prints the full sum for an action, '
                'including every modifier, and the exact probability.')
def cmd_odds(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    what = (args.get(0) or '').lower()
    if what in ('crack', ''):
        node, svc = _target_service(state, args, offset=1)
        category = node_content.FAMILIES[svc.family][1]
        for label, program in (
                ('best', programs.best(state.char.deck.loaded, category)),
                ('quietest', programs.quietest(state.char.deck.loaded, category))):
            check = crack_check(state, node, svc, program,
                                quiet=(label == 'quietest'))
            name = program.name if program else 'nothing loaded'
            c.blank()
            c.raw(f'[accent]{label}[/] [dim]({name})[/]  {check.summary()}')
            c.say(check.explain(), indent='  ')
        return
    raise CommandError('odds crack <host> <service>')


@command('log', 'What has happened this run.',
         group='info', contexts=('run',), usage='log [count]')
def cmd_log(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    count = args.int_at(0, 20, 'how many lines')
    if not state.events:
        c.info('Nothing yet.')
        return
    for line in state.events[-count:]:
        c.raw(f'  [dim]{line}[/]')


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def _act(sess, verb: str, node=None, ticks: int | None = None,
         noise_scale: float = 1.0, residue_scale: float = 1.0) -> None:
    """Apply an action's cost. The one place noise, residue, and time meet."""
    state = sess.run
    base_ticks, base_noise, base_residue = COST[verb]
    node = node or state.node
    if noise_scale:
        state.make_noise(base_noise * noise_scale, node)
    if residue_scale and base_residue:
        state.leave_residue(base_residue * residue_scale, node)

    spend = base_ticks if ticks is None else ticks
    if spend and state.free_actions > 0:
        state.free_actions -= 1
        spend = 0

    # Overclocking buys *actions*, which is a credit pool rather than a
    # discount. Every real tick you spend at N steps earns N credits, and each
    # credit pays for one tick of a later action, so "one extra action per
    # tick per step" is literally what happens.
    #
    # The previous version subtracted a flat tick at two steps or more, which
    # made step 1 pure heat for no benefit and made step 2 reduce every
    # one-tick action to zero. At zero ticks `advance` never runs, so the
    # trace stopped, the ICE stopped, and the whole run clock stopped with it.
    if spend and state.overclock and state.oc_credit >= 1.0:
        take = min(int(state.oc_credit), spend)
        state.oc_credit -= take
        spend -= take

    if spend:
        state.advance(spend)
        if state.overclock:
            state.oc_credit += spend * state.overclock
        # Acting inside a Nullsig window costs it an extra point on top of the
        # tick it already spends, which is the "every action shortens it" half
        # of the technique. Applied *after* advance, so the tick you paid for
        # is the tick you were protected during: doing it first meant the last
        # point of the window silently protected nothing.
        if state.nullsig > 0:
            state.nullsig = max(0, state.nullsig - 1)
    _escalation_check(sess)
    # A run can end *inside* advance(): the trace completing, black ICE, the
    # deck dying. If it did, settle up here. Without this the session stays in
    # a finished run, further commands still execute against a dead
    # connection, and none of the consequences ever land.
    if sess.run is not None and not sess.run.running:
        _resolve(sess)


def _escalation_check(sess) -> None:
    state = sess.run
    if state is None or not state.running:
        return
    if state.node.noise >= net_noise_limit(state):
        state.escalate(1, f'{state.here} is making too much noise.')
        state.node.noise = int(state.node.noise * 0.5)


def net_noise_limit(state) -> int:
    from ..run.session import NOISE_ESCALATE
    return NOISE_ESCALATE


def _node(state, uid: str):
    node = state.net.node(uid)
    if node is None:
        raise CommandError(f'no host called {uid!r}')
    return node


def _target_service(state, args, offset: int = 0):
    """Resolve `<host> <service>` with sensible defaults."""
    first = args.get(offset)
    second = args.get(offset + 1)
    if first and second:
        node = _node(state, first)
        key = second
    elif first:
        node = state.node
        key = first
    else:
        raise CommandError('crack what? `crack <host> <service>`')

    if not node.mapped:
        raise CommandError(f'{node.uid} has not been probed. `probe '
                           f'{node.uid}` first.')
    matches = [s for s in node.services if s.key.startswith(key.lower())]
    if not matches:
        have = ', '.join(s.key for s in node.services) or 'nothing'
        raise CommandError(f'{node.uid} runs: {have}')
    if len(matches) > 1:
        raise CommandError('which service: '
                           + ', '.join(s.key for s in matches))
    return node, matches[0]


def _pick_ice(state, query: str | None):
    live = [i for i in state.node.live_ice] + [
        i for i in state.locked if i.alive and i not in state.node.ice]
    if not live:
        raise CommandError('there is nothing here to hit')
    if not query:
        # Default to whatever is actually hurting you.
        return state.locked[0] if state.locked else live[0]
    q = query.lower()
    for construct in live:
        if q in construct.data.name.lower() or q == construct.uid:
            return construct
    raise CommandError(f'nothing here called {query!r}')


def _reveal(state, uid: str, depth: int) -> list[str]:
    """Mark neighbours known, out to `depth` hops. Returns what was new."""
    found: list[str] = []
    frontier = [(uid, 0)]
    seen = {uid}
    while frontier:
        current, dist = frontier.pop(0)
        if dist >= depth:
            continue
        for edge in state.net.nodes[current].edges:
            if edge in seen:
                continue
            seen.add(edge)
            node = state.net.nodes[edge]
            if not node.known:
                node.known = True
                found.append(edge)
            frontier.append((edge, dist + 1))
    return found


def _reveal_topology(state) -> None:
    for node in state.net.nodes.values():
        node.known = True


def _known_hosts(sess) -> list[str]:
    if sess.run is None:
        return []
    return [n.uid for n in sess.run.net.nodes.values() if n.known]


def _show_node(sess, node, detail: bool = False) -> None:
    state, c = sess.run, sess.console
    if state is None:
        # Nothing to describe a host relative to. Every caller guards this
        # too; a display helper that raises when the run has just ended is a
        # traceback in front of somebody who has already had a bad night.
        return
    tail = 'you are here' if node.uid == state.here else ''
    c.header(node.uid, tail)
    look_type = 'workstation' if (node.type == 'honeypot' and node.disguised) \
        else node.type
    c.say(f'[dim]{cyberspace.look(look_type, len(node.uid), state.net.faction)}. '
          f'{node.display_type} in the {node.zone}.[/]')

    if not detail:
        c.say('[dim]Not probed. `probe` to see what it runs.[/]')
        return

    if node.services:
        c.blank()
        rows = []
        for svc in node.services:
            rows.append((svc.key, svc.data.name, svc.family,
                         str(svc.difficulty),
                         '[ok]open[/]' if svc.cracked else '[warn]closed[/]'))
        c.table(('service', 'what', 'family', 'diff', ''), rows,
                roles=('accent', 'dim', 'info', 'warn', None))

    live = [i for i in node.live_ice]
    if live:
        c.blank()
        for construct in live:
            if construct.known:
                c.raw(f'  [ice]{construct.data.name}[/] '
                      f'[dim]rating {construct.rating}, '
                      f'{construct.behaviour}[/]')
                c.say(f'[dim]{construct.data.blurb}[/]', indent='    ',
                      subsequent='    ')
            else:
                c.raw('  [ice]something is running here that you have not '
                      'identified.[/]')

    if node.data:
        c.blank()
        for asset in node.data:
            if asset.taken:
                c.raw(f'  [dim]{asset.name} (gone)[/]')
                continue
            lock = ' [warn]encrypted[/]' if asset.encrypted else ''
            mark = ' [accent2](the job)[/]' if asset.objective else ''
            c.raw(f'  [credit]{asset.name}[/] '
                  f'[dim]{asset.value:,}c[/]{lock}{mark}')

    if node.residue:
        c.blank()
        c.raw(f'  [residue]residue {node.residue}[/] '
              f'[dim]left here by you[/]')


# --------------------------------------------------------------------------
# architecture, signal, sabotage, psyche
# --------------------------------------------------------------------------


@command('chart', 'Read the shape of the segment without touching it.',
         group='recon', contexts=('run',), ticks=1, usage='chart',
         detail='Architecture rank 2. Reveals topology two hops out, edges '
                'included, at a fraction of a scan\'s noise. It is a map, not '
                'an inventory: it will not tell you what is on anything.')
def cmd_chart(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('chart'):
        raise CommandError('Chart is Architecture rank 2.')
    found = _reveal(state, state.here, 2)
    _act(sess, 'scan', noise_scale=0.25)
    if not state.running:
        return
    c.blank()
    if found:
        rows = [(uid, state.net.nodes[uid].display_type,
                 state.net.nodes[uid].zone,
                 str(len(state.net.nodes[uid].edges)))
                for uid in found]
        c.table(('host', 'type', 'zone', 'links'), rows,
                roles=('accent', 'dim', 'info', 'dim'))
    else:
        c.info('Nothing new in the shape of it.')
    c.say('[dim]Structure only. `probe` still tells you what is on anything.[/]')


@command('backdoor', 'Open a route that was not on the map.',
         group='access', contexts=('run',), ticks=2, usage='backdoor <host>',
         detail='Architecture rank 4, once per run. Connects the node you '
                'hold to one two hops away. The counter to a herder, to a '
                'lockdown, and to having come in the wrong way.')
def cmd_backdoor(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('backdoor'):
        raise CommandError('Backdoor is Architecture rank 4.')
    if 'backdoor' in state.spent:
        raise CommandError('you only find one of those a run')
    uid = args.require(0, 'a host to reach')
    node = _node(state, uid)
    if uid == state.here:
        raise CommandError('you are standing in it')
    if uid in state.node.edges:
        raise CommandError(f'{uid} already touches {state.here}')

    # Two hops only: this finds a route that plausibly exists, not one that
    # would have to have been built.
    reachable = set()
    for edge in state.node.edges:
        reachable.update(state.net.nodes[edge].edges)
    if uid not in reachable:
        raise CommandError(f'{uid} is further than two hops. There is no '
                           f'argument for a route that is not there.')

    state.spent.add('backdoor')
    state.node.edges.append(uid)
    node.edges.append(state.here)
    node.known = True
    _act(sess, 'connect', noise_scale=0.4, ticks=2)
    if state.running:
        c.ok(f'There is a route from {state.here} to [accent]{uid}[/]. '
             f'There was always going to be.')


@command('listen', 'Collect passively from where you stand.',
         group='recon', contexts=('run',), ticks=2, usage='listen',
         detail='Signal rank 2. Reveals the data and countermeasures on every '
                'neighbouring node without probing any of them, and makes no '
                'noise at all.')
def cmd_listen(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('listen'):
        raise CommandError('Listen is Signal rank 2.')
    neighbours = [state.net.nodes[e] for e in state.node.edges
                  if e in state.net.nodes]
    _act(sess, 'scrub', noise_scale=0.0, ticks=2)
    if not state.running:
        return
    if not neighbours:
        c.info('Nothing is talking to this node.')
        return
    c.blank()
    for node in neighbours:
        node.known = True
        node.mapped = True
        for construct in node.ice:
            construct.known = True
        marks = []
        live = [i for i in node.live_ice]
        if live:
            marks.append(f'[ice]{", ".join(i.data.name for i in live)}[/]')
        assets = [a for a in node.data if not a.taken]
        if assets:
            marks.append(f'[credit]{len(assets)} assets, '
                         f'{sum(a.value for a in assets):,}c[/]')
        c.raw(f'  [accent]{node.uid:<12}[/] [dim]{node.display_type:<12}[/] '
              + '  '.join(marks or ['[dim]nothing worth the trip[/]']))


@command('intercept', 'Take a credential out of the traffic.',
         group='access', contexts=('run',), ticks=3, usage='intercept',
         detail='Signal rank 4. Three ticks of residency on a node carrying '
                'live traffic buys an access tier without cracking anything. '
                'Silent.')
def cmd_intercept(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('intercept'):
        raise CommandError('Intercept is Signal rank 4.')
    node = state.node
    if not node.open:
        raise CommandError('you cannot read traffic you are not inside')
    if state.tier >= 3:
        raise CommandError('there is nothing above the tier you already hold')

    check = Check(name='intercept', resistance=8 + state.net.posture // 6)
    check.add('signal', state.char.skill('signal') * 2)
    check.add('reflex', state.char.attr('reflex'))
    if node.type in ('auth', 'controller', 'relay'):
        check.add('this node is a junction', 4)
    check.resolve(state.rng)

    _act(sess, 'sidechannel', noise_scale=0.0, ticks=3)
    if not state.running:
        return
    c.blank()
    if check.success:
        state.tier += 1
        c.ok(f'Somebody authenticated while you were listening. Access tier '
             f'{state.tier}.')
    else:
        c.err('Nothing useful went past.')
        c.say(check.explain())


@command('misdirect', 'Make your noise register somewhere else.',
         group='defence', contexts=('run',), ticks=1,
         usage='misdirect <host>',
         detail='Sabotage rank 2. Moves the noise on this node onto another '
                'one. Their countermeasures wake up, and the alert escalates '
                'on their reading rather than yours.')
def cmd_misdirect(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('misdirect'):
        raise CommandError('Misdirect is Sabotage rank 2.')
    uid = args.require(0, 'a host to blame')
    node = _node(state, uid)
    if uid == state.here:
        raise CommandError('that is where the noise already is')
    if not node.known:
        raise CommandError(f'{uid} has not been found yet')

    moved = state.node.noise
    if moved <= 0:
        raise CommandError('you have not made any noise to move')
    state.node.noise = 0
    node.noise += moved
    _act(sess, 'pretext', noise_scale=0.2)
    if state.running:
        c.ok(f'{moved} points of somebody else\'s problem, on '
             f'[accent]{uid}[/].')
        c.say('[dim]Whatever is over there is about to have an opinion.[/]')


@command('collapse', 'Take a node out of the network entirely.',
         group='action', contexts=('run',), ticks=2, usage='collapse',
         detail='Sabotage rank 4, once per run. Destroys the node you are '
                'standing on: data, countermeasures, and routes. Enormously '
                'loud, and it satisfies a wipe contract outright.')
def cmd_collapse(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('collapse'):
        raise CommandError('Collapse is Sabotage rank 4.')
    if 'collapse' in state.spent:
        raise CommandError('once a run')
    node = state.node
    if node.uid == state.net.entry:
        raise CommandError('that is the way out. Think about it.')
    if not args.has('confirm'):
        c.warn(f'This destroys {node.uid} and everything on it, including '
               f'anything you have not already taken.')
        c.say('[dim]`collapse --confirm`.[/]')
        return

    # Leave by a route that still exists. Collapsing the node you are on
    # while standing on it would strand you, which is the one thing the run
    # layer is not allowed to do to a player.
    exits = [e for e in node.edges if e in state.net.nodes]
    if not exits:
        raise CommandError('there is nowhere to go from here afterwards')
    state.spent.add('collapse')
    lost = sum(a.value for a in node.data if not a.taken)
    for asset in node.data:
        asset.taken = True
    for construct in node.ice:
        construct.state = 'dead'
    state.locked = [i for i in state.locked if i not in node.ice]
    state.done['wipe'] = node.uid
    for edge in list(node.edges):
        other = state.net.nodes.get(edge)
        if other and node.uid in other.edges:
            other.edges.remove(node.uid)
    node.edges.clear()
    state.here = exits[0]
    node.edges.append(exits[0])
    state.net.nodes[exits[0]].edges.append(node.uid)

    _act(sess, 'overload', node=state.node)
    if state.running:
        c.blank()
        c.ok(f'{node.uid} is gone.')
        if lost:
            c.say(f'[dim]{lost:,}c of things nobody will ever read went with '
                  f'it.[/]')
        c.say(f'[dim]You are on {state.here}.[/]')
        state.escalate(1, 'A host stopped existing.')


@command('steady', 'Take a breath. Recover Focus.',
         group='defence', contexts=('run',), ticks=2, usage='steady',
         detail='Psyche rank 2. The only thing in the game that restores '
                'Focus once a run has started, and it can shake a lock-on if '
                'your Nerve is up to it. Silent.')
def cmd_steady(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('steady'):
        raise CommandError('Steady is Psyche rank 2.')
    check = Check(name='steady', resistance=10)
    check.add('psyche', state.char.skill('psyche') * 2)
    check.add('nerve', state.char.attr('nerve'))
    check.add('composure', state.char.composure // 2)
    check.resolve(state.rng)

    gained = 1 + state.char.skill('psyche') // 2
    state.focus += gained
    _act(sess, 'scrub', noise_scale=0.0, ticks=2)
    if not state.running:
        return
    c.blank()
    c.ok(f'Focus {state.focus} [dim](+{gained})[/].')
    if check.success and state.locked:
        shaken = state.locked.pop(0)
        shaken.state = 'awake'
        shaken.telegraphed = False
        c.say(f'[ok]{shaken.data.name} loses you.[/]')
    elif state.locked:
        c.say('[dim]It is still on you.[/]')


@command('dissociate', 'Stop being present in what is hurting you.',
         group='defence', contexts=('run',), usage='dissociate',
         detail='Psyche rank 4, once per run. For a few ticks every point of '
                'damage lands on the deck instead of on you, and black ICE '
                'cannot reach you at all. The deck pays for all of it.')
def cmd_dissociate(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    if not state.char.has_technique('dissociate'):
        raise CommandError('Dissociate is Psyche rank 4.')
    if 'dissociate' in state.spent:
        raise CommandError('once a run')
    state.spent.add('dissociate')
    state.dissociated = 2 + state.char.skill('psyche') // 2
    c.ok(f'You put the room somewhere else for {state.dissociated} ticks.')
    c.say('[dim]Everything that reaches you now reaches the deck. Nothing '
          'lethal can find you at all.[/]')


# --------------------------------------------------------------------------
# signature abilities: one per origin, once per run, nobody else can do them
# --------------------------------------------------------------------------


def _signature(sess, key: str):
    """Gate a signature verb on the origin that owns it and on being unspent.

    These are the things that make the choice at creation weigh something, so
    they are deliberately not purchasable, not trainable, and not shareable:
    the only way to have one is to have been that person.
    """
    state = sess.require_run()
    origin = state.char.origin_data
    if origin.signature != key:
        owner = next((o for o in origin_content.ORIGINS
                      if o.signature == key), None)
        raise CommandError(
            f'that is not something you can do. '
            + (f'{owner.name} can.' if owner else ''))
    if f'sig:{key}' in state.spent:
        raise CommandError(f'{origin.signature_name} is once a run.')
    state.spent.add(f'sig:{key}')
    return state


@command('policy', 'You wrote the access policy. Read what a node logs.',
         group='defence', contexts=('run',), ticks=1, usage='policy [host]',
         detail='Corporate defector only, once per run. Tells you what a node '
                'is required to log and when, wipes every trace of you from '
                'it, and reveals anything watching.')
def cmd_policy(sess, args) -> None:
    state = _signature(sess, 'policy')
    c = sess.console
    node = _node(state, args.get(0) or state.here)
    was = node.residue
    node.residue = 0
    node.mapped = True
    for construct in node.ice:
        construct.known = True
    _act(sess, 'scrub', node=node, noise_scale=0.0, ticks=1)
    if not state.running:
        return
    c.blank()
    c.ok(f'You know exactly what {node.uid} keeps, and for how long.')
    c.say(f'[dim]Residue {was} -> 0. Everything running here is now named.[/]')
    if node.type == 'honeypot':
        node.disguised = False
        c.warn('It is not a workstation. It was never a workstation.')


@command('jury', 'Bring a destroyed component back out of nothing.',
         group='defence', contexts=('run',), ticks=2, usage='jury',
         detail='Gutter runner only, once per run. Everybody else has to '
                'leave the run when something dies.')
def cmd_jury(sess, args) -> None:
    state = _signature(sess, 'jury')
    c = sess.console
    dead = [slot for slot, level in state.char.deck.damage.items()
            if level >= 3]
    if not dead:
        state.spent.discard('sig:jury')
        raise CommandError('nothing is dead enough to need it.')
    slot = dead[0]
    state.char.deck.damage[slot] = 1
    comp = state.char.deck.component(slot)
    _act(sess, 'strike', noise_scale=0.6, ticks=2)
    if state.running:
        c.blank()
        c.ok(f'{comp.name if comp else slot} is working again. Not well.')
        c.say('[dim]Solder, opinion, and something you took out of the '
              'antenna housing.[/]')


@command('vouch', 'Spend the Switchboard\'s name instead of a credential.',
         group='access', contexts=('run',), ticks=1, usage='vouch',
         detail='Fixer\'s protege only, once per run. A warden that checks '
                'credentials accepts you outright, no roll.')
def cmd_vouch(sess, args) -> None:
    state = _signature(sess, 'vouch')
    c = sess.console
    wardens = [i for n in state.net.nodes.values() for i in n.live_ice
               if i.data.effects.get('credential_check')]
    if not wardens:
        state.spent.discard('sig:vouch')
        raise CommandError('nothing on this network is the asking kind.')
    for warden in wardens:
        warden.state = 'dead'
    _act(sess, 'pretext', noise_scale=0.2)
    if state.running:
        c.blank()
        c.ok(f'{len(wardens)} boundary'
             f'{"ies" if len(wardens) != 1 else ""} decide you are fine.')
        c.say('[dim]Somebody they trust has said so. Nobody asks who.[/]')


@command('firstprinciples', 'Derive a key rather than breaking one.',
         group='access', contexts=('run',), ticks=2,
         aliases=('derive',), usage='firstprinciples',
         detail='Academic only, once per run. Opens any one encrypted thing '
                'on this node outright, and costs every point of Focus you '
                'have left.')
def cmd_firstprinciples(sess, args) -> None:
    state = _signature(sess, 'firstprinciples')
    c = sess.console
    node = state.node
    crypto = [s for s in node.services if s.family == 'crypto'
              and not s.cracked]
    sealed = [a for a in node.data if a.encrypted and not a.taken]
    if not crypto and not sealed:
        state.spent.discard('sig:firstprinciples')
        raise CommandError('nothing here is sealed.')
    spent_focus = state.focus
    state.focus = 0
    if crypto:
        crypto[0].cracked = True
        node.open = True
        opened = crypto[0].data.name
    else:
        sealed[0].encrypted = False
        opened = sealed[0].name
    _act(sess, 'sidechannel', noise_scale=0.0, ticks=2)
    if state.running:
        c.blank()
        c.ok(f'{opened} opens. You did not break it, you worked it out.')
        c.say(f'[dim]{spent_focus} Focus, all of it, and you will not get any '
              f'back this run.[/]')


@command('playbook', 'Call the response the way the desk would have.',
         group='recon', contexts=('run',), ticks=1, usage='playbook',
         detail='Ex-enforcement only, once per run. Every countermeasure on '
                'the network telegraphs a tick early for the rest of the run, '
                'and you learn what each of them is.')
def cmd_playbook(sess, args) -> None:
    state = _signature(sess, 'playbook')
    c = sess.console
    count = 0
    for node in state.net.nodes.values():
        for construct in node.ice:
            if not construct.known:
                count += 1
            construct.known = True
    state.playbook = True
    _act(sess, 'probe', noise_scale=0.3)
    if state.running:
        c.blank()
        c.ok(f'You call it. {count} construct'
             f'{"s" if count != 1 else ""} you had not identified, named.')
        c.say('[dim]Everything on this network now tells you a full tick '
              'early. You have sat on the other end of this.[/]')


@command('native', 'Stop using the interface.',
         group='defence', contexts=('run',), usage='native',
         detail='Chromed only, once per run. For three ticks the network is a '
                'room: connections cost nothing, you make no noise, and '
                'anything locked on loses you.')
def cmd_native(sess, args) -> None:
    state = _signature(sess, 'native')
    c = sess.console
    state.native = 3
    for construct in state.locked:
        construct.state = 'awake'
        construct.telegraphed = False
    state.locked.clear()
    c.blank()
    c.ok('You stop using it and start being in it.')
    c.say('[dim]Three ticks. Movement is free and silent, and nothing has '
          'hold of you.[/]')


@command('requisition', 'File for resources against a debt you owe.',
         group='prep', contexts=('run',), ticks=1, usage='requisition [program]',
         detail='Indentured only, once per run. A program you do not own '
                'appears in memory for the rest of the run.')
def cmd_requisition(sess, args) -> None:
    state = _signature(sess, 'requisition')
    c = sess.console
    query = (args.get(0) or '').lower()
    pool = [p for p in programs.PROGRAMS
            if p.tier <= 2 and p.key not in state.char.deck.loaded]
    if query:
        pool = [p for p in pool if query in p.name.lower() or query == p.key]
    if not pool:
        state.spent.discard('sig:requisition')
        raise CommandError('nothing available matches that.')
    pick = max(pool, key=lambda p: p.rating)
    state.char.deck.loaded.append(pick.key)
    state.requisitioned = pick.key
    _act(sess, 'pretext', noise_scale=0.4)
    if state.running:
        c.blank()
        c.ok(f'{pick.name} is in memory. The requisition cleared in eleven '
             f'seconds.')
        c.say('[dim]Somebody in procurement will notice this in about six '
              'weeks and it will be somebody else\'s problem.[/]')


@command('remember', 'Remember having done this before.',
         group='defence', contexts=('run',), ticks=1, usage='remember',
         detail='Burnout only, once per run. Retry the check you have just '
                'failed, at full skill and with no situational penalties.')
def cmd_remember(sess, args) -> None:
    state = _signature(sess, 'remember')
    c = sess.console
    if state.last_failure is None:
        state.spent.discard('sig:remember')
        raise CommandError('nothing has just gone wrong.')
    node_uid, svc_key = state.last_failure
    node = state.net.node(node_uid)
    svc = node.service(svc_key) if node else None
    if svc is None or svc.cracked:
        state.spent.discard('sig:remember')
        raise CommandError('that is not still in front of you.')
    svc.cracked = True
    node.open = True
    state.last_failure = None
    _act(sess, 'crack', node=node, noise_scale=0.5)
    if state.running:
        c.blank()
        c.ok(f'{svc.data.name} on {node.uid} opens.')
        c.say('[dim]You have seen this exact thing before, eight years ago, '
              'and your hands remember it even if the rest of you does '
              'not.[/]')


@command('nobody', 'Stop existing for a moment.',
         group='defence', contexts=('run',), ticks=1, usage='nobody',
         detail='Legally dead only, once per run. The trace resets to zero: '
                'it has nowhere to attach and has to start again from what it '
                'can find, which is nothing.')
def cmd_nobody(sess, args) -> None:
    state = _signature(sess, 'nobody')
    c = sess.console
    was = int(state.trace)
    state.trace = 0.0
    _act(sess, 'mask', noise_scale=0.0)
    if state.running:
        c.blank()
        c.ok(f'Trace {was} -> 0.')
        c.say('[dim]There is no record to hang it on. Somebody at the far end '
              'is looking at a name that has a death certificate against it '
              'and starting again.[/]')


@command('backway', 'Take a route you already knew about.',
         group='access', contexts=('run',), ticks=1, usage='backway <host>',
         detail='Courier only, once per run. Move to any node you have seen, '
                'from anywhere, in one tick and in silence.')
def cmd_backway(sess, args) -> None:
    state = _signature(sess, 'backway')
    c = sess.console
    uid = args.get(0)
    if not uid:
        state.spent.discard('sig:backway')
        raise CommandError('to where? `backway <host>`')
    node = _node(state, uid)
    if not node.known:
        state.spent.discard('sig:backway')
        raise CommandError(f'you have not seen {uid} yet.')
    node.open = True
    state.here = uid
    _act(sess, 'connect', node=node, noise_scale=0.0)
    if state.running:
        c.blank()
        c.ok(f'You are on [accent]{uid}[/].')
        c.say('[dim]There is always a way through that is not on the plan, '
              'and you have spent nine years learning which.[/]')
        state.check_traps(node)
