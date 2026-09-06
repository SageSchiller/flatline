"""Commands for the people in this city, and the threads they carry.

`look` is the discovery verb: it is the only way to find out who is standing
in the district you are in. Everything else follows from having met somebody.

Story scenes surface through `_check_story`, which runs whenever the world
moves. It never interrupts a run: being handed a scene about a dying friend
halfway through a vault would be the wrong moment for both of them.
"""

from __future__ import annotations

from ..content import factions
from ..content import npcs as npc_content
from ..content import offers
from ..content import threads as thread_content
from ..content import appearance
from ..content import districts
from ..content import shifts
from ..content import spots
from ..shell import CommandError, command
from ..world import story as story_mod


@command('look', 'Look at where you are.',
         group='city', aliases=('around',), usage='look',
         detail='In the city, this is how you find the people in it: who you '
                'run into depends on where you are, what you can get into '
                'there, and in some cases on what you have already done. '
                'Inside a run it shows you the node you are standing in.')
def cmd_look(sess, args) -> None:
    if sess.run is not None:
        # One verb that always means "look at where I am".
        from .run import cmd_here
        cmd_here(sess, args)
        return
    game, c = sess.require_game(), sess.console
    here = story_mod.present(game, game.story)
    district = game.city.district
    when = shifts.phase(game.city.phase)

    c.header(district.name, game.city.when)
    # Where you are, not just who is standing in it. `travel` prints the
    # district once on arrival and then never again, so a player who has been
    # somewhere for six shifts had nothing to look at.
    c.say(f'[dim]{district.blurb}[/]')
    if district.scale:
        # How big it is, in the terms the place itself uses (D67). The city
        # is supposed to be more than you can hold, and a district that
        # never says how many people are in it is one street with a name.
        c.say(f'[dim]{district.scale}[/]')
    c.blank()
    # This district at this hour, when somebody wrote it; the city-wide
    # shift scene otherwise (D53). Then who is in the street (D58).
    c.say(districts.scene(district.key, game.city.phase) or when.scene)
    street = districts.street_line(district.key, game.city.shift)
    if street:
        c.blank()
        c.say(f'[dim]{street}[/]')
    if district.quarters:
        c.blank()
        c.say(f'[dim]Quarters: {", ".join(district.quarters)}. '
              f'`district` for what the place is and what it does.[/]')

    # What the clock is doing to you, in the two places it is doing it.
    parts = []
    if when.danger != 1.0:
        parts.append(f'street {"busier" if when.danger > 1 else "quieter"}')
    if when.trace != 1.0:
        parts.append(f'trace {"faster" if when.trace > 1 else "slower"} in '
                     f'there')
    if when.price != 1.0:
        parts.append(f'prices up {(when.price - 1) * 100:.0f}%')
    if parts:
        c.blank()
        c.info(f'{", ".join(parts)}. [dim]{when.why}[/]')

    # What you have done to this place, standing in it. The city has always
    # remembered in the numbers; this is the first time it says so out here.
    posture = game.city.posture.get(district.controller, 0.0)
    watchers = (district.controller, *district.presence)
    attention = max((game.alias.attention(k) for k in watchers), default=0)
    for line in districts.mood(district, posture, attention):
        c.blank()
        c.say(f'[dim]{line}[/]')

    from .city import here_you_can
    here_you_can(sess, district, looking=True)
    _places_line(sess, district)

    # Who keeps other hours. Only people you have met, because "somebody you
    # have never seen is not here" is not information, and only the ones who
    # are away because of the clock rather than because of anything else.
    away = [n for n in story_mod.present(game, game.story, any_hour=True)
            if n not in here and n.key in game.story.met]

    # And the ones you have not met who keep other hours (D91): "nobody
    # here is interested in you" at night in the Vertical, with two people
    # who work mornings, read as an empty district.
    later = [n for n in story_mod.present(game, game.story, any_hour=True)
             if n not in here and n.key not in game.story.met]
    c.blank()
    if not here:
        c.say('[dim]Nobody here is interested in you, which in this district '
              'is a mercy.[/]')
        _away_line(sess, away)
        _later_line(sess, later)
        return
    c.rule(f'{len(here)} worth talking to')

    for npc in here:
        c.blank()
        if not introduce(sess, npc):
            c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
    c.blank()
    c.say('[dim]`talk <name>` to say something. `ask <name> <topic>` if you '
          'want something specific.[/]')
    _away_line(sess, away)
    _later_line(sess, later)
    _check_story(sess)


@command('people', 'Everybody you have met, where they keep, and how many '
                   'you have not.',
         group='info', contexts=('city',), usage='people',
         detail='D90. The map says twenty-nine people are worth finding and '
                'nothing listed them. This is the ones you have met, with '
                'the district they keep to and their hours, and a count of '
                'the rest by district, because the story in this city is '
                'gated on meeting people and a list of who is left is the '
                'honest answer to "where next". `who` is the other runners; '
                'this is everybody else.')
def cmd_people(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    met = [n for n in npc_content.NPCS if n.key in game.story.met]
    unmet = [n for n in npc_content.NPCS if n.key not in game.story.met]
    c.header('People', f'{len(met)} met, {len(unmet)} not')
    if met:
        rows = []
        flags = game.story.flags
        for n in sorted(met, key=lambda n: (n.where or '~', n.name)):
            where = (districts.BY_KEY[n.where].name if n.where in districts.BY_KEY
                     else 'moves around')
            # What is left to ask them (D164): the list used to be the same
            # whether you had asked everything or nothing.
            left = sum(1 for t in n.topics if f'asked:{n.key}:{t}' not in flags)
            rows.append((n.name, n.epithet, where, npc_content.hours_label(n),
                         f'{left} to ask' if left else 'asked out'))
        c.table(('name', 'who', 'keeps to', 'hours', 'topics'), rows,
                roles=('accent', 'dim', 'info', 'dim', 'dim'))
    else:
        c.say('[dim]Nobody yet. `look` around wherever you are.[/]')
    # The rest, counted by district and never named: meeting them is the
    # point, and a name in a list is not a meeting.
    by_district: dict[str, int] = {}
    for n in unmet:
        by_district[n.where or ''] = by_district.get(n.where or '', 0) + 1
    if by_district:
        parts = []
        for key, count in sorted(by_district.items(),
                                 key=lambda kv: (-kv[1], kv[0])):
            name = (districts.BY_KEY[key].name if key in districts.BY_KEY
                    else 'moving around, somewhere')
            parts.append(f'{count} in {name}' if key else
                         f'{count} {name}')
        c.blank()
        c.say('[dim]Not met yet: ' + ', '.join(parts)
              + '. Some keep hours and some want something of you first: '
                '`look` when you are there.[/]', subsequent='  ')


def introduce(sess, npc) -> bool:
    """The first meeting, if this is one. True when it was.

    Shared by `look`, which introduces everybody in the street at once,
    and by `talk` and `ask`, which used to refuse anybody `look` had not
    already introduced: "you have not met them" about somebody standing
    in front of you, every arrival and every shift (D86).
    """
    game, c = sess.game, sess.console
    if not game.story.meet(npc.key, game.city.shift):
        return False
    c.raw(f'[accent2][bold]{npc.name}[/][/]  [dim]{npc.epithet}[/]')
    c.say(npc.first)
    _noticed(sess)
    return True


def _later_line(sess, later) -> None:
    """How many strangers keep other hours here, and which hours."""
    if not later:
        return
    c = sess.console
    hours = sorted({npc_content.hours_label(n) for n in later})
    c.say(f'[dim]{len(later)} {"person" if len(later) == 1 else "people"} '
          f'you have not met keep{"s" if len(later) == 1 else ""} other '
          f'hours here: {", ".join(hours)}.[/]', subsequent='  ')


def handle(npc) -> str:
    """A word a player can type for somebody, for a hint. The key leaked
    once (`ask kestrel_kid <topic>`) about somebody called Sparrow."""
    for word in npc.name.lower().replace('.', '').split():
        if word in ('the', 'a', 'mr', 'mrs', 'ms', 'dr', 'doctor',
                    'councillor', 'in', 'of', 'who'):
            continue
        if _match(word) is npc:
            return word
    return npc.key


def _away_line(sess, away) -> None:
    """Who keeps other hours, and which. One line, so the clock is a reason
    to come back rather than a door that was shut without saying so."""
    if not away:
        return
    c = sess.console
    c.blank()
    c.say('[dim]Not about at this hour: ' + ', '.join(
        f'{n.name} ({npc_content.hours_label(n)})' for n in away) + '.[/]',
          subsequent='  ')


def _noticed(sess) -> None:
    """What the person in front of you does about how you look.

    Occasional rather than every time, and only for the genuinely striking,
    because a city that remarks on you constantly is a city of very rude
    people. This is what stops `memorable` being a number the sheet prints
    and nothing else: a stranger's eyes going to the same place every time is
    the evidence for the claim.
    """
    game = sess.game
    said = appearance.remark(game.rng('events'), game.char.look,
                             game.char.marks, game.char.memorable)
    if said:
        sess.console.blank()
        sess.console.say(f'[dim]{said}[/]')


def _places_line(sess, district) -> None:
    """The places you can go and stand in, one line, typeable."""
    c = sess.console
    places = spots.in_district(district.key)
    if not places:
        return
    sess.remember('spots', [s.key for s in places])
    bullet = c.caps.g('bullet')
    c.say('[dim]Places:[/] ' + f' [dim]{bullet}[/] '.join(
        f'[fg]{s.name}[/]' for s in places)
          + ' [dim](`visit <place>`, which costs nothing)[/]', subsequent='  ')


def give_item(game, key: str) -> tuple[str, bool]:
    """Put a catalogue thing in the right place (D63 e): programs, chrome
    and components in the bag, a drug in the stash. Returns (name, unique).
    One function, because a decision and a place both hand things over and
    a drug that went into the bag as a program was the bug waiting."""
    from ..content import cyberware, drugs, hardware, programs
    if key in drugs.BY_KEY:
        game.char.stash[key] = game.char.stash.get(key, 0) + 1
        item = drugs.BY_KEY[key]
        return item.name, bool(getattr(item, 'unique', False))
    game.char.library.append(key)
    item = next((table.BY_KEY[key] for table in (programs, cyberware, hardware)
                 if key in table.BY_KEY), None)
    if item is None:
        return key, False
    return item.name, bool(getattr(item, 'unique', False))


def _finds(sess, spot) -> None:
    """What is here to be found, now, for you (D63 e). Once each, ever."""
    game, c = sess.game, sess.console
    story = game.story
    here = spots.available(spot, game.city.phase,
                           lambda rule: story.satisfied(rule, game), story.flags)
    for find in here:
        story.flags.add(f'found:{find.item}')
        name, _ = give_item(game, find.item)
        c.blank()
        c.rule('something here is yours', role='accent2')
        c.say(find.text)
        c.blank()
        c.say(f'[accent2][bold]{name}[/][/] [dim]is in the bag. There is one '
              f'of it. `inspect {find.item}` for what it is and where it '
              f'came from.[/]')
        game.city.news.append(f'[accent2]{name}:[/] found at {spot.name}.')
        sess.record_progress()


def _sense(sess, spot) -> None:
    """Standing where a one-of-a-kind thing is makes you aware of it
    (D148), even when you cannot take it yet: wrong hour, or the person
    who hands it over is not here. It goes on the `rumours` board so the
    walking is a hunt you can see, not a line you had to catch."""
    game, c = sess.game, sess.console
    story = game.story
    for find in spot.finds:
        if f'found:{find.item}' in story.flags:
            continue
        if f'heard:{find.item}' in story.flags:
            continue
        lead = [r for r in find.requires if not r.startswith('met:')]
        if not all(story.satisfied(rule, game) for rule in lead):
            continue
        story.flags.add(f'heard:{find.item}')
        c.blank()
        c.say('[dim]There is something to this place you have not '
              'worked out. `rumours` keeps what you have heard.[/]')
        return


def _find_name(key: str) -> str:
    from ..content import cyberware, drugs, hardware, programs, weapons
    for table in (programs.BY_KEY, cyberware.BY_KEY, hardware.BY_KEY,
                  drugs.BY_KEY, weapons.BY_KEY):
        if key in table:
            return table[key].name
    return key


@command('rumours', 'The one-of-a-kind things: what you have found, and what you have heard of.',
         group='info', contexts=('city',), aliases=('rumors', 'legends'),
         usage='rumours',
         detail=(
                'The city keeps things back for the people who go and '
                'look (D148): one of a kind, at a place, at an hour, once the '
                'right thing is true. This is the hunt made visible: the ones '
                'you have found, and the ones you have heard of and not yet '
                'found, with where and when. The ones you have not heard of '
                'are not here, because hearing of them is the first half of '
                'finding them. Stand where nothing is, and ask the people who '
                'keep hours there.'))
def cmd_rumours(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    story = game.story
    found = [f for f in spots.FINDS if f'found:{f.item}' in story.flags]
    heard = [f for f in spots.FINDS
             if f'heard:{f.item}' in story.flags
             and f'found:{f.item}' not in story.flags]
    unheard = len(spots.FINDS) - len(found) - len(heard)
    c.header('Rumours', f'{len(found)} of {len(spots.FINDS)} found')
    if found:
        c.blank()
        c.rule('found', role='ok')
        for f in found:
            sp = spots.spot_of(f)
            c.raw(f'  [ok]{c.caps.g("check")}[/] [fg]{_find_name(f.item)}[/] '
                  f'[dim]{sp.name}, {districts.BY_KEY[sp.district].name}[/]')
    if heard:
        c.blank()
        c.rule('heard, not yet found', role='accent2')
        for f in heard:
            sp = spots.spot_of(f)
            where = f'{sp.name}, {districts.BY_KEY[sp.district].name}'
            when = ''
            if f.hours:
                when = ', ' + ' or '.join(f.hours)
            need = ''
            unmet = [r[4:] for r in f.requires if r.startswith('met:')
                     and not story.satisfied(r, game)]
            if unmet:
                npc = npc_content.BY_KEY.get(unmet[0])
                if npc is not None:
                    need = f'  [dim]somebody {npc.epithet} would know[/]'
            c.raw(f'  [accent2]·[/] [dim]{f.rumour}[/]')
            c.raw(f'      [dim]{where}{when}[/]{need}')
    if not found and not heard:
        c.blank()
        c.say('[dim]Nothing yet. The city keeps things back for the '
              'people who go and look. Stand in the places that are not '
              'on the way to anywhere, and ask whoever keeps hours '
              'there.[/]')
    elif unheard:
        c.blank()
        c.say(f'[dim]And {unheard} other{"s" if unheard != 1 else ""} you have '
              f'not heard of yet.[/]')


@command('visit', 'Go and stand somewhere in this district.',
         group='city', contexts=('city',), aliases=('enter', 'goto'),
         usage='visit [place|row number]',
         blocked='The places are out there, and so, for the moment, is the '
                 'rest of you.',
         detail='A district has two or three places in it that a person '
                'would actually go and stand: the noodle bar, the west gate, '
                'the crate outside the clinic. `look` lists them. Visiting '
                'one costs nothing, because it is inside the district you are '
                'already in; it shows you the place as it is at this hour, '
                'and whoever is usually there if they are there now. The '
                'people are the same people and the verbs are the same verbs: '
                'this is texture, and texture is most of what makes somewhere '
                'feel like it goes on when you are not looking.',
         complete=lambda sess, prefix: [
             s.key for s in spots.in_district(sess.game.city.where)
         ] if sess.game else [])
def cmd_visit(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    district = game.city.district
    places = spots.in_district(district.key)
    if not places:
        raise CommandError('nowhere in particular to stand here. `look` for '
                           'who is about.')
    if not len(args):
        stood = [sp for sp in places if f'visited:{sp.key}' in game.story.flags]
        c.header(district.name, f'{len(places)} places, {len(stood)} stood in')
        sess.remember('spots', [s.key for s in places])
        here = {n.key for n in story_mod.present(game, game.story)}
        for n, spot in enumerate(places, 1):
            who = [npc_content.BY_KEY[k].name for k in spot.who
                   if k in npc_content.BY_KEY and k in here]
            tail = f'  [dim]{", ".join(who)}[/]' if who else ''
            # Where you have stood, marked (D164): an explorer reads the
            # list for what is left, and the list used to keep that to itself.
            mark = (f'[ok]{c.caps.g("check")}[/]' if f'visited:{spot.key}' in game.story.flags
                    else '[dim]·[/]')
            c.raw(f'  [accent]{n}[/] {mark} [fg]{spot.name}[/]{tail}')
        c.blank()
        c.say('[dim]`visit <place>` or `visit <row number>`. It costs '
              'nothing.[/]')
        return

    token = sess.pick('spots', args.rest().lower(),
                      fallback=[s.key for s in places], what='place',
                      again='visit')
    spot = spots.find(district.key, token)
    if spot is None:
        raise CommandError(f'nowhere called {args.rest()!r} here. `visit` '
                           f'lists the places.')
    c.header(spot.name, district.name)
    c.say(spots.scene_for(spot, game.city.phase))
    # Standing somewhere is a thing a scene can wait for (D91).
    game.story.flags.add(f'visited:{spot.key}')
    _sense(sess, spot)
    here = {n.key for n in story_mod.present(game, game.story)}
    for key in spot.who:
        npc = npc_content.BY_KEY.get(key)
        if npc is None:
            continue
        c.blank()
        if key in here:
            if not introduce(sess, npc):
                c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
                c.say(f'[dim]Here, as usual. `talk {npc.key}`.[/]')
        elif not npc_content.about_now(npc, game.city.phase):
            c.say(f'[dim]{npc.name} is not here at this hour. '
                  f'{npc_content.hours_label(npc).capitalize()}.[/]')
        elif not npc_content.meets(npc, game.char, game.alias,
                                   game.char.runs):
            # Their hour, and still not here: they have not heard of you
            # yet. "Not here at the moment" in the afternoon after "not
            # here at this hour, afternoons" read as the place lying (D90).
            c.say(f'[dim]{npc.name} is not here for you yet. People like '
                  f'{npc.name} turn up once there is a name to turn up '
                  f'for.[/]')
        else:
            c.say(f'[dim]{npc.name} is not here at the moment.[/]')
    _finds(sess, spot)
    _check_story(sess)


@command('district', 'What this place is, what it is made of, what it does.',
         group='info', contexts=('city',), aliases=('here', 'place'),
         usage='district [name]',
         detail='D67. The long read on a district: how big it is, what it is '
                'built out of, what the people in it do for money, the '
                'quarters it is made of, who holds it and who else has '
                'people here, and what is past its edge. `look` is what is '
                'in front of you this hour; this is the place itself. Any '
                'district by name, from anywhere, because knowing what the '
                'Row is before you walk into it is the whole of preparation.')
def cmd_district(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    key = game.city.where
    if len(args):
        want = args.rest().lower().strip()
        # Exact first, then the start of a name, then anywhere in one:
        # `row` is Meridian Row and not Marrow, which contains it.
        exact = [d for d in districts.DISTRICTS
                 if want == d.key or want == d.name.lower()]
        starts = [d for d in districts.DISTRICTS
                  if d.name.lower().startswith(want)
                  or d.name.lower().removeprefix('the ').startswith(want)
                  or d.key.startswith(want)]
        loose = [d for d in districts.DISTRICTS if want in d.name.lower()]
        found = exact or starts or loose
        if len(found) != 1:
            raise CommandError('which district? '
                               + ', '.join(d.key for d in districts.DISTRICTS))
        key = found[0].key
    d = districts.BY_KEY[key]
    here = key == game.city.where
    hops = game.city.shifts_to(key)
    c.header(d.name, 'you are here' if here
             else f'{hops} shift{"s" if hops != 1 else ""} away')
    c.say(d.blurb)
    c.blank()
    if d.scale:
        c.say(d.scale)
        c.blank()
    if d.built:
        c.rule('what it is made of')
        c.say(d.built)
        c.blank()
    if d.works:
        c.rule('what it does')
        c.say(d.works)
        c.blank()
    if d.quarters:
        c.rule('quarters')
        c.say(', '.join(d.quarters) + '.')
        c.blank()
    if d.beyond:
        c.rule('past the edge')
        c.say(d.beyond)
        c.blank()
    holder = factions.BY_KEY[d.controller]
    rows = [('held by', f'{holder.name} [dim]{holder.doctrine.split(".")[0]}[/]')]
    if d.presence:
        rows.append(('also here', ', '.join(factions.BY_KEY[k].short
                                            for k in d.presence)))
    rows.append(('services', ', '.join(d.services) or 'nothing you can use'))
    rows.append(('market', f'tier {d.max_tier} and below, prices '
                           f'{"up" if d.price_mult > 1 else "down"} '
                           f'{abs(d.price_mult - 1) * 100:.0f}%'))
    rows.append(('security', str(d.security)))
    places = spots.in_district(key)
    if places:
        rows.append(('places', ', '.join(s.name for s in places)))
    neighbours = ', '.join(districts.BY_KEY[n].name for n in d.neighbours)
    rows.append(('next to', neighbours))
    c.kv(rows)
    if not here:
        c.blank()
        c.say(f'[dim]`{game.city.walk_to(key)}` to go.[/]')


@command('news', 'What the city did while you were not looking.',
         group='info', contexts=('city',), aliases=('wire',),
         usage='news [count]',
         blocked='The wire is out there. In here there is only the trace.',
         detail='The city keeps a scrollback of what it did: who took what '
                'off the board, who posted a number against your name, who '
                'died on whose job, what expired, what you sold. Most of it '
                'printed once as it happened and scrolled away. This is where '
                'it went. It costs nothing.')
def cmd_news(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    count = args.int_at(0, 12, 'how many lines')
    lines = game.city.news[-max(1, count):]
    c.header('The wire', game.city.when)
    if not lines:
        c.say('[dim]Nothing has happened that anybody wrote down. Give it a '
              'shift.[/]')
        return
    bullet = c.caps.g('bullet')
    for line in lines:
        c.say(f'[dim]{bullet}[/] {line}', subsequent='  ')
    if len(game.city.news) > len(lines):
        c.blank()
        c.say(f'[dim]`news {len(game.city.news)}` for all of it.[/]')


@command('talk', 'Say something to somebody.',
         group='city', contexts=('city',), usage='talk <name>',
         detail=(
                'Says something to somebody who is here. People keep hours '
                'and are not always about. They have topics they will talk '
                'about, and somebody standing in a district where something '
                'can be found will tell you what they have heard, once.'))
def cmd_talk(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not args.rest().strip():
        # `talk` on its own used to say "nobody called ''", which is the
        # game answering a question nobody asked. Who is here, instead.
        here = story_mod.present(game, game.story)
        met = [n for n in here if n.key in game.story.met]
        if not here:
            raise CommandError('nobody here is interested in you. `look`.')
        if not met:
            raise CommandError(f'{len(here)} here you have not met. `look` '
                               f'introduces them.')
        c.header('Here', game.city.district.name)
        c.kv([(n.key, f'[accent]{n.name}[/]  [dim]{n.epithet}[/]')
              for n in met])
        more = len(here) - len(met)
        c.blank()
        c.say('[dim]`talk <name>` to say something'
              + (f', and `look` for the {more} you have not met'
                 if more else '') + '.[/]')
        return
    npc = _find(sess, args.rest())
    line = game.rng('events').pick(npc.lines)
    c.blank()
    c.raw(f'[accent]{npc.name}[/]  [dim]{npc.epithet}[/]')
    c.blank()
    c.say(line)
    _noticed(sess)
    _lead(sess, npc)
    if npc.topics:
        c.blank()
        c.say('[dim]They will talk about: '
              + ', '.join(sorted(npc.topics)) + '. `ask '
              + handle(npc) + ' <topic>`.[/]')
    _check_story(sess)


def _lead(sess, npc) -> None:
    """What somebody standing here has heard (D65 depth).

    The rumour that leads to a relic is ambient weather, which means it
    arrives when the city feels like it. This is the other channel, and the
    one a player controls: talk to somebody in a district where something
    can be found and they say the thing they have heard, once each. It is
    the payoff for meeting people, and it is why a district with somebody
    in it is worth walking to.
    """
    game, c = sess.game, sess.console
    where = npc.where or game.city.where
    story = game.story
    for spot in spots.in_district(where):
        for find in spot.finds:
            if not find.rumour:
                continue
            if f'found:{find.item}' in story.flags:
                continue
            if f'heard:{find.item}' in story.flags:
                continue
            # The rumour leads (D148): it points at the place and the
            # person, so it cannot need you to have met the person
            # already. The `met:` rules are what the rumour is for; the
            # rest (runs, standing, drift) still gate whether it is
            # something you could go and get.
            lead = [r for r in find.requires if not r.startswith('met:')]
            if not all(story.satisfied(rule, game) for rule in lead):
                continue
            story.flags.add(f'heard:{find.item}')
            c.blank()
            c.say(f'[accent2]They have heard something.[/] [dim]{find.rumour}[/]')
            c.say(f'[dim]It would be somewhere in {spot.name}.[/]')
            game.city.news.append(f'[accent2]Heard in '
                                  f'{districts.BY_KEY[where].name}:[/] '
                                  f'{find.rumour[:90]}...')
            return


def ask_npc(sess, args) -> bool:
    """Try to answer `ask` as a question to one of the city's people.

    Returns False if the name is not somebody, so the caller can fall through
    to the rival-favour meaning of the verb. One word, two meanings, and the
    fiction absorbs it: you ask a person about a thing and you ask a colleague
    for a thing.
    """
    game, c = sess.require_game(), sess.console
    if len(args) < 2:
        return False
    npc = _match(args[0])
    if npc is None:
        return False
    if npc.key not in game.story.met:
        if any(n.key == npc.key for n in story_mod.present(game, game.story)):
            c.blank()
            introduce(sess, npc)
        else:
            raise CommandError(f'you have not met {npc.name}. `look` around '
                               f'where they are.')

    topic = args[1].lower()
    # "about" is the most natural filler a player types here, and the command
    # even calls itself "Ask somebody about something": skip a leading
    # about/for/on/of/re so `ask mara about deepwater` reads like `ask mara
    # deepwater`.
    if topic in ('about', 'for', 'on', 'of', 're') and len(args) >= 3:
        topic = args[2].lower()
    match = next((k for k in npc.topics if k.startswith(topic)), None)
    if match is None:
        raise CommandError(f'{npc.name} will talk about: '
                           + ', '.join(sorted(npc.topics)))
    flag = f'asked:{npc.key}:{match}'
    before = {(t, s.key) for t, s in game.story.available(game)}
    game.story.flags.add(flag)
    _asked_out(sess, npc)
    opened = [(t, s) for t, s in game.story.available(game)
              if (t, s.key) not in before and flag in s.requires]
    c.blank()
    c.raw(f'[accent]{npc.name}[/] [dim]on {match}[/]')
    if not opened:
        # The question is the scene when it gates one, and the topic line
        # and the scene said the same thing twice (D91).
        c.blank()
        said = npc.topics[match]
        # What they say once something has happened (D94): the last
        # variant whose rule holds.
        for topic, rule, text in npc.more:
            if topic == match and game.story.satisfied(rule, game):
                said = text
        c.say(said)
    _check_story(sess)
    return True


@command('who is', 'What you know about somebody you have met.',
         group='info', contexts=('city',), usage='who is <name>')
def cmd_who_is(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    npc = _find(sess, args.rest())
    c.header(npc.name, npc.epithet)
    c.say(npc.manner)
    where = npc.where or 'moves around'
    from ..content import districts
    if npc.where:
        where = districts.BY_KEY[npc.where].name
        if npc.at:
            where += f', where there is a {npc.at}'
    elif npc.at:
        where = f'anywhere with a {npc.at}'
    c.blank()
    c.kv([('found', where),
          ('about', npc_content.hours_label(npc)),
          ('offers', ', '.join(npc.offers))])
    live = [o for o in npc.offers if o != 'nothing']
    if live:
        c.blank()
        bits = []
        if [o for o in live if o != 'intel']:
            bits.append(f'`deal {npc.key}` for the business')
        if 'intel' in live and npc.topics:
            bits.append(f'`ask {npc.key} <topic>` for what they know')
        c.say('[dim]' + ', and '.join(bits) + '.[/]')


# --------------------------------------------------------------------------
# business
# --------------------------------------------------------------------------
#
# `Npc.offers` declared work, goods and favours for the whole life of the cast
# and `who is` printed the list, and none of the three did anything. This is
# where they became real. See `content/offers.py` for why they are one system
# and not three.


def _owed(game, key: str) -> int:
    return int(game.story.owed.get(key, 0))


def _standing(game, npc) -> str:
    """Where you are with somebody, in a phrase rather than a number."""
    owed = _owed(game, npc.key)
    if owed <= 0:
        return 'square'
    if owed >= offers.OWED_LIMIT:
        return 'as deep as they will let you get'
    return f'{owed} favour{"s" if owed != 1 else ""} down'


@command('deal', 'Do business with somebody you have met.',
         group='city', contexts=('city',), usage='deal [name] [work|goods|favour]',
         detail='The three things a person will do for you that a shop will '
                'not. `who is <name>` lists which of them they offer. Work is '
                'a contract that never reaches the board and pays better for '
                'it. Goods are what they keep under their own counter, which '
                'does not rotate with the market. A favour is them spending '
                'their own standing on your problem, and it goes on a tab: '
                'finishing work they gave you is how it comes off again.')
def cmd_deal(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    if not len(args):
        _deal_index(sess)
        return
    npc = _find(sess, args[0])
    kind = (args.get(1) or '').lower()
    if not kind:
        _deal_person(sess, npc)
        return
    if kind.startswith('w'):
        _deal_work(sess, npc, args)
    elif kind.startswith('g'):
        _deal_goods(sess, npc)
    elif kind.startswith('f'):
        _deal_favour(sess, npc, args)
    elif kind in ('muscle', 'street', 'job'):
        _deal_muscle(sess, npc, args)
    else:
        raise CommandError(f'{npc.name} deals in work, goods, muscle and favours, '
                           f'not {kind!r}')


def _deal_index(sess) -> None:
    """Who in this district will do business, and what kind."""
    game, c = sess.require_game(), sess.console
    here = [n for n in npc_content.NPCS
            if n.key in game.story.met
            and (not n.where or n.where == game.city.where)
            and (not n.at or n.at in game.city.district.services)
            and [o for o in n.offers if o != 'nothing']]
    c.header('Business', game.city.district.name)
    if not here:
        c.say('[dim]Nobody you know is doing business in '
              f'{game.city.district.name}. `look` to find people, and '
              '`who is <name>` for what somebody offers.[/]')
        return
    for npc in here:
        trades = ', '.join(o for o in npc.offers if o != 'nothing')
        c.raw(f'  [accent]{npc.key:<14}[/] [fg]{npc.name:<24}[/] '
              f'[dim]{trades}[/]')
    c.blank()
    c.say('[dim]`deal <name>` for the detail.[/]')


def _deal_person(sess, npc) -> None:
    game, c = sess.require_game(), sess.console
    c.header(npc.name, npc.epithet)
    c.kv([('offers', ', '.join(o for o in npc.offers if o != 'nothing')
                     or 'nothing'),
          ('between you', _standing(game, npc))])
    live = [o for o in npc.offers if o != 'nothing']
    c.blank()
    if 'work' in live:
        work = offers.BY_NPC_WORK.get(npc.key)
        ready, why = _work_ready(game, npc)
        c.say(f'[fg]deal {npc.key} work[/] [dim]'
              + ('a job they are holding for you' if ready else why) + '[/]')
    if 'goods' in live:
        c.say(f'[fg]deal {npc.key} goods[/] [dim]what is under their own '
              f'counter[/]')
    if 'intel' in live and npc.topics:
        c.say(f'[fg]ask {npc.key} <topic>[/] [dim]'
              + ', '.join(sorted(npc.topics)) + '[/]')
    if 'muscle' in live:
        c.say(f'[fg]deal {npc.key} muscle[/] [dim]physical work: somebody '
              f'hurt, something held, something got back[/]')
    if 'favour' in live:
        for fav in offers.favours_for(npc.key):
            c.say(f'[fg]deal {npc.key} favour {fav.key}[/] [dim]{fav.blurb}[/]')


def _work_ready(game, npc) -> tuple[bool, str]:
    """Whether they have something for you, and why not if they do not."""
    work = offers.BY_NPC_WORK.get(npc.key)
    if work is None:
        return False, 'they do not hand out work'
    if game.city.accepted:
        return False, 'you are already carrying something'
    for rule in work.requires:
        if not game.story.satisfied(rule, game):
            return False, 'they do not know you well enough yet'
    since = game.city.shift - int(game.story.asked.get(npc.key, -99))
    if since < offers.WORK_EVERY:
        return False, (f'nothing new for {offers.WORK_EVERY - since} more '
                       f'shifts')
    if _owed(game, npc.key) >= offers.OWED_LIMIT:
        return False, 'you are too far into them already'
    return True, ''


def _deal_work(sess, npc, args) -> None:
    game, c = sess.require_game(), sess.console
    work = offers.BY_NPC_WORK.get(npc.key)
    if work is None:
        raise CommandError(f'{npc.name} does not hand out work.')
    ready, why = _work_ready(game, npc)
    if not ready:
        raise CommandError(f'{npc.name}: {why}.')

    existing = next((x for x in game.city.board if x.from_npc == npc.key),
                    None)
    if existing is None:
        existing = game.city.offer_work(game.rng, game.alias, work)
        game.story.asked[npc.key] = game.city.shift
    c.blank()
    c.rule(npc.name)
    c.say(work.pitch)
    c.blank()
    from .city import _show_contract
    _show_contract(sess, existing)
    c.blank()
    c.say(f'[dim]It is on the board as [fg]{existing.cid}[/][dim], held for '
          f'{work.patience} shifts longer than a posting. `take '
          f'{existing.cid}` to agree to it.[/]')
    sess.autosave()


def _deal_muscle(sess, npc, args) -> None:
    """A fixer's street jobs (D134). Two a window; accept one and it is
    carried like an errand and met where it is."""
    from ..world import street as street_world
    game, c = sess.require_game(), sess.console
    if 'muscle' not in npc.offers:
        raise CommandError(f'{npc.name} does not hand out that kind of work.')
    jobs = street_world.fixer_jobs(game, npc)
    pick = args.get(2)
    if not pick:
        c.blank()
        c.rule(npc.name)
        if not jobs:
            c.say('[dim]Nothing physical this window. Ask again in a day.[/]')
            return
        c.say('[dim]Two things that need doing with your hands, not the '
              'deck. Each is a fight, where it is, at the tier they say. '
              'Combat is never the way to do a run; this is a second kind of '
              'work.[/]')
        c.blank()
        rows = []
        for n, job in enumerate(jobs, 1):
            fill = street_world.job_fill(game, job)
            from ..content import street as street_content
            rows.append((str(n), street_content.FIXER_JOBS[job['job']]['label'],
                         f'{fill["district"]}, {street_content.TIER_NAMES[job["tier"]]}'
                         + (', chromed' if job.get('chromed') else ''),
                         f'{job["pay"]:,}c'
                         + (f' + {fill["item"]}' if job['job'] == 'recover' else '')))
        c.table(('#', 'what', 'where, and how bad', 'pays'), rows,
                roles=('dim', 'accent', 'dim', 'credit'))
        c.blank()
        c.say(f'[dim]`deal {npc.key} muscle <#>` to take one. You carry it '
              f'like an errand, and it happens when you arrive.[/]')
        return
    if game.city.errand:
        raise CommandError(f'you are already carrying '
                           f'{game.city.errand.get("what", "something")}. '
                           f'`errands drop` to put it down.')
    try:
        job = jobs[int(pick) - 1]
    except (ValueError, IndexError):
        raise CommandError(f'which one? 1 to {len(jobs)}.')
    from ..content import street as street_content, districts
    fill = street_world.job_fill(game, job)
    game.city.errands_taken.add(job['key'])
    game.city.errand = dict(job)
    c.blank()
    c.say(f'[warn]{street_content.FIXER_JOBS[job["job"]]["pitch"].format(**fill)}[/]')
    to = districts.BY_KEY[job['to']]
    c.ok(f'Taken. {to.name}, {game.city.shifts_to(to.key)} shift'
         f'{"s" if game.city.shifts_to(to.key) != 1 else ""} from here; '
         f'[credit]{job["pay"]:,}c[/] when it is done.')
    sess.autosave()


def _deal_goods(sess, npc) -> None:
    game, c = sess.require_game(), sess.console
    stock = offers.BY_NPC_STOCK.get(npc.key)
    if stock is None:
        raise CommandError(f'{npc.name} does not sell anything.')
    if npc.where and npc.where != game.city.where:
        raise CommandError(f'{npc.name} keeps their stock in '
                           f'{districts.BY_KEY[npc.where].name}.')
    # A counter can close on you. D51: what you did to somebody is part of
    # whether they still get the cabinet out.
    for rule in stock.requires:
        if not game.story.satisfied(rule, game):
            raise CommandError(stock.refusal or f'{npc.name} has nothing '
                               f'under the counter for you.')
    game.city.open_counter(stock)
    c.header(npc.name, 'what they keep back')
    c.say(f'[dim]{stock.pitch}[/]')
    # First time you deal with *them*, rather than the first time a line of
    # stock is new. Ozymandias sells one thing that the Ninth's market also
    # carries, so his entire character never printed.
    flag = f'counter:{npc.key}'
    if flag not in game.story.flags:
        game.story.flags.add(flag)
        c.blank()
        c.say(stock.first)

    # Theirs, specifically. The goods join the district's shelf so that `buy`
    # and `market` work on them unchanged, and that also means the market
    # screen mixes them into thirty other lines with nothing saying which four
    # are the ones this person got out for you.
    from ..world import market as market_mod
    from .city import _item, _listing_detail
    rows = []
    for listing in game.city.listings():
        if listing.key not in stock.goods:
            continue
        item = _item(listing)
        if item is None:
            continue
        price, _ = market_mod.quote(listing, game.city.where, game.alias,
                                    game.char.dissonance,
                                    game.char.mult('price_mult'),
                                    game.city.phase,
                                    game.char.attr('guile'))
        rows.append((item.name, listing.kind,
                     _listing_detail(listing, item), f'{price:,}c'))
    c.blank()
    if rows:
        c.table(('item', 'kind', 'what it does', 'price'), rows,
                roles=('accent', 'dim', 'dim', 'credit'))
        c.blank()
        c.say('[dim]`buy <name>` as anywhere else. It is on the local shelf '
              'now and it does not rotate off it.[/]')
    else:
        c.say('[dim]The shelf is empty. They are not apologetic about it.[/]')
    sess.autosave()


def _deal_favour(sess, npc, args) -> None:
    game, c = sess.require_game(), sess.console
    available = offers.favours_for(npc.key)
    if not available:
        raise CommandError(f'{npc.name} is not somebody you ask for things.')
    want = (args.get(2) or '').lower()
    if not want:
        c.header(npc.name, _standing(game, npc))
        for fav in available:
            c.raw(f'  [accent]{fav.key:<10}[/] [dim]{fav.blurb}[/]')
        c.blank()
        c.say(f'[dim]`deal {npc.key} favour <name>`. Each one puts you a '
              f'favour down, and finishing work they gave you is how it '
              f'comes off.[/]')
        return
    fav = next((f for f in available if f.key.startswith(want)), None)
    if fav is None:
        raise CommandError(f'{npc.name} does: '
                           + ', '.join(f.key for f in available))
    if _owed(game, npc.key) >= offers.OWED_LIMIT:
        c.blank()
        c.say(f'[err]{fav.refusal}[/]')
        return
    for rule in fav.requires:
        if not game.story.satisfied(rule, game):
            raise CommandError(f'{npc.name} will not, and does not explain '
                               f'why, which is its own answer.')

    done, note = _do_favour(sess, fav)
    if not done:
        raise CommandError(note)
    game.story.owed[npc.key] = _owed(game, npc.key) + 1
    c.blank()
    c.rule(fav.name, role='accent2')
    for para in fav.text.split('\n\n'):
        c.say(para)
        c.blank()
    c.say(f'[dim]{note}[/]')
    c.say(f'[dim]You are {_standing(game, npc)} with {npc.name}.[/]')
    sess.autosave()


def _do_favour(sess, fav) -> tuple[bool, str]:
    """Apply one favour. Returns (happened, what to say about it).

    Every effect key here is in `offers.EFFECTS` and `validate.py` checks the
    other direction, so a favour cannot promise something nothing implements,
    which is the exact failure this whole feature exists to correct.
    """
    game = sess.game
    if fav.effect == 'heat':
        hot, heat = game.alias.hottest
        if not hot:
            return False, 'nobody is looking for you. Save it.'
        shed = min(fav.amount, heat)
        game.alias.add_heat(hot, -shed)
        return True, (f'{factions.BY_KEY[hot].short} attention down '
                      f'{int(shed)}.')
    if fav.effect == 'hold':
        contract = game.city.current
        if contract is None:
            return False, 'you are not carrying anything to hold.'
        contract.expires += fav.amount
        return True, (f'{contract.title} now runs to shift '
                      f'{contract.expires}.')
    if fav.effect == 'intel':
        contract = game.city.current
        if contract is None:
            return False, 'there is no job to read.'
        # The same network the run will generate, read the same way legwork
        # reads it, so a favour cannot know something a shift of asking
        # around could not have found out.
        from ..run import network as net_mod
        from .city import _legwork_result
        net = net_mod.generate(game.rng.fork('network', contract.cid),
                               contract.target, int(contract.posture),
                               contract.objective, contract.size_mod)
        for gives in ('topology', 'ice', 'assets'):
            contract.intel[gives] = _legwork_result(net, gives, 1, game)
        return True, 'Everything they can see about it is yours.'
    if fav.effect == 'detox':
        from ..content import drugs
        state = drugs.normalise(game.char.chem)
        if not state['habit']:
            return False, 'there is nothing on you to take off.'
        worst = max(state['habit'], key=lambda k: state['habit'][k])
        state['habit'][worst] = max(0, state['habit'][worst] - fav.amount)
        if not state['habit'][worst]:
            del state['habit'][worst]
        game.char.chem = state
        return True, f'{drugs.BY_KEY[worst].name} has less of you than it did.'
    if fav.effect == 'debt':
        if not game.debt.owed:
            return False, 'you do not owe anybody anything.'
        game.debt.pay(fav.amount)
        return True, f'{game.debt.amount:,}c outstanding.'
    if fav.effect == 'ground':
        floor = game.char.chrome_dissonance
        if game.char.dissonance <= floor:
            return False, ('there is nothing to walk back that is not '
                           'hardware.')
        before = game.char.dissonance
        game.char.dissonance = max(floor, before - fav.amount)
        return True, (f'Dissonance {before} to {game.char.dissonance}.')
    return False, 'nothing happens, which should be impossible.'


@command('journal', 'What you have got yourself into.',
         group='info', aliases=('threads',), usage='journal [name]',
         detail=(
                'Everything you have got yourself into, as a log: what is '
                'waiting on a decision, what you decided and what it cost, '
                'and which threads are still open. The flags are the story '
                'layer, and this is them, read back.'))
def cmd_journal(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    story = game.story

    if len(args):
        query = args.rest().lower()
        thread = next((t for t in thread_content.THREADS
                       if t.key.startswith(query)
                       or query in t.name.lower()), None)
        if thread is None or thread.key not in story.reached:
            raise CommandError(f'nothing in the journal about {query!r}')
        c.header(thread.name, thread.key)
        c.say(f'[dim]{thread.blurb}[/]')
        decided = {stage.key: choice
                   for stage, choice in story.decided(thread.key)}
        for stage in thread.stages:
            if stage.key not in story.reached[thread.key]:
                continue
            c.blank()
            c.rule(stage.headline)
            for para in story_fill(game, stage.text).split('\n\n'):
                c.say(para)
                c.blank()
            # What you decided, and what it cost, under the scene it
            # belonged to. The journal is a log now (D62), not a table of
            # contents.
            choice = decided.get(stage.key)
            if choice is not None:
                c.say(f'[accent2]You chose: {choice.label}.[/] '
                      f'[dim]{_cost_of(choice)}[/]', indent='  ',
                      subsequent='  ')
                c.blank()
            elif f'{thread.key}.{stage.key}' in story.pending:
                c.say('[warn]Waiting on you.[/] [dim]`choose`.[/]', indent='  ')
                c.blank()
        # And what it is short of, when what it is short of is somebody
        # rather than you (D76). Never flags, never what the scene is.
        short = story.waiting_on(thread, game)
        if short:
            c.blank()
            c.say(f'[dim]{short}[/]')
        crossing = [k for k in thread.crosses if k in story.reached]
        if crossing:
            c.say('[dim]Touches: '
                  + ', '.join(thread_content.BY_KEY[k].name
                              for k in crossing) + '[/]')
        return

    active = story.active_threads()
    c.header('Journal', f'{len(active)} of {len(thread_content.THREADS)}')
    if not active:
        c.say('[dim]Nothing yet. The city\'s stories open as you run jobs, '
              'fight, work the street and cross the people who matter, and '
              'most of them are not in this district. Take a couple of '
              'contracts or a couple of fights, `travel`, and `look` around, '
              'then check back here.[/]')
        return
    # What is waiting first, because it is the one thing in here that does
    # not move without you.
    waiting = []
    for tag in story.pending:
        tkey, _, skey = tag.partition('.')
        thread = thread_content.BY_KEY.get(tkey)
        stage = next((s for s in thread.stages if s.key == skey), None) \
            if thread else None
        if thread and stage:
            waiting.append((thread, stage))
    if waiting:
        c.say('[warn]Waiting on you:[/]')
        for thread, stage in waiting:
            c.say(f'[fg]{thread.name}[/] [dim]{stage.headline}[/]',
                  indent='  ', subsequent='  ')
        c.say('[dim]`choose` takes the first.[/]', indent='  ')
        c.blank()
    decisions = 0
    for thread in active:
        c.blank()
        c.raw(f'[accent]{thread.name}[/]  [dim]{thread.key}[/]')
        headline = story.headline(thread.key)
        if headline:
            c.say(f'[dim]{headline}[/]', indent='  ', subsequent='  ')
        for stage, choice in story.decided(thread.key):
            decisions += 1
            c.say(f'[accent2]decided:[/] {choice.label.lower()}',
                  indent='  ', subsequent='  ')
    c.blank()
    c.say(f'[dim]{decisions} decision{"s" if decisions != 1 else ""} made, '
          f'every one read by the world and every one with a line in the '
          f'ending. `journal <name>` to read one in full.[/]')


def _cost_of(choice) -> str:
    """What a decision cost or paid, in one clause, from its declared effects."""
    bits = []
    if choice.credits:
        bits.append(f'{abs(choice.credits):,}c '
                    f'{"in" if choice.credits > 0 else "gone"}')
    for faction, delta in choice.rep.items():
        short = factions.BY_KEY[faction].short if faction in factions.BY_KEY \
            else faction
        bits.append(f'{short} {"warmer" if delta > 0 else "colder"}')
    if choice.drift:
        bits.append(f'drift {choice.drift:+d}')
    if choice.gives:
        bits.append('something in the bag')
    if choice.ends:
        bits.append(choice.ends)
    return ('; '.join(bits) + '.') if bits else 'Nothing it would put a number on.'


@command('choose', 'Decide the thing that is waiting on you.',
         group='city', contexts=('city',), usage='choose [option]',
         detail=(
                'Answers the thing that is waiting on you. There is no going '
                'back on one, the whole city reads them afterwards, and the '
                'ending reads all of them.'))
def cmd_choose(sess, args) -> None:
    game, c = sess.require_game(), sess.console
    found = game.story.open_choice()
    if found is None:
        raise CommandError('nothing is waiting on a decision from you.')
    thread, stage = found

    if not len(args):
        c.header(thread.name, stage.headline)
        for para in story_fill(game, stage.text).split('\n\n'):
            c.say(para)
            c.blank()
        c.rule('what you do')
        for choice in stage.choices:
            c.blank()
            short = (-choice.credits > game.char.credits
                     if choice.credits < 0 else False)
            c.raw(f'  [accent]{choice.key}[/]  {choice.label}'
                  + (f'  [dim]({-choice.credits:,}c, which you do not '
                     f'have)[/]' if short else
                     f'  [dim]({-choice.credits:,}c)[/]'
                     if choice.credits < 0 else ''))
        c.blank()
        c.say('[dim]`choose <option>`. There is no going back on this one.[/]')
        return

    key = args[0].lower()
    choice = next((x for x in stage.choices if x.key.startswith(key)), None)
    if choice is None:
        raise CommandError('options: '
                           + ', '.join(x.key for x in stage.choices))
    if choice.credits < 0 and game.char.credits < -choice.credits:
        # It used to take nine thousand from five and clamp to nought,
        # which is a story choice quietly writing itself off (D91).
        raise CommandError(f'that costs {-choice.credits:,}c and you have '
                           f'{game.char.credits:,}c. Another option, or '
                           f'come back with it.')

    game.story.resolve(thread.key, stage.key, choice)
    game.city.news.append(f'[accent2]{thread.name}:[/] you chose '
                          f'{choice.label.lower()}.')
    c.blank()
    c.rule(choice.label, role='accent2')
    for para in story_fill(game, choice.text).split('\n\n'):
        c.say(para)
        c.blank()
    if set(choice.sets) & thread_content.SPINE_ENDINGS:
        # The main line has ended (D144): the posting with your name on it
        # comes down with it, whichever way you answered.
        taken = game.city.withdraw_story('deepwater.posting')
        if taken:
            c.say(taken)

    if choice.credits:
        game.char.credits = max(0, game.char.credits + choice.credits)
        word = 'in' if choice.credits > 0 else 'gone'
        c.say(f'[credit]{abs(choice.credits):,}c[/] {word}.')
    if choice.debt and game.debt.owed:
        if choice.debt < 0:
            applied = game.debt.pay(-choice.debt)
            c.say(f'[ok]{applied:,}c off the figure.[/] '
                  f'[dim]{game.debt.amount:,}c outstanding.[/]')
        else:
            game.debt.amount += choice.debt
            c.say(f'[err]{choice.debt:,}c onto the figure.[/] '
                  f'[dim]{game.debt.amount:,}c outstanding.[/]')
        if 'buyout_extended' in choice.sets and game.debt.instalment:
            # The terms extend: the same figure over more visits.
            game.debt.instalment = max(400, game.debt.instalment // 2)
            c.say(f'[dim]The instalments halve, to '
                  f'{game.debt.instalment:,}c a visit. The years do not.[/]')
    if choice.gives:
        for key in choice.gives:
            name, unique = give_item(game, key)
            c.say(f'[dim]{name} is in the bag.[/]'
                  + (' [accent2]`inspect` it: there is one of it.[/]'
                     if unique else ''))
    for faction, delta in choice.rep.items():
        game.alias.adjust_rep(faction, delta)
        c.say(f'[dim]{factions.BY_KEY[faction].short} '
              f'{"warmer" if delta > 0 else "colder"}.[/]')
    for rival_key, delta in choice.disposition.items():
        rival = game.city.rival(rival_key)
        if rival is not None:
            rival.adjust_disposition(delta)
    if choice.drift:
        before = game.char.dissonance
        game.char.dissonance = max(0, min(100, before + choice.drift))
        c.say(f'[accent2]Dissonance {before} to {game.char.dissonance}.[/]')
    _settle_paper(sess, choice)
    _settle_nine(sess, choice)
    _settle_systems(sess, choice)
    sess.autosave()
    if choice.ends:
        # The third exit. The choice has already said what happened; this
        # is the numbers, the decisions read back, and what is left.
        from .core import end_character
        end_character(sess, choice.ends)
        return
    _check_story(sess)


# --------------------------------------------------------------------------


def _match(query: str):
    query = (query or '').lower().strip()
    if not query:
        return None
    for npc in npc_content.NPCS:
        if query == npc.key or query in npc.name.lower():
            return npc
    return None


def _find(sess, query: str):
    game = sess.require_game()
    npc = _match(query)
    if npc is None:
        # A runner is not somebody you deal with, talk to or ask: the
        # campaigns typed `deal vesper` eight times and were told nobody
        # was called that, which is true and not the answer.
        low = (query or '').lower().strip()
        runner = next((r for r in game.city.rivals
                       if low in (r.key, r.name.lower(), getattr(r, 'handle', '').lower())
                       or low in r.name.lower()), None)
        if runner is not None:
            raise CommandError(f'{runner.name} is a runner, not somebody you '
                               f'do business with. `who {runner.key}` for '
                               f'where you stand, `hire {runner.key}` for a '
                               f'job, `crew take {runner.key}` for longer, '
                               f'`message {runner.key}` to say something.')
        raise CommandError(f'nobody called {query!r}')
    if npc.key not in game.story.met:
        # Standing here now: that is a meeting. Somewhere else, or not at
        # this hour, is the refusal it always was.
        if any(n.key == npc.key for n in story_mod.present(game, game.story)):
            sess.console.blank()
            introduce(sess, npc)
            sess.console.blank()
            return npc
        raise CommandError(f'you have not met them. `look` around'
                           + (f' {districts.BY_KEY[npc.where].name}'
                              if npc.where in districts.BY_KEY else '')
                           + '.')
    return npc


#: How many scenes fire on one command. See `_check_story`.
SCENES_AT_ONCE = 3


#: Tokens a scene may carry (D171): the world fills them at print time, so
#: a thread can be about whichever runner the city chose.
FILL_TOKENS = ('{runner}', '{runner_handle}', '{partner}', '{pet}', '{familiar}',
               '{Runner}', '{Partner}', '{Pet}', '{Familiar}', '{called}')


def story_fill(game, text: str) -> str:
    """The scene with the city\'s names in it."""
    if '{' not in text:
        return text
    ninth = game.city.rival(game.city.ninth) if game.city.ninth else None
    from ..world import rivals as rival_world
    partner = rival_world.active_partner(game.city.rivals)
    pet = game.city.pet or {}
    fam = game.char.deck.familiar or {}
    fill = {
        'runner': ninth.name if ninth is not None else 'the ninth runner',
        'runner_handle': ninth.data.handle if ninth is not None else 'the ninth',
        'partner': partner.name if partner is not None else 'nobody',
        'pet': pet.get('name') or 'nothing',
        'familiar': fam.get('name') or 'nothing',
    }
    # The name the city uses for you (D173): the pinned one, else the
    # newest, else none yet.
    try:
        from .. import save as save_mod
        from ..world import record as record_world
        meta = save_mod.read_meta()
        counts = record_world.counts(game, meta)
        fill['called'] = record_world.title_of(counts, meta.get('recorded'), meta) or 'no name yet'
    except Exception:  # noqa: BLE001
        fill['called'] = 'no name yet'
    for key, value in list(fill.items()):
        if key in ('runner', 'partner', 'pet', 'familiar'):
            fill[key[0].upper() + key[1:]] = value[0].upper() + value[1:]
    for key, value in fill.items():
        text = text.replace('{' + key + '}', value)
    return text


def _name_the_ninth(sess) -> None:
    """The ninth log has a name (D171): the runner the city chooses is the
    one you are bound to if you are bound to anybody, else the one with the
    most work behind them, alive. Chosen before the scene prints, because
    the scene says the name."""
    game = sess.game
    if game.city.ninth and game.city.rival(game.city.ninth) is not None:
        return
    living = [r for r in game.city.rivals if r.alive]
    if not living:
        return
    bonded = [r for r in living if r.bond in ('partner', 'nemesis')]
    pool = bonded or living
    game.city.ninth = max(pool, key=lambda r: (r.jobs, r.disposition, r.key)).key


def _settle_nine(sess, choice) -> None:
    """What the answers about the ninth log do to the runner it belongs to
    (D171). The runner is whoever the city chose, so this is code, not a
    static `disposition=` on the choice."""
    game = sess.game
    rival = game.city.rival(game.city.ninth) if game.city.ninth else None
    if rival is None or not rival.alive:
        return
    deltas = {'nine_told': 12, 'nine_sold': -10, 'nine_together': 40,
              'nine_alone': -5, 'nine_handed': -80}
    for flag, delta in deltas.items():
        if flag in choice.sets:
            rival.adjust_disposition(delta)
    if 'nine_together' in choice.sets and not game.city.crew and not game.city.hired:
        # They are in on your next one, their idea this time.
        game.city.hired = rival.key
        game.city.asked_in = rival.key


def _settle_systems(sess, choice) -> None:
    """What the subplots for the new systems do to those systems (D172):
    the animal goes, the construct is dropped or handed over, the name is
    worn or thrown back."""
    from .. import save as save_mod
    game, c = sess.game, sess.console
    if 'stray_given' in choice.sets and game.city.pet:
        game.city.pet = {}
    if ('construct_wiped' in choice.sets or 'construct_given' in choice.sets) and game.char.deck.familiar:
        game.char.deck.familiar = {}
    if 'names_worn' in choice.sets or 'names_refused' in choice.sets:
        try:
            meta = save_mod.read_meta()
            if 'names_worn' in choice.sets:
                from ..content import record as record_content
                earned = [t for t in record_content.TITLES if game.story.satisfied(t.rule, game)]
                if earned:
                    meta['called'] = earned[0].name
                    c.say(f'[dim]The city calls you [/][accent2]{earned[0].name}[/][dim] now. `called` to change it.[/]')
            else:
                meta['called'] = ''
            save_mod.write_meta(meta)
        except Exception:  # noqa: BLE001
            pass


def _scene_asides(sess, stage) -> None:
    """The systems that arrived after the main line was written, reading
    it (D171): the familiar on the deck when your own log comes out, the
    partner when the offer does, the animal and the construct when the
    city is handed back."""
    from ..content import pets as pet_content
    from ..world import pets as pet_world, rivals as rival_world
    game, c = sess.game, sess.console
    if 'dw_carried' in stage.sets:
        fam_state = game.char.deck.familiar or {}
        fam = pet_content.FAMILIAR_BY_KEY.get(fam_state.get('key', '')) if fam_state else None
        if fam is not None and fam.says.get('log'):
            c.say(f'[dim]{fam.says["log"][0]}[/]')
            c.blank()
    if 'dw_offer' in stage.sets:
        partner = rival_world.active_partner(game.city.rivals)
        if partner is not None:
            c.say(f'[dim]{partner.name} reads it over your shoulder, which they '
                  f'do not do, and asks what it pays, and then, after a while, '
                  f'what it costs.[/]')
            c.blank()
    if 'after_rest' in stage.sets:
        if game.city.pet:
            line = pet_world.greeting(game.city)
            if line:
                c.say(f'[dim]{line}[/]')
                c.blank()
        fam_state = game.char.deck.familiar or {}
        fam = pet_content.FAMILIAR_BY_KEY.get(fam_state.get('key', '')) if fam_state else None
        if fam is not None and fam.says.get('home'):
            c.say(f'[dim]{fam.says["home"][0]}[/]')
            c.blank()
    if 'nine_found' in stage.sets:
        rival = game.city.rival(game.city.ninth) if game.city.ninth else None
        if rival is not None and rival.alive:
            rival.adjust_disposition(-25)


def _take_paper(sess) -> None:
    """The collector has a name (D164): the runner who thinks least of you
    is the one who took the paper. Mara does not say it; the book does.
    `who` shows it until the thing is settled."""
    game, c = sess.game, sess.console
    living = [r for r in game.city.rivals if r.alive]
    if not living:
        return
    worst = min(living, key=lambda r: (r.disposition, r.key))
    game.city.paper = worst.key
    c.say(f'[dim]Mara does not say the name. The book does, upside down '
          f'across the counter: [/][accent]{worst.name}[/][dim].[/]')
    c.blank()


def _settle_paper(sess, choice) -> None:
    """What the answer did to the runner holding the paper (D164)."""
    game = sess.game
    if not game.city.paper:
        return
    rival = game.city.rival(game.city.paper)
    if rival is not None and rival.alive:
        if 'paper_bought' in choice.sets:
            # Paid, in cash, more than the paper promised: that is a
            # relationship of a kind.
            rival.adjust_disposition(6)
        elif 'paper_faced' in choice.sets:
            # Seen seeing them. Nobody likes that.
            rival.adjust_disposition(-4)
    if choice.sets and any(f.startswith('paper_') for f in choice.sets):
        game.city.paper = ''



def _asked_out(sess, npc) -> None:
    """Somebody you have asked everything tells you where to look (D166):
    the one thing in their district that a career would otherwise gate,
    once. A pure explorer or a pure talker earns the finds this way; the
    walking is still theirs to do."""
    game, c = sess.game, sess.console
    flags = game.story.flags
    if not npc.topics or not all(f'asked:{npc.key}:{t}' in flags for t in npc.topics):
        return
    if not npc.where:
        return
    for spot in spots.in_district(npc.where):
        for find in spot.finds:
            if f'found:{find.item}' in flags or f'told:{find.item}' in flags:
                continue
            if not any(r.startswith('runs:') for r in find.requires):
                continue
            if not all(game.story.satisfied(r, game) for r in find.requires
                       if not r.startswith('runs:')):
                continue
            flags.add(f'told:{find.item}')
            flags.add(f'heard:{find.item}')
            c.blank()
            c.say(f'[dim]{npc.name} has run out of things you have not asked, '
                  f'and says one more, quieter: there is something at '
                  f'{spot.name} that is not on the way to anywhere, and it '
                  f'is not there for people who have not been told.[/]')
            game.city.news.append(f'[dim]{npc.name} told you where to look: {spot.name}.[/]')
            return


def _check_story(sess) -> None:
    """Surface any scene that has become available.

    Never during a run: being handed a scene about a dying friend halfway
    through a vault is the wrong moment for both of them.
    """
    game = sess.game
    if game is None or sess.run is not None:
        return
    c = sess.console
    ready = game.story.available(game)
    # The ones written for this street first: a scene that names the
    # district you are standing in is about here, and the ones that could
    # happen anywhere can happen anywhere else. Without this the cap
    # below starved every place-bound scene behind the drift of the
    # anywhere ones, in thread order, for as long as there were three of
    # those.
    ready.sort(key=lambda pair: 0 if pair[1].where else 1)
    # Three at most in one breath (D86), and one per thread (D91): three
    # stages of Lark across one visit narrated "the second time you see
    # them" and "they are worse" in the same breath. Anything still ready
    # fires on the next thing you do out here.
    seen_threads: set = set()
    firing, held = [], []
    for pair in ready:
        if len(firing) < SCENES_AT_ONCE and pair[0] not in seen_threads:
            firing.append(pair)
            seen_threads.add(pair[0])
        else:
            held.append(pair)
    for thread_key, stage in firing:
        thread = thread_content.BY_KEY[thread_key]
        if 'nine_named' in stage.sets:
            _name_the_ninth(sess)
        game.story.reach(thread_key, stage, game.city.shift)
        # The wire carries the story too (D56): a scene is something the
        # city did, and `news` is where what the city did goes.
        game.city.news.append(f'[dim]{thread.name}:[/] {stage.headline}.')
        c.blank()
        c.rule(thread.name, role='accent2')
        c.say(f'[dim]{stage.headline}[/]')
        c.blank()
        for para in story_fill(game, stage.text).split('\n\n'):
            c.say(para)
            c.blank()
        _scene_asides(sess, stage)
        if 'paper_taken' in stage.sets:
            _take_paper(sess)
        if 'wash_washed' in stage.sets:
            # The name comes clean (D169): the numbers come off, and the
            # heat that put them there is halved.
            game.city.bounties.clear()
            for fac_key in list(factions.BY_KEY):
                hot = int(game.alias.attention(fac_key))
                if hot > 0:
                    game.alias.add_heat(fac_key, -(hot // 2))
        if stage.posts is not None:
            # The scene put something on the board. Said in the board's own
            # terms, because the next thing the player types is `board`.
            contract = game.city.post_story(game.rng, game.alias, stage.posts,
                                            f'{thread_key}.{stage.key}')
            c.say(f'[dim]On the board: [/][accent]{contract.title}[/]'
                  f'[dim], {contract.cid}, against '
                  f'{contract.target_data.short}. It does not expire and '
                  f'nobody else will take it. `board {contract.cid}` to read '
                  f'it, `take {contract.cid}` when you are ready.[/]')
            c.blank()
        if stage.choices:
            c.say('[warn]This one is waiting on you.[/] [dim]`choose`.[/]')
    if held:
        c.blank()
        c.say(f'[dim]There is more happening here than one street can hold: '
              f'{len(held)} more scene{"s" if len(held) != 1 else ""}, on '
              f'the next thing you do.[/]')
    _check_origin_past(sess)
    _check_ambitions(sess)
    _check_reckoning(sess)
    _check_partner_offer(sess)
    sess.autosave()


def _check_origin_past(sess) -> None:
    """The lifepath opening (D126): once you have a first job behind you, the
    complication you started under stops being a line on the sheet and comes
    to find you. Once, ever, per character."""
    game = sess.game
    if game is None or sess.run is not None:
        return
    if getattr(game.char, 'runs', 0) < 1:
        return
    flag = f'origin_past:{game.char.origin}'
    if flag in game.story.flags:
        return
    from ..content import origins
    text = origins.ORIGIN_OPENING.get(game.char.origin)
    if not text:
        return
    game.story.flags.add(flag)
    c = sess.console
    c.blank()
    c.rule('where you came from', role='accent2')
    c.say(f'[dim]{text}[/]')
    c.blank()


def _check_partner_offer(sess) -> None:
    """A partner deep enough comes to run with you for good (D121), the mirror
    of the reckoning. Only when nothing else is waiting, and never on top of a
    reckoning that the same breath may have raised."""
    game = sess.game
    if game is None or sess.run is not None or sess.pending is not None:
        return
    from ..world import rivals as rival_mod
    rival = rival_mod.offer_due(game.city.rivals, game.story.flags,
                                bool(game.city.crew))
    if rival is not None:
        rival_mod.offer_begin(sess, rival)


def _check_reckoning(sess) -> None:
    """A nemesis whose arc has boiled over comes to find you in the city
    (D119). Only when nothing else is already waiting on the next line, so it
    never lands on top of a scene or a question."""
    game = sess.game
    if game is None or sess.run is not None or sess.pending is not None:
        return
    from ..world import rivals as rival_mod
    rival = rival_mod.reckoning_due(game.city.rivals, game.story.flags)
    if rival is not None:
        rival_mod.reckoning_begin(sess, rival)


def _check_ambitions(sess) -> None:
    """Mark any ambition (D117) the player has just met: a beat, a small
    recognition bounty, and it is remembered. One per breath, so a veteran's
    first load drips its back-catalogue rather than dumping it."""
    game = sess.game
    if game is None or sess.run is not None:
        return
    from ..content import ambitions
    met = ambitions.newly_met(game)
    if not met:
        return
    won = met[0]
    ambitions.claim(game, won)
    c = sess.console
    c.blank()
    c.rule(won.title, role='ok')
    c.say(f'[ok]{won.line}[/]')
    if won.reward:
        game.char.credits += won.reward
        c.say(f'[dim]The street rounds up. [/][credit]+{won.reward:,}c[/][dim]'
              f', for being somebody worth paying attention to.[/]')
