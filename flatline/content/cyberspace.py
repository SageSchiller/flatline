"""What the net looks like from inside it.

The single most important thing this file does is stop a run reading like a
port scan. A network is a **place**. You are in it, not looking at it, and the
thing that sells that is not mechanics, it is that a Kagawa fileserver and a
Carrion fileserver do not look remotely alike from the inside.

Three layers of description, composed at render time:

- **Signature** is the faction's whole aesthetic: what their cyberspace is
  made of. One per faction, and it is the layer players will learn to read.
- **Node** is what this specific host presents as, phrased in the faction's
  visual language where it matters and generically where it does not.
- **Descent** is the transition text between zones, printed when you cross a
  boundary. This is what makes depth feel like depth rather than a counter.

Everything here is flavour with no mechanical weight, which is exactly why it
gets its own file: it can be rewritten wholesale without touching a rule.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Signature:
    faction: str
    #: Printed once on connection. Sets the visual key for the whole run.
    arrival: str
    #: Adjectives and materials the node descriptions draw on.
    texture: tuple[str, ...]
    #: What their ICE looks like when it wakes. Faction-specific menace.
    ice_wakes: str


SIGNATURES: tuple[Signature, ...] = (
    Signature(
        'kagawa',
        'Kagawa render their networks as agricultural terraces: endless '
        'stepped shelves of pale green process light receding further than the '
        'building could possibly be, everything growing on a schedule. It is '
        'restful in a way that is clearly deliberate and slightly obscene.',
        ('terraced', 'irrigated', 'pale green', 'stacked', 'gridded'),
        'A shelf of the terrace stops growing. Everything on it turns to face '
        'you at once.',
    ),
    Signature(
        'aoyama',
        'Aoyama build in clinical white and biological curve, corridors that '
        'branch like vasculature and seal behind you with a wet, unhurried '
        'competence. Everything is spotless. Everything is warm to the touch.',
        ('sterile', 'vascular', 'white', 'membranous', 'warm'),
        'The corridor constricts. Something in the wall has decided you are '
        'foreign material.',
    ),
    Signature(
        'sendai',
        'Sendai do not render an environment. They render *you*, at very high '
        'resolution, in a black volume with no floor, and let you work out '
        'what that implies about who is holding the camera.',
        ('black', 'reflective', 'weightless', 'exact', 'close'),
        'Your own reflection stops copying you and holds still, waiting.',
    ),
    Signature(
        'sixes',
        'The Sixes never commissioned a render, so you get the default: a '
        'wireframe city block in municipal blue, missing half its textures, '
        'with somebody\'s tag scrawled across a wall in eight-metre letters '
        'and a music stream nobody has turned off in four years.',
        ('wireframe', 'untextured', 'municipal blue', 'tagged', 'improvised'),
        'The music cuts out. In the silence you can hear something moving that '
        'has no reason to make a sound at all.',
    ),
    Signature(
        'carrion',
        'Carrion built theirs themselves, out of scavenged asset packs and '
        'genuine hatred: a slaughterhouse corridor in wet red, hung with the '
        'iconography of people they have taken apart, rendered at a framerate '
        'chosen to make you sick.',
        ('wet', 'red', 'hung', 'stuttering', 'meat-lit'),
        'The framerate drops. Something in the hanging shapes has started '
        'keeping time with you.',
    ),
    Signature(
        'fixers',
        'The Switchboard runs on borrowed infrastructure and it shows: a '
        'telephone exchange from a century that never had one, all brass jacks '
        'and patch cables, warm amber light, and forty thousand conversations '
        'running as a low sound just under hearing.',
        ('brass', 'amber', 'patched', 'humming', 'worn smooth'),
        'Every conversation in the exchange stops at once. The silence is the '
        'loudest thing that has happened all night.',
    ),
    Signature(
        'nightwatch',
        'Nightwatch render in procedural municipal grey, a precinct that '
        'extends in every direction with the same four office assets repeated '
        'to the horizon, lit by strip lighting that flickers on a timer '
        'somebody costed out.',
        ('grey', 'repeated', 'procedural', 'strip-lit', 'municipal'),
        'The strip lighting stops flickering. Every light in the precinct comes '
        'up to full at the same moment.',
    ),
    Signature(
        'freeport',
        'Freeport render their network as the docks, honestly and to scale, '
        'because they see no reason to lie about it. Containers stacked in the '
        'open, everything labelled, and a public log running down the side of '
        'the sky where anybody can read what you just did.',
        ('open', 'stacked', 'labelled', 'salt-bleached', 'public'),
        'Your name goes up on the public log, in the sky, in letters four '
        'containers high.',
    ),
    Signature(
        'meridian',
        'Meridian render nothing at all. You are in a grey volume the exact '
        'size of the node you are standing in, with the doors marked and '
        'everything else omitted as an unnecessary expense. It is the only '
        'network in the city that has clearly been costed by the same people '
        'who defend it.',
        ('grey', 'unrendered', 'costed', 'plain', 'exact'),
        'A door you had not noticed is marked. That is the whole of the '
        'warning and it is entirely sufficient.',
    ),
    Signature(
        'chorus',
        'The Chorus built theirs to be worth being in, and it is: a warm '
        'unbroken interior in gold and deep red, with a sound underneath it '
        'that resolves, if you stop and listen, into a great many people '
        'quietly agreeing about something.',
        ('warm', 'gold', 'unbroken', 'devotional', 'sung'),
        'The agreement stops. Several thousand voices are now paying '
        'attention to the same thing, and the thing is you.',
    ),
    Signature(
        'static',
        'Static is a broadcast studio that never existed, rendered from '
        'reference photographs of four different ones: mismatched furniture, '
        'a mixing desk with somebody\'s tea on it, and every wall a live feed '
        'of something happening elsewhere in the city right now.',
        ('mismatched', 'live', 'broadcast', 'lit', 'borrowed'),
        'Every wall cuts to the same feed at once. The feed is this room, '
        'from behind you.',
    ),
    Signature(
        'deepwater',
        'Deepwater does not render an environment and does not render you. '
        'There is depth, and pressure, and a sense of enormous slow structure '
        'somewhere below the resolution you are being permitted. Nothing here '
        'was built for a person to look at. It is not clear that anything '
        'here was built.',
        ('pressured', 'unlit', 'vast', 'slow', 'unmeant'),
        'The structure below you changes its mind about something. You feel '
        'it the way you feel a ship move.',
    ),
)

BY_FACTION: dict[str, Signature] = {s.faction: s for s in SIGNATURES}


#: node type -> what it presents as. Second person, present tense, one clause.
#: Written generically so that any faction's texture can sit alongside it.
NODE_LOOK: dict[str, tuple[str, ...]] = {
    'gateway': (
        'a doorway with too much traffic through it to notice one more body',
        'the front of the thing, worn smooth by everybody who has ever '
        'knocked on it',
    ),
    'relay': (
        'a junction, all through-traffic and no memory',
        'somewhere the network passes through rather than stops',
    ),
    'workstation': (
        'somebody\'s desk, still logged in, with four years of shortcuts on it',
        'a personal space, badly kept, full of the small keys people leave lying',
    ),
    'fileserver': (
        'bulk storage, stacked to the limit of the render and indexed by nobody',
        'the warehouse: everything anybody ever kept, in no order at all',
    ),
    'controller': (
        'a room that runs something in the physical world, and knows it',
        'the place where this network reaches out and touches the building',
    ),
    'auth': (
        'the office that issues the badges, and therefore the only room that '
        'matters',
        'where identity is decided, guarded like the mint it effectively is',
    ),
    'vault': (
        'the thing the whole network was built around, sealed and watched',
        'a strongroom, and everything else you have walked through was the '
        'argument for it',
    ),
    'honeypot': (
        'somebody\'s desk, still logged in, unusually convenient',
        'a personal space with nothing personal in it',
    ),
}


#: Crossing a boundary inward. Indexed by the zone being entered.
DESCENT: dict[str, tuple[str, ...]] = {
    'interior': (
        'The public render falls away. What is on the other side was built for '
        'staff and does not bother being welcoming.',
        'You cross the line where the network stops advertising and starts '
        'working.',
    ),
    'restricted': (
        'The texture density drops. Everything here is functional, nothing here '
        'is decorated, and the assumption that you belong stops being made.',
        'Past this point the network has opinions about who you are, and it '
        'checks them.',
    ),
    'core': (
        'It gets very quiet. The core does not render an environment at all, '
        'because nothing that reaches it is supposed to have eyes.',
        'The last boundary. Whatever is in here was worth all of the rest of '
        'it, and it is guarded like somebody believes that.',
    ),
}


#: Printed when the trace crosses a threshold. The clock made physical.
TRACE_PRESSURE: tuple[tuple[float, str], ...] = (
    (0.25, 'Somewhere behind you, a process you cannot see has started '
           'keeping a file.'),
    (0.50, 'The connection has developed a lag that is not distance. Somebody '
           'is standing in the middle of it, reading.'),
    (0.75, 'You can feel them narrowing it. The route home is getting shorter '
           'and more crowded at the same time.'),
    (0.90, 'They have you to within a building. There is no version of the '
           'next minute in which you are still here.'),
)


def signature(faction: str) -> Signature:
    return BY_FACTION.get(faction) or SIGNATURES[0]


def look(node_type: str, index: int = 0, faction: str = '') -> str:
    """What a node presents as, in the owner's visual language.

    The generic description carries the shape and the faction's texture
    carries the material, which is why a Kagawa fileserver and a Carrion
    fileserver read as different places while sharing one line of writing.
    """
    options = NODE_LOOK.get(node_type) or NODE_LOOK['relay']
    body = options[index % len(options)]
    if not faction:
        return body
    sig = BY_FACTION.get(faction)
    if sig is None or not sig.texture:
        return body
    # Two beats rather than a label: the material, then the shape. A colon
    # read like a database field and this reads like somebody describing a
    # room they are standing in.
    texture = sig.texture[index % len(sig.texture)]
    return f'{texture.capitalize()}. {body[0].upper()}{body[1:]}'



def descent(zone: str, index: int = 0) -> str:
    options = DESCENT.get(zone)
    return options[index % len(options)] if options else ''


def pressure(before: float, after: float) -> str:
    """The first threshold crossed by this tick, if any.

    Returns one line at most: the trace is tense enough without narrating
    every point of it.
    """
    for threshold, text in TRACE_PRESSURE:
        if before < threshold <= after:
            return text
    return ''
