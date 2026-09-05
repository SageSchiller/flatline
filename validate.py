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

import pathlib
import sys

from flatline import commands  # noqa: F401  (registers the command table)
from flatline import script as script_mod
from flatline import theme, ui
from flatline.content import appearance
from flatline.content import events
from flatline.content import rice
from flatline.content import shifts
from flatline.world import city as city_mod
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
_MODEL_SOURCE: str = ''
_WORLD_SOURCE: str = ''
_CONTENT_SOURCE: str = ''
_SESSION_SOURCE: str = ''


def _model_source() -> str:
    """The character model, for checks about things a build carries."""
    global _MODEL_SOURCE
    if not _MODEL_SOURCE:
        import pathlib
        _MODEL_SOURCE = '\n'.join(
            p.read_text(encoding='utf-8')
            for p in sorted(pathlib.Path('flatline/model').glob('*.py')))
    return _MODEL_SOURCE


def _content_source() -> str:
    """Every content module, for checks about a field being consumed at all."""
    global _CONTENT_SOURCE
    if not _CONTENT_SOURCE:
        import pathlib
        _CONTENT_SOURCE = '\n'.join(
            p.read_text(encoding='utf-8')
            for p in sorted(pathlib.Path('flatline/content').glob('*.py')))
    return _CONTENT_SOURCE


def _session_source() -> str:
    """The session and app modules, which own the meta counters."""
    global _SESSION_SOURCE
    if not _SESSION_SOURCE:
        import pathlib
        _SESSION_SOURCE = '\n'.join(
            pathlib.Path(f'flatline/{n}.py').read_text(encoding='utf-8')
            for n in ('session', 'app', 'save', 'anim', 'prompt'))
    return _SESSION_SOURCE


def _world_source() -> str:
    """The city layer, for checks about consequences landing."""
    global _WORLD_SOURCE
    if not _WORLD_SOURCE:
        import pathlib
        _WORLD_SOURCE = '\n'.join(
            p.read_text(encoding='utf-8')
            for p in sorted(pathlib.Path('flatline/world').glob('*.py')))
    return _WORLD_SOURCE


def _engine_source() -> str:
    """The run layer plus its commands, for promise-versus-implementation
    checks. Content declaring a rider nothing reads is the most expensive
    bug class this project has: it validates, it ships, and it lies."""
    global _ENGINE_SOURCE
    if not _ENGINE_SOURCE:
        import pathlib
        paths = sorted(pathlib.Path('flatline/run').glob('*.py'))
        paths += sorted(pathlib.Path('flatline/commands').glob('*.py'))
        # The street and the fight (D65, D128) read riders too, and the
        # session writes the record's counters (D142).
        paths += sorted(pathlib.Path('flatline/world').glob('*.py'))
        paths.append(pathlib.Path('flatline/session.py'))
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
        if p.rider:
            rep.check(p.rider in programs.RIDERS, where,
                      f'rider {p.rider!r} is not in RIDERS')
        if p.jobs:
            rep.check(p.category == 'payload', where,
                      'declares jobs and is not a payload')
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



def check_appearance(rep: Report) -> None:
    """Appearance is content that has to survive the same honesty rule.

    Two failure modes are specific to it. A feature that moves neither number
    and carries no effects is a costume item in a game that promised every
    choice weighs something. And an earned mark the engine never awards is the
    recurring bug in this project wearing a new hat: it validates, it ships,
    and no character ever gets it.
    """
    engine = (_engine_source() + _command_source() + _model_source()
              + _world_source())

    seen: set[tuple[str, str]] = set()
    for f in appearance.FEATURES:
        where = f'appearance/{f.slot}/{f.key}'
        rep.check(f.slot in appearance.SLOT_BY_KEY, where,
                  f'unknown slot {f.slot!r}')
        rep.check(bool(f.look), where, 'has no description')
        rep.check((f.slot, f.key) not in seen, where, 'duplicate key in slot')
        seen.add((f.slot, f.key))
        if not f.memorable and not f.presence and not f.effects:
            rep.error(where, 'moves nothing: it is a costume, not a choice')
        # The description completes a sentence stem, so it must not start with
        # a capital or end with punctuation the assembler adds itself.
        rep.check(not f.look[0].isupper(), where,
                  'description is capitalised, but it follows a sentence stem')
        rep.check(not f.look.rstrip().endswith(('.', ',')), where,
                  'description ends with punctuation the assembler adds')
        for problem in fx.check(f.effects, f'{where}/effects'):
            rep.error('effects', problem)

    for slot in appearance.SLOTS:
        options = appearance.BY_SLOT[slot.key]
        rep.check(len(options) >= 8, f'appearance/{slot.key}',
                  f'only {len(options)} options; a slot with fewer than eight '
                  f'is a dropdown, not a decision')
        rep.check(bool(slot.stem) and bool(slot.blurb),
                  f'appearance/{slot.key}', 'missing stem or blurb')
        # At least one option in each direction, or the slot has no trade in it.
        rep.check(any(o.memorable < 0 for o in options)
                  and any(o.memorable > 0 for o in options),
                  f'appearance/{slot.key}',
                  'every option pushes memorable the same way, so the slot is '
                  'a tax rather than a choice')

    for f in appearance.EARNED:
        where = f'appearance/earned/{f.key}'
        rep.check(f.slot == 'marks', where, 'earned features must be marks')
        rep.check(f"mark('{f.key}')" in engine, where,
                  'nothing in the engine ever awards this mark')
        rep.check(f.key not in {x.key for x in appearance.BY_SLOT['marks']},
                  where, 'collides with a choosable mark of the same key')

    # Every origin arrives wearing something, and it has to be legal.
    for o in origins.ORIGINS:
        where = f'origins/{o.key}/look'
        rep.check(set(o.look) == set(appearance.SLOT_KEYS), where,
                  f'covers {sorted(o.look)} rather than every slot')
        for slot_key, key in o.look.items():
            rep.check((slot_key, key) in appearance.BY_KEY, where,
                      f'{slot_key}={key!r} is not a feature')

    # Two origins wearing the same face defeats the point of the field.
    faces = {}
    for o in origins.ORIGINS:
        sig = tuple(sorted(o.look.items()))
        rep.check(sig not in faces, f'origins/{o.key}/look',
                  f'identical to {faces.get(sig)}')
        faces[sig] = o.key

    # The bands have to cover the whole range the content can produce.
    lo = sum(min(f.memorable for f in appearance.BY_SLOT[s.key])
             for s in appearance.SLOTS)
    hi = (sum(max(f.memorable for f in appearance.BY_SLOT[s.key])
              for s in appearance.SLOTS)
          + sum(f.memorable for f in appearance.EARNED))
    rep.check(appearance.BANDS[0][0] <= lo, 'appearance/bands',
              f'lowest reachable memorable is {lo}, below the first band')
    rep.check(appearance.BANDS[-1][0] <= hi, 'appearance/bands',
              f'highest band starts at {appearance.BANDS[-1][0]} but the '
              f'content only reaches {hi}, so it is unreachable')

    # Surgery. The `self` command refuses a fixed slot by telling the player
    # to go to a clinic, and that sentence has to be true.
    for key in appearance.FIXED_SLOTS:
        cost = appearance.SURGERY_COST.get(key)
        rep.check(cost is not None, 'appearance/surgery',
                  f'{key} is fixed but has no entry in SURGERY_COST, so the '
                  f'refusal message points at a service that does not exist')
    for key in appearance.FREE_SLOTS:
        rep.check(not appearance.SURGERY_COST.get(key), 'appearance/surgery',
                  f'{key} can be changed for free and is also priced')
    rep.check("args.opt('face')" in _command_source(), 'appearance/surgery',
              '`self` refuses fixed slots by pointing at `clinic --face`, '
              'and no command reads that option')
    rep.check(appearance.SURGERY_DISSONANCE > 0, 'appearance/surgery',
              'reconstruction is free of drift, which no other body work in '
              'this game is')

    # Remarks. Every genuinely striking feature has to draw a reaction, or
    # `memorable` is a number the character sheet prints and nothing else.
    for f in list(appearance.FEATURES) + list(appearance.EARNED):
        if f.memorable < 3:
            continue
        rep.check((f.slot, f.key) in appearance.REMARKS,
                  f'appearance/{f.slot}/{f.key}',
                  f'memorable {f.memorable} and nobody ever reacts to it')
    for (slot, key), line in appearance.REMARKS.items():
        where = f'appearance/remark/{slot}/{key}'
        rep.check((slot, key) in appearance.ALL_BY_KEY, where,
                  'is a reaction to a feature that does not exist')
        # Written from outside. A remark that starts with "You" is the
        # character narrating themselves, which is the one voice this cannot
        # be in: the whole point is that somebody else did the noticing.
        rep.check(not ui.plain(line).startswith('You '), where,
                  'is written from the inside; a remark is somebody else '
                  'noticing you')
        rep.check(ui.plain(line).rstrip().endswith(('.', '!', '?')), where,
                  'does not end in a full stop')
    rep.check('appearance.remark(' in _command_source(), 'appearance/remark',
              'twenty-two reactions exist and nothing ever draws one')

    # Sigils. A mark one column wider than its neighbours reads as a
    # rendering fault rather than as a design, so they are held to a
    # rectangle at both rungs of the ladder.
    for fac in factions.FACTIONS:
        for label, table in (('unicode', cyberspace.SIGILS),
                             ('ascii', cyberspace.SIGILS_ASCII)):
            rows = table.get(fac.key)
            where = f'cyberspace/sigil/{fac.key}'
            if rows is None:
                rep.error(where, f'has no {label} sigil')
                continue
            rep.check(len(rows) == cyberspace.SIGIL_HEIGHT, where,
                      f'{label} is {len(rows)} rows, not '
                      f'{cyberspace.SIGIL_HEIGHT}')
            widths = {ui.width(r) for r in rows}
            rep.check(widths == {cyberspace.SIGIL_WIDTH}, where,
                      f'{label} rows are {sorted(widths)} columns wide, not '
                      f'{cyberspace.SIGIL_WIDTH}')
        ascii_rows = cyberspace.SIGILS_ASCII.get(fac.key) or ()
        rep.check(all(ord(ch) < 128 for row in ascii_rows for ch in row),
                  f'cyberspace/sigil/{fac.key}',
                  'the ascii sigil is not ascii')
        rep.check(fac.kind in cyberspace.SIGIL_ROLE,
                  f'cyberspace/sigil/{fac.key}',
                  f'no colour declared for faction kind {fac.kind!r}')
    for role in cyberspace.SIGIL_ROLE.values():
        rep.check(role in theme.ROLES, 'cyberspace/sigil',
                  f'unknown palette role {role!r}')
    # Two factions with the same mark defeats the point of having marks.
    seen_sigils: dict[tuple, str] = {}
    for key, rows in cyberspace.SIGILS.items():
        rep.check(tuple(rows) not in seen_sigils, f'cyberspace/sigil/{key}',
                  f'identical to {seen_sigils.get(tuple(rows))}')
        seen_sigils[tuple(rows)] = key
    rep.check('cyberspace.sigil(' in _command_source(), 'cyberspace/sigil',
              'twelve sigils exist and nothing ever draws one')

    # And the numbers they feed have to be read somewhere that matters. Both
    # of them. `presence` shipped once as a number the character sheet printed
    # and nothing anywhere consumed, which is this project's oldest bug wearing
    # the newest hat.
    hooks = _world_source() + _command_source() + _engine_source()
    for promise, needle in (
            ('memorable feeds heat', 'appearance.heat_mult'),
            ('memorable feeds standing', 'appearance.rep_mult'),
            ('presence feeds the social layer', 'appearance.social_bonus')):
        rep.check(needle in hooks, 'appearance/hooks',
                  f'{promise}, but {needle} is never called')
    # Once is not enough for presence: it is displayed on the character sheet,
    # and a single call site that is itself the display would satisfy the
    # check above while still doing nothing.
    rep.check(hooks.count('appearance.social_bonus') >= 3, 'appearance/hooks',
              'presence is read in fewer than two places outside its own '
              'display, which is not "everything social"')



def check_events(rep: Report) -> None:
    """Ambient events, and the tonal budget that keeps the setting the setting.

    Tone drift is invisible one entry at a time and obvious after forty, which
    makes it exactly the kind of thing to encode rather than to trust. The
    budget in `events.TONE_BUDGET` is a design decision with a floor and a
    ceiling on each register: grim has to dominate or this stops being a
    grimdark game, and absurd has to exist or there is no relief in it, and
    absurd has a ceiling because relief arriving every other shift is not
    relief, it is just the tone.
    """
    total = len(events.EVENTS)
    rep.check(total >= 30, 'events',
              f'only {total} ambient events; the city repeats itself')

    seen: set[str] = set()
    for e in events.EVENTS:
        where = f'events/{e.key}'
        rep.check(e.key not in seen, where, 'duplicate key')
        seen.add(e.key)
        rep.check(e.tone in events.TONES, where, f'unknown tone {e.tone!r}')
        rep.check(bool(e.text.strip()), where, 'has no text')
        rep.check(e.weight > 0, where, f'weight {e.weight} would never fire')
        for d in e.districts:
            rep.check(d in districts.BY_KEY, where, f'unknown district {d!r}')
        for phase in e.phases:
            rep.check(phase in city_mod.SHIFT_NAMES, where,
                      f'unknown shift phase {phase!r}')
        # An event nothing can ever satisfy is dead content that validates.
        # Story rules are granted here and held to account in
        # `check_consequences`; this is the district-and-shift half.
        rep.check(any(e in events.eligible(d, p, lambda rule: True)
                      for d in districts.DISTRICT_KEYS
                      for p in city_mod.SHIFT_NAMES),
                  where, 'no district and shift combination can ever show it')
        # A consequence is a thing that happened to somebody else. Only the
        # gated events get the weight; weather that outranked consequences
        # would drown them, and consequences that outranked each other would
        # be a refrain.
        if e.requires or e.any_of:
            rep.check(e.weight == events.CONSEQUENCE_WEIGHT, where,
                      f'a consequence event at weight {e.weight}; they all '
                      f'carry {events.CONSEQUENCE_WEIGHT}')
        else:
            rep.check(e.weight < events.CONSEQUENCE_WEIGHT, where,
                      'weather weighted like a consequence')
        stripped, notes = ui.split_notes(e.text)
        body = ui.plain(stripped)
        # Length is measured on everything the player reads, asides included:
        # an event that is one line and three footnotes is still a scene, and
        # is in fact the most Pratchett shape available here.
        written = len(body) + sum(len(ui.plain(n)) for n in notes)
        rep.check(written > 80, where,
                  f'{written} characters is a caption, not a scene')
        # A trailing footnote marker sits after the full stop, so strip the
        # markers before asking whether the sentence was finished.
        tail = body.rstrip().rstrip(ui._SUPER + ']0123456789[')
        rep.check(tail.endswith(('.', '!', '?')), where,
                  'does not end in a full stop')
        for note in notes:
            flat = ui.plain(note).rstrip().rstrip(ui._SUPER + ']0123456789[')
            rep.check(flat.endswith(('.', '!', '?')), where,
                      'an aside does not end in a full stop')
        # The house style. An ambient event is something the city is doing,
        # not something happening to the player.
        rep.check(not body.lstrip().startswith('You '), where,
                  'opens on the player; ambient events are the city, not you')

    counts = {t: sum(1 for e in events.EVENTS if e.tone == t)
              for t in events.TONES}
    rep.check(sum(counts.values()) == total, 'events/tone',
              'an event has a tone outside events.TONES')
    for tone, (lo, hi) in events.TONE_BUDGET.items():
        share = counts[tone] / total
        rep.check(lo <= share <= hi, 'events/tone',
                  f'{tone} is {share:.0%} of {total} events, outside the '
                  f'{lo:.0%}-{hi:.0%} budget '
                  f'({counts[tone]} entries; '
                  f'{int(lo * total + 0.999)}-{int(hi * total)} allowed)')

    # Relief has to be reachable from the places the player actually spends
    # time, or the budget is satisfied on paper and never in play.
    for key in districts.DISTRICT_KEYS:
        for tone in events.TONES:
            reachable = any(e.tone == tone
                            for p in city_mod.SHIFT_NAMES
                            for e in events.eligible(key, p))
            rep.check(reachable, f'events/{key}',
                      f'nothing {tone} can ever happen here')

    # Footnotes are the tonal device and are worth their own rules. The
    # general markup check catches unbalanced braces everywhere; here we care
    # that they are used, and used in the register they exist for.
    with_notes = [e for e in events.EVENTS if '{{' in e.text]
    rep.check(len(with_notes) >= 4, 'events/footnotes',
              'almost nothing uses a footnote, which is the one device this '
              'register has')
    for e in with_notes:
        rep.check(e.tone != 'grim', f'events/{e.key}',
                  'a grim event with an aside in it is a wry event that has '
                  'not admitted to itself yet')

    # And the engine has to actually show them.
    rep.check('event_content.pick' in _world_source(), 'events/hooks',
              'nothing in the city layer ever picks an ambient event')
    rep.check('city.ambient' in _command_source(), 'events/hooks',
              'ambient events are picked but never printed')



def check_dead_fields(rep: Report) -> None:
    """Every field of a content record has to be read by something.

    This is the standing check for the bug class that has cost this project
    more than any other: a field that is written, validated, shipped, and
    consumed by nothing. It has appeared as an origin passive, an ICE rider, a
    technique flag, four pieces of display prose, a board-size argument, and
    most recently as `presence`, a number the character sheet printed and
    nothing anywhere used.

    Attribute access is the signal, because a bare field name like `key` or
    `name` occurs everywhere and proves nothing. `ALLOWED` is for the handful
    of fields that genuinely exist for `validate.py` itself; each one needs a
    reason written next to it.
    """
    import dataclasses

    #: field -> why it is allowed to have no reader outside validation.
    ALLOWED = {
        'Npc.tone': 'exists so validate can assert the cast spans registers',
        'Event.tone': 'exists so validate can enforce the tonal budget',
        'Slot.fixed': 'read through FIXED_SLOTS and FREE_SLOTS, which are\n'
                      'built from it, rather than by attribute',
    }

    source = (_engine_source() + _command_source() + _model_source()
              + _world_source() + _content_source())

    from flatline.content import conditions as cond_content
    from flatline.content import spots as spot_content
    records = [
        appearance.Feature, appearance.Slot, events.Event,
        cyberspace.Signature, npc_content.Npc, trait_content.Trait,
        icons.Icon, origins.Origin, spot_content.Spot, spot_content.Find,
        cond_content.Condition,
    ]
    for record in records:
        for field in dataclasses.fields(record):
            name = f'{record.__name__}.{field.name}'
            if name in ALLOWED:
                continue
            # Counted across the whole codebase including content, because a
            # field consumed only by the module that declares it is still
            # consumed.
            uses = source.count(f'.{field.name}')
            rep.check(uses > 0, 'dead-fields',
                      f'{name} is declared and nothing ever reads it')



def check_district_mood(rep: Report) -> None:
    """The city remembers, and has to say so somewhere the player is standing.

    The state was always there in the numbers. What was missing was any way to
    learn it without opening a reputation screen, which is the wrong surface
    for "this street is different because of you".
    """
    for value, text in districts.HARDENING:
        rep.check(value > 0, 'districts/mood',
                  f'HARDENING has a band at {value}; a negative threshold in '
                  f'this table swallows the neutral zone and makes a district '
                  f'at exactly baseline report itself as falling apart')
        rep.check(bool(text.strip()), 'districts/mood', 'an empty band')
    rep.check(districts.RELAXED_AT < 0, 'districts/mood',
              'RELAXED_AT is not below baseline, so it can never fire')
    for value, text in districts.WANTED:
        rep.check(value >= 0, 'districts/mood',
                  f'WANTED has a band at {value}; attention is never negative')

    # The neutral case has to be silent, or every district always narrates.
    for d in districts.DISTRICTS:
        base = districts.factions_posture(d.controller)
        rep.check(districts.mood(d, base, 0.0) == [], f'districts/{d.key}',
                  'reports something at baseline posture and no heat, so the '
                  'lines stop meaning anything has changed')
        rep.check(len(districts.mood(d, base + 40, 90.0)) == 2,
                  f'districts/{d.key}',
                  'a hardened district full of people looking for you says '
                  'fewer than two things')
    rep.check('districts.mood(' in _command_source(), 'districts/mood',
              'the district state is computed and never shown')


def check_shifts(rep: Report) -> None:
    """The clock, and the tension it is supposed to create.

    The design is that the street and the net want opposite hours: peak is
    dangerous outside and safe inside, night is the reverse. That only works
    if `danger` and `trace` actually pull in opposite directions, which is
    exactly the kind of thing that survives one careless retune and then
    quietly stops being a decision.
    """
    from flatline.world import city as city_layer
    rep.check(tuple(p.key for p in shifts.PHASES) == city_layer.SHIFT_NAMES,
              'shifts', 'the phases do not match the city clock')
    for phase in shifts.PHASES:
        where = f'shifts/{phase.key}'
        rep.check(bool(phase.scene) and bool(phase.why), where,
                  'has no scene or no explanation')
        for field_name in ('danger', 'trace', 'price'):
            value = getattr(phase, field_name)
            rep.check(0.5 <= value <= 1.6, where,
                      f'{field_name} is {value}, which is past a thumb on the '
                      f'scale and into making a shift unplayable')

    # The inversion. Whichever shift is worst on the street has to be best in
    # the net, or the clock is a tax rather than a choice.
    worst_street = max(shifts.PHASES, key=lambda p: p.danger)
    worst_net = max(shifts.PHASES, key=lambda p: p.trace)
    rep.check(worst_street is not worst_net, 'shifts',
              f'{worst_street.key} is the worst shift both outside and '
              f'inside, so there is no decision in the clock')
    rep.check(min(p.danger for p in shifts.PHASES) < 1.0
              and max(p.danger for p in shifts.PHASES) > 1.0, 'shifts',
              'every shift is at or above baseline danger, so waiting never '
              'helps')
    rep.check(min(p.trace for p in shifts.PHASES) < 1.0
              and max(p.trace for p in shifts.PHASES) > 1.0, 'shifts',
              'every shift is at or above baseline trace')

    # And all four hooks have to be real.
    hooks = _world_source() + _command_source() + _engine_source()
    for what, needle in (('travel danger', 'shifts.phase(city.phase).danger'),
                         ('the trace', 'shifts.phase(self.phase).trace'),
                         ('market prices', 'when.price'),
                         ('legwork', 'shifts.phase(game.city.phase).legwork')):
        rep.check(needle in hooks, 'shifts/hooks',
                  f'the clock is declared to affect {what}, and {needle} is '
                  f'never evaluated')



def check_rice(rep: Report) -> None:
    """The shell catalogue, and the two promises it makes.

    **Nothing here affects play.** It is the one system in the game that costs
    the player nothing and takes nothing, and the moment a cosmetic moves a
    number it stops being a reward and becomes a build decision that happens
    to be hidden in a menu.

    **Nothing here is bought.** Every condition has to be a thing you did,
    because a cosmetic you can buy with credits at level one is not a reward
    either, it is a shop.
    """
    from flatline import anim, prompt as prompt_mod, save as save_mod

    #: kind -> the table that actually has to contain the key.
    tables = {
        'palette': set(theme.PALETTES),
        'prompt': set(prompt_mod.BY_KEY),
        'frame': set(ui.FRAMES),
        'bars': set(ui.BARS),
        'marks': set(ui.MARKS),
        'banner': set(anim.BANNERS),
        'hud': set(rice.HUD_MODES),
        'render': set(rice.RENDER_MODES),
        'reveal': set(rice.REVEAL_STYLES),
    }

    seen: set[tuple[str, str]] = set()
    for item in rice.COSMETICS:
        where = f'rice/{item.kind}/{item.key}'
        rep.check(item.kind in rice.KINDS, where, f'unknown kind {item.kind!r}')
        rep.check((item.kind, item.key) not in seen, where, 'duplicate')
        seen.add((item.kind, item.key))
        rep.check(bool(item.name) and bool(item.blurb), where,
                  'has no name or no description')
        rep.check(item.key in tables.get(item.kind, set()), where,
                  f'names no real {item.kind}; the engine has '
                  f'{sorted(tables.get(item.kind, set()))}')
        kind, threshold = item.needs
        rep.check(kind in rice.COUNTERS, where,
                  f'unlocks on {kind!r}, which is not a condition')
        if kind == 'always':
            rep.check(threshold == 0, where,
                      'is always available and also has a threshold')
            rep.check(not item.hint, where,
                      'is always available and also explains how to get it')
        else:
            rep.check(threshold > 0, where,
                      f'unlocks at {threshold}, so it is free but pretends '
                      f'not to be')
            rep.check(bool(item.hint), where,
                      'is locked and never says what would unlock it')
            rep.check(item.hint.rstrip().endswith(('.', '!', '?')), where,
                      'hint does not end in a full stop')

    # Everything the engine can render has to be reachable. An orphan is a
    # palette nobody can ever wear, which is worse than not shipping it.
    for kind, keys in tables.items():
        listed = {i.key for i in rice.BY_KIND[kind]}
        for key in keys - listed:
            rep.error(f'rice/{kind}', f'the engine has {key!r} and the '
                                      f'catalogue never offers it')

    # Every axis must have something available from the first minute, and the
    # default has to be one of those.
    for kind in rice.KINDS:
        free = [i for i in rice.BY_KIND[kind] if i.needs[0] == 'always']
        rep.check(bool(free), f'rice/{kind}',
                  'has nothing available before you have played, so a new '
                  'player cannot have one at all')
        default = rice.DEFAULTS.get(kind)
        rep.check(default in {i.key for i in free}, f'rice/{kind}',
                  f'defaults to {default!r}, which is not always available')
        rep.check(len(rice.BY_KIND[kind]) >= 4, f'rice/{kind}',
                  'has fewer than four options, which is not a choice')

    # Every counter must exist in meta and be written by something. An unlock
    # keyed to a counter nothing increments is a cosmetic nobody can earn.
    engine = _command_source() + _engine_source() + _session_source()
    for kind, counter in rice.COUNTERS.items():
        if not counter:
            continue
        used = any(c.needs[0] == kind for c in rice.COSMETICS)
        if not used:
            continue
        rep.check(counter in save_mod.META_DEFAULT, 'rice/counters',
                  f'{kind!r} reads meta[{counter!r}], which is not a field')
        rep.check(f'{counter}=' in engine, 'rice/counters',
                  f'{kind!r} unlocks against {counter}, and nothing in the '
                  f'engine ever writes it')

    # The conditions have to be spread. Everything gated on run count would
    # make the whole catalogue one number going up.
    from collections import Counter
    spread = Counter(c.needs[0] for c in rice.COSMETICS if c.needs[0] != 'always')
    rep.check(len(spread) >= 6, 'rice/spread',
              f'only {len(spread)} kinds of condition in use; the catalogue '
              f'is one activity repeated')
    top = spread.most_common(1)[0][1] if spread else 0
    rep.check(top <= sum(spread.values()) * 0.45, 'rice/spread',
              f'{top} of {sum(spread.values())} unlocks share one condition')

    # And the hard rule about prompts: whatever the style, the trace survives.
    for style in prompt_mod.STYLES:
        rep.check(bool(style.sample), f'rice/prompt/{style.key}',
                  'has no sample for the catalogue')


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
    # D63 b: style knobs name a declared key and are positive multipliers.
    for f in factions.FACTIONS:
        for key, value in f.style.items():
            rep.check(key in factions.STYLE_KEYS, f'factions/{f.key}',
                      f'style key {key!r} is not in STYLE_KEYS')
            rep.check(isinstance(value, (int, float)) and value > 0
                      and not isinstance(value, bool), f'factions/{f.key}',
                      f'style {key} is {value!r}, expected a positive number')
    for key in factions.STYLE_KEYS:
        rep.check(any(key in f.style for f in factions.FACTIONS), 'factions',
                  f'style key {key!r} is declared and no faction uses it')
    # D67: a structural signature is a promise the engine has to keep.
    from flatline.run import network as net_world
    engine = _wide_source()
    for key, line in net_world.SIGNATURES.items():
        where = f'factions/{key}'
        rep.check(key in factions.BY_KEY, 'factions',
                  f'{key!r} has a signature and is not a faction')
        rep.check(engine.count(f"'{key}'") >= 2, where,
                  f'declares a signature the engine never acts on')
        rep.check(len(line) > 20 and not line.endswith('.'), where,
                  'signature reads badly in a list')

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
        # D67: the city is a place. Every district says how big it is, what
        # it is made of, what the people in it do for money, what its parts
        # are called, and what is past its edge, because a district that
        # says none of those is a name with services attached.
        for field in ('scale', 'built', 'works', 'beyond'):
            text = getattr(d, field)
            rep.check(len(text) >= 90, where,
                      f'{field} is {len(text)} characters; a district needs '
                      f'more than a phrase of it')
            rep.check(text.rstrip().endswith(('.', '!', '?')), where,
                      f'{field} does not end in a full stop')
        rep.check(len(d.quarters) >= 4, where,
                  f'only {len(d.quarters)} quarters; a district is not one '
                  f'street')
        for quarter in d.quarters:
            rep.check(quarter == quarter.strip() and len(quarter) > 3, where,
                      f'quarter {quarter!r} is not a name')
        rep.check(len(set(d.quarters)) == len(d.quarters), where,
                  'two quarters with the same name')
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

    check_city_shape(rep)


#: The most shifts any district may be from any other. Three while the city
#: was nine districts; four since D64 b grew it to twelve, because a bigger
#: city takes longer to cross and that is part of what bigger means. The
#: contract lifetime (6 to 12 shifts) still reaches every corner.
MAX_WALK = 4


def check_city_shape(rep: Report) -> None:
    """The city as a graph: what the map draws and what `travel` routes over.

    The map is generated from `neighbours` and cannot disagree with it. What it
    can do is disagree with what a player can actually walk, which is why the
    route finder is checked against every pair rather than against a sample.
    """
    from flatline import ui

    graph = districts.GRAPH
    rep.check(set(graph) == set(districts.DISTRICT_KEYS), 'districts',
              'GRAPH does not cover exactly the districts that exist')
    for key, edges in graph.items():
        rep.check(list(edges) == list(districts.BY_KEY[key].neighbours),
                  f'districts/{key}', 'GRAPH disagrees with neighbours')
        rep.check(key not in edges, f'districts/{key}',
                  'is its own neighbour')
        rep.check(len(set(edges)) == len(edges), f'districts/{key}',
                  'lists a neighbour twice')

    # Every pair, both ways. Nine districts is 72 ordered pairs, which is
    # cheap enough to check exhaustively and therefore not worth sampling.
    for a in districts.DISTRICT_KEYS:
        for b in districts.DISTRICT_KEYS:
            if a == b:
                rep.check(ui.shortest_path(graph, a, b) == [],
                          f'districts/{a}', 'has a route to itself')
                continue
            path = ui.shortest_path(graph, a, b)
            if not path:
                rep.error(f'districts/{a}', f'no route to {b}')
                continue
            rep.check(path[-1] == b, f'districts/{a}',
                      f'route to {b} does not end at {b}')
            rep.check(len(path) <= MAX_WALK, f'districts/{a}',
                      f'{b} is {len(path)} shifts away, over {MAX_WALK}')
            # Each step has to be a step you are allowed to take, or the
            # route is a line of commands the game will refuse.
            for i, step in enumerate(path):
                came_from = a if i == 0 else path[i - 1]
                rep.check(step in graph[came_from], f'districts/{a}',
                          f'route to {b} steps {came_from} to {step}, '
                          f'which do not join')

    # The map is drawn as a tree from START, and every district has to appear
    # on it. A district the tree cannot reach is one the player never sees.
    rows = ui.tree_rows(graph, districts.START, set(districts.DISTRICT_KEYS))
    drawn = {key for _, key in rows}
    for key in districts.DISTRICT_KEYS:
        rep.check(key in drawn, f'districts/{key}',
                  'does not appear on the map drawn from START')
    rep.check(len(rows) == len(districts.DISTRICTS), 'districts',
              'the map draws a district twice')


# --------------------------------------------------------------------------
# the run layer
# --------------------------------------------------------------------------


def check_ice(rep: Report) -> None:
    # D63 b: a construct that declares `alert_jump` must declare more than
    # the default, or the whole distinguishing feature is decorative. Traps
    # are the exception: a tripwire publishing at all is the feature.
    for i in ice_content.ICE:
        jump = i.effects.get('alert_jump')
        if jump is not None and i.behaviour != 'trap':
            rep.check(int(jump) >= 2, f'ice/{i.key}',
                      f'alert_jump {jump} is the default escalation, so the '
                      f'declared effect changes nothing')

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


def _weight(effects: dict) -> float:
    """How much a modifier block is worth, as one number.

    Crude on purpose. It exists to compare a high against its own crash, and
    for that the only thing that matters is that both sides are measured the
    same way. Rates count for more than a flat point because a rate applies to
    everything you do for as long as it is on you.
    """
    total = 0.0
    for key, value in effects.items():
        if key in fx.MULTIPLICATIVE:
            total += abs(value - 1.0) * 12
        else:
            total += abs(value)
    return total


def check_drugs(rep: Report) -> None:
    """The chemistry, per D40.

    The one rule the whole system rests on is that a dose is a loan: the crash
    lasts longer than the high and costs more than it paid. A drug that came
    out ahead on either axis would be equipment with a cooldown, and it would
    be the correct thing to take before every single run, which is the exact
    opposite of a decision.
    """
    from flatline.content import drugs
    from flatline.world import market as market_mod

    hookless = []
    curers = []
    for drug in drugs.DRUGS:
        where = f'drugs/{drug.key}'
        for problems in (fx.check(drug.high, f'{where}.high'),
                         fx.check(drug.crash, f'{where}.crash'),
                         fx.check(drug.withdrawal, f'{where}.withdrawal')):
            for problem in problems:
                rep.error(where, problem)

        rep.check(bool(drug.high), where, 'does nothing while it is in you')
        rep.check(bool(drug.crash), where,
                  'has no comedown, which makes it equipment')
        rep.check(drug.down >= drug.up, where,
                  f'is up for {drug.up} and down for {drug.down}: the crash '
                  f'may not be shorter than the high')
        rep.check(_weight(drug.crash) >= _weight(drug.high), where,
                  f'the high is worth {_weight(drug.high):.1f} and the crash '
                  f'costs {_weight(drug.crash):.1f}: a dose has to be a loan')
        # You miss what it gave you. A withdrawal that took something the drug
        # never provided would be the game inventing a punishment rather than
        # taking back a loan.
        stray = set(drug.withdrawal) - set(drug.high) - set(drug.crash)
        rep.check(not stray, where,
                  f'withdrawal touches {sorted(stray)}, which this drug never '
                  f'gave you')
        for key, value in drug.withdrawal.items():
            if key in fx.MULTIPLICATIVE:
                continue
            rep.check(value <= 0, where,
                      f'withdrawal improves {key}, which is not withdrawal')

        rep.check(1 <= drug.tier <= 3, where, f'tier {drug.tier}')
        rep.check(drug.price > 0, where, 'is free')
        rep.check(0 <= drug.hook <= 4, where, f'hook {drug.hook}')
        rep.check(bool(drug.sold) or drug.unique, where, 'is sold nowhere')
        for service in drug.sold:
            rep.check(service in districts.SERVICES, where,
                      f'sold at {service!r}, which is not a district service')
            rep.check('drug' in market_mod.STOCK_KINDS.get(service, ()), where,
                      f'sold at {service!r}, which does not stock drugs')
        rep.check(bool(drug.onset) and bool(drug.turn), where,
                  'does not say what taking it or losing it feels like')
        rep.check(drug.turn.rstrip().endswith('.') and drug.onset[0].isupper(),
                  where, 'onset and turn are not written as prose')
        if drug.rider:
            rep.check(drug.rider in _engine_source(), where,
                      f'rider {drug.rider!r} is read by nothing')
        if not drug.hook:
            hookless.append(drug.key)
        if drug.cures_crash:
            curers.append(drug.key)

        # Somewhere has to actually stock it, or it is a catalogue entry.
        reachable = any(
            service in drug.sold and drug.tier <= d.max_tier
            for d in districts.DISTRICTS for service in d.services)
        rep.check(reachable or drug.unique, where,
                  'no district both stocks its tier and has a seller for it')

    rep.check(len(hookless) <= 1, 'drugs',
              f'{len(hookless)} drugs have no hook: the joke only works once')
    rep.check(len(curers) <= 1, 'drugs',
              f'{len(curers)} drugs end a comedown early; that is a trap and '
              f'traps do not want competition')

    # Keys are a flat namespace as far as `buy` is concerned, and it resolves
    # by name across every catalogue at once.
    from flatline.content import cyberware as cw, hardware as hw
    clash = (set(drugs.BY_KEY) & (set(programs.BY_KEY) | set(cw.BY_KEY)
                                  | set(hw.BY_KEY)))
    rep.check(not clash, 'drugs', f'keys collide with other goods: {clash}')
    names = {d.name.lower() for d in drugs.DRUGS}
    others = ({p.name.lower() for p in programs.PROGRAMS}
              | {w.name.lower() for w in cw.WARE})
    rep.check(not (names & others), 'drugs',
              f'names collide with other goods: {names & others}')

    # The numbers behind the spiral have to leave a way out of it, per D6.
    rep.check(drugs.WITHDRAWAL_AT < drugs.HABIT_MAX, 'drugs',
              'withdrawal starts at or above the ceiling, so nobody reaches it')
    rep.check(drugs.CLEAN_SHIFTS * drugs.HABIT_MAX <= 80, 'drugs',
              f'climbing out of a full habit takes '
              f'{drugs.CLEAN_SHIFTS * drugs.HABIT_MAX} shifts, which is not a '
              f'spiral, it is a wall')
    rep.check(0 < drugs.TOLERANCE_FLOOR < 1, 'drugs',
              'tolerance floor is not a fraction')


def check_games(rep: Report) -> None:
    """The two games, per D40. See `content/games.py`.

    The rule worth enforcing is that the odds printed on the wall are the odds
    the resolver uses. A gambling system whose stated edge and actual edge
    drift apart is the one kind of bug in this game that would be genuinely
    dishonest rather than merely wrong.
    """
    from flatline.content import games

    for venue in games.VENUES:
        where = f'games/{venue.key}'
        rep.check(venue.game in ('dice', 'cards'), where,
                  f'plays {venue.game!r}, which nothing implements')
        rep.check(venue.where in districts.BY_KEY, where,
                  f'is in {venue.where!r}, which does not exist')
        if venue.where in districts.BY_KEY:
            rep.check(venue.at in districts.BY_KEY[venue.where].services,
                      where, f'needs {venue.at!r}, which {venue.where} has '
                             f'not got')
        rep.check(venue.house in factions.BY_KEY, where,
                  f'house {venue.house!r} is not a faction')
        rep.check(bool(venue.arrival) and bool(venue.pitch), where,
                  'has no description of the room')

    # Both games have to be findable, and not in the same place, or the second
    # one is a feature nobody encounters.
    for game_key in ('dice', 'cards'):
        rooms = [v for v in games.VENUES if v.game == game_key]
        rep.check(len(rooms) >= 2, 'games',
                  f'{game_key} is played in {len(rooms)} place(s)')
        houses = {v.house for v in rooms}
        rep.check(len(houses) >= 2, 'games',
                  f'every {game_key} table belongs to the same faction, so '
                  f'winning only ever annoys one of them')

    # The wall and the resolver have to agree. `WAYS` is what the table shows;
    # `CALLS` is what the dice are checked against.
    for call, (totals, pays) in games.CALLS.items():
        ways = sum(1 for a in range(1, 7) for b in range(1, 7)
                   if a + b in totals)
        rep.check(ways == games.WAYS[call], f'games/{call}',
                  f'the wall says {games.WAYS[call]} ways and the dice give '
                  f'{ways}')
        rep.check(pays > 0, f'games/{call}', 'pays nothing')
    covered = sorted(t for _, (totals, _) in games.CALLS.items()
                     for t in totals)
    rep.check(len(covered) == len(set(covered)), 'games',
              'two calls win on the same total, so one bet covers another')
    rep.check(set(covered) <= set(range(2, 13)), 'games',
              'a call wins on a total two dice cannot make')

    # One edge, the same for every call. A game where one bet is quietly the
    # correct one is a game with a right answer, and a right answer is not a
    # decision.
    edges = {call: round(games.edge(call), 6) for call in games.CALLS}
    rep.check(len(set(edges.values())) == 1, 'games',
              f'the house edge differs by call: {edges}')
    house = next(iter(edges.values()))
    rep.check(0 < house < 0.25, 'games',
              f'the house edge is {house:.1%}, which is either charity or '
              f'robbery')

    rep.check(games.MIN_STAKE < games.MAX_STAKE, 'games', 'stake range is empty')
    rep.check(games.THREES_MIN < games.THREES_MAX, 'games',
              'threes stake range is empty')
    # A scrape has to pay less than the stake, or a coin-flip build grinds it.
    tiers = games.THREES_PAYOUT
    rep.check(tiers[-1][1] < 1.0, 'games',
              f'the worst winning read still pays {tiers[-1][1]}x, so barely '
              f'reading the table is profitable')
    rep.check([m for _, m in tiers] == sorted((m for _, m in tiers),
                                              reverse=True), 'games',
              'reading them better pays less')
    rep.check(tiers[0][0] > tiers[-1][0], 'games',
              'the payout tiers are not ordered by margin')
    rep.check(0 < games.THREES_FLOOR < 0.5, 'games',
              'the floor below which a table refuses you is not a probability')


def check_mods(rep: Report) -> None:
    """Bench work, per D47. See `content/mods.py`.

    One rule carries this file, and it is the same one the drugs are written
    under: **nothing comes out ahead**. A modification that were simply better
    would not be a decision, it would be an upgrade you do to everything once,
    and it would make every price in the component shop mean less.
    """
    from flatline.content import mods as mod_content

    for mod in mod_content.MODS:
        where = f'mods/{mod.key}'
        for problems in (fx.check(mod.gives, f'{where}.gives'),
                         fx.check(mod.takes, f'{where}.takes')):
            for problem in problems:
                rep.error(where, problem)
        rep.check(bool(mod.gives), where, 'changes nothing')
        rep.check(bool(mod.takes), where,
                  'costs nothing, which makes it an upgrade rather than a '
                  'decision')
        rep.check(_weight(mod.takes) >= _weight(mod.gives), where,
                  f'gives {_weight(mod.gives):.1f} and takes '
                  f'{_weight(mod.takes):.1f}: bench work is a trade')
        # And the two halves have to be different axes, or it is a rounding
        # error dressed up as a choice.
        rep.check(not (set(mod.gives) & set(mod.takes)), where,
                  f'gives and takes the same keys: '
                  f'{sorted(set(mod.gives) & set(mod.takes))}')
        for key, value in mod.gives.items():
            rep.check(fx.improves(key, value), where,
                      f'"gives" {key} {value}, which is not an improvement')
        for key, value in mod.takes.items():
            rep.check(not fx.improves(key, value), where,
                      f'"takes" {key} {value}, which is not a cost')

        rep.check(bool(mod.slots), where, 'can be done to nothing')
        for slot in mod.slots:
            rep.check(slot in hardware.SLOTS, where,
                      f'names slot {slot!r}, which does not exist')
            rep.check(any(c.slot == slot for c in hardware.COMPONENTS), where,
                      f'{slot} has no components in it')
        rep.check(mod.scrap > 0 and mod.price > 0, where, 'is free')
        rep.check(bool(mod.blurb) and bool(mod.bench), where,
                  'has nothing to say about itself')
        rep.check(mod.name and mod.name[0].isupper(), where,
                  'is not named like a thing')

    # Every slot needs something worth doing to it, or a component in that
    # slot can never be worked on and the screen has a hole in it.
    for slot in hardware.SLOTS:
        rep.check(bool(mod_content.for_slot(slot)), 'mods',
                  f'nothing can be done to a {slot}')
    rep.check(mod_content.MAX_PER_COMPONENT >= 2, 'mods',
              'one piece of work per component, so there is never a second '
              'choice made against the first')
    rep.check(len({m.key for m in mod_content.MODS})
              == len(mod_content.MODS), 'mods', 'two mods share a key')

    # Salvage has to be a poor deal. If breaking things down paid near list,
    # it would be a way to turn goods into a currency rather than a use for
    # things nobody will buy.
    rep.check(0 < mod_content.SALVAGE_RATE < 0.4, 'mods',
              f'salvage returns {mod_content.SALVAGE_RATE:.0%} of list, which '
              f'is a second economy')
    rep.check(0 < mod_content.BROKEN_RATE <= 1.0, 'mods',
              'a wreck is worth more than the working component')
    rep.check(mod_content.salvage_value(1000, broken=True)
              < mod_content.salvage_value(1000), 'mods',
              'breaking a component first pays better')
    # And the cheapest work has to cost more scrap than the cheapest thing
    # you could break down returns, or one spare part buys a modification.
    floor = min(mod_content.salvage_value(p.price) for p in programs.PROGRAMS)
    rep.check(min(m.scrap for m in mod_content.MODS) > floor, 'mods',
              'the cheapest bench work is paid for by one junk program')


def check_crew(rep: Report) -> None:
    """A crew rather than a hire, per D46. See `content/rivals.py`."""
    from flatline.content import rivals as rival_content
    from flatline.world import rivals as rival_mod

    styles = {r.style for r in rival_content.RIVALS}
    for label, table in (('joined', rival_content.CREW_JOINED),
                         ('released', rival_content.CREW_RELEASED)):
        missing = styles - set(table)
        rep.check(not missing, 'crew',
                  f'{label} has nothing for {sorted(missing)}')
        for style, line in table.items():
            where = f'crew/{label}/{style}'
            rep.check('{name}' in line, where, 'names nobody')
            rep.check(len(line) > 60, where, 'is too short to be a moment')

    # Signing somebody has to be a harder ask than hiring them, or a crew is
    # simply a cheaper hire and nobody would ever do the other one.
    rep.check(rival_content.CREW_AT > rival_mod.HIRE_FLOOR, 'crew',
              'a crew is easier to get than a hire')
    rep.check(rival_content.CREW_CUT < rival_mod.HIRE_CUT, 'crew',
              'a permanent crew takes more of the haul than a one-run hire')
    for rival in rival_mod.seed_pool():
        rep.check(rival_mod.crew_retainer(rival)
                  > rival_mod.hire_price(rival), f'crew/{rival.key}',
                  'a retainer is cheaper than a single job')
        ok, _ = rival_mod.can_crew(rival)
        rep.check(not ok, f'crew/{rival.key}',
                  'will sign on before you have done anything')

    # They get better, up to a cap, and it takes real time.
    rep.check(rival_mod.crew_bonus(0) == 0, 'crew',
              'somebody is better at working with you before they have')
    rep.check(rival_mod.crew_bonus(10_000)
              == rival_content.CREW_MAX_STEPS, 'crew',
              'the skill they gain is uncapped')
    rep.check(rival_content.CREW_RUNS_PER_STEP >= 3, 'crew',
              'they learn how you move in a couple of runs')

    # Losing somebody has to say something different depending on how long
    # they were there. That is the entire reason this exists.
    thresholds = [after for after, _ in rival_content.CREW_LOST]
    rep.check(thresholds == sorted(thresholds), 'crew',
              'the loss scenes are out of order')
    rep.check(thresholds[0] == 0, 'crew',
              'losing somebody early has nothing to say')
    seen = {rival_content.crew_loss(n) for n in (0, 5, 12, 25, 99)}
    rep.check(len(seen) == len(rival_content.CREW_LOST), 'crew',
              'not every loss scene is reachable')
    for after, text in rival_content.CREW_LOST:
        where = f'crew/lost/{after}'
        rep.check('{name}' in text and '{runs}' in text, where,
                  'does not name who or how long')
        rep.check(len(text) > 120, where, 'is too short for what it is')


def check_safehouses(rep: Report) -> None:
    """Somewhere of your own, per D45. See `content/safehouses.py`."""
    from flatline.content import safehouses

    for prop in safehouses.PROPERTIES:
        where = f'safehouses/{prop.key}'
        district = districts.BY_KEY.get(prop.where)
        rep.check(district is not None, where,
                  f'is in {prop.where!r}, which does not exist')
        if district is not None:
            # A place to hide in a district with nowhere to hide is a
            # contradiction the map would notice before the player did.
            rep.check('safehouse' in district.services, where,
                      f'{district.name} has no safehouse service')
        rep.check(prop.price > 0, where, 'is free')
        rep.check(0 < prop.security < 100, where,
                  f'security {prop.security} is not a rating')
        rep.check(bool(prop.blurb) and bool(prop.arrival), where,
                  'has nothing to say about itself')

    # What you buy is security, so price and security have to move together
    # or one of the four is simply the right answer.
    ordered = sorted(safehouses.PROPERTIES, key=lambda p: p.price)
    ranks = [p.security for p in ordered]
    rep.check(ranks == sorted(ranks), 'safehouses',
              f'price and security disagree: {[(p.key, p.price, p.security) for p in ordered]}')
    rep.check(len(safehouses.PROPERTIES) >= 3, 'safehouses',
              'too few places for the choice to be one')
    rep.check(len({p.where for p in safehouses.PROPERTIES})
              == len(safehouses.PROPERTIES), 'safehouses',
              'two properties share a district, so one is unreachable')

    # Being unknown has to be free and has to be the best security there is.
    rep.check(safehouses.raid_chance(0, safehouses.SAFE_BELOW - 1) == 0.0,
              'safehouses', 'somebody looks even when nobody is interested')
    rep.check(safehouses.raid_chance(0, 100)
              > safehouses.raid_chance(90, 100), 'safehouses',
              'security does not reduce the risk')
    rep.check(0 < safehouses.raid_chance(0, 100) < 0.5, 'safehouses',
              'the worst case is either impossible or a certainty')
    rep.check(safehouses.BURN_AFTER >= 2, 'safehouses',
              'one visit ends the place, so security buys nothing')
    rep.check(0 < safehouses.RAID_TAKES <= 1.0, 'safehouses',
              'a raid takes none of it or more than all of it')
    rep.check(safehouses.CAPACITY > 0, 'safehouses', 'holds nothing')
    for label, lines in (('raids', safehouses.RAIDS),):
        rep.check(len(lines) >= 3, 'safehouses',
                  f'{label} has {len(lines)} lines and will repeat')
        for line in lines:
            rep.check(line.rstrip().endswith('.'), 'safehouses',
                      'a raid line is not a sentence')


def check_bonds(rep: Report) -> None:
    """Rival arcs, per D44. See the bottom of `content/rivals.py`.

    Seven named runners took work off the board for the life of this project
    and the whole relationship was one number nothing ever read. A bond is
    that number becoming a person, and the checks here are that it can be
    reached, that it says something when it is, and that both ends exist.
    """
    from flatline.content import rivals as rival_content
    from flatline.world import rivals as rival_mod

    styles = {r.style for r in rival_content.RIVALS}
    for kind, table in (('nemesis', rival_content.NEMESIS_DECLARED),
                        ('partner', rival_content.PARTNER_DECLARED)):
        rep.check(kind in rival_content.BOND_KINDS, 'rivals',
                  f'{kind!r} is not a declared bond')
        missing = styles - set(table)
        rep.check(not missing, 'rivals',
                  f'{kind} has no declaration for {sorted(missing)}')
        for style, line in table.items():
            where = f'rivals/{kind}/{style}'
            rep.check(style in styles, where, 'is not a style anybody has')
            rep.check('{name}' in line, where, 'names nobody')
            rep.check(len(line) > 100, where, 'is too short to be a scene')
        rep.check(f"'{kind}'" in _engine_source()
                  or f"'{kind}'" in _world_source(), 'rivals',
                  f'nothing reads the {kind} bond')

    for label, acts in (('nemesis', rival_content.NEMESIS_ACTS),
                        ('partner', rival_content.PARTNER_ACTS)):
        rep.check(len(acts) >= 3, 'rivals',
                  f'{label} has {len(acts)} things it does, which will repeat')
        for line in acts:
            rep.check('{name}' in line, f'rivals/{label}',
                      f'an act names nobody: {line[:40]}...')
            rep.check(line.rstrip().endswith('.'), f'rivals/{label}',
                      'an act is not a sentence')

    # Both poles have to be reachable from where people start, and neither by
    # accident: an arc you cross on your fourth shift is a mood.
    bands = [low for low, _ in rival_content.DISPOSITION_BANDS]
    rep.check(rival_content.NEMESIS_AT in bands
              or rival_content.NEMESIS_AT <= min(bands) + 40, 'rivals',
              'the nemesis threshold does not line up with any band')
    rep.check(rival_content.NEMESIS_AT < 0 < rival_content.PARTNER_AT,
              'rivals', 'the two poles are not on opposite sides of neutral')
    rep.check(rival_content.BOND_AFTER_JOBS >= 2, 'rivals',
              'a bond forms before anybody has done anything')
    for rival in rival_content.RIVALS:
        rep.check(rival_content.NEMESIS_AT < rival.disposition
                  < rival_content.PARTNER_AT, f'rivals/{rival.key}',
                  f'starts at {rival.disposition}, which is already a bond')
    rep.check(0 < rival_content.BOND_CHANCE < 0.5, 'rivals',
              'a bond acts every shift, which is weather rather than a person')
    rep.check(rival_content.NEMESIS_HEAT > 0
              and rival_content.PARTNER_HEAT > 0, 'rivals',
              'a bond changes nothing')


def check_legacy(rep: Report) -> None:
    """Getting out, and what is left of you, per D43.

    Two rules carry this file. Every gate `retire` names has to be a gate the
    command implements, and every bequest has to be something the creation
    path can actually hand over: a legacy that promises a thing nobody grants
    is this project's oldest failure wearing the game's most emotional scene.
    """
    from flatline.content import cyberware as cw, drugs, legacy

    for key, want, missing in legacy.GATES:
        where = f'legacy/{key}'
        rep.check(f"'{key}':" in _engine_source(), where,
                  f'gate {key!r} is checked by nothing')
        rep.check(bool(want) and want == want.lower().lstrip(), where,
                  'the gate is not a lowercase phrase')
        rep.check(bool(missing) and missing.rstrip().endswith('.'), where,
                  'has no sentence for not having got there')
    rep.check(len({k for k, _, _ in legacy.GATES}) == len(legacy.GATES),
              'legacy', 'two gates share a key')

    # The stake has to be a real target: reachable, and not reachable by
    # accident. Priced against what the board pays.
    from flatline.world import contracts as contract_mod
    top = 900 + 75 * 34
    rep.check(legacy.STAKE > top * 5, 'legacy',
              f'the stake is {legacy.STAKE:,}c, which is a few good contracts '
              f'rather than a career')
    rep.check(legacy.STAKE < top * 40, 'legacy',
              'the stake is so high that retiring is theoretical')

    # Every drift band has an ending, and the drift never refuses one.
    bands = [b for b, _, _ in legacy.ENDINGS]
    rep.check(bands == sorted(bands), 'legacy', 'endings are out of order')
    rep.check(bands[0] == 0, 'legacy', 'somebody at zero drift has no ending')
    declared = [b for b, _, _ in cw.DISSONANCE_BANDS]
    rep.check(bands == declared, 'legacy',
              f'endings sit on {bands} and the drift bands are {declared}')
    for band, title, text in legacy.ENDINGS:
        where = f'legacy/ending/{band}'
        rep.check(bool(title) and bool(text), where, 'is empty')
        rep.check(len(text) > 120, where, 'is too short to be an ending')
    for level in (0, 24, 25, 49, 50, 74, 75, 200):
        title, text = legacy.ending(level)
        rep.check(bool(title) and bool(text), 'legacy',
                  f'drift {level} produces no ending')

    # Bequests. Both halves: a kind of ending must have something to leave,
    # and everything leavable must be granted by the creation path.
    for how in ('retired', 'flatlined'):
        rep.check(bool(legacy.candidates(how)), 'legacy',
                  f'{how} leaves nothing behind')
    for bequest in legacy.BEQUESTS:
        where = f'legacy/{bequest.key}'
        rep.check(bequest.after in ('retired', 'flatlined'), where,
                  f'follows {bequest.after!r}, which is not an ending')
        rep.check(bool(bequest.summary) and bequest.summary.endswith('.'),
                  where, 'summary is not a sentence')
        rep.check(len(bequest.text) > 150, where,
                  'the scene is too short to land')
        rep.check(f"bequest.key == '{bequest.key}'" in _engine_source()
                  or f"picked.key == '{bequest.key}'" in _engine_source(),
                  where, f'nothing grants {bequest.key!r} to the next '
                         f'character')
    rep.check(0 < legacy.STAKE_SHARE < 0.5, 'legacy',
              'a retirement leaves so much that the next character skips the '
              'early game')
    rep.check(0 < legacy.DEBT_SHARE <= 1.0, 'legacy',
              'an inherited debt is not a fraction of the original')
    rep.check(legacy.NAME_STANDING > 0, 'legacy',
              'a remembered name is worth nothing')

    # The city has to have words for somebody who is gone, and they have to
    # be about a handle rather than about a person the player can meet.
    rep.check(len(legacy.REMEMBERED) >= 4, 'legacy',
              'too few ways to mention the departed; it will repeat')
    for line in legacy.REMEMBERED:
        rep.check('{handle}' in line, 'legacy',
                  f'a remembered line names nobody: {line[:40]}...')
        rep.check(line.rstrip().endswith('.'), 'legacy',
                  'a remembered line is not a sentence')


def check_offers(rep: Report) -> None:
    """What people do for you, per D42. See `content/offers.py`.

    The rule with teeth is the first one: an offer may only exist for somebody
    who declares it. `Npc.offers` was a label attached to nothing for the whole
    life of the cast, and the way that stops happening again is for the label
    and the implementation to be unable to disagree.
    """
    from flatline.content import cyberware as cw, drugs, hardware as hw
    from flatline.content import npcs, offers

    catalogues = (('program', programs.BY_KEY), ('ware', cw.BY_KEY),
                  ('component', hw.BY_KEY), ('drug', drugs.BY_KEY))

    for work in offers.WORK:
        where = f'offers/work/{work.npc}'
        npc = npcs.BY_KEY.get(work.npc)
        rep.check(npc is not None, where, 'is nobody')
        if npc is not None:
            rep.check('work' in npc.offers, where,
                      f'{npc.name} hands out work and does not declare it')
        rep.check(work.patron in factions.BY_KEY, where,
                  f'fronting for {work.patron!r}, which is not a faction')
        for target in work.targets:
            rep.check(target in factions.BY_KEY, where,
                      f'wants {target!r} hit, which is not a faction')
            rep.check(target != work.patron, where,
                      'wants their own patron hit')
        rep.check(work.pay > 1.0, where,
                  'pays no better than the board, so there is no reason to '
                  'have a relationship with anybody')
        rep.check(work.patience > 0, where, 'holds it no longer than a posting')
        for text in ('pitch', 'closing', 'dropped'):
            rep.check(bool(getattr(work, text)), where, f'has no {text}')

    for stock in offers.STOCK:
        where = f'offers/stock/{stock.npc}'
        npc = npcs.BY_KEY.get(stock.npc)
        rep.check(npc is not None, where, 'is nobody')
        if npc is not None:
            rep.check('goods' in npc.offers, where,
                      f'{npc.name} sells things and does not declare it')
        rep.check(bool(stock.goods), where, 'sells nothing')
        for key in stock.goods:
            found = [kind for kind, table in catalogues if key in table]
            rep.check(len(found) == 1, where,
                      f'sells {key!r}, which is in {found or "no catalogue"}')
        rep.check(0.5 <= stock.markup <= 1.5, where,
                  f'markup {stock.markup} is charity or robbery')
        rep.check(bool(stock.pitch) and bool(stock.first), where,
                  'has nothing to say about their own stock')

    for fav in offers.FAVOURS:
        where = f'offers/favour/{fav.npc}.{fav.key}'
        npc = npcs.BY_KEY.get(fav.npc)
        rep.check(npc is not None, where, 'is nobody')
        if npc is not None:
            rep.check('favour' in npc.offers, where,
                      f'{npc.name} does favours and does not declare it')
        rep.check(fav.effect in offers.EFFECTS, where,
                  f'does {fav.effect!r}, which is not a declared effect')
        # And the other direction, which is the one that actually catches
        # things: an effect nothing implements would be a favour that prints
        # its own prose and changes nothing.
        rep.check(f"fav.effect == '{fav.effect}'" in _engine_source(), where,
                  f'effect {fav.effect!r} is implemented by nothing')
        rep.check(fav.amount > 0, where, 'gives nothing')
        rep.check(bool(fav.text) and bool(fav.refusal), where,
                  'has no words for doing it or for declining')
        rep.check(fav.blurb == fav.blurb.strip()
                  and fav.blurb.endswith('.'), where,
                  'blurb is not a sentence')

    # Every declared offer has to be served by something, which is the whole
    # point of this file existing.
    served = {'work': {w.npc for w in offers.WORK},
              'goods': {s.npc for s in offers.STOCK},
              'favour': {f.npc for f in offers.FAVOURS}}
    for npc in npcs.NPCS:
        for kind in ('work', 'goods', 'favour'):
            if kind in npc.offers:
                rep.check(npc.key in served[kind], f'npcs/{npc.key}',
                          f'declares {kind!r} and nothing serves it')
        if 'intel' in npc.offers:
            rep.check(bool(npc.topics), f'npcs/{npc.key}',
                      'declares intel and has no topics')
        if 'nothing' in npc.offers:
            rep.check(len(npc.offers) == 1, f'npcs/{npc.key}',
                      'offers nothing, and also some things')

    rep.check(offers.OWED_LIMIT >= 2, 'offers',
              'the favour ceiling is so low the tab is a coin flip')
    rep.check(offers.WORK_EVERY > 0, 'offers',
              'people hand out work every shift, which is a board with a face')


def check_lenders(rep: Report) -> None:
    """Who lends, per D40. See `content/lenders.py`."""
    from flatline.content import lenders, npcs
    from flatline.world import debt as debt_mod

    for lender in lenders.LENDERS:
        where = f'lenders/{lender.key}'
        # The key is the faction on purpose: a debt records who it is owed to
        # and the fallout ladder resolves a visit by asking that faction what
        # its people do, so a lender whose key is not a faction is a debt that
        # can never be collected.
        rep.check(lender.key in factions.BY_KEY, where,
                  'key is not a faction, so the debt can never be collected')
        rep.check(lender.where in districts.BY_KEY, where,
                  f'lends in {lender.where!r}, which does not exist')
        if lender.where in districts.BY_KEY:
            rep.check(lender.at in districts.BY_KEY[lender.where].services,
                      where,
                      f'lends at {lender.at!r}, which '
                      f'{lender.where} does not have')
        rep.check(0 < lender.rate < 0.2, where,
                  f'rate {lender.rate} is not a per-shift rate')
        rep.check(lender.grace > 0, where, 'has no grace period at all')
        rep.check(lender.floor >= 0 and lender.ceiling >= lender.floor, where,
                  'the floor is above the ceiling')
        rep.check(lender.key in lenders.REFUSALS
                  and lender.key in lenders.NOTHING, where,
                  'has no words for refusing you')
        for field_name in ('offer', 'handover', 'warning'):
            rep.check(bool(getattr(lender, field_name)), where,
                      f'has no {field_name}')
        # Two of the three are people the city already had. If a lender wears
        # an existing name, they have to be standing where that person stands,
        # or the game has one character in two places.
        for npc in npcs.NPCS:
            if npc.name == lender.name:
                rep.check(npc.where == lender.where and npc.at == lender.at,
                          where,
                          f'{npc.name} is an NPC in {npc.where}/{npc.at} and '
                          f'lends in {lender.where}/{lender.at}')

    # A rate that never bites and a rate that ends the game are both a debt
    # nobody has to think about.
    rates = [x.rate for x in lenders.LENDERS]
    rep.check(max(rates) / min(rates) >= 2, 'lenders',
              'every lender charges about the same, so the choice is not one')
    rep.check(any(x.rate > debt_mod.RATE for x in lenders.LENDERS)
              and any(x.rate < debt_mod.RATE for x in lenders.LENDERS),
              'lenders', 'nobody is worse or nobody is better than the house '
                         'rate the origins ship with')

    # Somebody has to lend to a runner nobody has heard of, or the system is
    # invisible until you no longer need it.
    fresh = max(lenders.limit(x, 0, 0) for x in lenders.LENDERS)
    rep.check(fresh > 0, 'lenders',
              'nobody will lend a new character anything, so the first time '
              'this system exists is after it stopped mattering')
    starting = min(p.price for p in programs.by_category('payload'))
    rep.check(fresh >= starting, 'lenders',
              f'the most a new character can borrow is {fresh:,}c and the '
              f'cheapest payload is {starting:,}c: borrowing has to solve the '
              f'problem it is there for')


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

    check_briefs(rep)


#: Fields the brief fills in from the network. Anything else in an aim is a
#: `KeyError` at the moment a player asks what they are doing, which is the
#: worst possible moment for one.
AIM_FIELDS = {'node', 'asset', 'ticks', 'who'}


def check_briefs(rep: Report) -> None:
    """`job`, and the sentence it prints. See `run/session.py: brief`.

    The aim is the only piece of content in the game that is read out loud at
    the moment somebody has admitted they are lost, so it has a shorter leash
    than most: it has to name a verb they can type, and it has to be one
    sentence they can act on rather than three they have to parse.
    """
    import string

    for o in contract_mod.OBJECTIVES:
        where = f'contracts/{o}'
        aim = contract_mod.OBJECTIVE_AIM.get(o)
        if not aim:
            rep.error(where, 'has no aim, so `job` cannot say what it wants')
            continue
        fields = {name for _, name, _, _ in string.Formatter().parse(aim)
                  if name}
        unknown = fields - AIM_FIELDS
        rep.check(not unknown, where,
                  f'aim uses fields nothing fills in: {sorted(unknown)}')
        # It has to name something to type. An aim that describes the outcome
        # without naming the verb is a restatement of the blurb.
        rep.check('`' in aim or o in ('exfiltrate', 'escort'), where,
                  'aim names no command to type')
        rep.check(aim[0].isupper() and aim.rstrip().endswith('.'), where,
                  'aim is not a sentence')
        rep.check(len(aim) <= 220, where,
                  f'aim is {len(aim)} characters, which is a paragraph')
        rep.check(contract_mod.OBJECTIVE_BLURB[o] != aim, where,
                  'aim and blurb are the same text, so one of them is unused')

    # Every alert level says what it costs and what answers it, except the one
    # where nothing has happened.
    for level in ice_content.ALERT_LEVELS:
        rep.check(level in ice_content.ALERT_ADVICE, 'ice',
                  f'alert level {level!r} has no advice')
    rep.check(not ice_content.ALERT_ADVICE.get('green'), 'ice',
              'green is not an event and should not be advised about')
    for level in ('amber', 'red', 'lockdown'):
        rep.check(bool(ice_content.ALERT_ADVICE.get(level)), 'ice',
                  f'{level} escalates and says nothing about what to do')


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
            # Numeric rules the content layer evaluates itself, or story
            # rules the world layer evaluates (a flag, or `not:` a flag),
            # which `check_consequences` holds to naming a real flag.
            rep.check(kind in npc_content.NUMERIC_RULES
                      or _story_flag(rule) is not None, where,
                      f'unknown requirement {rule!r}')
        # D54: hours are real shifts, and somebody with hours keeps at least
        # one; a person who is never about is a person who does not exist.
        for hour in n.hours:
            rep.check(hour in city_mod.SHIFT_NAMES, where,
                      f'keeps unknown hour {hour!r}')
        rep.check(len(set(n.hours)) == len(n.hours), where,
                  'lists an hour twice')
        # The voice pass: enough to say that `talk` does not repeat itself
        # inside a shift, and enough topics to be worth asking.
        rep.check(len(n.lines) >= 5, where,
                  f'{len(n.lines)} lines; `talk` repeats itself')
        rep.check(len(n.topics) >= 3, where,
                  f'{len(n.topics)} topics; not worth asking')
    # Everybody with hours has to share an hour with Marrow's morning or the
    # tutorial's first `look` shows a city with nobody in it. Not everybody:
    # enough.
    morning = [n for n in npc_content.NPCS
               if n.where in ('marrow', '') and npc_content.about_now(n, 'morning')]
    rep.check(len(morning) >= 2, 'npcs/hours',
              'fewer than two people about in Marrow on the first morning')

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
            # A scene's district is a gate the engine reads (D86), so it
            # has to be a real one.
            rep.check(not st.where or st.where in districts.BY_KEY, sw,
                      f'happens in {st.where!r}, which is not a district')
            for rule in tuple(st.requires) + tuple(st.any_of):
                # `not:` is the world layer's one combinator (D51), and
                # a stage may use it too (D144): the close that knows
                # the wall, and the one for everybody else.
                rule = rule[4:] if rule.startswith('not:') else rule
                if ':' in rule:
                    kind = rule.split(':')[0]
                    rep.check(kind in thread_content.CONDITIONS, sw,
                              f'unknown condition {kind!r}')
                    if kind == 'asked':
                        _, who, _, topic = rule.split(':', 3)[0:1] + \
                            [rule.split(':', 2)[1], '', rule.split(':', 2)[2]]
                        npc = npc_content.BY_KEY.get(who)
                        rep.check(npc is not None, sw,
                                  f'asks {who!r}, who is nobody')
                        if npc is not None:
                            rep.check(topic in npc.topics, sw,
                                      f'asks {npc.name} about {topic!r}, '
                                      f'which they will not talk about')
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

    check_documented(rep)
    check_landing(rep)


#: Content modules that are deliberately not documented for the player, and
#: why. Anything else under `flatline/content/` must be claimed by a topic.
NOT_PLAYER_FACING = {
    'effects': 'the modifier vocabulary: an implementation detail of every '
               'other system, and named by none of them in play',
    'manual': 'the manual itself',
}


def check_documented(rep: Report) -> None:
    """Every system has a topic, and every topic points at a real system.

    This is the project's oldest rule turned on its own prose. Content that
    declares something the engine never reads is a lie that ships because it
    works; a system nobody wrote a topic for is the same lie told by omission,
    and it also ships, and it also works. Adding a content module now fails
    the build until somebody either explains it or says out loud that it does
    not need explaining.
    """
    import pathlib

    modules = {p.stem for p in pathlib.Path('flatline/content').glob('*.py')}
    modules.discard('__init__')
    claimed: dict[str, list[str]] = {}
    for topic in manual.TOPICS:
        for name in topic.covers:
            claimed.setdefault(name, []).append(topic.key)

    for name in sorted(modules):
        if name in NOT_PLAYER_FACING:
            rep.check(name not in claimed, 'manual',
                      f'{name} is both documented and declared not to need it')
            continue
        owners = claimed.get(name, [])
        rep.check(bool(owners), 'manual',
                  f'content/{name}.py is a system with no topic explaining '
                  f'it: give one a `covers`, or add it to NOT_PLAYER_FACING '
                  f'with a reason')
        rep.check(len(owners) <= 1, 'manual',
                  f'content/{name}.py is claimed by {owners}, so a player '
                  f'reading either does not know they have the whole of it')

    for name, owners in claimed.items():
        rep.check(name in modules, 'manual',
                  f'{owners} claims to document content/{name}.py, which is '
                  f'not there')

    # Declared search terms are what a player types. Two topics claiming the
    # same one is the real hazard: search scores terms above body text, so a
    # word owned by two pages is a word that opens neither (D68). A term
    # that also appears in the prose is fine and often necessary: `trace`
    # belongs to `triangle` and saying so is how the search finds it, which
    # the old rule against it made impossible.
    owners: dict[str, str] = {}
    for topic in manual.TOPICS:
        where = f'manual/{topic.key}'
        for term in topic.terms:
            rep.check(term == term.lower().strip(), where,
                      f'search term {term!r} is not normalised')
            first = owners.setdefault(term, topic.key)
            rep.check(first == topic.key, where,
                      f'search term {term!r} is also claimed by '
                      f'{first!r}, so it opens neither')
    for topic in manual.TOPICS:
        where = f'manual/{topic.key}'
        body = ui.plain(topic.body).lower()
        for term in ():
            rep.check(term not in body, where,
                      f'search term {term!r} is already in the body, so the '
                      f'search finds this topic without it')
            rep.check(term not in topic.key, where,
                      f'search term {term!r} is the topic key')
    # Two topics claiming the same search word send the player somewhere
    # arbitrary.
    seen: dict[str, str] = {}
    for topic in manual.TOPICS:
        for term in topic.terms:
            if term in seen:
                rep.error('manual', f'both {seen[term]} and {topic.key} claim '
                                    f'the search term {term!r}')
            seen[term] = topic.key


def check_landing(rep: Report) -> None:
    """The one screen `help` opens on has to stay one screen.

    It replaced a hundred and forty line index, and the only thing stopping it
    growing back into one is this.
    """
    rep.check(len(manual.STARTER_PATH) <= 5, 'manual',
              f'the starter path is {len(manual.STARTER_PATH)} topics, which '
              f'is a reading list rather than a first step')
    for key in manual.STARTER_PATH:
        rep.check(key in manual.BY_KEY, 'manual',
                  f'STARTER_PATH names unknown topic {key!r}')
    rep.check(len(manual.ORIENTATION) <= 6, 'manual',
              'the "lost right now" list is long enough to get lost in')
    for name, blurb in manual.ORIENTATION:
        cmd = REGISTRY.lookup(name)
        rep.check(cmd is not None, 'manual',
                  f'ORIENTATION names no command: {name!r}')
        rep.check(bool(blurb) and blurb == blurb.lower().lstrip(), 'manual',
                  f'ORIENTATION blurb for {name!r} is not a lowercase phrase')
        if cmd is not None:
            # These are offered to somebody who is lost. Every one of them has
            # to be free, or the advice costs the player the thing they are
            # short of.
            rep.check(cmd.ticks == 0, 'manual',
                      f'ORIENTATION offers {name!r}, which costs '
                      f'{cmd.ticks} ticks')
            rep.check('any' in cmd.contexts, 'manual',
                      f'ORIENTATION offers {name!r}, which does not work in '
                      f'both halves of the game')


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
        # The sentence appended to "only works in the city". It is only ever
        # read by somebody who has just been refused, so it has to explain the
        # rule rather than restate the refusal.
        if cmd.blocked:
            rep.check('any' not in cmd.contexts, where,
                      'explains why it is blocked but is legal everywhere')
            rep.check(cmd.blocked[0].isupper()
                      and cmd.blocked.rstrip().endswith('.'), where,
                      'blocked reason is not a sentence')
            rep.check('only works' not in cmd.blocked, where,
                      'blocked reason restates the refusal instead of the rule')

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


def check_palette_separation(rep: Report) -> None:
    """Every role in every palette has to be tellable from every other one.

    A palette where `trace` and `dim` render the same is not a mood, it is a
    bug, and the author's eye is the wrong instrument for catching it: the two
    colours look different in the source and identical on the screen.

    Checked at both rungs, because they fail differently. Truecolour fails by
    two hexes being too close together; the 256-colour cube fails by two
    genuinely different colours quantising onto the same index, which is
    invisible in the source and total on the terminal.
    """
    from itertools import combinations

    #: Pairs the palettes deliberately make identical, per the one-idea-one-
    #: colour rule: a failed check and a rising trace mean the same thing.
    twins = {frozenset(('err', 'trace')), frozenset(('warn', 'noise')),
             frozenset(('info', 'ice')), frozenset(('ok', 'credit'))}
    #: Minimum RGB distance between any two roles that are not twins.
    floor = 20.0

    for name, pal in theme.PALETTES.items():
        # `ansi` never consults its hex values; it exists to be rendered at
        # the sixteen-colour rung against somebody else's scheme.
        if name == 'ansi':
            continue
        for a, b in combinations(theme.ROLES, 2):
            if frozenset((a, b)) in twins:
                continue
            ca, cb = getattr(pal, a), getattr(pal, b)
            gap = sum((x - y) ** 2 for x, y in zip(ca.rgb, cb.rgb)) ** 0.5
            rep.check(gap >= floor, f'theme/{name}',
                      f'{a} and {b} are {gap:.0f} apart, under the {floor:.0f} '
                      f'needed to tell them apart on a screen')
            rep.check(ca.c256 != cb.c256, f'theme/{name}',
                      f'{a} and {b} both quantise to 256-colour index '
                      f'{ca.c256}, so they are the same colour on most '
                      f'terminals over ssh')

    # The quantiser itself. A saturated colour must never land on the grey
    # ramp: that was the original bug and it rendered the entire game in
    # greyscale at the 256-colour rung.
    for probe in ('#00f0ff', '#ff5f8f', '#72f1b8', '#ff5fd7', '#6cb6ff'):
        index = theme.Color(probe, 'white').c256
        rep.check(not 232 <= index <= 255, 'theme/quantise',
                  f'{probe} quantises to {index}, which is a grey')


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
            if span.role and span.role not in known \
                    and not span.role.startswith('#'):
                rep.error('markup', f'{where}: unknown role {span.role!r}')

    # Footnotes. An unbalanced brace does not crash, it swallows the rest of
    # the line into an aside, which is worse: it looks deliberate.
    for where, text in sources:
        if '{{' not in text and '}}' not in text:
            continue
        if text.count('{{') != text.count('}}'):
            rep.error('footnotes', f'{where}: unbalanced {{{{ }}}}')
            continue
        stripped, notes = ui.split_notes(text)
        if len(notes) > ui.MAX_NOTES:
            rep.error('footnotes',
                      f'{where}: {len(notes)} notes in one block, and only '
                      f'{ui.MAX_NOTES} will print')
        for note in notes:
            if not note.strip():
                rep.error('footnotes', f'{where}: an empty footnote')
            elif len(ui.plain(note)) > 320:
                rep.warn('footnotes',
                         f'{where}: a {len(ui.plain(note))}-character aside, '
                         f'which is a paragraph wearing a hat')
        # The marker has to attach to something. A note opening a line has
        # nothing to be an aside from.
        if stripped.lstrip().startswith(tuple(ui._SUPER) + ('[1]',)):
            rep.error('footnotes',
                      f'{where}: opens on a footnote marker, with nothing '
                      f'before it for the note to be about')

    # Content is authored to fit the reading column at the ASCII rung.
    caps = ui.Caps(color=ui.ColorLevel.NONE, glyphs=ui.GlyphLevel.ASCII,
                   width=80, palette=theme.NEUTRAL)
    for where, text in sources:
        text = ui.split_notes(text, ascii_only=True)[0]
        for line in ui.wrap(text, caps.text_width):
            if ui.width(line) > caps.text_width:
                rep.error('layout', f'{where}: a line exceeds '
                                    f'{caps.text_width} columns after wrapping')


# --------------------------------------------------------------------------
# balance sanity
# --------------------------------------------------------------------------


def check_heat(rep: Report) -> None:
    """Heat must actually decay at the twelve rates the factions declare.

    This check exists because it did not. `decay_heat` rounded to an integer
    every shift, which quietly collapsed twelve declared rates into four
    behaviours and made Carrion and Sixes heat permanent, because 0.4 and 0.5
    both round away to nothing. Nobody noticed for the life of the project:
    the number on the screen was an integer either way, and "they hold a
    grudge" is exactly what you would expect a gang to do.

    The lesson generalises past heat. A rate declared as a float and applied
    to a value stored as an int is not a slow effect, it is no effect, and it
    looks identical to a slow one from outside.
    """
    from flatline.model import identity as ident

    def shifts_to_clear(key: str, cover: int = 0) -> int:
        """Drive the real decay, not a copy of it.

        A check that reimplements the arithmetic it is checking will agree
        with itself forever. This one adds heat through the same method the
        game uses and cools it with the same method the city calls every
        shift, so a rounding step reintroduced anywhere in that path shows up
        here as a faction that stops forgetting.
        """
        alias = ident.Alias(name='probe')
        alias.add_heat(key, 90)
        for n in range(1, 2001):
            alias.decay_heat(cover=cover)
            if alias.attention(key) <= 0:
                return n
        return 2001

    seen: dict[float, str] = {}
    times: dict[str, int] = {}
    for f in factions.FACTIONS:
        where = f'factions/{f.key}'
        rep.check(f.heat_decay > 0, where,
                  f'heat_decay is {f.heat_decay}: heat would never cool')
        n = shifts_to_clear(f.key)
        times[f.key] = n
        rep.check(n <= 400, where,
                  f'90 heat takes {n} shifts to cool at {f.heat_decay}/shift, '
                  f'which is longer than a campaign: this faction never '
                  f'forgets anything')
        # Two factions with different declared rates that behave identically
        # is the signature of the rounding bug, in whatever form it comes back.
        if f.heat_decay in seen:
            rep.check(times[seen[f.heat_decay]] == n, where,
                      f'same decay as {seen[f.heat_decay]} but a different '
                      f'cooling time')
        else:
            for rate, other in seen.items():
                if abs(rate - f.heat_decay) > 1e-9 and times[other] == n:
                    rep.error(where,
                              f'decays at {f.heat_decay} and {other} decays at '
                              f'{rate}, but both take {n} shifts: the rates '
                              f'are being rounded away somewhere')
            seen[f.heat_decay] = f.key

    # Cover has to be worth having at the top of the range and survive being
    # zero at the bottom, or it is a stat the sheet prints and nothing reads.
    slow = shifts_to_clear(_DECAY_PROBE, cover=0)
    fast = shifts_to_clear(_DECAY_PROBE,
                           cover=attr_content.cover(attr_content.ATTR_MAX))
    rep.check(fast < slow, 'attributes/cover',
              f'maximum Cover changes nothing: {fast} shifts either way')
    rep.check(slow - fast >= 5, 'attributes/cover',
              f'maximum Cover saves {slow - fast} shifts out of {slow}, which '
              f'no player will ever feel')
    rep.check(attr_content.cover(attr_content.ATTR_MIN) >= 0, 'attributes/cover',
              'cover goes negative at the bottom of the range')


#: A faction to measure Cover against. The middle of the declared range, so
#: the measurement is about Cover rather than about one faction's temper.
_DECAY_PROBE = sorted(factions.FACTIONS,
                      key=lambda f: f.heat_decay)[len(factions.FACTIONS) // 2].key


def check_guile(rep: Report) -> None:
    """Guile has to be read by the city, not just by the run.

    Guile was the thinnest attribute in the game for a long time in a way that
    was invisible from the content: every piece of it declared a use, and the
    uses were all inside a run. The city priced you by reputation, drift,
    faction attention and the hour, and never once asked how well you asked.

    So this check is source-level and blunt: the two city sums that should
    read Guile must mention it, and the market's quote must be handed a real
    value at every call site rather than defaulting to zero, which is what a
    keyword argument with a default quietly does to four call sites out of
    five.
    """
    import ast
    import pathlib

    root = pathlib.Path('flatline')

    market_src = (root / 'world' / 'market.py').read_text()
    rep.check('guile' in market_src, 'market',
              'quote() does not read Guile: prices in this city do not care '
              'who is asking')

    tree = ast.parse(market_src)
    quote = next((n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == 'quote'), None)
    if quote is None:
        rep.error('market', 'no quote() to check')
    else:
        names = [a.arg for a in quote.args.args]
        rep.check('guile' in names, 'market',
                  'quote() takes no guile argument')

    # Every caller must pass it. A default of 0 means forgetting one is silent.
    for path in sorted(root.rglob('*.py')):
        src = path.read_text()
        if 'quote(' not in src or path.name == 'market.py':
            continue
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == 'quote'):
                continue
            # `shlex.quote` is not this quote.
            owner = getattr(func.value, 'id', '')
            if 'market' not in owner:
                continue
            passed = len(node.args) + len(node.keywords)
            rep.check(passed >= 7, f'{path.name}:{node.lineno}',
                      f'quote() called with {passed} arguments: it is not '
                      f'being told the buyer\'s Guile, so this price ignores '
                      f'it')

    legwork_src = (root / 'commands' / 'city.py').read_text()
    rep.check('LEGWORK_PER_GUILE' in legwork_src, 'legwork',
              'legwork quality does not read Guile: what you are told depends '
              'on your face and the hour but not on how you ask')

    # No dead points. Every value the attribute range allows has to buy
    # something, or the sheet is selling a point that does nothing: worse than
    # a weak attribute, because the character screen still charges for it and
    # the manual still describes it as an improvement.
    from flatline.world import market as market_mod
    lo, hi = attr_content.ATTR_MIN, attr_content.ATTR_MAX
    ladders = {
        'Cover': lambda g: attr_content.cover(g),
        'market haggle': lambda g: min(market_mod.HAGGLE_CAP,
                                       g * market_mod.HAGGLE_PER_GUILE),
    }
    for label, f in ladders.items():
        for g in range(lo, hi):
            rep.check(f(g + 1) > f(g), f'guile/{label}',
                      f'{label} is the same at Guile {g} and {g + 1}: that '
                      f'point of the attribute buys nothing here')


def check_roster(rep: Report) -> None:
    """The character management layer, and the two rules that hold it up.

    Rule one: nothing except `delete` may remove a character. Everybody used
    to share one slot called 'default', so making a second character wrote
    over the first at the next autosave, with no warning, because from the
    save layer's point of view nothing unusual had happened. `new` refused
    until you passed `--force`, and the word it used was "abandon".

    Rule two: every command a player is told to type has to exist. The splash
    said `load` to continue a character. `load` puts a program on a deck. The
    command is `restore`, and the game had been sending new players to the
    wrong verb from the first line they ever read.
    """
    import ast
    import pathlib

    from flatline.shell import AFTER_THE_END, REGISTRY

    root = pathlib.Path('flatline')

    # Every command named in something the player reads must resolve.
    # Restricted to console output and refusals rather than every string in
    # the tree: a docstring saying `parse` is talking to me, and a `c.say`
    # saying `parse` is telling a player to type it.
    known = set(REGISTRY.commands)
    for cmd in REGISTRY.commands.values():
        known.update(cmd.aliases)
    # Words that are vocabulary rather than verbs: things you type *at* a
    # command. Taken from the content tables, so adding an origin or a theme
    # does not fail the build.
    vocabulary = set(known)
    vocabulary |= set(origins.ORIGIN_KEYS) | set(theme.PALETTES)
    vocabulary |= set(districts.DISTRICT_KEYS) | set(factions.FACTION_KEYS)
    vocabulary |= set(attr_content.ATTR_KEYS) | set(skills.SKILL_KEYS)

    # Scoped to what a new player reads before they know anything: the boot
    # path, the messages the shell prints when it refuses, the manual and the
    # tutorial. Every file in the project was the obvious scope and it was
    # the wrong one, because a `detail=` string listing the modes a daemon
    # takes is not an instruction to type `grind`. The bug this is for lived
    # in exactly these four files: the line under the banner said `load`,
    # which is the command that puts a program on a deck.
    for name in ('app.py', 'session.py', 'content/manual.py',
                 'content/tutorial.py'):
        path = root / name
        for text, line in _prose(path.read_text()):
            for quoted in _BACKTICKED.findall(text):
                words = quoted.split()
                if not words:
                    continue
                # Longest match first, so `jack in` is not read as `jack`.
                if (' '.join(words[:2]) in vocabulary
                        or words[0] in vocabulary):
                    continue
                word = words[0]
                if not word.isalpha() or word in _NOT_A_COMMAND:
                    continue
                rep.error(f'{path.name}:{line}',
                          f'tells the player to type `{word}`, which is '
                          f'not a command')

    # A finished character must be able to look and to leave, and must not be
    # able to work. The allowlist is the rule, so it has to be real.
    for name in sorted(AFTER_THE_END):
        rep.check(name in known, 'shell/AFTER_THE_END',
                  f'{name!r} still works after the end, but is not a command')
    for need in ('new', 'switch', 'characters', 'quit', 'help', 'char'):
        rep.check(need in AFTER_THE_END, 'shell/AFTER_THE_END',
                  f'a finished character cannot type {need!r}, which leaves '
                  f'them with no way to look at what happened or to leave')
    for banned in ('board', 'travel', 'buy', 'legwork'):
        rep.check(banned not in AFTER_THE_END, 'shell/AFTER_THE_END',
                  f'a flatlined character can still {banned}')

    # Nothing but `delete` may unlink a save. Source level, because the
    # damage is permanent and a test can only catch the paths it thought of.
    for path in sorted(root.rglob('*.py')):
        if path.name in ('save.py',):
            continue
        src = path.read_text()
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (isinstance(func, ast.Attribute) and func.attr == 'delete'):
                continue
            if 'save' not in getattr(func.value, 'id', ''):
                continue
            fn = _enclosing_def(ast.parse(src), node)
            rep.check(fn in ('cmd_delete', 'cmd_reset'),
                      f'{path.name}:{node.lineno}',
                      f'{fn or "something"} deletes a save. Only `delete` may '
                      f'do that, and only after --confirm')


#: Backticked words in player-facing prose, which are instructions to type.
_BACKTICKED = __import__('re').compile(r'`([^`]+)`')

def _prose(src: str):
    """Every string in a module that is not a docstring, with its line.

    Docstrings are talking to whoever is reading the code; everything else in
    a quoted string in this project is, sooner or later, printed. An f-string
    is reassembled from its literal pieces first, with interpolations standing
    in as a placeholder, because yielding the pieces separately makes
    backticks pair across the gap where a `{name}` used to be: `rest` until it
    cools, or `burn` would otherwise read as a quoted phrase called "until it
    cools, or".
    """
    import ast

    tree = ast.parse(src)
    skip = set()
    for scope in (tree, *[n for n in ast.walk(tree) if isinstance(
            n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]):
        body = getattr(scope, 'body', [])
        if body and isinstance(body[0], ast.Expr):
            first = body[0].value
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                skip.add(id(first))

    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            for part in ast.walk(node):
                skip.add(id(part))
            yield ('_'.join(v.value for v in node.values
                            if isinstance(v, ast.Constant)
                            and isinstance(v.value, str)), node.lineno)
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in skip):
            yield node.value, node.lineno


#: Backticked things that are not commands: flags, files, shell, fiction.
_NOT_A_COMMAND = frozenset({
    # The scripting language, which is typed into `script` rather than at the
    # prompt. See content/scripting.
    'if', 'not', 'for', 'stop', 'repeat', 'when', 'needs', 'alert',
    # Prose about the shell rather than instructions to it.
    'fine', 'flatline', 'conn',
    # A slot name, in the sentence explaining where an imported save lands.
    'imported',
})


def _enclosing_def(tree, target) -> str:
    """Which function a node sits in, by line number."""
    import ast

    best, best_line = '', -1
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.lineno <= target.lineno and node.lineno > best_line:
                best, best_line = node.name, node.lineno
    return best


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


def check_guide(rep: Report) -> None:
    """D50: the onboarding layer names only things that exist.

    The arrival line maps district services to verbs, the `now` panel and the
    guided `new` offer commands by name, and the suggested spend is a plan
    the engine has to be able to carry out. All of it is content telling the
    player what to type, which is the one kind of content this project has
    learned to distrust on sight.
    """
    from flatline.commands import guide
    from flatline.commands.city import SERVICE_VERBS

    seen = set()
    for service, verb, what in SERVICE_VERBS:
        where = f'guide/here/{service}'
        seen.add(service)
        rep.check(service in districts.SERVICES, where,
                  f'names unknown service {service!r}')
        rep.check(REGISTRY.lookup(verb) is not None, where,
                  f'offers {verb!r}, which is not a command')
        rep.check(bool(what) and what[0].islower(), where,
                  'the gloss is not a lowercase phrase')
    for service in districts.SERVICES:
        rep.check(service in seen, 'guide/here',
                  f'{service!r} has no verb on the arrival line, so a player '
                  f'reading it has nothing to type')

    cmd = REGISTRY.lookup('now')
    rep.check(cmd is not None, 'guide/now', 'there is no `now`')
    if cmd is not None:
        rep.check(cmd.ticks == 0, 'guide/now', 'costs ticks')
        rep.check('any' in cmd.contexts, 'guide/now',
                  'does not work in both halves')
        rep.check(cmd.bare, 'guide/now', 'needs a character, and the empty '
                                          'line has to work before there is one')
    for name in ('new', 'spend'):
        rep.check(REGISTRY.lookup(name) is not None, 'guide',
                  f'there is no `{name}`')
    for prompt in (guide.ASK_ORIGIN, guide.ASK_HANDLE, guide.ASK_SPEND):
        rep.check(prompt.endswith('? ') and len(prompt) <= 40, 'guide/ask',
                  f'question prompt {prompt!r} is not short and ending in "? "')

    for o in origins.ORIGINS:
        where = f'guide/spend/{o.key}'
        char = Character.from_origin(o.key, 'probe')
        char.points = attr_content.CREATION_POINTS
        char.xp = skills.CREATION_XP
        plan = guide.suggest(char)
        rep.check(bool(plan), where, 'suggests nothing at creation')
        for verb, key in plan:
            ok, why = (char.can_boost(key) if verb == 'boost'
                       else char.can_train(key))
            rep.check(ok, where, f'{verb} {key} is illegal: {why}')
            if not ok:
                break
            if verb == 'boost':
                char.boost(key)
            else:
                char.train(key)
        rep.check(char.points == 0, where,
                  f'leaves {char.points} attribute points unspent')
        rep.check(char.xp < skills.RANK_COST[2], where,
                  f'leaves {char.xp} experience, which buys a rank')
        rep.check(max(char.base_attrs.values()) < attr_content.ATTR_MAX, where,
                  'pushes an attribute to its ceiling at creation')
        rep.check(any(r >= 2 for r in char.base_skills.values()), where,
                  'buys no technique, so nothing new to type')


def _story_flag(rule: str) -> str | None:
    """The plain flag a story rule reads, or None for a numeric condition.

    `not:lark_dead` reads `lark_dead`; `runs:3` reads nothing. A rule that is
    a flag is only a real reader of that flag if something sets it, which is
    the other half of what `check_consequences` does with this.
    """
    inner = rule[4:] if rule.startswith('not:') else rule
    if not inner or ':' in inner:
        return None
    return inner


def check_consequences(rep: Report) -> None:
    """D51: a decision is content that claims a consequence, and a claim the
    engine never reads is a lie that validates.

    Every flag a choice sets (and nothing else sets, so it is a decision and
    not merely a thing that happened) has to be read by something other than
    the ending: a later scene, an offer, a counter, somebody's presence in
    the city, an ambient event, the streets, or the board. And every one of
    them has to be in the epilogue, because an ending that does not mention
    what you did to Lark is an ending to somebody else's game.

    The same pass holds every story rule anywhere to naming a flag that
    something sets, which is the old rule from `check_threads` turned on the
    four other places that grew rules today.
    """
    from flatline.content import legacy, offers
    from flatline.world import contracts as contract_world
    from flatline.world import story as story_mod

    known = thread_content.flags_set()
    chosen = thread_content.flags_chosen()
    staged = {f for t in thread_content.THREADS for s in t.stages
              for f in s.sets}
    decisions = {f: who for f, who in chosen.items() if f not in staged}
    rep.check(len(decisions) >= 40, 'consequences',
              f'only {len(decisions)} decisions in the whole story')

    readers: dict[str, set[str]] = {f: set() for f in decisions}

    def reads(rule: str, who: str, where: str) -> None:
        flag = _story_flag(rule)
        if flag is None:
            inner = rule[4:] if rule.startswith('not:') else rule
            kind = inner.split(':')[0]
            rep.check(kind in thread_content.CONDITIONS
                      or kind in ('met', 'ran'), where,
                      f'{rule!r} is not a rule anything can evaluate')
            return
        rep.check(flag in known, where,
                  f'reads {flag!r}, which nothing in the story ever sets')
        if flag in readers:
            readers[flag].add(who)

    for t in thread_content.THREADS:
        for s in t.stages:
            for rule in tuple(s.requires) + tuple(s.any_of):
                reads(rule, f'stage {t.key}.{s.key}', f'threads/{t.key}')
    for e in events.EVENTS:
        for rule in tuple(e.requires) + tuple(e.any_of):
            reads(rule, f'event {e.key}', f'events/{e.key}')
    for n in npc_content.NPCS:
        for rule in n.requires:
            if rule.split(':')[0] not in npc_content.NUMERIC_RULES:
                reads(rule, f'npc {n.key}', f'npcs/{n.key}')
        for topic, rule, text in n.more:
            rep.check(topic in n.topics, f'npcs/{n.key}/more',
                      f'varies {topic!r}, which they do not talk about')
            rep.check(bool(text), f'npcs/{n.key}/more/{topic}', 'is empty')
            reads(rule, f'npc {n.key} on {topic}', f'npcs/{n.key}/more')
    from flatline.content import spots as spot_content
    for f in spot_content.FINDS:
        for rule in f.requires:
            reads(rule, f'find {f.item}', f'spots/finds/{f.item}')
    for w in offers.WORK:
        for rule in w.requires:
            reads(rule, f'work {w.npc}', f'offers/work/{w.npc}')
    for fav in offers.FAVOURS:
        for rule in fav.requires:
            reads(rule, f'favour {fav.npc}.{fav.key}',
                  f'offers/favour/{fav.npc}/{fav.key}')
    for st in offers.STOCK:
        for rule in st.requires:
            reads(rule, f'stock {st.npc}', f'offers/stock/{st.npc}')
        if st.requires:
            rep.check(bool(st.refusal), f'offers/stock/{st.npc}',
                      'can close the counter but has nothing to say about it')
    for flag, faction, mult in story_mod.STREET_RIDERS:
        where = f'story/streets/{flag}'
        rep.check(flag in decisions, where, 'is not a decision a choice makes')
        rep.check(faction in factions.BY_KEY, where,
                  f'names unknown faction {faction!r}')
        rep.check(0 < mult < 1.0 or mult > 1.0, where,
                  f'multiplier {mult} changes nothing')
        if flag in readers:
            readers[flag].add('streets')
    for flag, faction, mult in contract_world.PATRON_RIDERS:
        where = f'contracts/patrons/{flag}'
        rep.check(flag in decisions, where, 'is not a decision a choice makes')
        rep.check(faction in factions.BY_KEY, where,
                  f'names unknown faction {faction!r}')
        rep.check(mult != 1.0, where, 'multiplier of one changes nothing')
        if flag in readers:
            readers[flag].add('board')
    for flag in legacy.ENDING_FLAGS:
        rep.check(flag in decisions, f'legacy/ending/{flag}',
                  'is not a decision a choice makes')
        if flag in readers:
            readers[flag].add('ending')
    for flag in legacy.CODAS:
        rep.check(flag in legacy.ENDING_FLAGS, f'legacy/coda/{flag}',
                  'has a coda but is not declared an ending flag')

    # The epilogue: complete, and nothing in it that is not a decision.
    epi_flags = [flag for flag, _ in legacy.EPILOGUE]
    rep.check(len(epi_flags) == len(set(epi_flags)), 'legacy/epilogue',
              'a decision has two epilogue lines')
    for flag, line in legacy.EPILOGUE:
        where = f'legacy/epilogue/{flag}'
        rep.check(flag in decisions, where,
                  'is not a decision any choice makes')
        rep.check(bool(line) and line.rstrip().endswith('.'), where,
                  'is not a sentence')
        rep.check(len(ui.plain(line)) > 40, where,
                  'is a caption, not a line of an ending')
    epi = set(epi_flags)
    for flag, (thread, stage, choice) in sorted(decisions.items()):
        where = f'threads/{thread}/{stage}/{choice}'
        rep.check(flag in epi, where,
                  f'decision {flag!r} has no epilogue line: the ending '
                  f'forgets it')
        rep.check(bool(readers[flag]), where,
                  f'decision {flag!r} is read by nothing but the ending: '
                  f'prose with a flag on it')

    # Every choice whose prose hands something over has to hand it over, and
    # what it hands over has to exist.
    from flatline.content import cyberware as ware_content
    from flatline.content import hardware as hw_content
    from flatline.content import programs as prog_content
    for t in thread_content.THREADS:
        for s in t.stages:
            for ch in s.choices:
                for key in ch.gives:
                    rep.check(key in hw_content.BY_KEY or key in prog_content.BY_KEY
                              or key in ware_content.BY_KEY,
                              f'threads/{t.key}/{s.key}/{ch.key}',
                              f'gives {key!r}, which is not in any catalogue')


def check_spine(rep: Report) -> None:
    """D52: the spine, and story inside runs.

    Every posting names real content and draws a run that can be finished;
    finishing it is required by a later scene, or it is a run nobody comes
    back from; the Deepwater thread has the shape the plan promised (five
    acts, more than one way into the offer, and a door that only crossings
    open, which goes somewhere); and every ending flag is a Deepwater
    decision.
    """
    from flatline.content import legacy
    from flatline.rng import Rng
    from flatline.run import network as net_mod

    all_stages = [(t, s) for t in thread_content.THREADS for s in t.stages]
    for t, s in all_stages:
        if s.posts is None:
            continue
        where = f'threads/{t.key}/{s.key}/posts'
        p = s.posts
        rep.check(p.patron in factions.BY_KEY, where,
                  f'unknown patron {p.patron!r}')
        rep.check(p.target in factions.BY_KEY, where,
                  f'unknown target {p.target!r}')
        rep.check(p.objective in contract_mod.OBJECTIVES, where,
                  f'unknown objective {p.objective!r}')
        rep.check(bool(p.title and p.blurb), where, 'has no title or blurb')
        rep.check(p.pay >= 0, where, 'pays less than nothing')
        if p.objective in ('exfiltrate', 'corrupt', 'wipe'):
            rep.check(bool(p.label), where,
                      'is about a record and does not say which')
        tag = f'did:{t.key}.{s.key}'
        readers = [f'{t2.key}.{s2.key}' for t2, s2 in all_stages
                   if tag in s2.requires or tag in s2.any_of]
        rep.check(bool(readers), where,
                  f'nothing requires {tag!r}: a run nobody comes back from')
        if p.target in factions.BY_KEY and p.objective in contract_mod.OBJECTIVES:
            net = net_mod.generate(Rng(7).fork('network', f'{t.key}.{s.key}'),
                                   p.target, factions.BY_KEY[p.target].posture,
                                   p.objective, 1.0)
            rep.check(bool(net.objective_node), where,
                      'draws a network with no objective')
            if p.label:
                rep.check(bool(net.objective_asset), where,
                          'names a record but the run has no objective record')

    for t, s in all_stages:
        for ch in s.choices:
            where = f'threads/{t.key}/{s.key}/{ch.key}'
            if ch.ends:
                rep.check(ch.ends == ch.ends.lower()
                          and not ch.ends.endswith('.')
                          and len(ch.ends.split()) >= 2, where,
                          f'`ends` should be a short past-tense phrase, not '
                          f'{ch.ends!r}')
            rep.check(-20 <= ch.drift <= 20, where,
                      f'drift {ch.drift} is a cliff, not a mark')

    dw = thread_content.BY_KEY.get('deepwater')
    rep.check(dw is not None, 'spine', 'there is no Deepwater thread')
    if dw is None:
        return
    keys = [s.key for s in dw.stages]
    rep.check(len(keys) >= 8, 'spine', f'{len(keys)} scenes is not a spine')
    for key in ('hear', 'posting', 'carried', 'offer', 'under'):
        rep.check(key in keys, 'spine', f'has no {key!r} act')
    by_key = {s.key: s for s in dw.stages}
    offer = by_key.get('offer')
    if offer is not None:
        rep.check(len(offer.any_of) >= 2, 'spine', 'the offer has one way in')
    posting = by_key.get('posting')
    if posting is not None:
        rep.check(len(posting.any_of) >= 3, 'spine',
                  'the posting has fewer than three ways in')
        rep.check(posting.posts is not None, 'spine',
                  'the posting scene posts nothing')
    under = by_key.get('under')
    if under is not None:
        others = set()
        for rule in under.requires:
            for t2, s2 in all_stages:
                if t2.key == 'deepwater':
                    continue
                if rule in s2.sets or any(rule in ch.sets for ch in s2.choices):
                    others.add(t2.key)
        rep.check(len(others) >= 2, 'spine',
                  f'the door is opened by {len(others)} other thread(s); it '
                  f'should take crossings')
        rep.check(any(ch.ends for ch in under.choices), 'spine',
                  'the door does not go anywhere')
    decided = {flag for s in dw.stages for ch in s.choices for flag in ch.sets}
    for flag in legacy.ENDING_FLAGS:
        rep.check(flag in decided, 'spine',
                  f'ending flag {flag!r} is not a Deepwater decision')
    rep.check(sum(1 for s in dw.stages for ch in s.choices) >= 8, 'spine',
              'fewer than eight decisions in the whole spine')


def check_city_texture(rep: Report) -> None:
    """D53: every district has a scene for every hour, two or three places
    to stand in, and the street has something to say below an incident.

    Texture is content too, and content that is missing for one district at
    one hour is the kind of gap nobody notices until they stand in it.
    """
    from flatline.content import spots as spot_content
    from flatline.world import fallout

    def sentence(where: str, text: str, what: str,
                 lo: int = 80, hi: int = 700) -> None:
        stripped, notes = ui.split_notes(text)
        body = ui.plain(stripped)
        written = len(body) + sum(len(ui.plain(n)) for n in notes)
        rep.check(lo < written <= hi, where,
                  f'{what} is {written} characters; wanted {lo} to {hi}')
        tail = body.rstrip().rstrip(ui._SUPER + ']0123456789[')
        rep.check(tail.endswith(('.', '!', '?')), where,
                  f'{what} does not end in a full stop')
        for note in notes:
            flat = ui.plain(note).rstrip().rstrip(ui._SUPER + ']0123456789[')
            rep.check(flat.endswith(('.', '!', '?')), where,
                      f'an aside in {what} does not end in a full stop')

    for d in districts.DISTRICTS:
        for phase in city_mod.SHIFT_NAMES:
            where = f'districts/{d.key}/{phase}'
            text = districts.scene(d.key, phase)
            rep.check(bool(text), where, 'has no scene for this hour')
            if text:
                sentence(where, text, 'the scene')
    for key in districts.SCENES:
        rep.check(key in districts.BY_KEY, 'districts/scenes',
                  f'a scene is written for unknown district {key!r}')
        for phase in districts.SCENES[key]:
            rep.check(phase in city_mod.SHIFT_NAMES, f'districts/{key}',
                      f'a scene is written for unknown hour {phase!r}')

    seen: set[str] = set()
    for s in spot_content.SPOTS:
        where = f'spots/{s.key}'
        rep.check(s.key not in seen, where, 'duplicate key')
        seen.add(s.key)
        rep.check(s.district in districts.BY_KEY, where,
                  f'in unknown district {s.district!r}')
        rep.check(s.name.startswith('the '), where,
                  'name should read "the <place>", the way a person says it')
        sentence(where, s.blurb, 'the blurb')
        if s.night:
            sentence(where, s.night, 'the night variant', lo=40)
        for who in s.who:
            npc = npc_content.BY_KEY.get(who)
            rep.check(npc is not None, where, f'names unknown person {who!r}')
            if npc is not None and npc.where:
                rep.check(npc.where == s.district, where,
                          f'{who} lives in {npc.where}, not {s.district}')
            if npc is not None and npc.at:
                rep.check(npc.at in districts.BY_KEY[s.district].services
                          if s.district in districts.BY_KEY else True, where,
                          f'{who} needs a {npc.at} and {s.district} has none')
    for d in districts.DISTRICTS:
        count = len(spot_content.in_district(d.key))
        rep.check(3 <= count <= 7, f'districts/{d.key}',
                  f'{count} places to stand in; wanted three to seven')
        # D58: the street has something in it, at every hour, and it is the
        # same thing twice in a shift.
        pool = districts.STREET.get(d.key, ())
        rep.check(len(pool) >= 6, f'districts/{d.key}/street',
                  f'{len(pool)} things in the street; wanted six or more')
        # Two lines that open the same way read as a stutter when the
        # picker puts them in one sentence: the Hall had "two of
        # Carrion's at the back of the clinic queue" and "two of
        # Carrion's at the back, not in the queue" and printed both,
        # because the picker only ever compared whole strings.
        openings: dict[str, str] = {}
        for item in pool:
            head = ' '.join(item.lower().replace(',', ' ').split()[:4])
            rep.check(head not in openings, f'districts/{d.key}/street',
                      f'two lines open the same way ({head}...): '
                      f'{openings.get(head, "")!r} and {item!r}')
            openings[head] = item
        for shift in range(9):
            line = districts.street_line(d.key, shift)
            rep.check(line.startswith('In the street:') and line.endswith('.'),
                      f'districts/{d.key}/street', 'is not a sentence')
            rep.check(line == districts.street_line(d.key, shift),
                      f'districts/{d.key}/street', 'changes between looks')
            rep.check(len(ui.plain(line)) <= 300, f'districts/{d.key}/street',
                      'is a paragraph')
        # Finding by name has to work for every name, and must not be
        # ambiguous within a district.
        for s in spot_content.in_district(d.key):
            found = spot_content.find(d.key, s.name)
            rep.check(found is s, f'spots/{s.key}',
                      'cannot be found by its own name')
            found = spot_content.find(d.key, s.name.removeprefix('the '))
            rep.check(found is s, f'spots/{s.key}',
                      'cannot be found without the article')

    # D57: the drawn map claims exactly the joins the city has, and fits.
    from flatline import citymap
    from flatline.game import Game
    from flatline.model.character import Character
    # D67: every road between two districts has something on it, and
    # nothing has a road that the map does not draw.
    graph_edges = {frozenset((a, b)) for a, bs in districts.GRAPH.items()
                   for b in bs}
    for edge in graph_edges:
        a, b = sorted(edge)
        rep.check(edge in districts.CROSSINGS, f'districts/{a}',
                  f'nothing is between {a} and {b}')
    for edge in districts.CROSSINGS:
        a, b = sorted(edge)
        rep.check(edge in graph_edges, 'districts/crossings',
                  f'{a} to {b} is written and is not a road')
        for line in districts.CROSSINGS[edge]:
            rep.check(len(line) >= 60, 'districts/crossings',
                      f'{a} to {b} is too short to be a walk')
            rep.check(line.rstrip().endswith(('.', '!', '?')),
                      'districts/crossings', f'{a} to {b} has no full stop')
    rep.check(citymap.MAP_EDGES == graph_edges, 'citymap',
              f'the drawing and the city disagree about the joins: '
              f'{sorted(map(sorted, citymap.MAP_EDGES ^ graph_edges))}')
    game = Game.new(Character.from_origin('gutter', 'probe'), seed=1)
    for glyphs in (ui.GlyphLevel.UNICODE, ui.GlyphLevel.ASCII):
        caps = ui.Caps(color=ui.ColorLevel.NONE, glyphs=glyphs, width=80,
                       palette=theme.NEUTRAL)
        lines = citymap.draw(game, caps)
        plain = [ui.plain(line) for line in lines]
        rep.check(all(len(line) <= 76 for line in plain), 'citymap',
                  f'the drawing is wider than the text column ({glyphs.name})')
        joined = '\n'.join(plain)
        for key in districts.DISTRICT_KEYS:
            rep.check(key in joined, 'citymap',
                      f'{key} is not on the drawing ({glyphs.name})')
        rep.check(citymap.MARK_HERE in joined, 'citymap',
                  f'you are not on the drawing ({glyphs.name})')
        if glyphs is ui.GlyphLevel.ASCII:
            rep.check(all(ord(ch) < 128 for ch in joined), 'citymap',
                      'the ASCII rung draws a non-ASCII character')

    rep.check(len(fallout.CLOSE_CALLS) >= 4, 'fallout/close',
              'fewer than four ways for the street to let you know')
    for i, text in enumerate(fallout.CLOSE_CALLS):
        where = f'fallout/close/{i}'
        rep.check('{district}' in text, where, 'does not say where')
        sentence(where, text.format(district='Marrow', fac='Kagawa'),
                 'the close call')
    rep.check(0 < fallout.CLOSE_CALL_HEAT < 10, 'fallout/close',
              'a close call should cost a little, not a lot')


def check_portraits(rep: Report) -> None:
    """D62: every behaviour has a mark, three rows, the same width, and the
    ASCII rung draws it in ASCII."""
    for behaviour in ice_content.BEHAVIOURS:
        where = f'ice/portrait/{behaviour}'
        pair = ice_content.PORTRAITS.get(behaviour)
        rep.check(pair is not None, where, 'has no portrait')
        if pair is None:
            continue
        for rows, rung in ((pair[0], 'unicode'), (pair[1], 'ascii')):
            rep.check(len(rows) == 3, where, f'{rung}: not three rows')
            widths = {ui.width(r) for r in rows}
            rep.check(len(widths) == 1, where, f'{rung}: rows differ in width')
            rep.check(all(1 <= w <= 7 for w in widths), where,
                      f'{rung}: wider than a mark should be')
        rep.check(all(ord(ch) < 128 for r in pair[1] for ch in r), where,
                  'the ASCII rung draws a non-ASCII character')
    for key in ice_content.PORTRAITS:
        rep.check(key in ice_content.BEHAVIOURS, 'ice/portrait',
                  f'a portrait for unknown behaviour {key!r}')


def check_conditions(rep: Report) -> None:
    """D61: tonight's weather inside a network changes something, says so,
    and stays inside sane bounds.

    A condition that is neutral is a lie with a name; one that moves a number
    past these bounds is a difficulty setting wearing weather; a slow verb
    that is not a run command is a claim the engine never reads.
    """
    from flatline.content import conditions as cond_content
    from flatline.commands.run import COST
    from flatline.rng import Rng

    # Tonight, outside (D133): the street's own weather, held to the same
    # standard as the run's.
    rep.check(len(cond_content.NIGHTS) >= 4, 'nights', 'fewer than four nights')
    rep.check(0.2 <= cond_content.NIGHT_CHANCE <= 0.7, 'nights',
              f'NIGHT_CHANCE {cond_content.NIGHT_CHANCE} out of band')
    for n in cond_content.NIGHTS:
        where = f'nights/{n.key}'
        rep.check(bool(n.name) and bool(n.blurb) and bool(n.summary), where,
                  'missing name, blurb or summary')
        rep.check(n.blurb.rstrip().endswith('.'), where, 'blurb does not end')
        rep.check(not n.neutral, where, 'changes nothing: weather with a name')
        rep.check(0.4 <= n.rough <= 2.0 and 0 <= n.tier <= 1
                  and 0.5 <= n.muscle <= 2.0 and 0.5 <= n.loud <= 3.0
                  and 0.5 <= n.loot <= 2.0, where, 'a number out of band')
        rep.check(n.weight > 0, where, 'can never be drawn')
    rep.check(len(cond_content.CONDITIONS) >= 6, 'conditions',
              f'only {len(cond_content.CONDITIONS)} conditions; the weather '
              f'repeats')
    rep.check(0.2 <= cond_content.CHANCE <= 0.6, 'conditions',
              'a condition should be something that happened tonight, not the '
              'way networks are, and not so rare nobody meets one')
    seen: set[str] = set()
    for c in cond_content.CONDITIONS:
        where = f'conditions/{c.key}'
        rep.check(c.key not in seen, where, 'duplicate key')
        seen.add(c.key)
        rep.check(bool(c.name) and bool(c.blurb) and bool(c.summary), where,
                  'is missing its name, blurb or summary')
        rep.check(c.blurb.rstrip().endswith('.'), where,
                  'the blurb is not a sentence')
        rep.check(not c.neutral, where, 'changes nothing: weather with a name')
        rep.check(0.5 <= c.trace <= 2.0 and 0.5 <= c.noise <= 2.0
                  and 0.5 <= c.residue <= 2.0 and 0.5 <= c.pay <= 2.0, where,
                  'a multiplier is outside 0.5 to 2')
        rep.check(-3 <= c.wake <= 3 and -2 <= c.crack <= 2, where,
                  'an offset is a cliff, not weather')
        rep.check(c.weight > 0, where, 'can never be drawn')
        for verb in c.slow:
            rep.check(verb in COST and COST[verb][0] > 0, where,
                      f'slows {verb!r}, which is not a run verb that costs '
                      f'ticks')
        rep.check(len(c.terms()) >= 1, where, 'has nothing to say at the door')
    # The draw: deterministic per stream, sometimes nothing, and every
    # condition reachable.
    drawn = set()
    for i in range(400):
        got = cond_content.pick(Rng(i).fork('condition', f'c{i:03d}'))
        if got is not None:
            drawn.add(got.key)
    rep.check(drawn == set(cond_content.CONDITION_KEYS), 'conditions',
              f'not every condition comes up in four hundred nights: missing '
              f'{sorted(set(cond_content.CONDITION_KEYS) - drawn)}')
    a = cond_content.pick(Rng(9).fork('condition', 'c001'))
    b = cond_content.pick(Rng(9).fork('condition', 'c001'))
    rep.check(a is b, 'conditions', 'the same night draws differently twice')



# --------------------------------------------------------------------------
# the street (D65)
# --------------------------------------------------------------------------


def check_record(rep: Report) -> None:
    """The record (D142): four sections, and no line counting something
    the engine never writes."""
    from flatline.content import record as record_content
    from flatline import save as save_mod
    rep.check(len(record_content.SECTIONS) == 4, 'record',
              'the record is four sections, one per reason to play')
    seen = set()
    for e in record_content.ENTRIES:
        where = f'record/{e.key}'
        rep.check(e.key not in seen, where, 'duplicate key')
        seen.add(e.key)
        rep.check(e.section in record_content.SECTION_KEYS, where,
                  f'unknown section {e.section!r}')
        rep.check(e.target >= 1, where, 'a target of nothing')
        rep.check(bool(e.name and e.earned), where, 'has no line to say')
        rep.check(e.earned.rstrip().endswith('.'), where, 'the line does not end')
        # The counter has to be a real profile counter, and something
        # outside content has to move it, or it is a line nobody can cross.
        rep.check(e.counter in save_mod.META_DEFAULT, where,
                  f'counts {e.counter!r}, which the profile does not keep')
        rep.check(f"'{e.counter}'" in _engine_source()
                  or f'{e.counter}=' in _engine_source(), where,
                  f'counts {e.counter!r}, which nothing ever writes')
    for key in record_content.SECTION_KEYS:
        n = len(record_content.BY_SECTION[key])
        rep.check(n >= 4, f'record/{key}', f'only {n} lines in the section')
        rep.check(key in record_content.SECTION_TITLE, f'record/{key}',
                  'a section with no name for finishing it')
    titled = sum(1 for e in record_content.ENTRIES if e.title)
    rep.check(titled >= 8, 'record', f'only {titled} lines earn a name')
    # The flavoured titles (D151): each reads a rule the world layer
    # can evaluate, and the three registers are all represented.
    import collections
    reg = collections.Counter(t.register for t in record_content.TITLES)
    for register in record_content.REGISTERS:
        rep.check(reg[register] >= 3, 'record/titles',
                  f'fewer than three {register} titles')
    seen_t = set()
    for t in record_content.TITLES:
        where = f'record/title/{t.key}'
        rep.check(t.key not in seen_t, where, 'duplicate key')
        seen_t.add(t.key)
        rep.check(t.register in record_content.REGISTERS, where,
                  f'unknown register {t.register!r}')
        rep.check(bool(t.name and t.earned)
                  and t.earned.rstrip().endswith('.'), where,
                  'has no name or no line')
        # The rule is a real one: a flag, a `not:`, or a known kind.
        inner = t.rule[4:] if t.rule.startswith('not:') else t.rule
        kind = inner.split(':')[0] if ':' in inner else ''
        rep.check(not kind or kind in thread_content.CONDITIONS, where,
                  f'reads unknown condition {kind!r}')


def check_feed(rep: Report) -> None:
    """The deck in the city (D135): ads held to their predicates and the
    tone vocabulary, and a reply for every opinion a runner can hold."""
    from flatline.content import feed
    from flatline.content import rivals as rival_content
    rep.check(len(feed.ADS) >= 12, 'feed', 'fewer than twelve ads')
    rep.check(sum(1 for a in feed.ADS if a.when == 'any') >= 3, 'feed',
              'fewer than three ads for everybody')
    seen = set()
    for a in feed.ADS:
        where = f'feed/ad/{a.key}'
        rep.check(a.key not in seen, where, 'duplicate key')
        seen.add(a.key)
        rep.check(a.when in feed.WHEN, where, f'unknown predicate {a.when!r}')
        rep.check(a.tone in events.TONES, where, f'tone {a.tone!r}')
        rep.check(bool(a.sponsor) and a.text.rstrip().endswith('.'), where,
                  'has no sponsor or does not end')
    absurd = sum(1 for a in feed.ADS if a.tone == 'absurd') / len(feed.ADS)
    rep.check(absurd <= 0.75, 'feed', f'{absurd:.0%} of the ads are absurd: too many')
    bands = {name for _, name in rival_content.DISPOSITION_BANDS} | {'partner', 'nemesis'}
    for band in bands:
        rep.check(bool(feed.REPLIES.get(band)), 'feed', f'no reply for {band!r}')
    for name in ('PARTNER_MAIL', 'NEMESIS_MAIL', 'FIXER_MAIL', 'WORK_MAIL',
                 'LENDER_MAIL', 'PIT_MAIL', 'BOUNTY_MAIL'):
        rep.check(bool(getattr(feed, name)), 'feed', f'{name} is empty')
    # Every predicate declared is evaluated by the world layer.
    source = pathlib.Path('flatline/world/deck.py').read_text(encoding='utf-8')
    for key in feed.WHEN:
        rep.check(f"'{key}'" in source, 'feed', f'predicate {key!r} is read nowhere')


def check_pit(rep: Report) -> None:
    """The pit (D134): a ladder that is a ladder, in a place that exists,
    with a blade at the top that is never sold."""
    from flatline.content import pit, weapons, districts as dist_content
    rungs = sorted(f.rung for f in pit.FIGHTERS)
    rep.check(rungs == list(range(1, len(rungs) + 1)), 'pit',
              f'rungs {rungs} are not 1..n')
    tiers = [pit.BY_RUNG[r].tier for r in rungs]
    rep.check(tiers == sorted(tiers), 'pit', 'tiers do not climb the wall')
    purses = [pit.BY_RUNG[r].purse for r in rungs]
    rep.check(purses == sorted(purses) and purses[0] > 0, 'pit',
              'purses do not climb the wall')
    for f in pit.FIGHTERS:
        where = f'pit/{f.key}'
        rep.check(bool(f.intro and f.beaten and f.epithet and f.style), where,
                  'is not written')
        rep.check(1 <= f.tier <= 4 and f.pool_bonus >= 0 and f.hit_bonus >= 0,
                  where, 'numbers out of band')
    rep.check(pit.HOUSE in factions.BY_KEY, 'pit', f'house {pit.HOUSE!r} is no faction')
    rep.check(pit.WHERE in dist_content.BY_KEY
              and pit.AT in dist_content.BY_KEY[pit.WHERE].services, 'pit',
              'the pit is somewhere that does not exist')
    relic = weapons.BY_KEY.get(pit.RELIC)
    rep.check(relic is not None and relic.unique and relic not in weapons.carriable(),
              'pit', 'the blade at the top is sold, or missing')
    rep.check(0 < pit.HOUSE_CUT < 0.5 and pit.MAX_STAKE > 0 and pit.RANK_DECAY_SHIFTS > 0,
              'pit', 'house numbers out of band')


def check_weapons(rep: Report) -> None:
    """The street's shelf (D128, D130). One axis that matters, and every
    rider read by the engine."""
    from flatline.content import weapons
    seen_loud = seen_quiet = False
    for w in weapons.WEAPONS:
        where = f'weapons/{w.key}'
        rep.check(w.damage > 0, where, 'does no damage')
        rep.check(w.price >= 0, where, 'negative price')
        rep.check(1 <= w.tier <= 3, where, f'tier {w.tier} out of range')
        rep.check(bool(w.blurb and w.drawback), where,
                  'has no blurb or no stated drawback (D11)')
        rep.check(not w.name[:3] in ('A ', 'An ') and not w.name.startswith('A '),
                  where, 'name carries an article: it reads after "with the"')
        if w.rider:
            rep.check(w.rider in weapons.RIDERS, where,
                      f'unknown rider {w.rider!r}')
        seen_loud = seen_loud or w.loud
        seen_quiet = seen_quiet or not w.loud
    rep.check(seen_loud and seen_quiet, 'weapons',
              'the shelf needs both a loud and a quiet option')
    # A fitted weapon (price 0) must be granted by chrome that exists, and
    # must never reach the fence.
    for ware_key, weapon_key in weapons.CHROME_WEAPONS.items():
        rep.check(ware_key in cyberware.BY_KEY, 'weapons',
                  f'{weapon_key} is granted by {ware_key}, which is not chrome')
        rep.check(weapon_key in weapons.BY_KEY, 'weapons',
                  f'chrome grants {weapon_key}, which is not a weapon')
        rep.check(weapons.BY_KEY[weapon_key] not in weapons.carriable(),
                  'weapons', f'{weapon_key} is fitted but on the fence shelf')


def check_street(rep: Report) -> None:
    """D65: every encounter is answerable, every answer is a real check or a
    real price, only the top tier can kill and only after a warning, and
    every technique key the skills declare has a reader in the engine."""
    from flatline.content import street as street_content
    from flatline.world import story as story_mod
    seen: set[str] = set()
    for e in street_content.ENCOUNTERS:
        where = f'street/{e.key}'
        rep.check(e.key not in seen, where, 'duplicate key')
        seen.add(e.key)
        rep.check(1 <= e.tier <= 4, where, f'tier {e.tier}')
        rep.check(e.who in ('faction', 'street'), where, f'who {e.who!r}')
        rep.check(e.tone in events.TONES, where, f'tone {e.tone!r}')
        rep.check('{district}' in e.setup or bool(e.districts), where,
                  'setup never names the district, and it can happen in any '
                  'of them')
        if e.who == 'faction':
            rep.check('{fac}' in e.setup, where, 'a faction encounter never '
                                                 'names the faction')
        rep.check(len(e.options) >= 2, where, 'fewer than two answers')
        keys = [o.key for o in e.options]
        rep.check(len(keys) == len(set(keys)), where, 'duplicate answers')
        for o in e.options:
            ow = f'{where}/{o.key}'
            rep.check(o.check in street_content.CHECKS or o.check in ('pay', 'none'),
                      ow, f'check {o.check!r} is not a thing anybody can roll')
            rep.check(bool(o.label), ow, 'has no label')
            if o.check not in ('pay', 'none'):
                rep.check(bool(o.win.text) and bool(o.lose.text), ow,
                          'a checked answer needs both outcomes written')
            for out in (o.win, o.lose):
                lo, hi = out.hurt
                rep.check(lo <= hi, ow, f'hurt range {out.hurt} is backwards')
                rep.check(0.0 <= out.credits <= 1.0, ow,
                          f'credits share {out.credits} out of range')
                if out.lethal:
                    rep.check(e.tier == 4, ow,
                              'can kill below the top of the ladder')
                    rep.check(out.hurt[0] >= 8, ow,
                              'lethal and does not hit hard enough to be')
        if e.tier == 4:
            rep.check(any(o.lose.lethal for o in e.options), where,
                      'the kind that kills cannot')
            rep.check(all(o.check != 'pay' for o in e.options), where,
                      'the kind that kills takes money, which is a lower rung')
        for hour in e.phases:
            rep.check(hour in shifts.PHASE_KEYS, where, f'hour {hour!r}')
        for key in e.districts:
            rep.check(key in districts.BY_KEY, where,
                      f'happens in {key!r}, which is not a district')
        for rule in e.requires:
            inner = rule[4:] if rule.startswith('not:') else rule
            kind = inner.split(':')[0]
            rep.check(':' not in inner or kind in thread_content.CONDITIONS
                      or kind in ('met', 'ran'), where,
                      f'{rule!r} is not a rule anything can evaluate')
    tiers = {e.tier for e in street_content.ENCOUNTERS}
    rep.check(tiers == {1, 2, 3, 4}, 'street',
              f'the ladder has rungs {sorted(tiers)}; wanted all four')
    for who in ('faction', 'street'):
        rep.check(any(e.who == who and e.tier >= 3 for e in street_content.ENCOUNTERS),
                  'street', f'{who} trouble never gets serious')
    # Every technique has a reader.
    source = _wide_source()
    for sk in skills.SKILLS:
        for t in sk.techniques:
            rep.check(f"has_technique('{t.key}')" in source, f'skills/{sk.key}/{t.key}',
                      'technique is declared and nothing reads has_technique '
                      'for it')



# --------------------------------------------------------------------------
# relics (D63 e)
# --------------------------------------------------------------------------


def check_relics(rep: Report) -> None:
    """D63 e: a thing there is one of has a history, a way to get it, and no
    price tag anywhere.

    Every `unique` item in any catalogue is given by exactly one route (a
    `Find` at a place, or a `Choice.gives`), has a lore paragraph, and never
    appears in a market roll. Every find names a unique item that exists,
    an hour that exists, rules the story can evaluate, a moment and a rumour
    in the right tone, and lives in a place. `found:<item>` flags are read
    only through the rumour's `not:` rule, which is what makes the rumour
    stop."""
    from flatline.content import drugs as drug_content
    from flatline.content import spots as spot_content
    from flatline.content import arcs as arc_content
    from flatline.world import market as market_mod

    catalogues = (('program', programs.PROGRAMS), ('ware', cyberware.WARE),
                  ('component', hardware.COMPONENTS),
                  ('drug', drug_content.DRUGS))
    uniques: dict[str, object] = {}
    for kind, table in catalogues:
        for item in table:
            if getattr(item, 'unique', False):
                uniques[item.key] = item
    rep.check(len(uniques) >= 12, 'relics',
              f'only {len(uniques)} relics in the whole city')

    given: dict[str, list[str]] = {k: [] for k in uniques}
    for f in spot_content.FINDS:
        if f.item in given:
            given[f.item].append(f'find at {spot_content.spot_of(f).key}')
    for t in thread_content.THREADS:
        for st in t.stages:
            for ch in st.choices:
                for key in ch.gives:
                    if key in given:
                        given[key].append(f'choice {t.key}.{st.key}.{ch.key}')
    for key, item in uniques.items():
        where = f'relics/{key}'
        rep.check(len(given[key]) == 1, where,
                  f'is given by {len(given[key])} routes ({given[key]}); '
                  f'a relic has exactly one')
        rep.check(len(getattr(item, 'lore', '')) >= 200, where,
                  'has no history worth the name')
        for kind, _ in catalogues:
            for k, _tier, _price in market_mod._catalogue(kind):
                rep.check(k != key, where, f'can be rolled by a {kind} market')
        for service in ('market', 'clinic', 'fence', 'fixer', 'workshop'):
            for k, _tier, _price in market_mod._catalogue('drug', service):
                rep.check(k != key, where, f'can be rolled by a {service}')

    # D65 depth: every district has something in it to find, so that
    # exploring anywhere is worth the hour it costs.
    covered = {spot_content.spot_of(f).district for f in spot_content.FINDS}
    for d in districts.DISTRICTS:
        rep.check(d.key in covered, f'relics/{d.key}',
                  'nothing in this district can be found')
    phases = set(shifts.PHASE_KEYS)
    for f in spot_content.FINDS:
        where = f'spots/finds/{f.item}'
        rep.check(f.item in uniques, where,
                  f'{f.item!r} is not a unique item in any catalogue')
        for hour in f.hours:
            rep.check(hour in phases, where, f'hour {hour!r} is not a phase')
        rep.check(len(f.text) >= 80, where, 'the moment is too short to land')
        rep.check(bool(f.rumour), where, 'has no rumour, so nothing leads here')
        rep.check(f.tone in events.TONES, where, f'tone {f.tone!r}')
        rep.check(bool(f.requires), where,
                  'has no conditions: it would be found on the first visit')
    # The flags are read only through the rumours' `not:` rules.
    for e in events.EVENTS:
        for rule in tuple(e.requires) + tuple(e.any_of):
            if 'found:' in rule:
                rep.check(rule.startswith('not:found:'), f'events/{e.key}',
                          f'reads {rule!r}; a found flag is only ever a reason '
                          f'for a rumour to stop')
    rep.check(bool(arc_content.PARTNER_GIFTS), 'relics',
              'nobody you work with ever gives you anything')



# --------------------------------------------------------------------------
# every number reads (D63)
# --------------------------------------------------------------------------

_WIDE_SOURCE: str = ''


def _wide_source() -> str:
    """Everything that is not content: the run layer, the commands, the
    world, the model, and the session. The recurring bug in this project is
    content declaring a number the engine never reads; this is the haystack
    the reader has to be found in."""
    global _WIDE_SOURCE
    if not _WIDE_SOURCE:
        import pathlib
        paths = []
        for folder in ('flatline/run', 'flatline/commands', 'flatline/world',
                       'flatline/model'):
            paths += sorted(pathlib.Path(folder).glob('*.py'))
        paths += [pathlib.Path('flatline/session.py'),
                  pathlib.Path('flatline/shell.py'),
                  pathlib.Path('flatline/script.py')]
        _WIDE_SOURCE = '\n'.join(p.read_text(encoding='utf-8')
                                 for p in paths if p.exists())
    return _WIDE_SOURCE


def check_reads(rep: Report) -> None:
    """D63: a modifier key or a rider that nothing outside content reads is a
    lie with a number on it. `tempo` shipped on the sheet, on three implants,
    two traits and a drug, and was consumed by nothing; `evade_bonus` was
    sold eleven times. Every key in the effects vocabulary and every rider
    string any catalogue can set must appear, quoted, somewhere that is not
    content. Attribute and skill keys are read generically by `attr()` and
    `skill()` and are exempt."""
    from flatline.content import attributes as attr_content
    from flatline.content import drugs, skills as skill_content
    from flatline.content import traits as trait_content
    source = _wide_source()
    generic = set(attr_content.ATTR_KEYS)
    for key in fx.ALL:
        if key in generic or key.startswith('skill_'):
            continue
        rep.check(f"'{key}'" in source, 'reads',
                  f'effect key {key!r} is declared and nothing outside '
                  f'content reads it')
    riders: set[str] = set()
    riders |= set(cyberware.RIDERS)
    riders |= set(trait_content.RIDERS)
    riders |= set(icons.RIDERS)
    riders |= set(origins.RIDERS)
    riders |= {d.rider for d in drugs.DRUGS if d.rider}
    riders |= set(programs.RIDERS)
    from flatline.content import weapons as _weapons
    riders |= set(_weapons.RIDERS)
    for rider in sorted(riders):
        rep.check(f"'{rider}'" in source, 'reads',
                  f'rider {rider!r} is declared and nothing outside content '
                  f'reads it')
    # The skills-per-attribute rule the attributes docstring promises: no
    # attribute may govern fewer than two skills, or the sheet has a number
    # that only one technique ever asks about.
    governed: dict[str, int] = {k: 0 for k in attr_content.ATTR_KEYS}
    for sk in skill_content.SKILLS:
        governed[sk.attr] = governed.get(sk.attr, 0) + 1
    for attr, n in governed.items():
        rep.check(n >= 2, 'reads', f'{attr} governs only {n} skill(s)')


def catalogue() -> list[tuple[int, str]]:
    """Every count the README states that is derivable from a module, as
    (value, the exact fragment it must appear in). The single source of the
    numbers: `tools/counts.py` prints them and `check_readme` holds the
    README to them, so a count can never drift again without the build
    saying so (D146). The one number not derivable in a line, "151 things to
    see in the street", is deliberately not here.
    """
    from flatline.content import (skills as S, traits as TR, origins as OR,
        icons as IC, cyberware as CW, weapons as WP, programs as PR,
        hardware as HW, drugs as DR, ice as IS, factions as FA, rivals as RV,
        events as EV, appearance as AP, manual as MA, record as RC,
        ambitions as AM, pit as PT, districts as DI, threads as TH,
        npcs as NP, rice as RI)
    from flatline.session import REGISTRY
    techniques = sum(len(getattr(s, 'techniques', ())) for s in S.SKILLS)
    scenes = sum(len(t.stages) for t in TH.THREADS)
    decisions = sum(len(st.choices) for t in TH.THREADS for st in t.stages)
    quarters = sum(len(getattr(d, 'quarters', ())) for d in DI.DISTRICTS)
    topics = sum(len(n.topics) for n in NP.NPCS)
    uniq = (sum(1 for w in CW.WARE if getattr(w, 'unique', False))
            + sum(1 for p in PR.PROGRAMS if getattr(p, 'unique', False))
            + sum(1 for w in WP.WEAPONS if getattr(w, 'unique', False))
            + sum(1 for c in HW.COMPONENTS if getattr(c, 'unique', False))
            + sum(1 for d in DR.DRUGS if getattr(d, 'unique', False)))
    axes = len({c.kind for c in RI.COSMETICS})
    try:
        commands = len({c.name for c in REGISTRY.all()})
    except Exception:
        commands = len(REGISTRY.commands)
    return [
        (len(S.SKILLS), 'skills with'),
        (techniques, 'techniques'),
        (len(TR.TRAITS), 'traits'),
        (len(OR.ORIGINS), 'origins'),
        (len(IC.ICONS), 'icons'),
        (len(CW.WARE), 'implants'),
        (len(WP.WEAPONS), 'weapons'),
        (len(PR.PROGRAMS), 'programs'),
        (len(HW.COMPONENTS), 'deck components'),
        (uniq, 'of all of those one of a kind'),
        (len(IS.ICE), 'countermeasures'),
        (len(FA.FACTIONS), 'factions'),
        (len(RV.RIVALS), 'rival runners'),
        (len(NP.NPCS), 'named characters'),
        (len(TH.THREADS), 'storylines'),
        (scenes, 'scenes'),
        (decisions, 'decisions'),
        (len(AP.FEATURES), 'appearance features'),
        (quarters, 'quarters in all'),
        (len(EV.EVENTS), 'ambient city events'),
        (len(MA.TOPICS) if hasattr(MA, 'TOPICS') else len(MA.BY_KEY), 'manual topics'),
        (len(DR.DRUGS), 'drugs'),
        (commands, 'commands'),
        (axes, 'axes'),
    ]


def check_readme(rep: Report) -> None:
    readme = pathlib.Path('README.md')
    if not readme.exists():
        return
    text = readme.read_text()
    for value, fragment in catalogue():
        needle = f'{value:,} {fragment}' if value >= 1000 else f'{value} {fragment}'
        rep.check(needle in text, 'README.md',
                  f'says something other than "{needle}" (the count moved; '
                  f'run `python3 tools/counts.py --write` or fix the wording)')

def check_pets(rep: Report) -> None:
    """Pets (D152): a spread of animals, each with the care profile and the
    lines the keeping of it needs, and none of it reaching the work."""
    from flatline.content import pets as pet_content
    rep.check(len(pet_content.ANIMALS) >= 5, 'pets', 'fewer than five animals')
    tones = {a.tone for a in pet_content.ANIMALS}
    rep.check('unsettling' in tones or 'grim' in tones, 'pets',
              'nothing here is a bad idea you love anyway')
    rep.check(len(tones) >= 3, 'pets', 'the animals are all one register')
    seen = set()
    for a in pet_content.ANIMALS:
        where = f'pets/{a.key}'
        rep.check(a.key not in seen, where, 'duplicate key')
        seen.add(a.key)
        rep.check(a.tone in pet_content.TONES, where, f'tone {a.tone!r}')
        rep.check(bool(a.name and a.species and a.blurb), where, 'is thin')
        rep.check(a.price >= 0, where, 'costs less than nothing')
        for stat in ('food', 'water', 'play'):
            rep.check(a.decay.get(stat, 0) > 0, where,
                      f'does not lose {stat} at all')
        rep.check(bool(a.happy and a.low and a.failing), where,
                  'has no lines for how it is')
        rep.check(bool(a.kept_coda and a.lost_coda)
                  and a.kept_coda.rstrip().endswith('.'), where,
                  'has no ending')
    # The animal (D152) is never read by a run, a fight or the street: it
    # is pure meat-side, and nothing about the work can see it.
    for mod in ('run/session.py', 'commands/run.py', 'world/fight.py',
                'world/street.py'):
        src = pathlib.Path('flatline/' + mod).read_text(encoding='utf-8')
        rep.check('city.pet' not in src, f'pets/{mod}',
                  'the work reads the animal: it must not')
    # The familiar (D153) does ride the run, but only to talk: its one method
    # reads the deck for a line and touches nothing a check can see. Held by
    # reading the method's own body, so a familiar that ever moved a number
    # would fail the build.
    run_src = pathlib.Path('flatline/run/session.py').read_text(encoding='utf-8')
    rep.check('def familiar_say' in run_src, 'pets/familiar',
              'the familiar has lost its one method')
    body = run_src.split('def familiar_say', 1)[1].split('\n    def ', 1)[0]
    for forbidden in ('self.trace', 'self.noise', 'self.alert =', 'escalate',
                      'check(', 'return True', 'return False'):
        rep.check(forbidden not in body, 'pets/familiar',
                  f'the familiar\'s voice touches {forbidden!r}: it must only '
                  f'ever print')
    rep.check('self.console' in body, 'pets/familiar',
              'the familiar does not even speak')
    # And the familiars themselves: a spread of tones and a line for every
    # beat of a run.
    rep.check(len(pet_content.FAMILIARS) >= 4, 'pets', 'too few familiars')
    fam_tones = {f.tone for f in pet_content.FAMILIARS}
    rep.check(len(fam_tones) >= 3
              and ('unsettling' in fam_tones or 'grim' in fam_tones),
              'pets/familiar', 'the familiars are all one register')
    beats = ('connect', 'amber', 'red', 'lockdown', 'blackice', 'clean',
             'burned', 'idle', 'dormant')
    for f in pet_content.FAMILIARS:
        where = f'pets/familiar/{f.key}'
        rep.check(f.memory >= 1, where, 'costs no memory: not a real choice')
        rep.check(f.tone in pet_content.TONES, where, f'tone {f.tone!r}')
        for beat in beats:
            lines = f.says.get(beat)
            rep.check(bool(lines) and all(l.rstrip().endswith(('.', '"'))
                                          for l in lines), where,
                      f'has nothing to say on {beat!r}')

CHECKS = (
    check_effects, check_cyberware, check_programs, check_hardware,
    check_guide, check_consequences, check_spine, check_city_texture,
    check_conditions, check_portraits,
    check_icons, check_dissonance, check_cyberspace, check_rivals, check_debt,
    check_origins, check_appearance, check_events, check_rice, check_shifts, check_district_mood, check_dead_fields, check_skills, check_factions, check_districts,
    check_ice, check_nodes, check_contracts, check_drugs, check_lenders, check_games, check_offers, check_legacy, check_bonds, check_safehouses, check_crew, check_mods, check_commands,
    check_traits, check_scripting, check_npcs, check_threads,
    check_manual, check_tutorial, check_theme, check_palette_separation, check_markup, check_balance,
    check_heat, check_guile, check_roster, check_reads, check_relics, check_street,
    check_weapons, check_pit, check_feed, check_record, check_readme,
    check_pets,
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
