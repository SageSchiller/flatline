#!/usr/bin/env python3
"""Content graph checks. Run after every content change.

`validate.py` looks at what the content *says*; `test.py` looks at what the
game *does*. The split matters because most of what goes wrong in a
content-heavy game is a dangling reference or a rule quietly broken in one
entry out of two hundred, and that is cheap to catch here and expensive to
catch by playing.

Errors fail the build. Warnings are things worth seeing that may be
deliberate, so they are reported and do not fail.
"""

from __future__ import annotations

import sys

from flatline import commands  # noqa: F401  (registers the command table)
from flatline import script as script_mod
from flatline import theme, ui
from flatline.content import attributes as attr_content
from flatline.content import cyberspace, cyberware
from flatline.content import dissonance as drift
from flatline.content import districts
from flatline.content import effects as fx, factions
from flatline.content import hardware, ice as ice_content, icons
from flatline.content import manual, npcs as npc_content
from flatline.content import threads as thread_content
from flatline.content import tutorial as tut
from flatline.content import nodes as node_content
from flatline.content import origins, programs
from flatline.content import rivals as rival_content
from flatline.content import skills
from flatline.content import traits as trait_content
from flatline.model.character import Character
from flatline.shell import CONTEXTS, GROUPS, REGISTRY
from flatline.world import contracts as contract_mod


_COMMAND_SOURCE: str = ''


def _command_source() -> str:
    """The text of every command module, for promise-versus-implementation
    checks that cannot be made any other way."""
    global _COMMAND_SOURCE
    if not _COMMAND_SOURCE:
        import pathlib
        _COMMAND_SOURCE = '\n'.join(
            p.read_text(encoding='utf-8')
            for p in sorted(pathlib.Path('flatline/commands').glob('*.py')))
    return _COMMAND_SOURCE


_ENGINE_SOURCE: str = ''


def _engine_source() -> str:
    """The run layer plus its commands, for promise-versus-implementation
    checks. Content declaring a rider nothing reads is the most expensive
    bug class this project has: it validates, it ships, and it lies."""
    global _ENGINE_SOURCE
    if not _ENGINE_SOURCE:
        import pathlib
        paths = sorted(pathlib.Path('flatline/run').glob('*.py'))
        paths += sorted(pathlib.Path('flatline/commands').glob('*.py'))
        _ENGINE_SOURCE = '\n'.join(p.read_text(encoding='utf-8')
                                   for p in paths)
    return _ENGINE_SOURCE


def _option_of(verb: str) -> str:
    """The `--flag` a technique's verb claims, if any."""
    import re
    match = re.search(r'--([a-z][a-z0-9_-]*)', verb)
    return match.group(1) if match else ''


def _probe_rng():
    """A throwaway stream for validation-time generation probes."""
    from flatline.rng import Rng
    return Rng(1).fork('network', 'validate')


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f'{where}: {msg}')

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f'{where}: {msg}')

    def check(self, cond: bool, where: str, msg: str) -> None:
        if not cond:
            self.error(where, msg)


# --------------------------------------------------------------------------
# effects vocabulary
# --------------------------------------------------------------------------


def check_effects(rep: Report) -> None:
    """Nothing may name a modifier that does not exist (see content/effects)."""
    for w in cyberware.WARE:
        for problems in (fx.check(w.effects, f'cyberware/{w.key}/effects'),
                         fx.check(w.penalty, f'cyberware/{w.key}/penalty')):
            for p in problems:
                rep.error('effects', p)
    for p in programs.PROGRAMS:
        for problem in fx.check(p.effects, f'programs/{p.key}'):
            rep.error('effects', problem)
    for c in hardware.COMPONENTS:
        for problems in (fx.check(c.effects, f'hardware/{c.key}/effects'),
                         fx.check(c.penalty, f'hardware/{c.key}/penalty')):
            for problem in problems:
                rep.error('effects', problem)
    for i in ice_content.ICE:
        for key in i.effects:
            if key not in fx.ALL and key not in ice_content.ICE_RIDERS:
                rep.error('effects',
                          f'ice/{i.key}: unknown effect key {key!r}')


# --------------------------------------------------------------------------
# cyberware
# --------------------------------------------------------------------------


def check_cyberware(rep: Report) -> None:
    for w in cyberware.WARE:
        where = f'cyberware/{w.key}'
        rep.check(w.location in cyberware.SLOTS, where,
                  f'unknown location {w.location!r}')
        rep.check(w.bandwidth > 0, where, 'costs no bandwidth')
        rep.check(w.dissonance > 0, where, 'costs no dissonance')
        rep.check(w.price > 0, where, 'is free')
        rep.check(1 <= w.tier <= 3, where, f'tier {w.tier} out of range')
        # D11: every piece must have an honest downside, stated and mechanical.
        rep.check(bool(w.drawback), where, 'has no stated drawback (D11)')
        if not w.penalty and not w.rider:
            rep.error(where, 'drawback is prose only: needs a penalty dict or '
                             'a rider the engine implements (D11)')
        if w.rider:
            rep.check(w.rider in cyberware.RIDERS, where,
                      f'rider {w.rider!r} is not in RIDERS')

    # Signatures must be unique and each must belong to exactly one origin.
    claimed = [o.signature for o in origins.ORIGINS if o.signature]
    if len(claimed) != len(set(claimed)):
        rep.error('origins', 'two origins claim the same signature ability')
    for sig in origins.SIGNATURES:
        owners = [o.key for o in origins.ORIGINS if o.signature == sig]
        rep.check(len(owners) == 1, 'origins',
                  f'signature {sig!r} is owned by {owners or "nobody"}')

    # Every location must have something worth fitting in it.
    for location in cyberware.SLOTS:
        if not cyberware.by_location(location):
            rep.error('cyberware', f'nothing exists for the {location} slot')

    for rider in cyberware.RIDERS:
        if not any(w.rider == rider for w in cyberware.WARE):
            rep.warn('cyberware', f'rider {rider!r} is declared but unused')


# --------------------------------------------------------------------------
# programs and hardware
# --------------------------------------------------------------------------


def check_programs(rep: Report) -> None:
    for p in programs.PROGRAMS:
        where = f'programs/{p.key}'
        rep.check(p.category in programs.CATEGORIES, where,
                  f'unknown category {p.category!r}')
        rep.check(p.memory > 0, where, 'takes no memory')
        rep.check(1 <= p.rating <= 6, where, f'rating {p.rating} out of range')
        rep.check(p.signature >= 0, where, 'negative signature')
        rep.check(p.price > 0, where, 'is free')
    for category in programs.CATEGORIES:
        if not programs.by_category(category):
            rep.error('programs', f'no programs in category {category!r}')

    # A category whose every member is strictly better than every other is a
    # category with no decision in it.
    for category in programs.CATEGORIES:
        pool = programs.by_category(category)
        if len(pool) < 2:
            continue
        signatures = {p.signature for p in pool}
        if len(signatures) == 1:
            # Passive categories (masks, armour) are never "used" and so have
            # no signature to trade against. They differentiate on memory cost,
            # which is checked by the memory warning instead.
            continue
        best_rating = max(p.rating for p in pool)
        quietest = min(p.signature for p in pool)
        top = [p for p in pool if p.rating == best_rating]
        if any(p.signature == quietest for p in top) and len(pool) > 2:
            rep.warn('programs', f'{category}: the strongest option is also '
                                 f'the quietest, so the loadout choice is free')


def check_hardware(rep: Report) -> None:
    for c in hardware.COMPONENTS:
        where = f'hardware/{c.key}'
        rep.check(c.slot in hardware.SLOTS, where, f'unknown slot {c.slot!r}')
        rep.check(c.heat >= 0, where, 'negative heat')
    for slot in hardware.SLOTS:
        options = hardware.by_slot(slot)
        rep.check(len(options) >= 2, f'hardware/{slot}',
                  'fewer than two options, so the slot is not a choice')

    for preset in hardware.PRESETS:
        where = f'hardware/preset/{preset.key}'
        for slot in hardware.SLOTS:
            key = preset.parts.get(slot)
            if key is None:
                rep.error(where, f'no component for the {slot} slot')
            elif key not in hardware.BY_KEY:
                rep.error(where, f'{slot} points at unknown {key!r}')
            elif hardware.BY_KEY[key].slot != slot:
                rep.error(where, f'{key!r} is a {hardware.BY_KEY[key].slot} '
                                 f'part, fitted to {slot}')
        for key in preset.parts:
            if key not in hardware.SLOTS:
                rep.error(where, f'unknown slot {key!r}')


# --------------------------------------------------------------------------
# origins
# --------------------------------------------------------------------------


def check_icons(rep: Report) -> None:
    """Icons are the fourth build axis and follow the same honesty rule."""
    for i in icons.ICONS:
        where = f'icons/{i.key}'
        rep.check(bool(i.render), where, 'has no render description')
        rep.check(bool(i.blurb), where, 'has no blurb')
        rep.check(bool(i.drawback), where, 'has no stated drawback')
        rep.check(i.coherence >= 0, where, 'negative coherence requirement')
        rep.check(i.price >= 0, where, 'negative price')
        if not i.penalty and not i.rider:
            rep.error(where, 'drawback is prose only: needs a penalty dict or '
                             'a rider the engine implements')
        if i.rider:
            rep.check(i.rider in icons.RIDERS, where,
                      f'rider {i.rider!r} is not in RIDERS')
        for problems in (fx.check(i.effects, f'{where}/effects'),
                         fx.check(i.penalty, f'{where}/penalty')):
            for problem in problems:
                rep.error('effects', problem)

    rep.check(icons.DEFAULT in icons.BY_KEY, 'icons',
              f'DEFAULT icon {icons.DEFAULT!r} does not exist')
    rep.check(icons.BY_KEY[icons.DEFAULT].price == 0, 'icons',
              'the default icon is not free')
    rep.check(icons.BY_KEY[icons.DEFAULT].coherence == 0, 'icons',
              'the default icon cannot be worn by a new character')

    # The coherence penalty must always be a penalty, never a gift.
    for i in icons.ICONS:
        penalty = icons.coherence_penalty(i.key, 0)
        for key, value in penalty.items():
            if key in fx.MULTIPLICATIVE:
                rep.check(value >= 1.0, f'icons/{i.key}',
                          f'coherence gap improves {key}')
            else:
                rep.check(value <= 0, f'icons/{i.key}',
                          f'coherence gap improves {key}')
        rep.check(not icons.coherence_penalty(i.key, 999),
                  f'icons/{i.key}', 'still penalised at maximum Dissonance')


def check_rivals(rep: Report) -> None:
    """Rivals are content and follow the same reference rules as anything else."""
    for r in rival_content.RIVALS:
        where = f'rivals/{r.key}'
        rep.check(r.style in rival_content.STYLES, where,
                  f'unknown style {r.style!r}')
        rep.check(1 <= r.skill <= 10, where, f'skill {r.skill} out of range')
        rep.check(bool(r.blurb and r.manner), where, 'has no description')
        rep.check(bool(r.prefers), where, 'prefers no objectives')
        for objective in r.prefers:
            rep.check(objective in contract_mod.OBJECTIVES, where,
                      f'prefers unknown objective {objective!r}')
        for key in r.standing:
            rep.check(key in factions.BY_KEY, where, f'unknown faction {key!r}')
        rep.check(-100 <= r.disposition <= 100, where,
                  'starting disposition out of range')
        # Every rival can end up as an escort, and an escort that cannot speak
        # when hurt is a missing line at the worst possible moment.
        rep.check(bool(r.panic), where, 'has no panic lines')

    for style in rival_content.STYLES:
        rep.check(style in rival_content.STYLE_BLURB, 'rivals',
                  f'style {style!r} has no blurb')
        if not [r for r in rival_content.RIVALS if r.style == style]:
            rep.warn('rivals', f'no rival uses style {style!r}')

    # The band centred on zero has to contain zero, or a neutral rival reads
    # as hostile on the one screen that shows it.
    rep.check(rival_content.disposition_band(0) == 'neutral', 'rivals',
              f'disposition 0 reads as '
              f'{rival_content.disposition_band(0)!r}, not neutral')
    last = -1000
    for low, name in rival_content.DISPOSITION_BANDS:
        rep.check(low > last, 'rivals', 'disposition bands must ascend')
        last = low

    for outcome in ('clean', 'messy', 'failed', 'dead'):
        rep.check(outcome in rival_content.OUTCOME_LINES, 'rivals',
                  f'no outcome lines for {outcome!r}')
    rep.check(bool(rival_content.TAKEN_LINES), 'rivals', 'no taken lines')

    # -- the social layer ---------------------------------------------
    from flatline.world import rivals as rival_world

    for style in rival_content.STYLES:
        rep.check(style in rival_content.ALLY_SPECIALTY, 'rivals',
                  f'style {style!r} has no ally specialty, so hiring one does '
                  f'nothing')
    for style, pair in rival_content.ALLY_SPECIALTY.items():
        rep.check(style in rival_content.STYLES, 'rivals',
                  f'ally specialty for unknown style {style!r}')
        rep.check(len(pair) == 2 and all(pair), f'rivals/{style}',
                  'ally specialty is incomplete')

    ceiling = rival_content.DISPOSITION_BANDS[-1][0]
    for kind, entry in rival_content.FAVOURS.items():
        where = f'rivals/favour/{kind}'
        rep.check(len(entry) == 3 and all(entry), where, 'favour is incomplete')
        cost = entry[0]
        rep.check(0 < cost <= 100, where, f'cost {cost} out of range')
        # A favour nobody can ever reach is content that does not exist.
        rep.check(cost <= ceiling + 20, where,
                  f'costs {cost}, which is past anything reachable')

    for outcome in ('taken', 'killed', 'escaped'):
        rep.check(outcome in rival_content.SALE_OUTCOMES, 'rivals',
                  f'no sale outcome lines for {outcome!r}')
    for name in ('SALE_LINES', 'SALE_FALLOUT', 'REFUSALS'):
        rep.check(bool(getattr(rival_content, name)), 'rivals',
                  f'{name} is empty')

    # Hiring must be affordable relative to what a contract pays, or the
    # whole social layer is decoration for a build nobody has yet.
    for r in rival_content.RIVALS:
        stub = rival_world.Rival(key=r.key, disposition=r.disposition)
        price = rival_world.hire_price(stub)
        rep.check(price > 0, f'rivals/{r.key}', 'hire price is not positive')
        if price > 6000:
            rep.warn(f'rivals/{r.key}',
                     f'hire price {price:,}c is more than an early contract pays')


def check_dissonance(rep: Report) -> None:
    """The drift arc: bands, passages, and the doors they open and close."""
    floors = tuple(f for f, _, _ in cyberware.DISSONANCE_BANDS)
    rep.check(drift.BANDS == floors, 'dissonance',
              f'band floors {drift.BANDS} disagree with cyberware '
              f'{floors}, so a passage would land on the wrong band')

    # Every band above the first needs writing, or crossing it says nothing.
    for floor in drift.BANDS[1:]:
        passage = drift.BY_BAND.get(floor)
        if passage is None:
            rep.error('dissonance', f'band {floor} has no passage')
            continue
        rep.check(bool(passage.title), f'dissonance/{floor}', 'passage has no title')
        rep.check(len(passage.text) > 80, f'dissonance/{floor}',
                  'passage is too short to be worth firing')
    rep.check(0 not in drift.BY_BAND, 'dissonance',
              'the bottom band has a passage, which would fire at creation')

    last = -1
    for passage in drift.PASSAGES:
        rep.check(passage.band > last, 'dissonance',
                  'passages must be in ascending band order')
        last = passage.band

    # The doors have to sit inside the band range to be reachable.
    for name, value in (('DEEP_CLINIC_BAND', drift.DEEP_CLINIC_BAND),
                        ('RESONANCE_BAND', drift.RESONANCE_BAND),
                        ('SOCIAL_FLOOR_BAND', drift.SOCIAL_FLOOR_BAND)):
        rep.check(0 < value <= 100, 'dissonance',
                  f'{name} is {value}, outside a reachable range')
        rep.check(value in drift.BANDS, 'dissonance',
                  f'{name} is {value}, which is not a band floor')

    rep.check(0 < drift.DEEP_CLINIC_DISCOUNT < 1.0, 'dissonance',
              'the back room is not actually cheaper')
    lo, hi = drift.GROUND_POINTS
    rep.check(0 < lo <= hi, 'dissonance', 'grounding returns a bad range')
    lo, hi = drift.GROUND_HURT
    rep.check(0 < lo <= hi, 'dissonance', 'grounding damage is a bad range')
    rep.check(drift.GROUND_COST > 0, 'dissonance', 'grounding is free')
    rep.check(drift.GROUND_SHIFTS > 0, 'dissonance', 'grounding takes no time')

    for name in ('DEEP_CLINIC_ARRIVAL', 'DEEP_CLINIC_REFUSED', 'RESONANCE_TEXT',
                 'SOCIAL_REFUSED', 'GROUND_TEXT', 'GROUND_FLOOR_TEXT'):
        rep.check(bool(getattr(drift, name)), 'dissonance', f'{name} is empty')

    # The back room must have something to sell, or the arc unlocks nothing.
    restricted = [w for w in cyberware.WARE if w.tier >= 3]
    rep.check(len(restricted) >= 3, 'dissonance',
              f'only {len(restricted)} restricted implants exist, so the back '
              f'room is thin')

    # Legwork gates must name legwork that exists.
    from flatline.commands.city import LEGWORK, LEGWORK_DRIFT
    for key, (kind, threshold) in LEGWORK_DRIFT.items():
        rep.check(key in LEGWORK, 'dissonance',
                  f'drift gate names unknown legwork {key!r}')
        rep.check(kind in ('floor', 'ceiling'), 'dissonance',
                  f'drift gate {key!r} has unknown kind {kind!r}')
        rep.check(threshold in drift.BANDS, 'dissonance',
                  f'drift gate {key!r} sits at {threshold}, not a band floor')
    for key, (cost, blurb, gives) in LEGWORK.items():
        rep.check(bool(blurb), f'legwork/{key}', 'has no description')
        rep.check(cost >= 0, f'legwork/{key}', 'costs a negative amount')


def check_cyberspace(rep: Report) -> None:
    """Every faction has to look like something, or the run reads as a scan."""
    for f in factions.FACTIONS:
        if f.key not in cyberspace.BY_FACTION:
            rep.error('cyberspace', f'{f.key} has no visual signature')
    for sig in cyberspace.SIGNATURES:
        where = f'cyberspace/{sig.faction}'
        rep.check(sig.faction in factions.BY_KEY, where, 'unknown faction')
        rep.check(bool(sig.arrival), where, 'has no arrival text')
        rep.check(bool(sig.ice_wakes), where, 'has no ice-wakes text')
        rep.check(len(sig.texture) >= 3, where, 'has fewer than three textures')

    for n in node_content.NODE_TYPES:
        if n.key not in cyberspace.NODE_LOOK:
            rep.error('cyberspace', f'node type {n.key!r} has no description')
    # Every zone below the perimeter is crossed into and needs descent text.
    for zone in node_content.ZONES[1:]:
        if zone not in cyberspace.DESCENT:
            rep.error('cyberspace', f'zone {zone!r} has no descent text')

    last = 0.0
    for threshold, text in cyberspace.TRACE_PRESSURE:
        rep.check(0.0 < threshold <= 1.0, 'cyberspace',
                  f'trace threshold {threshold} out of range')
        rep.check(threshold > last, 'cyberspace',
                  'trace pressure thresholds must ascend')
        last = threshold
        rep.check(bool(text), 'cyberspace', 'empty trace pressure line')


def check_origins(rep: Report) -> None:
    for o in origins.ORIGINS:
        where = f'origins/{o.key}'
        for key in o.attrs:
            rep.check(key in attr_content.ATTR_KEYS, where,
                      f'unknown attribute {key!r}')
        for key in o.skills:
            rep.check(key in skills.SKILL_KEYS, where, f'unknown skill {key!r}')
        for key in o.cyberware:
            rep.check(key in cyberware.BY_KEY, where,
                      f'unknown cyberware {key!r}')
        for key in o.programs:
            rep.check(key in programs.BY_KEY, where, f'unknown program {key!r}')
        rep.check(o.deck in hardware.PRESETS_BY_KEY, where,
                  f'unknown deck preset {o.deck!r}')
        rep.check(o.icon in icons.BY_KEY, where, f'unknown icon {o.icon!r}')
        for key in o.standing:
            rep.check(key in factions.BY_KEY, where, f'unknown faction {key!r}')
        rep.check(bool(o.passive and o.passive_detail), where,
                  'has no passive')
        # A passive that is only prose is a promise the game does not keep.
        if not o.effects and not o.rider:
            rep.error(where, 'passive has no mechanical half: needs an '
                             'effects dict or a rider the engine implements')
        if o.rider:
            rep.check(o.rider in origins.RIDERS, where,
                      f'rider {o.rider!r} is not in origins.RIDERS')
        for problem in fx.check(o.effects, f'{where}/effects'):
            rep.error('effects', problem)
        rep.check(bool(o.complication), where, 'has no complication')
        # D32: the thing nobody else can do. Without it, two origins with the
        # same numbers are the same origin.
        rep.check(bool(o.signature), where, 'has no signature ability')
        rep.check(o.signature in origins.SIGNATURES, where,
                  f'signature {o.signature!r} is not declared')
        rep.check(bool(o.signature_name and o.signature_detail), where,
                  'signature has no description')
        if o.signature and REGISTRY.lookup(o.signature) is None:
            rep.error(where, f'signature {o.signature!r} names no command')
        rep.check(bool(o.story), where, 'has no story')

        # The build it produces has to be legal, or a new character starts
        # over capacity and every derived number is wrong from turn one.
        char = Character.from_origin(o.key, 'validate')
        if char.bandwidth_used > char.bandwidth:
            rep.error(where, f'starts over bandwidth: '
                             f'{char.bandwidth_used}/{char.bandwidth}')
        for location, capacity in cyberware.SLOTS.items():
            used = char.slots_used(location)
            if used > capacity:
                rep.error(where, f'starts with {used} pieces in {location}, '
                                 f'which holds {capacity}')
        if char.deck.memory_used > char.deck.memory:
            rep.error(where, f'starts over memory: {char.deck.memory_used}/'
                             f'{char.deck.memory}')
        if char.deck.heat > char.deck.heat_cap:
            rep.warn(where, f'starts over thermal budget: {char.deck.heat}/'
                            f'{char.deck.heat_cap}, so the deck cooks at rest')
        # Somebody has to be able to do the objective they are handed.
        if not char.deck.loaded:
            rep.error(where, 'starts with nothing loaded')


# --------------------------------------------------------------------------
# skills
# --------------------------------------------------------------------------


def check_debt(rep: Report) -> None:
    """The debt clock. Above all, it has to be survivable (D6)."""
    from flatline.world import debt as debt_mod

    rep.check(0 < debt_mod.RATE < 0.2, 'debt',
              f'interest of {debt_mod.RATE} per shift is not a rate anybody '
              f'can live with')
    rep.check(debt_mod.GRACE > 0, 'debt', 'no grace period at all')
    rep.check(debt_mod.COLLECT_EVERY > 0, 'debt', 'collection interval is zero')
    rep.check(0 < debt_mod.COLLECT_FRACTION <= 1.0, 'debt',
              'collection fraction out of range')

    # The load-bearing invariant: a collection must remove more than the
    # interest accrued between collections, or the debt is a death sentence
    # and D6 says nothing but black ICE is one.
    growth = (1.0 + debt_mod.RATE) ** debt_mod.COLLECT_EVERY - 1.0
    rep.check(debt_mod.COLLECT_FRACTION > growth, 'debt',
              f'interest grows {growth:.0%} between collections but a '
              f'collection only takes {debt_mod.COLLECT_FRACTION:.0%}, so the '
              f'debt is unpayable and the character is dead (D6)')

    for name in ('FIRST_VISIT', 'IN_KIND'):
        rep.check(bool(getattr(debt_mod, name)), 'debt', f'{name} is empty')
    rep.check(bool(debt_mod.COLLECT_LINES), 'debt', 'no collection lines')


def check_skills(rep: Report) -> None:
    seen: set[str] = set()
    for s in skills.SKILLS:
        where = f'skills/{s.key}'
        rep.check(s.attr in attr_content.ATTR_KEYS, where,
                  f'checks against unknown attribute {s.attr!r}')
        ranks = sorted(t.rank for t in s.techniques)
        rep.check(ranks == [2, 4], where,
                  f'techniques at ranks {ranks}, expected [2, 4] (D10)')
        for t in s.techniques:
            rep.check(t.key not in seen, where, f'duplicate technique {t.key!r}')
            seen.add(t.key)
            rep.check(bool(t.summary and t.detail), f'{where}/{t.key}',
                      'technique has no description')
            if t.verb:
                # A technique that claims a verb has to name a real one, or
                # the skill tree is promising something the shell cannot do.
                head = t.verb.split()[0].split('--')[0].strip()
                if head and REGISTRY.lookup(head) is None:
                    rep.error(f'{where}/{t.key}',
                              f'verb {t.verb!r} names no command')
                # And if it claims an *option*, something has to read it.
                # `crack --chain` shipped for weeks naming a real command and
                # a flag no handler looked at, so the technique unlocked,
                # announced itself, and did nothing. Checking the verb alone
                # is not enough.
                flag = _option_of(t.verb)
                if flag and f"args.has('{flag}')" not in _command_source():
                    rep.error(f'{where}/{t.key}',
                              f'verb {t.verb!r} names an option no command '
                              f'handler reads')

    for rank in range(1, skills.MAX_RANK + 1):
        rep.check(rank in skills.RANK_COST, 'skills',
                  f'no experience cost for rank {rank}')


# --------------------------------------------------------------------------
# factions and districts
# --------------------------------------------------------------------------


def check_factions(rep: Report) -> None:
    # Every place the code branches on faction kind must handle every kind, or
    # adding a faction is a KeyError a player finds rather than the build.
    from flatline.run import network as net_mod
    for kind in factions.KINDS:
        probe = next((f for f in factions.FACTIONS if f.kind == kind), None)
        if probe is None:
            rep.warn('factions', f'no faction of kind {kind!r}')
            continue
        try:
            net_mod.generate(_probe_rng(), probe.key, probe.posture)
        except KeyError as e:
            rep.error('factions',
                      f'generating a {kind!r} network raises KeyError({e}): '
                      f'some branch does not handle this kind')

    for f in factions.FACTIONS:
        where = f'factions/{f.key}'
        rep.check(f.kind in factions.KINDS, where, f'unknown kind {f.kind!r}')
        rep.check(0 <= f.posture <= 100, where, f'posture {f.posture} out of range')
        rep.check(bool(f.doctrine), where, 'has no doctrine')
        for key, value in f.relations.items():
            if key not in factions.BY_KEY:
                rep.error(where, f'relation to unknown faction {key!r}')
                continue
            rep.check(-1.0 <= value <= 1.0, where,
                      f'relation to {key} is {value}, outside -1..1')
            # Asymmetry in a table this small is always a typo.
            back = factions.BY_KEY[key].relations.get(f.key, 0.0)
            if abs(back - value) > 1e-9:
                rep.error(where, f'feels {value} about {key}, but {key} feels '
                                 f'{back} about {f.key}')
        for want in f.wants:
            rep.check(want in contract_mod.OBJECTIVES, where,
                      f'wants unknown objective {want!r}')




def check_districts(rep: Report) -> None:
    for d in districts.DISTRICTS:
        where = f'districts/{d.key}'
        rep.check(d.controller in factions.BY_KEY, where,
                  f'controlled by unknown faction {d.controller!r}')
        for s in d.services:
            rep.check(s in districts.SERVICES, where, f'unknown service {s!r}')
        for p in d.presence:
            rep.check(p in factions.BY_KEY, where, f'unknown faction {p!r}')
        rep.check(bool(d.arrival), where, 'has no arrival text')
        rep.check(1 <= d.max_tier <= 3, where, f'max_tier {d.max_tier}')
        for n in d.neighbours:
            if n not in districts.BY_KEY:
                rep.error(where, f'neighbour {n!r} does not exist')
            elif d.key not in districts.BY_KEY[n].neighbours:
                rep.error(where, f'{n} is a neighbour but does not list '
                                 f'{d.key} back')

    rep.check(districts.START in districts.BY_KEY, 'districts',
              f'START district {districts.START!r} does not exist')

    # Every district must be reachable, or content is stranded.
    seen = {districts.START}
    frontier = [districts.START]
    while frontier:
        key = frontier.pop()
        for n in districts.BY_KEY[key].neighbours:
            if n not in seen:
                seen.add(n)
                frontier.append(n)
    for d in districts.DISTRICTS:
        if d.key not in seen:
            rep.error('districts', f'{d.key} is unreachable from '
                                   f'{districts.START}')

    # Every service has to exist somewhere or a command is unusable.
    for service in districts.SERVICES:
        if not districts.with_service(service):
            rep.error('districts', f'no district offers {service!r}')


# --------------------------------------------------------------------------
# the run layer
# --------------------------------------------------------------------------


def check_ice(rep: Report) -> None:
    for i in ice_content.ICE:
        where = f'ice/{i.key}'
        rep.check(i.behaviour in ice_content.BEHAVIOURS, where,
                  f'unknown behaviour {i.behaviour!r}')
        for f in i.factions:
            rep.check(f in factions.BY_KEY, where, f'unknown faction {f!r}')
        lo, hi = i.rating
        rep.check(0 < lo <= hi, where, f'rating range {i.rating} is backwards')
        rep.check(bool(i.strike), where, 'has no strike line')
        # The fairness contract: anything that can act on the clock must
        # telegraph. Traps are the deliberate exception, and are countered by
        # `probe` rather than by reflexes.
        if i.behaviour == 'trap':
            rep.check(not i.tells, where,
                      'traps must not telegraph: that is what makes them traps')
        else:
            rep.check(len(i.tells) >= 2, where,
                      'needs at least two tells, or it reads identically every '
                      'time it appears')
        if i.behaviour in ('hunter', 'black', 'warden'):
            rep.check(i.damage > 0, where, 'does no damage')

    for behaviour in ice_content.BEHAVIOURS:
        if not ice_content.by_behaviour(behaviour):
            rep.error('ice', f'no constructs with behaviour {behaviour!r}')

    # Every faction needs a warden and a generic fallback, or generation
    # cannot place a chokepoint guard for them.
    for f in factions.FACTIONS:
        for behaviour in ('sentry', 'probe', 'hunter', 'trap', 'warden',
                          'herder'):
            if not ice_content.available(behaviour, f.key):
                rep.error('ice', f'{f.key} has no {behaviour} available')

    # A herder that does damage is a hunter with extra steps. The whole design
    # question it asks depends on it never touching you.
    for i in ice_content.by_behaviour('herder'):
        rep.check(i.damage == 0, f'ice/{i.key}',
                  'a herder must do no damage: it cuts routes, it does not '
                  'fight')
        rep.check(i.effects.get('route_cut'), f'ice/{i.key}',
                  'a herder that does not cut a route does nothing at all')

    # Every declared rider must be read by the engine. Three wardens carried
    # `credential_check` for weeks with nothing anywhere reading it, so the
    # one thing that distinguished them did nothing at all.
    engine = _engine_source()
    for rider in sorted(ice_content.ICE_RIDERS):
        if rider not in engine:
            rep.error('ice', f'rider {rider!r} is declared by content and read '
                             f'nowhere in the run layer')
    for i in ice_content.ICE:
        for key in i.effects:
            if key in ice_content.ICE_RIDERS:
                continue
            if key not in fx.ALL:
                rep.error(f'ice/{i.key}', f'unknown effect {key!r}')

    for level in ice_content.ALERT_LEVELS:
        rep.check(level in ice_content.ALERT_BLURB, 'ice',
                  f'alert level {level!r} has no blurb')
        rep.check(level in ice_content.ALERT_TRACE_MULT, 'ice',
                  f'alert level {level!r} has no trace multiplier')


def check_nodes(rep: Report) -> None:
    for n in node_content.NODE_TYPES:
        where = f'nodes/{n.key}'
        for z in n.zones:
            rep.check(z in node_content.ZONES, where, f'unknown zone {z!r}')
        rep.check(bool(n.zones), where, 'appears in no zone')
        lo, hi = n.services
        rep.check(0 < lo <= hi, where, f'service range {n.services} is backwards')
        found = node_content.services_for(n.key)
        rep.check(bool(found), where, 'services_for returns nothing')
        rep.check(len(found) >= lo, where,
                  f'wants up to {hi} services but only {len(found)} are '
                  f'plausible for it')

    for zone in node_content.ZONES:
        if not [n for n in node_content.NODE_TYPES if zone in n.zones]:
            rep.error('nodes', f'no node type can appear in {zone!r}')
        rep.check(zone in node_content.ZONE_BLURB, 'nodes',
                  f'zone {zone!r} has no blurb')

    for s in node_content.SERVICES:
        where = f'services/{s.key}'
        rep.check(s.family in node_content.FAMILIES, where,
                  f'unknown family {s.family!r}')
        lo, hi = s.difficulty
        rep.check(0 < lo <= hi, where, f'difficulty {s.difficulty} is backwards')

    for family, (skill_key, category) in node_content.FAMILIES.items():
        rep.check(skill_key in skills.SKILL_KEYS, 'nodes',
                  f'family {family!r} names unknown skill {skill_key!r}')
        rep.check(category in programs.CATEGORIES, 'nodes',
                  f'family {family!r} names unknown category {category!r}')
        if not [s for s in node_content.SERVICES if s.family == family]:
            rep.error('nodes', f'no services in family {family!r}')

    for d in node_content.DATA_KINDS:
        lo, hi = d.value
        rep.check(0 < lo <= hi, f'data/{d.key}', f'value {d.value} is backwards')


# --------------------------------------------------------------------------
# contracts
# --------------------------------------------------------------------------


def check_contracts(rep: Report) -> None:
    for o in contract_mod.OBJECTIVES:
        rep.check(o in contract_mod.OBJECTIVE_BLURB, 'contracts',
                  f'objective {o!r} has no blurb')
        rep.check(o in contract_mod.OBJECTIVE_PAY, 'contracts',
                  f'objective {o!r} has no pay multiplier')
        rep.check(o in contract_mod.OBJECTIVE_PROGRAM, 'contracts',
                  f'objective {o!r} does not declare its required program')
        rep.check(o in contract_mod._FRAMES, 'contracts',
                  f'objective {o!r} has no blurb frames')
        need = contract_mod.OBJECTIVE_PROGRAM.get(o)
        if need:
            rep.check(need in programs.CATEGORIES, 'contracts',
                      f'objective {o!r} needs unknown category {need!r}')
    # Somebody has to want each objective, or it never appears on a board.
    wanted = {w for f in factions.FACTIONS for w in f.wants}
    for o in contract_mod.OBJECTIVES:
        if o not in wanted:
            rep.warn('contracts', f'no faction wants {o!r}, so it is rare')


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def check_scripting(rep: Report) -> None:
    """The scripting language, per D22, and everything it ships with."""
    for name, (reader, blurb) in script_mod.NUMERIC.items():
        rep.check(bool(blurb), f'script/{name}', 'condition has no description')
        rep.check(callable(reader), f'script/{name}', 'condition has no reader')
    for name, (reader, blurb) in script_mod.FLAGS.items():
        rep.check(bool(blurb), f'script/{name}', 'flag has no description')
        rep.check(callable(reader), f'script/{name}', 'flag has no reader')
    overlap = set(script_mod.NUMERIC) & set(script_mod.FLAGS)
    rep.check(not overlap, 'script',
              f'names are both numeric and flags: {sorted(overlap)}')
    rep.check('alert' not in script_mod.NUMERIC
              and 'alert' not in script_mod.FLAGS, 'script',
              'alert must stay its own case, not a number or a flag')

    # Every shipped example must parse, and every command it names must exist.
    for name, lines in script_mod.EXAMPLES.items():
        where = f'script/example/{name}'
        try:
            steps = script_mod.parse(lines)
        except script_mod.ScriptError as e:
            rep.error(where, f'does not parse: {e}')
            continue
        rep.check(bool(steps), where, 'is empty')
        for step in steps:
            if not step.command:
                continue
            head = step.command.split()[0].lower()
            if REGISTRY.lookup(head) is None:
                # Two-word verbs like `jack out` resolve on the pair.
                pair = ' '.join(step.command.split()[:2]).lower()
                if REGISTRY.lookup(pair) is None:
                    rep.error(where, f'names no command: {step.command!r}')
        rep.check(any(s.condition is not None for s in steps), where,
                  'has no conditions, so it teaches nothing a macro would not')

    rep.check(script_mod.MAX_STEPS > 0, 'script', 'MAX_STEPS is not positive')
    rep.check(script_mod.MAX_DISPATCH >= script_mod.MAX_STEPS, 'script',
              'MAX_DISPATCH is below MAX_STEPS, so a legal script cannot run')


def check_traits(rep: Report) -> None:
    """Traits follow the same honesty rule as chrome, origins and icons."""
    engine = _engine_source() + _command_source()
    for t in trait_content.TRAITS:
        where = f'traits/{t.key}'
        rep.check(t.group in trait_content.GROUPS, where,
                  f'unknown group {t.group!r}')
        rep.check(bool(t.blurb), where, 'has no description')
        rep.check(bool(t.drawback), where, 'has no stated drawback')
        if not t.effects:
            rep.error(where, 'has no benefit, so nobody would ever take it')
        if not t.penalty and not t.rider:
            rep.error(where, 'drawback is prose only: needs a penalty dict or '
                             'a rider the engine implements')
        if t.rider:
            rep.check(t.rider in trait_content.RIDERS, where,
                      f'rider {t.rider!r} is not in traits.RIDERS')
        for problems in (fx.check(t.effects, f'{where}/effects'),
                         fx.check(t.penalty, f'{where}/penalty')):
            for problem in problems:
                rep.error('effects', problem)
        for other in t.excludes:
            rep.check(other in trait_content.BY_KEY, where,
                      f'excludes unknown trait {other!r}')
            back = trait_content.BY_KEY.get(other)
            if back and t.key not in back.excludes:
                rep.error(where, f'excludes {other!r}, which does not exclude '
                                 f'it back')

    for rider in sorted(trait_content.RIDERS):
        if rider not in engine:
            rep.error('traits', f'rider {rider!r} is declared and read nowhere')
        if not any(t.rider == rider for t in trait_content.TRAITS):
            rep.warn('traits', f'rider {rider!r} is declared but unused')

    for group in trait_content.GROUPS:
        rep.check(group in trait_content.GROUP_TITLES, 'traits',
                  f'group {group!r} has no title')
        if not [t for t in trait_content.TRAITS if t.group == group]:
            rep.warn('traits', f'group {group!r} is empty')

    # The pool has to be much larger than the slots, or every character
    # converges on the same picks and the axis does nothing.
    rep.check(len(trait_content.TRAITS) >= trait_content.MAX_TRAITS * 4,
              'traits',
              f'{len(trait_content.TRAITS)} traits for '
              f'{trait_content.MAX_TRAITS} slots is not enough spread')
    rep.check(trait_content.CREATION_PICKS < trait_content.MAX_TRAITS,
              'traits', 'creation hands out every slot at once')

    # A fresh character must be able to pick, and exclusions must never
    # empty the pool.
    fresh = Character.from_origin('gutter', 'validate')
    rep.check(len(trait_content.available(fresh.traits, fresh)) > 10,
              'traits', 'too few traits open to a new character')
    for t in trait_content.TRAITS:
        after = trait_content.available([t.key], fresh)
        rep.check(len(after) >= 5, f'traits/{t.key}',
                  'taking it closes off almost everything else')


def check_npcs(rep: Report) -> None:
    """The cast. Its job is range, so the range is checked."""
    for n in npc_content.NPCS:
        where = f'npcs/{n.key}'
        rep.check(n.tone in npc_content.TONES, where, f'unknown tone {n.tone!r}')
        rep.check(bool(n.offers), where, 'offers nothing at all')
        for offer in n.offers:
            rep.check(offer in npc_content.OFFERS, where,
                      f'unknown offer {offer!r}')
        rep.check(bool(n.first and n.manner), where, 'has no introduction')
        rep.check(len(n.lines) >= 2, where,
                  'has fewer than two lines, so they repeat immediately')
        if n.where:
            rep.check(n.where in districts.BY_KEY, where,
                      f'lives in unknown district {n.where!r}')
            if n.at:
                rep.check(n.at in districts.BY_KEY[n.where].services, where,
                          f'needs a {n.at} and {n.where} has none')
        if n.at:
            rep.check(n.at in districts.SERVICES, where,
                      f'unknown service {n.at!r}')
        for rule in n.requires:
            kind = rule.split(':')[0]
            rep.check(kind in ('runs', 'diss', 'heat', 'rep'), where,
                      f'unknown requirement {rule!r}')

    # A city of one register is a city with one joke in it.
    from collections import Counter
    tones = Counter(n.tone for n in npc_content.NPCS)
    for tone in npc_content.TONES:
        if not tones.get(tone):
            rep.warn('npcs', f'nobody is written in the {tone!r} register')
    top = tones.most_common(1)[0][1]
    rep.check(top <= len(npc_content.NPCS) * 0.4, 'npcs',
              f'{top} of {len(npc_content.NPCS)} share one tone; the cast is '
              f'too samey')

    # Somebody has to be findable before the player has done anything.
    early = [n for n in npc_content.NPCS if not n.requires]
    rep.check(len(early) >= 6, 'npcs',
              'too few people are findable by a brand new character')


def check_threads(rep: Report) -> None:
    """Storylines: reachable, crossing both ways, and never stranded."""
    sets = thread_content.flags_set()
    for t in thread_content.THREADS:
        where = f'threads/{t.key}'
        rep.check(bool(t.stages), where, 'has no stages')
        rep.check(bool(t.blurb), where, 'has no blurb')
        keys = [st.key for st in t.stages]
        rep.check(len(keys) == len(set(keys)), where, 'duplicate stage keys')
        for other in t.crosses:
            rep.check(other in thread_content.BY_KEY, where,
                      f'crosses unknown thread {other!r}')
            back = thread_content.BY_KEY.get(other)
            if back and t.key not in back.crosses:
                rep.error(where, f'crosses {other!r}, which does not cross '
                                 f'it back')
        for st in t.stages:
            sw = f'{where}/{st.key}'
            rep.check(bool(st.headline and st.text), sw, 'is empty')
            for rule in tuple(st.requires) + tuple(st.any_of):
                if ':' in rule:
                    kind = rule.split(':')[0]
                    rep.check(kind in thread_content.CONDITIONS, sw,
                              f'unknown condition {kind!r}')
                elif rule not in sets:
                    rep.error(sw, f'requires flag {rule!r}, which nothing '
                                  f'sets: this stage is unreachable')
            ckeys = [c.key for c in st.choices]
            rep.check(len(ckeys) == len(set(ckeys)), sw, 'duplicate choices')
            for choice in st.choices:
                rep.check(bool(choice.label and choice.text),
                          f'{sw}/{choice.key}', 'is empty')
                for faction in choice.rep:
                    rep.check(faction in factions.BY_KEY, f'{sw}/{choice.key}',
                              f'unknown faction {faction!r}')
                for rival in choice.disposition:
                    rep.check(rival in rival_content.BY_KEY,
                              f'{sw}/{choice.key}',
                              f'unknown rival {rival!r}')

    # Two origin-gated threads can never both exist on one character, so a
    # crossing between them is impossible rather than merely unshared.
    def _origin_of(thread):
        for st in thread.stages:
            for rule in tuple(st.requires) + tuple(st.any_of):
                if rule.startswith('origin:'):
                    return rule.split(':', 1)[1]
        return ''

    for t in thread_content.THREADS:
        mine = _origin_of(t)
        if not mine:
            continue
        for other_key in t.crosses:
            theirs = _origin_of(thread_content.BY_KEY[other_key])
            if theirs and theirs != mine:
                rep.error(f'threads/{t.key}',
                          f'crosses {other_key!r}, but they belong to '
                          f'different origins and can never both exist')

    # Every thread must have at least one stage a new character can reach,
    # or it exists and nobody will ever see it.
    for t in thread_content.THREADS:
        openers = [st for st in t.stages
                   if all(':' in r or r not in sets for r in st.requires)
                   or not st.requires]
        rep.check(bool(openers), f'threads/{t.key}',
                  'has no stage that can be reached first')

    # And the crossing has to be real: a thread that shares no flag with the
    # thread it claims to cross is a claim rather than a design.
    for t in thread_content.THREADS:
        mine = set()
        for st in t.stages:
            mine.update(st.sets)
            for c in st.choices:
                mine.update(c.sets)
        for other_key in t.crosses:
            other = thread_content.BY_KEY[other_key]
            theirs = set()
            wants = set()
            for st in other.stages:
                theirs.update(st.sets)
                wants.update(r for r in tuple(st.requires) + tuple(st.any_of)
                             if ':' not in r)
                for c in st.choices:
                    theirs.update(c.sets)
            mywants = {r for st in t.stages
                       for r in tuple(st.requires) + tuple(st.any_of)
                       if ':' not in r}
            # An NPC shared between two threads is also a crossing: both are
            # gated on the same person.
            npcs_mine = {r for st in t.stages
                         for r in tuple(st.requires) + tuple(st.any_of)
                         if r.startswith('met:')}
            npcs_theirs = {r for st in other.stages
                           for r in tuple(st.requires) + tuple(st.any_of)
                           if r.startswith('met:')}
            shared = ((mine & wants) or (theirs & mywants)
                      or (npcs_mine & npcs_theirs))
            if not shared:
                rep.warn(f'threads/{t.key}',
                         f'claims to cross {other_key!r} but shares no flag '
                         f'with it')


def check_manual(rep: Report) -> None:
    """The manual has to be reachable, linked correctly, and about something."""
    for t in manual.TOPICS:
        where = f'manual/{t.key}'
        rep.check(bool(t.title and t.summary), where, 'has no title or summary')
        rep.check(len(t.body) > 200, where, 'body is too short to be help')
        rep.check(t.group in manual.GROUPS, where, f'unknown group {t.group!r}')
        for link in t.see:
            rep.check(link in manual.BY_KEY, where,
                      f'links to unknown topic {link!r}')
            rep.check(link != t.key, where, 'links to itself')
        for name in t.commands:
            if REGISTRY.lookup(name) is None:
                rep.error(where, f'names no command: {name!r}')
        # The rule this file is written under: a topic that explains a number
        # without saying what to do differently is a glossary entry.
        # Phrasing varies; substance does not. A topic must tell the player
        # something to do differently, however it words it.
        markers = ('decision', 'The mistake', 'tension', 'The rule',
                   'you can always ask', 'obliged to show')
        if not any(m in t.body for m in markers):
            rep.warn(where, 'does not close on a decision')

    for group in manual.GROUPS:
        rep.check(group in manual.GROUP_TITLES, 'manual',
                  f'group {group!r} has no title')
        if not [t for t in manual.TOPICS if t.group == group]:
            rep.warn('manual', f'group {group!r} is empty')

    # Every topic must be reachable from another topic or the starter set,
    # or it exists and nobody will ever find it.
    linked = set(manual.STARTER)
    for t in manual.TOPICS:
        linked.update(t.see)
    for t in manual.TOPICS:
        if t.key not in linked:
            rep.warn(f'manual/{t.key}', 'nothing links to it')
    for key in manual.STARTER:
        rep.check(key in manual.BY_KEY, 'manual',
                  f'STARTER names unknown topic {key!r}')


def check_tutorial(rep: Report) -> None:
    """Tutorial conditions run after every command. They must be total."""
    class _Empty:
        game = None
        run = None
        seen: set = set()

    blank = _Empty()
    for step in tut.STEPS:
        where = f'tutorial/{step.key}'
        rep.check(bool(step.instruction), where, 'has no instruction')
        rep.check(bool(step.why), where, 'has no reason, so it teaches nothing')
        rep.check(callable(step.done), where, 'has no condition')
        if step.topic:
            rep.check(step.topic in manual.BY_KEY, where,
                      f'points at unknown topic {step.topic!r}')
        # A condition that raises would take the shell down mid-run, and the
        # tutorial is optional: it is never worth a traceback.
        try:
            result = step.done(blank)
            rep.check(isinstance(result, bool) or result in (0, 1), where,
                      f'condition returned {result!r}, not a truth value')
        except Exception as e:
            rep.error(where, f'condition raises on an empty session: {e!r}')

    keys = [s.key for s in tut.STEPS]
    rep.check(len(keys) == len(set(keys)), 'tutorial', 'duplicate step keys')
    rep.check(bool(tut.OPENING and tut.CLOSING), 'tutorial',
              'missing opening or closing text')
    for name in tut.WATCHED:
        rep.check(REGISTRY.lookup(name) is not None, 'tutorial',
                  f'WATCHED names no command: {name!r}')


def check_commands(rep: Report) -> None:
    for name, cmd in REGISTRY.commands.items():
        where = f'commands/{name}'
        rep.check(bool(cmd.summary), where, 'has no summary (D9)')
        rep.check(bool(cmd.usage), where,
                  'has no usage line, so `help` cannot show how to type it')
        rep.check(cmd.group in GROUPS, where, f'unknown group {cmd.group!r}')
        for c in cmd.contexts:
            rep.check(c in CONTEXTS, where, f'unknown context {c!r}')
        rep.check(bool(cmd.contexts), where, 'is legal nowhere')
        if cmd.summary and not cmd.summary[0].isupper():
            rep.warn(where, 'summary does not start with a capital')
        if cmd.summary and not cmd.summary.endswith('.'):
            rep.warn(where, 'summary does not end with a full stop')
        if cmd.ticks and 'run' not in cmd.contexts:
            rep.error(where, 'costs ticks but is not a run command')
        # D9's whole point: `market` must not exist while you are inside
        # somebody's network. `contexts` defaults to ('any',), so anything
        # that transacts, travels, spends shifts or changes the build has to
        # say so explicitly. Twenty-seven of them did not, and were legal
        # mid-run for weeks.
        if cmd.group in ('city', 'prep') and 'any' in cmd.contexts:
            if cmd.name not in ('look',):
                rep.error(where, 'is city work but is legal inside a run: '
                                 "declare contexts=('city',)")

    # Both contexts need to be usable on their own.
    for context in ('city', 'run'):
        available = REGISTRY.in_context(context)
        rep.check(len(available) >= 5, 'commands',
                  f'only {len(available)} commands work in {context}')

    # Every group that exists should have something in it.
    for group in GROUPS:
        if not [c for c in REGISTRY.commands.values() if c.group == group]:
            rep.warn('commands', f'group {group!r} is empty')

    # The run command table must price every verb it claims to price.
    from flatline.commands.run import COST
    for verb in COST:
        head = verb.split()[0]
        if REGISTRY.lookup(verb) is None and REGISTRY.lookup(head) is None:
            rep.error('commands', f'COST prices {verb!r}, which is not a command')


# --------------------------------------------------------------------------
# presentation
# --------------------------------------------------------------------------


def check_theme(rep: Report) -> None:
    for name, palette in theme.PALETTES.items():
        for role in theme.ROLES:
            colour = getattr(palette, role, None)
            if colour is None:
                rep.error(f'theme/{name}', f'missing role {role!r}')
                continue
            rep.check(colour.ansi in theme.ANSI16, f'theme/{name}/{role}',
                      f'unknown ANSI name {colour.ansi!r}')
            try:
                int(colour.hex.lstrip('#'), 16)
            except ValueError:
                rep.error(f'theme/{name}/{role}', f'bad hex {colour.hex!r}')

    # D16: the ASCII rung must actually be ASCII.
    for name, (uni, ascii_form) in ui.GLYPHS.items():
        if not ascii_form.isascii():
            rep.error('ui/glyphs', f'{name!r} ASCII form is not ASCII: '
                                   f'{ascii_form!r}')


def check_markup(rep: Report) -> None:
    """Every role named in content markup has to exist.

    This is the check that stops `[acccent]` from silently rendering plain.
    """
    known = set(theme.ROLES) | ui.ATTRS
    sources: list[tuple[str, str]] = []

    def collect(where: str, text) -> None:
        if isinstance(text, str):
            sources.append((where, text))

    for o in origins.ORIGINS:
        for field in ('blurb', 'story', 'passive_detail', 'complication'):
            collect(f'origins/{o.key}', getattr(o, field))
    for w in cyberware.WARE:
        collect(f'cyberware/{w.key}', w.blurb)
        collect(f'cyberware/{w.key}', w.drawback)
    for n in npc_content.NPCS:
        collect(f'npcs/{n.key}', n.first)
        collect(f'npcs/{n.key}', n.manner)
        for line in n.lines:
            collect(f'npcs/{n.key}/line', line)
        for topic, text in n.topics.items():
            collect(f'npcs/{n.key}/{topic}', text)
    for t in thread_content.THREADS:
        collect(f'threads/{t.key}', t.blurb)
        for st in t.stages:
            collect(f'threads/{t.key}/{st.key}', st.headline)
            for para in st.text.split('\n\n'):
                collect(f'threads/{t.key}/{st.key}', para)
            for ch in st.choices:
                collect(f'threads/{t.key}/{st.key}/{ch.key}', ch.label)
                for para in ch.text.split('\n\n'):
                    collect(f'threads/{t.key}/{st.key}/{ch.key}', para)
    for t in trait_content.TRAITS:
        collect(f'traits/{t.key}', t.blurb)
        collect(f'traits/{t.key}', t.drawback)
    for t in manual.TOPICS:
        collect(f'manual/{t.key}', t.summary)
    for step in tut.STEPS:
        collect(f'tutorial/{step.key}', step.instruction)
        collect(f'tutorial/{step.key}', step.why)
        collect(f'tutorial/{step.key}', step.payoff)
    for r in rival_content.RIVALS:
        collect(f'rivals/{r.key}', r.blurb)
        collect(f'rivals/{r.key}', r.manner)
        for line in r.panic:
            collect(f'rivals/{r.key}/panic', line)
    for passage in drift.PASSAGES:
        collect(f'dissonance/{passage.band}', passage.text)
    for i in icons.ICONS:
        collect(f'icons/{i.key}', i.blurb)
        collect(f'icons/{i.key}', i.render)
        collect(f'icons/{i.key}', i.drawback)
    for n in npc_content.NPCS:
        collect(f'npcs/{n.key}', n.first)
        collect(f'npcs/{n.key}', n.manner)
        for line in n.lines:
            collect(f'npcs/{n.key}/line', line)
        for topic, text in n.topics.items():
            collect(f'npcs/{n.key}/{topic}', text)
    for t in thread_content.THREADS:
        collect(f'threads/{t.key}', t.blurb)
        for st in t.stages:
            collect(f'threads/{t.key}/{st.key}', st.headline)
            for para in st.text.split('\n\n'):
                collect(f'threads/{t.key}/{st.key}', para)
            for ch in st.choices:
                collect(f'threads/{t.key}/{st.key}/{ch.key}', ch.label)
                for para in ch.text.split('\n\n'):
                    collect(f'threads/{t.key}/{st.key}/{ch.key}', para)
    for t in trait_content.TRAITS:
        collect(f'traits/{t.key}', t.blurb)
        collect(f'traits/{t.key}', t.drawback)
    for t in manual.TOPICS:
        collect(f'manual/{t.key}', t.summary)
    for step in tut.STEPS:
        collect(f'tutorial/{step.key}', step.instruction)
        collect(f'tutorial/{step.key}', step.why)
        collect(f'tutorial/{step.key}', step.payoff)
    for r in rival_content.RIVALS:
        collect(f'rivals/{r.key}', r.blurb)
        collect(f'rivals/{r.key}', r.manner)
        for line in r.panic:
            collect(f'rivals/{r.key}/panic', line)
    for sig in cyberspace.SIGNATURES:
        collect(f'cyberspace/{sig.faction}', sig.arrival)
        collect(f'cyberspace/{sig.faction}', sig.ice_wakes)
    for key, options in cyberspace.NODE_LOOK.items():
        for text in options:
            collect(f'cyberspace/node/{key}', text)
    for key, options in cyberspace.DESCENT.items():
        for text in options:
            collect(f'cyberspace/descent/{key}', text)
    for _, text in cyberspace.TRACE_PRESSURE:
        collect('cyberspace/pressure', text)
    for p in programs.PROGRAMS:
        collect(f'programs/{p.key}', p.blurb)
        collect(f'programs/{p.key}', p.note)
    for i in ice_content.ICE:
        collect(f'ice/{i.key}', i.blurb)
        collect(f'ice/{i.key}', i.strike)
        for tell in i.tells:
            collect(f'ice/{i.key}/tell', tell)
    for d in districts.DISTRICTS:
        collect(f'districts/{d.key}', d.blurb)
        collect(f'districts/{d.key}', d.arrival)
    for f in factions.FACTIONS:
        collect(f'factions/{f.key}', f.blurb)
        collect(f'factions/{f.key}', f.doctrine)
    for cmd in REGISTRY.commands.values():
        collect(f'commands/{cmd.name}', cmd.summary)
        collect(f'commands/{cmd.name}', cmd.detail)

    for where, text in sources:
        for span in ui.parse(text):
            if span.role and span.role not in known:
                rep.error('markup', f'{where}: unknown role {span.role!r}')

    # Content is authored to fit the reading column at the ASCII rung.
    caps = ui.Caps(color=ui.ColorLevel.NONE, glyphs=ui.GlyphLevel.ASCII,
                   width=80, palette=theme.NEUTRAL)
    for where, text in sources:
        for line in ui.wrap(text, caps.text_width):
            if ui.width(line) > caps.text_width:
                rep.error('layout', f'{where}: a line exceeds '
                                    f'{caps.text_width} columns after wrapping')


# --------------------------------------------------------------------------
# balance sanity
# --------------------------------------------------------------------------


def check_balance(rep: Report) -> None:
    """Cheap invariants that catch a decimal point in the wrong place."""
    for w in cyberware.WARE:
        # Price should track what it costs you to wear.
        weight = w.bandwidth * 900 + w.dissonance * 240
        if w.price > weight * 4.5:
            rep.warn(f'cyberware/{w.key}',
                     f'{w.price}c looks steep for {w.bandwidth}bw/'
                     f'{w.dissonance}dis')
    for p in programs.PROGRAMS:
        if p.memory > 4:
            rep.warn(f'programs/{p.key}', f'{p.memory} memory is more than the '
                                          f'smallest bank holds')
    smallest = min(c.effects.get('memory', 0) for c in hardware.by_slot('memory'))
    rep.check(smallest >= 3, 'hardware',
              f'the smallest memory bank holds {smallest}, which cannot carry '
              f'a working loadout')
    # Attributes must produce sane derived values across their whole range.
    for value in range(attr_content.ATTR_MIN, attr_content.ATTR_MAX + 1):
        rep.check(attr_content.bandwidth(value) > 0, 'attributes',
                  f'bandwidth({value}) is not positive')
        rep.check(attr_content.integrity(value) > 0, 'attributes',
                  f'integrity({value}) is not positive')
        rep.check(1 <= attr_content.tempo(value) <= 3, 'attributes',
                  f'tempo({value}) = {attr_content.tempo(value)} out of range')


# --------------------------------------------------------------------------


CHECKS = (
    check_effects, check_cyberware, check_programs, check_hardware,
    check_icons, check_dissonance, check_cyberspace, check_rivals, check_debt,
    check_origins, check_skills, check_factions, check_districts,
    check_ice, check_nodes, check_contracts, check_commands,
    check_traits, check_scripting, check_npcs, check_threads,
    check_manual, check_tutorial, check_theme, check_markup, check_balance,
)


def main() -> int:
    rep = Report()
    for check in CHECKS:
        check(rep)

    for w in rep.warnings:
        print(f'warning  {w}')
    for e in rep.errors:
        print(f'ERROR    {e}')

    counts = (f'{len(rep.errors)} error{"s" if len(rep.errors) != 1 else ""}, '
              f'{len(rep.warnings)} warning'
              f'{"s" if len(rep.warnings) != 1 else ""}')
    if rep.errors:
        print(f'\nvalidate: {counts}')
        return 1
    print(f'validate: clean ({counts})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
