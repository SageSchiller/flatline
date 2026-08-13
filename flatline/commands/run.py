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

from ..content import factions as fac_content
from ..content import ice as ice_content
from ..content import nodes as node_content
from ..content import programs
from ..run import network as net_mod
from ..run.checks import Check
from ..run.session import RunState, crack_check
from ..shell import CommandError, command
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
        raise CommandError(
            f'the job is in {districts.BY_KEY[contract.district].name}. '
            f'`travel {contract.district}`.')

    need = OBJECTIVE_PROGRAM.get(contract.objective)
    if need and not game.char.deck.has_category(need) and not args.has('force'):
        raise CommandError(
            f'a {contract.objective} contract needs a {need} program loaded '
            f'and you have none. `load` one, or `jack in --force` to go in '
            f'anyway.')

    stream = game.rng.fork('network', contract.cid)
    net = net_mod.generate(stream, contract.target, int(contract.posture),
                           contract.objective, contract.size_mod)
    state = RunState.begin(net, game.char, game.rng('combat'), c,
                           contract=contract.to_dict())

    if 'credential' in contract.intel:
        state.tier = max(state.tier, 1)
    sess.run = state

    c.blank()
    c.rule('connected')
    c.say(f'[dim]Target: [/][err]{contract.target_data.name}[/][dim], posture '
          f'{int(contract.posture)}. Objective: {contract.objective}.[/]')
    c.say(f'[dim]You are on [/][accent]{net.entry}[/][dim], a '
          f'{net.node(net.entry).display_type}.[/]')
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
    c.blank()
    c.say('[dim]`scan` to look around. `status` for where you stand. '
          '`jack out` to leave.[/]')


@command('jack out', 'Leave the run and settle up.',
         group='defence', contexts=('run',), ticks=1, usage='jack out')
def cmd_jack_out(sess, args) -> None:
    state = sess.require_run()
    c = sess.console
    _act(sess, 'jack out')
    if state.running:
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
        'clean': '[ok]You are out.[/]',
        'burned': '[warn]You are out, without what you came for.[/]',
        'severed': '[err]They cut you loose.[/]',
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
        c.say('[err]The Coffin held long enough. Somebody will find the deck '
              'still warm and the chair still occupied.[/]')
        c.say(f'[dim]{game.char.handle} ran {game.char.runs} times.[/]')
        sess.autosave()
        return

    for line in game.city.apply_run(game.alias, summary, game.rng):
        c.say(line)

    contract = game.city.current
    if contract is not None:
        pay, told = game.city.pay_out(game.alias, contract, summary,
                                      game.char.mult('pay_mult'))
        game.char.credits += pay
        game.earned += pay
        for line in told:
            c.say(line)
        if summary.get('objective'):
            game.city.board = [x for x in game.city.board
                               if x.cid != contract.cid]
            game.city.accepted = ''

    # Selling the haul is a city action, but crediting it here keeps the run
    # readable: what you carried out is worth what it is worth.
    extra = sum(v for v in [summary['haul_value']] if v)
    if extra:
        take = int(extra * 0.5)
        game.char.credits += take
        game.earned += take
        c.say(f'[credit]{take:,}c[/] for the rest of the haul.')

    gained = 2 + summary['ticks'] // 12 + (2 if summary.get('objective') else 0)
    game.char.xp += gained
    c.say(f'[dim]{gained} experience.[/]')

    from ..commands.city import _advance
    _advance(sess, 1)


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
    _show_node(sess, node, detail=True)


@command('map', 'Everything you have learned so far.',
         group='recon', contexts=('run',), usage='map')
def cmd_map(sess, args) -> None:
    state, c = sess.require_run(), sess.console
    known = [n for n in state.net.nodes.values() if n.known]
    c.header('Known hosts', f'{len(known)} of {len(state.net.nodes)}')
    for zone in node_content.ZONES:
        group = [n for n in known if n.zone == zone]
        if not group:
            continue
        c.blank()
        c.raw(f'[info]{zone}[/] [dim]{node_content.ZONE_BLURB[zone]}[/]')
        for node in group:
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
            tail = '  '.join(marks)
            c.raw(f'  [accent]{node.uid:<12}[/] [dim]{node.display_type:<12}[/] '
                  f'{tail}')


@command('here', 'What is in front of you right now.',
         group='recon', contexts=('run',), aliases=('look',), usage='here')
def cmd_here(sess, args) -> None:
    state = sess.require_run()
    _show_node(sess, state.node, detail=state.node.mapped)


# --------------------------------------------------------------------------
# access
# --------------------------------------------------------------------------


@command('connect', 'Move to an adjacent node you have opened.',
         group='access', contexts=('run',), aliases=('cd',), ticks=1,
         usage='connect <host> [--ghost]',
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
        raise CommandError(
            f'{wardens[0].data.name} holds {uid}. Break it, or get past it '
            f'with credentials.')

    ghost = args.has('ghost')
    if ghost and not state.char.has_technique('ghost'):
        raise CommandError('you have not learned to ghost. Stealth rank 2.')

    state.here = uid
    _act(sess, 'connect', node=node,
         noise_scale=0.0 if ghost else 1.0,
         ticks=2 if ghost else 1)
    if state.running:
        state.check_traps(node)
    if state.running:
        c.blank()
        _show_node(sess, node, detail=node.mapped)


@command('crack', 'Break a service open.',
         group='access', contexts=('run',), ticks=1,
         usage='crack <host> <service> [--quiet] [--key]',
         detail='Uses your best loaded breaker. `--quiet` swaps to the '
                'lowest-signature one and takes a penalty. `--key` uses the '
                'Keygrind technique: Focus instead of ticks, and no noise.')
def cmd_crack(sess, args) -> None:
    state, c = sess.require_run(), sess.console
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
        c.say(check.explain())
        culprit = check.culprit()
        if culprit and culprit.value < 0:
            c.say(f'[dim]What sank it: {culprit.label}.[/]')
        if check.fumble:
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


@command('daemon', 'Deploy an autonomous process.',
         group='action', contexts=('run',), ticks=1,
         usage='daemon <hold|grind|noise> [host] [service]',
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
    if task not in ('hold', 'grind', 'noise'):
        raise CommandError('daemon hold|grind|noise')

    host = args.get(1) or state.here
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
        'task': task, 'arg': arg,
        'life': 4 + state.char.skill('daemonology') * 2,
    })
    _act(sess, 'strike', node=node, noise_scale=prog.signature * 0.5)
    if state.running:
        c.ok(f'{uid} is running on [accent]{node.uid}[/]: {task}'
             + (f' {arg}' if arg else '') + '.')


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
    c.ok(f'You go quiet. {state.nullsig} ticks with no trace at all.')


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
        return

    state = sess.run
    node = state.node
    c.header(state.here, f'tick {state.tick}')
    c.raw('  ' + c.bar(state.trace_pct, 'trace', 24,
                       f'trace {state.trace_label()}'))
    c.raw('  ' + c.bar(min(1.0, node.noise / 20), 'noise', 24,
                       f'noise {node.noise} here'))
    c.blank()
    c.kv([
        ('alert', f'[warn]{state.alert}[/] [dim]'
                  f'{ice_content.ALERT_BLURB[state.alert]}[/]'),
        ('zone', f'{node.zone} [dim](tier {node.tier}, you hold '
                 f'{state.tier})[/]'),
        ('integrity', f'{state.char.integrity_max - state.char.hurt - state.hurt}'
                      f'/{state.char.integrity_max}'),
        ('focus', str(state.focus)),
        ('residue', f'[residue]{state.residue_total} across the network[/]'),
        ('haul', f'{len(state.haul)} assets'),
    ])
    if state.locked:
        c.blank()
        for construct in state.locked:
            c.raw(f'  [err]{construct.data.name} is locked on to you.[/]')
    if state.nullsig:
        c.info(f'Nullsig holding, {state.nullsig} ticks.')
    if state.overclock:
        c.info(f'Overclocked {state.overclock} steps.')


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
    if state.overclock:
        # Overclocking buys actions, which is modelled as ticks costing less.
        spend = max(0, spend - (1 if state.overclock >= 2 else 0))
    if state.nullsig > 0:
        state.nullsig = max(0, state.nullsig - 1)
    if spend:
        state.advance(spend)
    _escalation_check(sess)


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
    tail = 'you are here' if node.uid == state.here else ''
    c.header(node.uid, tail)
    c.say(f'[dim]{node.display_type} in the {node.zone}. '
          f'{node_content.ZONE_BLURB[node.zone]}[/]')

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
