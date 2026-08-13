"""Chrome, per D11. Nothing here is a pure upgrade.

**The rule this file is written under:** if a piece of cyberware cannot be
given an honest drawback, it does not ship. Not a price, not a Bandwidth cost,
an actual mechanical downside that will make a player hesitate. A "+1 Logic
implant" is not a decision and is not in this file.

Two costs on every piece:

- **Bandwidth** is hard capacity. You have 8 + Grit and that is that.
- **Dissonance** is the long arc. It never goes down on its own. High
  Dissonance is genuinely good in the net and genuinely bad in the city, so a
  full-chrome build is a legitimate playstyle rather than a punishment track.

Slots are per location and are tight on purpose. The interesting question is
never "can I afford this", it is "what am I taking out to fit it".
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: location -> how many pieces fit there.
SLOTS: dict[str, int] = {
    'neural': 2,     # the deck interface itself, and what sits beside it
    'ocular': 1,     # you get one set of eyes
    'cortex': 2,     # processing, memory, the parts that change how you think
    'spinal': 1,     # bandwidth trunk, the expensive one
    'limb': 2,       # hands and arms, physical interface work
    'subdermal': 2,  # under the skin: power, cooling, storage
}

LOCATIONS: tuple[str, ...] = tuple(SLOTS)

#: Dissonance thresholds and what they do. Read by the city layer for prices
#: and social options, and by the run layer for composure.
DISSONANCE_BANDS: tuple[tuple[int, str, str], ...] = (
    (0, 'Grounded', 'You still think of the net as somewhere you go.'),
    (25, 'Drifting', 'The transitions have started to feel arbitrary.'),
    (50, 'Submerged',
     'Meat-side conversation has acquired a lag you can measure. '
     'Fixers notice. Clinics charge more.'),
    (75, 'Dissolved',
     'You are a process that occasionally runs on a body. Something in the '
     'net answers to you now, and the city has stopped pretending otherwise.'),
)


@dataclass(frozen=True, slots=True)
class Ware:
    key: str
    name: str
    maker: str
    location: str
    bandwidth: int
    dissonance: int
    price: int
    tier: int                      # 1 street, 2 professional, 3 restricted
    blurb: str
    effects: dict = field(default_factory=dict)
    #: The honest downside, in the fiction.
    drawback: str = ''
    #: The honest downside, in numbers. Merged with `effects` at fit time; kept
    #: separate so the shop can print the two halves under different headings
    #: and a player can never say they were not told.
    penalty: dict = field(default_factory=dict)
    #: Free-text mechanical rider the engine special-cases by key.
    rider: str = ''


WARE: tuple[Ware, ...] = (
    # -- neural ------------------------------------------------------------
    Ware('corp_neural_shunt', 'Kagawa CX-4 Neural Shunt', 'Kagawa Vertical',
         'neural', 2, 8, 3200, 2,
         'Standard corporate interface. Clean, documented, and logged by '
         'design, because it was never built for people doing this.',
         effects={'crack_bonus': 2, 'tick_mult': 0.92},
         drawback='It phones home. The telemetry endpoint is dead, but the '
                  'attempt itself is a signature that corporate ICE recognises.',
         penalty={'noise_mult': 1.15}),
    Ware('salvage_reflex_loop', 'Salvaged Reflex Loop', 'unbranded',
         'neural', 1, 5, 400, 1,
         'Pulled out of something and put into you by somebody who was mostly '
         'sure which way round it went.',
         effects={'reflex': 1},
         drawback='It misfires under load. Any tick in which you take three or '
                  'more actions has a chance of dropping one of them.',
         penalty={},
         rider='misfire'),
    Ware('deep_jack', 'Sendai Deepjack', 'Sendai Interface',
         'neural', 3, 14, 9800, 3,
         'Direct cortical coupling. No interface layer, no translation, no '
         'buffer between what you intend and what the deck does.',
         effects={'tempo': 1, 'tick_mult': 0.85},
         drawback='Nothing stands between you and feedback either. All damage '
                  'from countermeasures is dealt to Integrity, never to the deck.',
         penalty={'ice_dr': 1.4}),

    # -- ocular ------------------------------------------------------------
    Ware('threat_overlay', 'Nightwatch Threat Overlay', 'Nightwatch surplus',
         'ocular', 2, 7, 4100, 2,
         'Issue optics from the intrusion response desk. Paints countermeasures '
         'in the colours the manual uses.',
         effects={'tell_lead': 1, 'evade_bonus': 2},
         drawback='It is issue hardware with an issue serial. Nightwatch '
                  'networks read it as one of their own, right up until they '
                  'check the number against a list of returned equipment.',
         penalty={},
         rider='nightwatch_serial'),
    Ware('ocular_suite', 'Aoyama Full Ocular Suite', 'Aoyama Biotech',
         'ocular', 3, 12, 7400, 2,
         'Complete replacement. Spectral range well past useful, latency near '
         'zero, and a rendering layer that treats the net as a place with '
         'depth rather than a log.',
         effects={'scan_depth': 1, 'logic': 1, 'evade_bonus': 1},
         drawback='Aoyama retains a diagnostic channel. It is documented, it is '
                  'legal, and it means Aoyama always knows roughly where you are.',
         penalty={'heat_mult': 1.2}),

    # -- cortex ------------------------------------------------------------
    Ware('cortex_annex', 'Cortex Annex', 'Freeport Collective',
         'cortex', 2, 9, 5200, 2,
         'Additional working memory that is not on the deck and therefore not '
         'on the network. Open hardware, community audited, no telemetry.',
         effects={'focus': 2, 'crypto_bonus': 2},
         drawback='Cortical memory is not neutral storage. What you hold there '
                  'you keep, including the parts of a run you would rather not.',
         penalty={'composure': -2}),
    Ware('reflex_governor', 'Reflex Governor', 'Sendai Interface',
         'cortex', 2, 11, 6600, 3,
         'Removes the hesitation between deciding and acting. It does this by '
         'removing the hesitation.',
         effects={'tempo': 1, 'evade_bonus': 2},
         drawback='It also removes the pause in which you would have '
                  'reconsidered. Pretexts and any check that rewards patience '
                  'suffer for it.',
         penalty={'pretext_bonus': -3}),
    Ware('threadpuller', 'Kohler-Reyes Threadpuller', 'Kohler-Reyes',
         'cortex', 3, 13, 8900, 3,
         'Run two programs against one target at once. The classic '
         'multithreading implant and still the loudest thing on the market.',
         effects={},
         drawback='Both threads announce themselves. Everything you do through '
                  'it is twice as loud as doing it once would have been.',
         penalty={'noise_mult': 2.0},
         rider='dual_thread'),

    # -- spinal ------------------------------------------------------------
    Ware('spinal_bus', 'Spinal Trunk Bus', 'Sendai Interface',
         'spinal', 4, 15, 11500, 3,
         'The big one. Replaces the spinal interface wholesale with a trunk '
         'rated for traffic no human nervous system was specified for.',
         effects={'bandwidth': 4, 'memory': 2, 'tick_mult': 0.9},
         drawback='Your thermal signature is now that of a small appliance. '
                  'Everything you do is easier to find.',
         penalty={'trace_mult': 1.25}),
    Ware('dampener_spine', 'Aoyama Dampener Spine', 'Aoyama Biotech',
         'spinal', 3, 6, 8200, 2,
         'Medical-grade signal dampening, marketed to people with tremors and '
         'bought almost exclusively by people with warrants.',
         effects={'noise_mult': 0.7, 'composure': 3},
         drawback='Dampening is not selective. Everything you do arrives at '
                  'the deck slightly late.',
         penalty={'tick_mult': 1.15}),

    # -- limb --------------------------------------------------------------
    Ware('interface_hands', 'Interface Hands', 'Kohler-Reyes',
         'limb', 2, 8, 4600, 2,
         'Fingertip contact ports and a haptic layer fast enough that physical '
         'taps stop being a specialist operation.',
         effects={'skill_hardware': 1, 'legwork_bonus': 2},
         drawback='They are obviously not hands. Every social interaction in '
                  'the city begins with somebody deciding what you are.',
         penalty={'pretext_bonus': -2, 'price_mult': 1.08}),
    Ware('deadman_grip', 'Deadman Grip', 'unbranded',
         'limb', 1, 4, 1900, 1,
         'A relay wired into the arm that cuts the connection if your pulse '
         'does something it should not.',
         effects={},
         drawback='It is not clever and it does not ask. A hard enough spike '
                  'of stress ends the run whether or not you wanted it to.',
         penalty={},
         rider='deadman'),
    Ware('surgical_arm', 'Surgical Arm', 'Aoyama Biotech',
         'limb', 3, 10, 7100, 2,
         'Sub-millimetre control, originally for microsurgery, repurposed for '
         'the kind of hardware work that has to be done quietly and once.',
         effects={'skill_forensics': 1, 'residue_mult': 0.75},
         drawback='The calibration is delicate and the arm knows it. Combat '
                  'feedback throws it out for the rest of the run.',
         penalty={'ice_damage': -2}),

    # -- subdermal ---------------------------------------------------------
    Ware('coolant_mesh', 'Subdermal Coolant Mesh', 'Kohler-Reyes',
         'subdermal', 2, 5, 3400, 2,
         'A closed loop under the skin that takes heat off the deck through '
         'you. Uncomfortable, effective, entirely legal.',
         effects={'heat_cap': 4},
         drawback='You are the heatsink. Sustained overclocking costs Integrity '
                  'directly, and it accumulates across a run.',
         penalty={},
         rider='thermal_load'),
    Ware('ghost_layer', 'Ghost Layer', 'Freeport Collective',
         'subdermal', 2, 9, 6300, 3,
         'Signal-absorbing dermal weave. Community design, printed in six '
         'places, illegal in four districts.',
         effects={'trace_mult': 0.78},
         drawback='It absorbs your own diagnostics too. You cannot read your '
                  'exact trace level, only a coarse band.',
         penalty={},
         rider='blind_trace'),
    Ware('social_lattice', 'Social Lattice', 'Kagawa Vertical',
         'subdermal', 1, 6, 2800, 1,
         'Facial micro-actuators and a voice layer. Sales issue. It makes you '
         'likeable in a way that is measurable and therefore slightly awful.',
         effects={'guile': 1, 'pretext_bonus': 2, 'price_mult': 0.94},
         drawback='It runs whether or not you want it to, and people who know '
                  'what it is find its output insulting.',
         penalty={'rep_mult': 0.9}),
    Ware('adrenal_governor', 'Adrenal Governor', 'Aoyama Biotech',
         'subdermal', 2, 7, 4900, 2,
         'Chemical regulation of the panic response, tuned for people whose '
         'work involves being calm at the wrong moments.',
         effects={'nerve': 1, 'composure': 4},
         drawback='Regulated adrenaline is flattened adrenaline. You do not '
                  'get the burst either, and recovery afterwards takes longer.',
         penalty={'grit': -1}),
    Ware('blacksite_stack', 'Blacksite Memory Stack', 'unbranded',
         'cortex', 2, 16, 12400, 3,
         'Nobody will tell you where these come from. It holds a run\'s worth '
         'of state outside your head and outside the deck, which means a '
         'severed connection does not cost you what you were carrying.',
         effects={'memory': 3},
         drawback='Whatever it was built for, it was not built for you. '
                  'Dissonance accrues from wearing it, not merely from '
                  'installing it: +1 every time you complete a run.',
         penalty={},
         rider='creeping_dissonance'),
)

BY_KEY: dict[str, Ware] = {w.key: w for w in WARE}
WARE_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Riders the engine implements. A rider on a piece that is not in this set is
#: a validation error, which is what stops a drawback existing only in prose.
RIDERS: frozenset[str] = frozenset({
    'misfire', 'nightwatch_serial', 'dual_thread', 'deadman', 'thermal_load',
    'blind_trace', 'creeping_dissonance',
})


def band(dissonance: int) -> tuple[int, str, str]:
    """The Dissonance band a value falls in."""
    out = DISSONANCE_BANDS[0]
    for threshold, name, text in DISSONANCE_BANDS:
        if dissonance >= threshold:
            out = (threshold, name, text)
    return out


def by_location(location: str) -> list[Ware]:
    return [w for w in WARE if w.location == location]
