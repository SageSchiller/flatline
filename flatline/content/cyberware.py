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
    #: One of a kind (D63 e). Never in a market: found somewhere, given by
    #: somebody, or handed over by a decision. `lore` is its history, shown
    #: by `inspect` and when it is found.
    unique: bool = False
    lore: str = ''


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
                  'more actions has about a one-in-three chance of dropping '
                  'one of them: the free action is spent and the tick is '
                  'charged anyway.',
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
    Ware('targeting', 'Targeting Suite', 'Militech, grey-market', 'ocular', 2, 6,
         3800, 2,
         'A reticle you did not ask for on everything you look at, and a '
         'small honest number beside it that is the distance. Made for '
         'soldiers. On the street it makes the pistol yours in a way it was '
         'not, and it makes a punch land where you meant.',
         effects={'strike_bonus': 2},
         drawback='Everything is a target now, including the people you '
                  'love. The suite does not have an off. The number is '
                  'always there.',
         penalty={'composure': -1}),
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
    Ware('pain_editor', 'Pain Editor', 'Kohler-Reyes', 'cortex', 2, 8,
         4600, 2,
         'It does not stop the damage. It stops the report. You are hit '
         'and you know it the way you know the weather, as information, '
         'and you keep doing what you were doing, which in a fight is '
         'the whole of the difference.',
         effects={},
         drawback='You do not notice you are dying. The clinic gets a lot '
                  'of people with pain editors, and they all arrive '
                  'surprised.',
         penalty={'integrity': -2},
         rider='pain_editor'),
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
         'Run two programs against one target at once: your second-best '
         'breaker rides every crack at its full rating. The classic '
         'multithreading implant and still the loudest thing on the market.',
         effects={},
         drawback='Both threads announce themselves. Everything you do through '
                  'it is twice as loud as doing it once would have been.',
         penalty={'noise_mult': 2.0},
         rider='dual_thread'),

    # -- spinal ------------------------------------------------------------
    Ware('reflex_boost', 'Reflex Booster', 'Sendai Precision', 'spinal', 3, 9,
         5400, 2,
         'A second signal path down the spine, faster than the one you '
         'were born with, that fires before you have decided. Your arm '
         'is up before the swing. The swing was the slow part.',
         effects={'guard_bonus': 2, 'reflex': 1},
         drawback='It fires before you have decided about other things '
                  'too. You flinch at doors. You drop cups. In the net it '
                  'is noise on the line.',
         penalty={'composure': -1}),
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
    Ware('muscle_graft', 'Muscle Grafts', 'Freeport, rebuilt', 'limb', 2, 6,
         3200, 2,
         'Vat fibre laid alongside the fibre you have, in the arms and '
         'across the back. You do not look different. Things you lift '
         'come up faster, and things you hit stay hit.',
         effects={'strike_damage': 2},
         drawback='It eats. You are hungry all the time, and the grafts '
                  'take what they need from the rest of you when you do '
                  'not feed them.',
         penalty={'integrity': -1}),
    Ware('gorilla', 'Hydraulic Arms', 'Militech, grey-market', 'limb', 3, 14,
         8400, 3,
         'Both arms, from the shoulder, replaced with something that was '
         'designed to open doors that did not want opening. A punch is '
         'not a punch any more. It is an event that happens to a person.',
         effects={'strike_damage': 3, 'grit': 1},
         drawback='You are careful with everything now, because '
                  'everything breaks. Deck keys, door handles, hands you '
                  'shake. And the arms are not quiet in the net.',
         penalty={'tick_mult': 1.08, 'composure': -1}),
    Ware('wolvers', 'Wolvers', 'Militech, grey-market', 'limb', 3, 12,
         7200, 3,
         'Four ceramic blades per arm, sprung into the ulna, out in a '
         'quarter-second and back in a second nobody watches. Militech built '
         'them for people who are the weapon; the grey market fits them to '
         'anybody with the bandwidth and the nerve.',
         effects={'skill_violence': 1},
         drawback='They are always there. A scanner reads them from across a '
                  'lobby, and the arm they are in is a little less an arm and '
                  'a little more a sheath, forever.',
         penalty={'heat_mult': 1.15}),
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
    Ware('adrenal', 'Adrenal Pump', 'Freeport, rebuilt', 'subdermal', 1, 4,
         1900, 1,
         'A reservoir under the collarbone and a trigger that reads the '
         'body\'s own alarm. The first second of a fight, you have already '
         'had it: the arm is up and the weight is right and the world is '
         'slow and very clear.',
         effects={},
         drawback='The second after the fight you pay for the first. Every '
                  'time. The clinics call it the crash and they are not '
                  'being poetic.',
         penalty={'composure': -1},
         rider='adrenal'),
    Ware('dermal_weave', 'Dermal Weave', 'Freeport, rebuilt', 'subdermal', 2, 5,
         2600, 1,
         'A mesh grown into the skin of the chest and forearms, dock chrome '
         'for people who get hit by things at work. It takes the edge off a '
         'blow, which on the street is the difference between a bad night and '
         'a clinic.',
         effects={'armour': 1},
         drawback='It itches in the net. Something about the mesh and the '
                  'trode field never agreed, and every run is a little less '
                  'comfortable to sit in.',
         penalty={'composure': -1}),
    Ware('plating', 'Subdermal Plating', 'Kohler-Reyes', 'subdermal', 3, 9,
         6400, 2,
         'Ceramic plates under the skin, over what matters. Made for '
         'executives who expect to be shot at and want to be able to say so '
         'at dinner. A hit that would have put you down puts you down less.',
         effects={'armour': 2, 'integrity': 2},
         drawback='You are carrying it everywhere, and everywhere includes '
                  'the chair. Everything you do at the deck takes '
                  'fractionally longer, forever.',
         penalty={'tick_mult': 1.06}),
    Ware('bonelacing', 'Bone Lacing', 'Freeport, rebuilt', 'subdermal', 2, 7,
         4100, 2,
         'The long bones threaded with a lattice that does not break the way '
         'bone breaks. You do not hit harder, you just stop being the thing '
         'in the exchange that gives first, which changes the exchange more '
         'than hitting harder would.',
         effects={'armour': 1, 'integrity': 4},
         drawback='It aches in the cold and the cold is most of the year '
                  'here, and it sets off every scanner built to find people '
                  'wearing exactly this.',
         penalty={'heat_mult': 1.08}),
    Ware('milplate', 'Milspec Trauma Plate', 'Militech, grey-market', 'subdermal', 3, 12,
         9200, 3,
         'What plating wants to be when it grows up: layered trauma plate off '
         'a Militech line, fitted by somebody who should not have it, over '
         'everything a round wants. A hit that would end most people is a '
         'hit most people notice you shrugging.',
         effects={'armour': 3, 'integrity': 3},
         drawback='You are wearing a vehicle. It is heavy everywhere and '
                  'heaviest in the chair, and the net was not built for '
                  'somebody sitting in this.',
         penalty={'tick_mult': 1.1, 'composure': -1}),
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
    # -- second wave: depth for the thin slots and the back room ----------
    Ware('optic_lattice', 'Kohler-Reyes Optic Lattice', 'Kohler-Reyes',
         'ocular', 2, 6, 3900, 2,
         'Overlays a structural read of whatever you are looking at. Built '
         'for surveyors and adopted immediately by people surveying things '
         'they did not own.',
         effects={'scan_depth': 1, 'crack_bonus': 1},
         drawback='It renders constantly and it renders everything. Extended '
                  'use is exhausting in a way that does not show up until you '
                  'are already tired.',
         penalty={'composure': -2}),
    Ware('nictitating', 'Nictitating Shutter', 'unbranded',
         'ocular', 1, 3, 1400, 1,
         'A second eyelid, more or less. Cuts the feedback flash that black '
         'ICE uses to blind you before it does anything worse.',
         effects={'ice_dr': 0.88},
         drawback='It closes on its own when it thinks it should. Roughly one '
                  'time in twenty it thinks so during something important.',
         penalty={'evade_bonus': -1}),
    Ware('pale_cortex', 'Pale Cortex', 'Aoyama Biotech',
         'cortex', 3, 18, 13800, 3,
         'Cultured neural tissue grown against your own and wired in as a '
         'coprocessor. Aoyama will not say whose it was originally.',
         effects={'logic': 1, 'focus': 3, 'crypto_bonus': 2},
         drawback='It dreams. Not metaphorically: it runs when you are not '
                  'using it, and what it produces has begun turning up in '
                  'your working memory unannounced.',
         penalty={},
         rider='creeping_dissonance'),
    Ware('vagus_tap', 'Vagus Tap', 'Sendai Interface',
         'spinal', 2, 9, 5600, 2,
         'Taps the nerve that runs the autonomic system and gives the deck a '
         'vote in what it does. Your heart rate becomes a configurable.',
         effects={'nerve': 1, 'composure': 3, 'tick_mult': 0.94},
         drawback='The deck now has a vote in what your heart does, and the '
                  'deck is a machine that takes damage.',
         penalty={'ice_dr': 1.2}),
    Ware('grave_governor', 'Grave Governor', 'unbranded',
         'neural', 3, 17, 14900, 3,
         'Nobody sells these. They are made, one at a time, by somebody in '
         'Freeport who does not take appointments. It holds a session open '
         'through feedback that would drop anybody else.',
         effects={'integrity': 6, 'composure': 6},
         drawback='It holds the session open. That is the entire function, '
                  'and it does not distinguish between a session you want '
                  'held and one you are trying to leave: jacking out takes an '
                  'extra tick, always, including the tick you do not have.',
         penalty={},
         rider='slow_exit'),
    Ware('quiet_hands', 'Quiet Hands', 'Freeport Collective',
         'limb', 2, 7, 4300, 2,
         'Community-printed replacements with the haptic layer tuned down '
         'rather than up. Everything you do through them is deliberate.',
         effects={'residue_mult': 0.7, 'skill_forensics': 1},
         drawback='Tuned down is tuned down. Anything that rewards speed '
                  'rewards somebody else.',
         penalty={'tick_mult': 1.1}),
    Ware('lamprey', 'Lamprey Interface', 'Carrion Column',
         'subdermal', 3, 20, 11200, 3,
         'Carrion make these and Carrion install these, and the waiting list '
         'is short because of what the waiting list knows. It draws power '
         'from you directly and it is very, very fast.',
         effects={'tempo': 1, 'tick_mult': 0.8, 'ice_damage': 2},
         drawback='It feeds. Every run costs you Integrity that rest returns '
                  'slowly, and the number is not negotiable.',
         penalty={},
         rider='thermal_load'),
    Ware('archivist', 'Archivist Node', 'Kagawa Vertical',
         'cortex', 2, 10, 6900, 3,
         'Corporate compliance hardware: it records everything you do, '
         'perfectly, forever, and indexes it. Kagawa issue it to auditors.',
         effects={'legwork_bonus': 2, 'skill_cryptography': 1},
         drawback='It records everything you do, perfectly, forever. That '
                  'archive is on you, in you, and admissible.',
         penalty={'heat_mult': 1.3}),

    # -- third wave -------------------------------------------------------
    Ware('cartographer_lobe', 'Cartographer Lobe', 'Freeport Collective',
         'cortex', 2, 8, 5800, 2,
         'Community-printed spatial processing. You stop reading a network '
         'and start remembering it, the way you remember a building you have '
         'been in.',
         effects={'skill_architecture': 1, 'scan_depth': 1},
         drawback='Spatial memory is not selective either. You now remember '
                  'every network you have ever been inside, in order, and '
                  'some of them you would rather not.',
         penalty={'composure': -3}),
    Ware('cochlear_array', 'Cochlear Array', 'Sendai Interface',
         'neural', 2, 9, 6100, 2,
         'Hears traffic the way you hear a room: as something with a shape '
         'and a direction and a number of people in it.',
         effects={'skill_signal': 1, 'tell_lead': 1},
         drawback='You cannot switch it off. Every network you enter arrives '
                  'as noise before it arrives as information.',
         penalty={'focus': -2}),
    Ware('vagal_brake', 'Vagal Brake', 'Aoyama Biotech',
         'spinal', 2, 11, 7900, 3,
         'Clinical panic suppression, developed for surgical patients and '
         'adopted immediately by people who go somewhere a Coffin lives.',
         effects={'skill_psyche': 1, 'composure': 6},
         drawback='It suppresses the panic and everything sharing a channel '
                  'with it. Your reactions are slower and you will not feel '
                  'them getting slower.',
         penalty={'evade_bonus': -3}),
    Ware('liar_larynx', 'Liar\'s Larynx', 'unbranded',
         'subdermal', 2, 12, 6700, 3,
         'Voice synthesis with a tell-suppression layer, built by somebody in '
         'the Shambles who does very good work and asks no questions at all.',
         effects={'skill_sabotage': 1, 'pretext_bonus': 4},
         drawback='It suppresses your tells by suppressing your voice. What '
                  'comes out is convincing and is not quite yours, and people '
                  'who know you notice.',
         penalty={'rep_mult': 0.88}),
    Ware('ninth_finger', 'Ninth Finger', 'Kohler-Reyes',
         'limb', 1, 5, 2600, 1,
         'An additional digit, mounted where a watch would go, dedicated '
         'entirely to interface work. Absurd, cheap, and startlingly '
         'effective.',
         effects={'tick_mult': 0.93},
         drawback='It is visible, it is strange, and it moves on its own '
                  'when you are concentrating.',
         penalty={'pretext_bonus': -2}),
    Ware('mourner', 'Mourner', 'Chorus',
         'cortex', 3, 22, 10400, 3,
         'The Chorus do not sell these. They fit them, for free, to anybody '
         'who asks twice. Nobody outside the Chorus will tell you what it '
         'does and everybody inside describes it differently.',
         effects={'composure': 8, 'trace_mult': 0.85, 'focus': 2},
         drawback='It was fitted by people who wanted something. Dissonance '
                  'accrues from wearing it: +1 every run, and the Chorus now '
                  'know where you are.',
         penalty={'heat_mult': 1.15},
         rider='creeping_dissonance'),
    Ware('deadhand', 'Deadhand Relay', 'Nightwatch surplus',
         'limb', 2, 7, 3800, 2,
         'Issue equipment for officers going somewhere they might not come '
         'back from. It finishes the job when the operator cannot.',
         effects={'ice_damage': 3, 'integrity': 2},
         drawback='It is issue equipment with an issue serial, and it '
                  'finishes the job on its own terms rather than yours.',
         penalty={},
         rider='nightwatch_serial'),
    Ware('quiet_room', 'Quiet Room', 'Freeport Collective',
         'neural', 3, 13, 8600, 3,
         'A shielded volume around the interface itself. Inside it, nothing '
         'from the network can reach you and nothing you do reaches the '
         'network either.',
         effects={'ice_dr': 0.7, 'noise_mult': 0.75},
         drawback='Nothing reaches you, including the tells. You are safer '
                  'and considerably blinder.',
         penalty={'tell_lead': -2, 'scan_depth': -1}),
    # -- D69: what the audit found nothing for -------------------------------
    Ware('doorman', 'Doorman', 'unbranded, Ninth Ward', 'subdermal', 1, 4,
         1600, 1,
         'A subdermal plate across the forearm and a way of standing that '
         'comes with it. Everybody who has one recognises everybody else who '
         'has one, which is most of what it does.',
         effects={'skill_streetcraft': 1, 'cover': 2},
         drawback='Being known cuts both ways. The people who recognise it '
                  'include the people who are looking for somebody with one.',
         penalty={'heat_mult': 1.12}),
    Ware('longhaul', 'Longhaul Frame', 'Freeport, rebuilt', 'spinal', 2, 6,
         4200, 2,
         'Dock chrome: a load frame off the cranes, cut down and put in a '
         'person, which Freeport have been doing to themselves for years and '
         'will do to you for a fee.',
         effects={'skill_fieldcraft': 1, 'integrity': 4},
         drawback='It was built to carry, not to sit still. Everything you '
                  'do at a desk takes fractionally longer, forever.',
         penalty={'tick_mult': 1.08}),
    Ware('choirmaster', 'Choirmaster', 'Kohler-Reyes', 'cortex', 2, 11, 6200,
         2,
         'Runs processes the way a conductor runs a section: not faster, '
         'together. Daemonologists say it is the difference between owning '
         'daemons and having them.',
         effects={'skill_daemonology': 1, 'tempo': 1},
         drawback='What they are doing, you are doing. Their noise is filed '
                  'against your session and their mistakes feel like yours.',
         penalty={'focus': -2},
         rider='choir_noise'),
    Ware('second_voice', 'Second Voice', 'Aoyama, discontinued', 'neural', 2,
         10, 5400, 2,
         'A laryngeal implant that gives you another person\'s cadence on '
         'demand. Aoyama sold it to negotiators for a year and then stopped '
         'answering questions about it.',
         effects={'skill_subterfuge': 1, 'pretext_bonus': 2},
         drawback='It is not your voice. Nobody remembers the person you '
                  'were not, and standing does not accrue to a stranger.',
         penalty={'rep_mult': 0.85}),
    Ware('gutterloop', 'Gutter Loop', 'unbranded, salvage', 'subdermal', 1, 3,
         900, 1,
         'A cooling loop for a deck, wired into a person, because the person '
         'was cheaper to modify than the deck. It works. It is cold.',
         effects={'heat_cap': 3},
         drawback='It runs coolant under your skin and you can feel it, and '
                  'people can see where it goes.',
         penalty={'composure': -1}),
    Ware('cold_spine', 'Cold Spine', 'Sendai Interface', 'spinal', 3, 14,
         11800, 3,
         'A thermal trunk that takes the heat out of a deck and puts it into '
         'you, where there is more of you to put it in.',
         effects={'heat_cap': 9, 'tick_mult': 0.92},
         drawback='It puts the heat in you. Every step of overclock past the '
                  'budget costs Integrity as well as components.',
         penalty={},
         rider='thermal_load'),
    Ware('long_eye', 'Long Eye', 'Nightwatch, decommissioned', 'ocular', 2,
         13, 8600, 3,
         'Surveillance optics from a decommissioned watch post. It reads a '
         'network the way it read a street: from further away than anybody '
         'is comfortable with.',
         effects={'scan_depth': 2, 'skill_architecture': 1},
         drawback='It was built to watch and not to be watched back. What it '
                  'shows you is hard to stop looking at.',
         penalty={'composure': -3}),
    Ware('breaker_hand', 'Breaker Hand', 'Carrion, made to order',
         'limb', 3, 15, 9700, 3,
         'An arm built for one purpose by people who do not ask what the '
         'purpose is. It hits countermeasures the way it was told to.',
         effects={'ice_damage': 5, 'skill_warfare': 1},
         drawback='Nothing about it is subtle and nothing about it is '
                  'concealable. Every door you talk your way through, you '
                  'talk through in spite of it.',
         penalty={'pretext_bonus': -4}),
    Ware('quiet_step', 'Quiet Step', 'Freeport Collective', 'limb', 2, 7,
         3900, 2,
         'Open-hardware feet, more or less: gait dampers that Freeport '
         'publish the plans for and half the Ninth has fitted badly.',
         effects={'skill_stealth': 1, 'noise_mult': 0.92},
         drawback='Published plans mean published signatures. Anybody who '
                  'has read the specification knows what to look for.',
         penalty={'trace_mult': 1.08}),
)



#: The ones there is one of (D63 e). Not sold over any counter.
RELICS: tuple[Ware, ...] = (
    Ware('remnant_graft', 'Remnant\'s Graft', 'unbranded, reworked',
         'cortex', 2, 1, 9000, 3,
         'The piece Remnant had taken out last, the day they stopped. It '
         'went back in somebody else, which is you, and it does not drift. '
         'Nobody who has looked at it can say why.',
         effects={'composure': 4, 'trace_mult': 0.9},
         drawback='It does not drift, and Remnant will not say what that '
                  'cost, and you are a little slower to find your own hands.',
         penalty={'focus': -1},
         unique=True,
         lore='Remnant had everything taken out over eleven months and kept '
              'one piece, in a drawer in the dark room that is not locked '
              'because nobody who goes in there opens drawers. It is the one '
              'that was in longest. Dissonance is a record of what you have '
              'done to yourself, and this piece carries almost none, which '
              'by every rule in the city should not be possible; Remnant\'s '
              'theory, offered once and not repeated, is that it did its '
              'drifting already, in them, and has nothing left to do in '
              'anybody else. You found it on a night when the room was empty '
              'and you were far enough gone yourself to think of looking.'),
    Ware('waterbearer', 'The Water Bearer', 'unbranded, older than most',
         'limb', 1, 2, 2100, 2,
         'A shoulder brace off somebody who carried cans up stairwells for '
         'forty years, adjusted by somebody who did the same, and it '
         'remembers the stairs better than you do.',
         effects={'grit': 1, 'skill_fieldcraft': 1},
         drawback='It was fitted to somebody else and it has opinions about '
                  'the angle of your arm.',
         penalty={'reflex': -1},
         unique=True,
         lore='The Widow at the water point has outlived a husband, two '
              'children and most of a stairwell, and has carried two cans up '
              'six floors every day of it, and this is what let her. It came '
              'out of her husband, who did not need it any more, and she '
              'wore it for thirty years, and she took it off and put it in '
              'your hands on a landing on the way up because you had carried '
              'the third can without being asked twice. It is not good '
              'chrome. It is the best-worn piece of anything in this city, '
              'and it knows exactly how far it is to the sixth floor.'),
    Ware('lark_piece', 'What Came Out of Lark', 'Aoyama, second-hand',
         'neural', 2, 9, 2400, 2,
         'A reflex shunt, load-bearing by the end. It was keeping Lark '
         'upright and it does not know you are not Lark.',
         effects={'reflex': 1, 'tick_mult': 0.9},
         drawback='It expects a body that was already failing, and it takes '
                  'a little of yours to make up the difference.',
         penalty={'integrity': -2},
         unique=True,
         lore='Lark died because nobody paid, and somebody went through the '
              'crate outside the clinic afterwards looking for things worth '
              'money, and missed the thing taped inside the lid because it '
              'was not worth money: it was worth Lark, for about a fortnight '
              'at the end. It is good chrome. It is faster than it has any '
              'right to be and it costs you a little every night, which is '
              'the same deal Lark had, at the same clinic, from the same '
              'people. The Blue Surgeon will fit it without comment.'),
    Ware('aftercare_bead', 'Aftercare Bead', 'Aoyama Biotech, Greenward',
         'subdermal', 1, 3, 1800, 2,
         'A bead under the skin of the wrist, the kind the Green gives '
         'patients who have stopped coming in. It steadies you. It also '
         'reports.',
         effects={'composure': 2, 'price_mult': 0.96},
         drawback='Aftercare means somebody is keeping notes. What it files '
                  'about you converts into heat a little faster.',
         penalty={'heat_mult': 1.1},
         unique=True,
         lore='The dispensary keeps a tray of them for people who were '
              'discharged and did not come back, which is most people, and '
              'the orderly gave you one because you had been polite to the '
              'orderly more than once, which is rare enough on that floor to '
              'count as a relationship. It does what it says: a small '
              'steadiness, a small discount at any counter Aoyama supplies, '
              'and a small file, somewhere in the Green, that grows by a '
              'line every time you do something a file would want to know.'),
)

WARE = WARE + RELICS

BY_KEY: dict[str, Ware] = {w.key: w for w in WARE}
WARE_KEYS: tuple[str, ...] = tuple(BY_KEY)

#: Riders the engine implements. A rider on a piece that is not in this set is
#: a validation error, which is what stops a drawback existing only in prose.
RIDERS: frozenset[str] = frozenset({
    'pain_editor', 'adrenal',
    'misfire', 'nightwatch_serial', 'dual_thread', 'deadman', 'thermal_load',
    'blind_trace', 'creeping_dissonance', 'slow_exit', 'choir_noise',
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
