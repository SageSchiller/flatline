"""The deck: six component slots, every one of them a trade.

The deck is the only part of the build that can be changed cheaply and often,
which makes it the tuning layer. Chrome is a commitment measured in Dissonance,
skills are a commitment measured in experience, and the deck is a commitment
measured in whether you can be bothered to walk to a market.

The slots are chosen so that no two of them are the same axis:

- **cpu** buys actions and pays in heat
- **memory** buys programs and pays in everything else
- **io** buys throughput, which sets how much a tick is worth
- **cooling** buys headroom, which is what makes overclocking survivable
- **masking** buys trace resistance and pays in memory or speed
- **antenna** buys reach and pays in signature

A deck that is good at everything does not exist at any price, which is the
point.
"""

from __future__ import annotations

from dataclasses import dataclass, field

SLOTS: tuple[str, ...] = ('cpu', 'memory', 'io', 'cooling', 'masking', 'antenna')

SLOT_BLURB: dict[str, str] = {
    'cpu': 'Actions per tick, and the heat that buys.',
    'memory': 'How many programs you carry.',
    'io': 'Throughput. How much a tick is worth.',
    'cooling': 'Thermal headroom. Gates overclocking.',
    'masking': 'Trace resistance.',
    'antenna': 'Range, remote runs, and how far your signature carries.',
}


@dataclass(frozen=True, slots=True)
class Component:
    key: str
    name: str
    slot: str
    tier: int
    price: int
    blurb: str
    effects: dict = field(default_factory=dict)
    drawback: str = ''
    penalty: dict = field(default_factory=dict)
    #: Thermal output. The cooling budget has to cover the sum of these.
    heat: int = 0
    #: One of a kind (D63 e). Never in a market: found somewhere, given by
    #: somebody, or handed over by a decision. `lore` is its history, shown
    #: by `inspect` and when it is found.
    unique: bool = False
    lore: str = ''


COMPONENTS: tuple[Component, ...] = (
    # -- cpu ---------------------------------------------------------------
    Component('cpu_salvage', 'Salvaged Core', 'cpu', 1, 200,
              'It works. That is the entire specification.',
              effects={}, heat=2,
              drawback='No headroom at all. Overclocking it is a coin flip '
                       'against component death.',
              penalty={}),
    Component('cpu_standard', 'Kagawa Standard Core', 'cpu', 1, 1100,
              'The core most decks ship with, because it is adequate and '
              'nobody was ever fired for specifying one.',
              effects={'tick_mult': 0.95}, heat=3),
    Component('cpu_hotrod', 'Kohler-Reyes Hotrod', 'cpu', 2, 4300,
              'Rated well past what the cooling in this price bracket can '
              'sustain, which the marketing calls headroom.',
              effects={'tempo': 1, 'tick_mult': 0.88}, heat=7,
              drawback='Runs hot enough that a stock cooler cannot hold it '
                       'through a long run.',
              penalty={}),
    Component('cpu_refit', 'Refitted Core', 'cpu', 2, 2400,
              'Somebody else\'s Hotrod, after the somebody else. Re-lidded, '
              're-pasted, and honest about its second life.',
              effects={'tick_mult': 0.9}, heat=5,
              drawback='It runs warm for what it does, and nobody will say '
                       'how many owners it has had.',
              penalty={}),
    Component('cpu_glacier', 'Sendai Glacier', 'cpu', 3, 9800,
              'Fast and cold, because Sendai solved the problem rather than '
              'moving it. Priced accordingly.',
              effects={'tempo': 1, 'tick_mult': 0.82}, heat=3,
              drawback='Sendai firmware is signed and closed, and the price '
                       'is the price.',
              penalty={},
              ),

    # -- memory ------------------------------------------------------------
    Component('mem_thin', 'Thin Bank', 'memory', 1, 300,
              'Four slots. You will resent it within an hour.',
              effects={'memory': 4}, heat=1),
    Component('mem_standard', 'Standard Bank', 'memory', 1, 1500,
              'Six slots, which is enough to have a plan.',
              effects={'memory': 6}, heat=2),
    Component('mem_stacked', 'Stacked Bank', 'memory', 2, 2900,
              'Two standard banks on one carrier, sharing a bus that was '
              'designed for one. It holds more than it should and it knows.',
              effects={'memory': 7}, heat=3,
              drawback='The shared bus chatters, and chatter is trace.',
              penalty={'trace_mult': 1.04}),
    Component('mem_wide', 'Wide Bank', 'memory', 2, 5200,
              'Nine slots. Enough to bring the answer to a question you have '
              'not asked yet.',
              effects={'memory': 9}, heat=4,
              drawback='Wide banks are power-hungry and the draw is visible.',
              penalty={'trace_mult': 1.1}),
    Component('mem_cascade', 'Cascade Array', 'memory', 3, 12600,
              'Twelve slots and a paging layer fast enough that you stop '
              'thinking about which ones are live.',
              effects={'memory': 12}, heat=5,
              drawback='The paging layer writes. Some of what it writes '
                       'survives the run, on the network, where you left it.',
              penalty={'residue_mult': 1.25}),

    # -- io ----------------------------------------------------------------
    Component('io_copper', 'Copper Line', 'io', 1, 150,
              'Physical, slow, and impossible to intercept without being in '
              'the room.',
              effects={}, heat=1,
              drawback='It is a wire. It does what a wire does and nothing '
                       'more, and nothing about it is fast.',
              penalty={}),
    Component('io_standard', 'Standard Bus', 'io', 1, 1200,
              'What everybody has.',
              effects={'tick_mult': 0.95}, heat=2),
    Component('io_broadwave', 'Broadwave Bus', 'io', 2, 4800,
              'Throughput enough that bulk exfiltration stops being a separate '
              'phase of the run.',
              effects={'tick_mult': 0.85}, heat=4,
              drawback='It is a wide, obvious pipe.',
              penalty={'noise_mult': 1.15}),
    Component('io_coax', 'Coax Trunk', 'io', 2, 2600,
              'Building-grade cable, liberated. Wider than copper and it '
              'remembers everything that went down it.',
              effects={'tick_mult': 0.9}, heat=3,
              drawback='It keeps a buffer, and buffers are evidence.',
              penalty={'residue_mult': 1.08}),
    Component('io_needle', 'Needlecast', 'io', 3, 10900,
              'Narrow, fast, and pointed. The connection is a line rather than '
              'a cloud, which is as hard to find as it is to widen.',
              effects={'tick_mult': 0.8, 'trace_mult': 0.9}, heat=3,
              drawback='Narrow is narrow. It does one thing, and the thing '
                       'costs what a flat costs.',
              penalty={}),

    # -- cooling -----------------------------------------------------------
    Component('cool_passive', 'Passive Sink', 'cooling', 1, 100,
              'A block of metal. It has never failed and it has never helped.',
              effects={'heat_cap': 6}),
    Component('cool_fan', 'Forced Air', 'cooling', 1, 800,
              'Adequate, cheap, and audible in a quiet room.',
              effects={'heat_cap': 11},
              drawback='Audible. Physical infiltration is harder with a deck '
                       'that whines.',
              penalty={'pretext_bonus': -1}),
    Component('cool_block', 'Cold Block', 'cooling', 2, 1900,
              'A machined heatsink the size of a brick, bolted where the '
              'case was never meant to take one.',
              effects={'heat_cap': 14}, heat=0,
              drawback='It needs a fan to be worth the weight, and the fan '
                       'is not quiet.',
              penalty={'noise_mult': 1.05}),
    Component('cool_loop', 'Closed Loop', 'cooling', 2, 3900,
              'Liquid, sealed, silent. The point at which overclocking becomes '
              'a tactic rather than a gamble.',
              effects={'heat_cap': 18}),
    Component('cool_cryo', 'Cryo Cell', 'cooling', 3, 11400,
              'Runs the core below ambient. Expensive, and it makes the deck '
              'sweat in a way that has ruined more than one contact.',
              effects={'heat_cap': 28},
              drawback='The cell is consumable and it is not cheap to refill.',
              penalty={'repair_mult': 1.3}),

    # -- masking -----------------------------------------------------------
    Component('mask_none', 'Open Config', 'masking', 1, 0,
              'No masking layer at all. Every byte you send says who sent it.',
              effects={}),
    Component('mask_stock', 'Stock Scrambler', 'masking', 1, 900,
              'Defeats casual attribution and nothing else.',
              effects={'trace_mult': 0.92}, heat=1),
    Component('mask_foil', 'Foil Wrap', 'masking', 2, 2200,
              'A second skin of junk traffic. Cheap to be wrong about who you '
              'are, and it rustles.',
              effects={'trace_mult': 0.86}, heat=1,
              drawback='The junk is itself a noise, on every host you touch.',
              penalty={'noise_mult': 1.06}),
    Component('mask_shroud', 'Shroud Layer', 'masking', 2, 4100,
              'Real masking, at the cost of a memory slot the layer keeps for '
              'itself.',
              effects={'trace_mult': 0.78, 'memory': -1}, heat=2),
    Component('mask_palindrome', 'Palindrome', 'masking', 3, 12200,
              'Traffic that reads the same from either end, so a trace that '
              'follows it arrives back where it started.',
              effects={'trace_mult': 0.6, 'memory': -2}, heat=3,
              drawback='The layer is computationally expensive and everything '
                       'you do runs slower through it.',
              penalty={'tick_mult': 1.12}),

    # -- antenna -----------------------------------------------------------
    Component('ant_none', 'Hardline Only', 'antenna', 1, 0,
              'No radio. You go where the cable is.',
              effects={'trace_mult': 0.9},
              drawback='You hear nothing of the city while you are on the '
                       'wire, and legwork is mostly hearing.',
              penalty={'legwork_bonus': -1}),
    Component('ant_short', 'Short Whip', 'antenna', 1, 600,
              'Enough range to work from the building rather than the room, '
              'and to hear what the building is saying.',
              effects={}, heat=1),
    Component('ant_dish', 'Window Dish', 'antenna', 2, 1900,
              'A flat panel taped to the inside of a window. Block range, '
              'and the block talks.',
              effects={'legwork_bonus': 1}, heat=1,
              drawback='Anything pointed can be pointed at.',
              penalty={'trace_mult': 1.06}),
    Component('ant_long', 'Longwire', 'antenna', 2, 3600,
              'District range. You can run a job from a bar on the other side '
              'of it, which is exactly as good an alibi as it sounds.',
              effects={'legwork_bonus': 2}, heat=2,
              drawback='A signature that carries district-wide carries to the '
                       'people looking for it as well.',
              penalty={'trace_mult': 1.18}),
    Component('ant_relay', 'Relay Mesh', 'antenna', 3, 9200,
              'Bounces through civilian infrastructure. Citywide reach and a '
              'point of origin that resolves to a laundromat.',
              effects={'legwork_bonus': 2, 'trace_mult': 0.88}, heat=3,
              drawback='It is illegal in a way that is easy to prove. Being '
                       'caught with one is its own charge.',
              penalty={'heat_mult': 1.2}),
)


#: The ones there is one of (D63 e). Not sold over any counter.
RELICS: tuple[Component, ...] = (
    Component('cool_cloth', 'A Wet Cloth', 'cooling', 1, 5,
              'It is a wet cloth. It goes over the case. Sparrow solved '
              'thermal load this way, and was right about how often it works, '
              'which is most of the time, which is the problem.',
              effects={'heat_cap': 3}, heat=0,
              drawback='It is a wet cloth.',
              penalty={},
              unique=True,
              lore='You taught Sparrow how a deck actually works, and she '
                   'listened, and then she gave you this, folded, still damp, '
                   'with the air of somebody handing over a trade secret. It '
                   'does in fact cool a deck. It cools a deck by about a '
                   'third of what the cheapest sink in the catalogue manages, '
                   'and it weighs nothing, and it was free, and it is '
                   'impossible to look at it fitted to a nine-thousand-credit '
                   'rig without hearing her explain it. There is no better '
                   'item in the game and there are many stronger ones.'),
    Component('ant_pip', 'Pip\'s Dish', 'antenna', 2, 2600,
              'A flat dish off tower three, pointed by somebody who knew '
              'exactly where everything was and did not know what any of it '
              'was worth. It hears the city the way a child on a water tower '
              'hears it: all of it, at once, in lists.',
              effects={'legwork_bonus': 2}, heat=1,
              drawback='It was pointed at the Vertical when you got it, and '
                       'the Vertical noticed. Anything pointed can be '
                       'pointed at.',
              penalty={'trace_mult': 1.08},
              unique=True,
              lore='Pip took the bottom rungs off the ladders so that only '
                   'kids could climb them, and put this on tower three, and '
                   'pointed it at the Vertical for reasons, and traded it to '
                   'you for a thing you wanted less than Pip wanted the thing '
                   'Pip asked for, which is how all of Pip\'s trades go and '
                   'why Pip has so much. It is the best legwork antenna in '
                   'the city by a distance, because it was never built to be '
                   'an antenna: it was built to hear everything, by somebody '
                   'who had not yet learned what not to listen to.'),
    Component('mem_ledger', 'A Ledger Page', 'memory', 3, 7000,
              'A sheet of Meridian\'s own storage, the kind the ledger is '
              'kept on, which holds more than it should because it was built '
              'to hold a line that never ends.',
              effects={'memory': 8}, heat=1,
              drawback='It keeps a line. Everything you load is written '
                       'somewhere Meridian can read, and they convert it to '
                       'heat a little faster.',
              penalty={'heat_mult': 1.08},
              unique=True,
              lore='The Notary left it on the counter, after the line was '
                   'ended, without looking up: a sheet of whatever the '
                   'ledger is kept on, which is not paper and is not a drive '
                   'and is, fitted to a deck, eight memory with almost no '
                   'heat. Nobody at Meridian gives anything away, and the '
                   'Notary did not: it is an arrangement. The page keeps a '
                   'line, the way all of their pages do, and the line is '
                   'what you carry, and the line is very long, and they can '
                   'read it.'),
    Component('io_landline', 'Mara\'s Landline', 'io', 2, 3300,
              'A number on the old exchange that rings back. Nobody traces a '
              'landline, because nobody remembers they exist.',
              effects={'tick_mult': 0.92, 'trace_mult': 0.85}, heat=1,
              drawback='Everybody in the building hears one ring.',
              penalty={'noise_mult': 1.1},
              unique=True,
              lore='Mara ran the noodle bar and before that she ran something '
                   'else, and the something else left her with a number on '
                   'the copper exchange that still answers. You did a thing '
                   'for her that was not a transaction and she gave you the '
                   'number, which is a transaction, in her way. Routed through '
                   'it a connection is older than anything that is watching '
                   'for connections, and the trace has to go the long way '
                   'round through a switch that was built to carry voices. '
                   'The bell, though. There is always the bell.'),
)

COMPONENTS = COMPONENTS + RELICS

BY_KEY: dict[str, Component] = {c.key: c for c in COMPONENTS}
COMPONENT_KEYS: tuple[str, ...] = tuple(BY_KEY)


@dataclass(frozen=True, slots=True)
class DeckPreset:
    key: str
    name: str
    blurb: str
    parts: dict          # slot -> component key


#: The decks origins hand out. Each is a coherent argument about how its owner
#: works, not a random draw from the tier-1 pool.
PRESETS: tuple[DeckPreset, ...] = (
    DeckPreset('kagawa_issue', 'Kagawa Issue',
               'Corporate standard, complete and unremarkable. Everything on '
               'it is documented, which cuts both ways.',
               {'cpu': 'cpu_standard', 'memory': 'mem_standard',
                'io': 'io_standard', 'cooling': 'cool_fan',
                'masking': 'mask_stock', 'antenna': 'ant_short'}),
    DeckPreset('scrapdeck', 'Scrapdeck',
               'Six components, four manufacturers, one owner who knows '
               'exactly which solder joint to press when it stops.',
               {'cpu': 'cpu_salvage', 'memory': 'mem_thin',
                'io': 'io_standard', 'cooling': 'cool_passive',
                'masking': 'mask_none', 'antenna': 'ant_short'}),
    DeckPreset('midline', 'Midline Build',
               'What a working runner buys when the first real payday clears.',
               {'cpu': 'cpu_standard', 'memory': 'mem_standard',
                'io': 'io_standard', 'cooling': 'cool_fan',
                'masking': 'mask_stock', 'antenna': 'ant_short'}),
    DeckPreset('university_loan', 'University Loan Unit',
               'Signed out for a research project that concluded four years '
               'ago. Excellent core, no masking whatsoever, and a cooling '
               'budget the core consumes entirely: zero headroom, so no '
               'overclocking until something here is replaced.',
               {'cpu': 'cpu_hotrod', 'memory': 'mem_standard',
                'io': 'io_standard', 'cooling': 'cool_fan',
                'masking': 'mask_none', 'antenna': 'ant_none'}),
    DeckPreset('decommissioned', 'Decommissioned Unit',
               'Nightwatch response-desk hardware, wiped once, badly. Built to '
               'survive contact rather than to avoid it: heavy cooling, real '
               'masking, and a memory bank the masking layer takes a slice of.',
               {'cpu': 'cpu_standard', 'memory': 'mem_standard',
                'io': 'io_copper', 'cooling': 'cool_loop',
                'masking': 'mask_shroud', 'antenna': 'ant_none'}),
)

PRESETS_BY_KEY: dict[str, DeckPreset] = {p.key: p for p in PRESETS}


def by_slot(slot: str) -> list[Component]:
    return [c for c in COMPONENTS if c.slot == slot]
