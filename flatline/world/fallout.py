"""The D6 failure ladder, above the run layer.

The run layer knows how to sever a connection and how to kill you. Everything
between those two is a *city* consequence, and it lives here: bounties, being
picked up in a district somebody owns, chrome coming out of you in a room you
did not choose, and an identity that has become a liability.

**The design rule is that no rung is a game over.** Losing a deck component,
an implant, or a name is expensive and it changes what you can do next, which
is the point. A player who has been caught twice is playing a different, worse,
more interesting character than the one they built, and that is a story rather
than a punishment.

The one thing that ends a character is black ICE, and that is handled in the
run layer where the player can see it coming.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..content import cyberware, districts, factions, hardware
from ..content import shifts
from ..rng import Stream

#: Heat at which a faction stops merely noticing and starts paying for names.
BOUNTY_THRESHOLD = 55
#: What a fresh bounty is worth, before it grows.
BOUNTY_BASE = 20
#: Per-shift growth while the heat that caused it stays high.
BOUNTY_GROWTH = 2.0
#: Danger score above which arriving somewhere risks an incident.
INCIDENT_FLOOR = 45


@dataclass(frozen=True, slots=True)
class Incident:
    """One thing that happened to you in a street somewhere."""

    kind: str
    text: str
    #: Player-facing consequence, already applied by `pick_up`.
    detail: str = ''


#: What being picked up costs, weighted. The ladder from D6, in order of how
#: much it hurts, and none of them end the game.
OUTCOMES = {
    'shakedown': 3.0,
    'deck': 2.0,
    'chrome': 1.2,
    'beating': 2.2,
    'burn': 1.4,
}


def bounty_check(alias, city, rng: Stream) -> list[str]:
    """Turn sustained heat into standing bounties. Called on the shift tick."""
    told: list[str] = []
    for key in factions.FACTION_KEYS:
        heat = alias.attention(key)
        current = city.bounties.get(key, 0)
        if heat >= BOUNTY_THRESHOLD:
            if not current:
                city.bounties[key] = BOUNTY_BASE
                fac = factions.BY_KEY[key]
                told.append(
                    f'[err]{fac.short} have stopped looking for what happened '
                    f'and started paying for who did it.[/] [dim]There is a '
                    f'number attached to your name now.[/]')
            else:
                city.bounties[key] = min(100, current + BOUNTY_GROWTH)
        elif current:
            # Bounties decay slower than the heat that created them: getting
            # quiet does not immediately un-print the poster.
            city.bounties[key] = max(0, current - 1.0)
            if city.bounties[key] <= 0:
                del city.bounties[key]
                told.append(f'[dim]{factions.BY_KEY[key].short} have taken '
                            f'your name off the board. Nobody is being paid '
                            f'to find you today.[/]')
    return told


#: Being noticed without being picked up. The rung below the ladder (D53):
#: the street letting you know it has your name, at a cost of nothing but
#: the noticing itself, which is a cost. `{district}` and `{fac}` are filled.
CLOSE_CALLS: tuple[str, ...] = (
    'Somebody in {fac}\'s colours steps off the kerb in {district} as you '
    'pass and walks beside you for eleven paces without saying anything, and '
    'then does not, and you do not look round to find out where they went.',
    'A handset comes up across the street in {district}, pointed, and goes '
    'down again, and the person holding it has the expression of somebody '
    'who has just been told the price of something.',
    'Two people in a doorway in {district} stop talking as you pass and '
    'start again when you have passed, and what they start again with is a '
    'question, and you are fairly sure of the subject.',
    'Somebody says your name in {district}. Not to you. The right name, the '
    'one on the posters, said the way you say a thing to check how it sounds '
    'out loud.',
    'A shutter comes down in {district} as you reach it, not fast, and the '
    'face behind it belongs to somebody who knows {fac} pay for faces and '
    'has just decided how much yours is worth, and decided it is not worth '
    'the trouble today.',
    'In {district} somebody from {fac} looks at you for exactly as long as '
    'it takes to be sure, and then looks at the time, and then writes '
    'something down, and the writing down is the part that follows you out '
    'of the district.',
)

#: Attention a close call adds. Small: they saw you, and now there is one
#: more person who can say so.
CLOSE_CALL_HEAT = 3


def close_call(rng: Stream, alias, city, faction: str,
               danger: int) -> Incident | None:
    """Maybe the street lets you know. None when it keeps it to itself.

    Fires in the band below an incident, on a chance that climbs with the
    danger, so that a district you are merely watched in is a district where
    things happen rather than a warning line. It costs a little heat, which
    is the honest cost of having been seen.
    """
    if not rng.chance(min(0.5, danger / 160.0)):
        return None
    fac = factions.BY_KEY[faction]
    text = rng.pick(CLOSE_CALLS).format(district=city.district.name,
                                        fac=fac.short)
    alias.add_heat(faction, CLOSE_CALL_HEAT)
    return Incident('close', text,
                    f'{fac.short} attention up {CLOSE_CALL_HEAT}.')


def pick_up(rng: Stream, char, alias, city, faction: str) -> Incident:
    """You were recognised. Apply one rung of the ladder and describe it.

    Never fatal, never a total loss, always specific. The player should be able
    to say afterwards exactly what it cost and what they will do differently.
    """
    fac = factions.BY_KEY[faction]
    district = city.district
    kind = rng.weighted(dict(OUTCOMES))

    if kind == 'shakedown':
        take = min(char.credits, max(200, int(char.credits * rng.spread(35, 0.3) / 100)))
        char.credits -= take
        return Incident(
            'shakedown',
            f'Two of {fac.short}\'s people are waiting by the stairwell in '
            f'{district.name} and they already know your face. Nobody draws '
            f'anything. It does not take that long.',
            f'[credit]{take:,}c[/] gone.')

    if kind == 'beating':
        damage = rng.int(3, 8)
        char.hurt = min(char.integrity_max - 1, char.hurt + damage)
        alias.add_heat(faction, -8)
        # Filing leaves a record on you as well as in their system.
        char.mark('bounty_mark')
        return Incident(
            'beating',
            f'They put you on the ground behind a service door in '
            f'{district.name} and take their time about it. It is not an '
            f'interrogation. It is filing.',
            f'Integrity down {damage}. [dim]{fac.short} feel slightly better '
            f'about you, in the way that people do.[/]')

    if kind == 'deck':
        working = [s for s in hardware.SLOTS if char.deck.working(s)]
        if not working:
            return pick_up(rng, char, alias, city, faction)
        slot = rng.pick(working)
        level = char.deck.hurt(slot, rng.int(1, 2))
        comp = char.deck.component(slot)
        name = comp.name if comp else slot
        return Incident(
            'deck',
            f'They take the deck off you in the street and hand it back '
            f'having done something specific to it. The message is the '
            f'point.',
            f'{name} damaged [dim]({level}/3)[/]. '
            f'[dim]Repairs: '
            f'{char.deck.repair_cost(char.mult("repair_mult")):,}c[/]')

    if kind == 'chrome':
        fitted = [k for k in char.installed if k in cyberware.BY_KEY]
        if not fitted:
            return pick_up(rng, char, alias, city, faction)
        key = rng.pick(fitted)
        ware = cyberware.BY_KEY[key]
        char.uninstall(key)
        return Incident(
            'chrome',
            f'You wake up in a room in {district.name} that smells of '
            f'disinfectant and someone else\'s cigarettes, with a dressing '
            f'taped over a socket that is now empty. The work was competent. '
            f'That is the part that stays with you.',
            f'[err]{ware.name} is gone.[/] [dim]The Dissonance is not.[/]')

    # burn: the name itself is the casualty
    alias.add_heat(faction, 25)
    return Incident(
        'burn',
        f'Somebody photographs you crossing {district.name} and sells it to '
        f'{fac.short} inside the hour. The name is finished. Everything it '
        f'was worth to anybody is finished with it.',
        f'[err]{alias.name} is burned in everything but paperwork.[/] '
        f'[dim]`burn --confirm` when you can afford a new one.[/]')


def arrival_risk(rng: Stream, alias, city, target: str,
                 flags=()) -> tuple[int, str]:
    """Whether arriving somewhere goes badly, and who made it go badly.

    Returns (score, faction). The caller decides what to do with it, because
    travel and legwork want the same check with different thresholds.
    `flags` is the story's flag set: a decision about a faction changes how
    its streets treat you (D51, `story.STREET_RIDERS`).
    """
    from . import story as story_mod
    district = districts.BY_KEY[target]
    watchers = (district.controller, *district.presence)
    # How many people are on the street to be one of the ones who recognises
    # you. The clock is not decoration: crossing a district that wants you is
    # a different proposition at three in the afternoon and at three at night.
    when = shifts.phase(city.phase).danger
    worst, who = 0, ''
    for key in watchers:
        score = alias.attention(key) + int(city.bounties.get(key, 0)) * 1.5
        score = int(score * (0.5 + district.security / 100.0) * when
                    * story_mod.street_rider(flags, key))
        if score > worst:
            worst, who = score, key
    return worst, who
