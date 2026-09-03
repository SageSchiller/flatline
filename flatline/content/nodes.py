"""What a network is made of: node types, services, data, and their names.

**Zones give a network a readable shape.** A run is not a random mesh; it is
four concentric bands, and a player can always tell roughly how deep they are
and what it cost to get there. Chokepoints between zones are where wardens sit,
which is what makes depth feel earned rather than arbitrary.

Services are the attack surface. A node's services are what `crack` operates
on, and each one has a family, which is what makes Cryptography a different
skill from Intrusion rather than a synonym for it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Outermost to innermost. Access tier required rises with the index.
ZONES = ('perimeter', 'interior', 'restricted', 'core')

ZONE_BLURB = {
    'perimeter': 'Public-facing. Everything here expects strangers.',
    'interior': 'Staff side. Expects a badge and does not check it often.',
    'restricted': 'Expects a specific badge, and checks.',
    'core': 'Expects nobody. Everything here is an exception.',
}


@dataclass(frozen=True, slots=True)
class NodeType:
    key: str
    name: str
    blurb: str
    #: Zones this type can appear in.
    zones: tuple[str, ...]
    #: How many services it tends to run.
    services: tuple[int, int]
    #: Relative chance of carrying a data asset.
    data_chance: float
    #: Relative chance of hosting ICE, before posture scaling.
    ice_chance: float
    #: Multiplier on noise generated here. Busy nodes hide you.
    noise_mult: float = 1.0


NODE_TYPES: tuple[NodeType, ...] = (
    NodeType('gateway', 'gateway',
             'The way in. Everything passes through it and it remembers none '
             'of it for long.',
             zones=('perimeter',), services=(2, 3), data_chance=0.05,
             ice_chance=0.5, noise_mult=0.8),
    NodeType('relay', 'relay',
             'Moves traffic between segments. Quiet, dull, and an excellent '
             'place to stand while you work out where you are.',
             zones=('perimeter', 'interior'), services=(1, 2), data_chance=0.1,
             ice_chance=0.3, noise_mult=0.7),
    NodeType('workstation', 'workstation',
             'Somebody\'s desk. Badly patched, full of credentials, and '
             'logged in at all hours by people with no idea.',
             zones=('perimeter', 'interior'), services=(2, 4), data_chance=0.4,
             ice_chance=0.25, noise_mult=1.2),
    NodeType('fileserver', 'fileserver',
             'Bulk storage. The unglamorous place most of the actually '
             'valuable material turns out to live.',
             zones=('interior', 'restricted'), services=(2, 3), data_chance=0.85,
             ice_chance=0.5),
    NodeType('controller', 'controller',
             'Runs something physical, or runs the people who do. Access here '
             'is worth more than the data on it.',
             zones=('interior', 'restricted'), services=(3, 4), data_chance=0.3,
             ice_chance=0.7, noise_mult=1.1),
    NodeType('auth', 'auth server',
             'Issues the credentials everything else trusts. Breaking it is '
             'slow and it pays for the entire rest of the run.',
             zones=('interior', 'restricted'), services=(3, 5), data_chance=0.25,
             ice_chance=0.8, noise_mult=1.3),
    NodeType('vault', 'vault',
             'What the network is for. Encrypted, watched, and worth the trip.',
             zones=('restricted', 'core'), services=(2, 3), data_chance=1.0,
             ice_chance=1.0, noise_mult=1.4),
    NodeType('honeypot', 'workstation',
             'Presents as a soft target because that is the entire idea. Reads '
             'as a workstation until you are standing in it.',
             zones=('interior', 'restricted'), services=(3, 4), data_chance=0.6,
             ice_chance=0.2, noise_mult=1.0),
)

BY_KEY: dict[str, NodeType] = {n.key: n for n in NODE_TYPES}

#: One-cell glyphs per host type, so a scan reads as a shape and not only a
#: word. Keyed by the *display* name, which means a disguised honeypot borrows
#: the workstation glyph and gives nothing away until it is unmasked (D111).
#: Each entry is (unicode, ascii) so a plain terminal still gets a marker.
HOST_GLYPHS: dict[str, tuple[str, str]] = {
    'gateway': ('⊟', '>'),
    'relay': ('◇', '-'),
    'workstation': ('⌂', '.'),
    'fileserver': ('▤', '='),
    'controller': ('◎', '*'),
    'auth server': ('▦', '#'),
    'vault': ('▣', 'X'),
}


def host_glyph(display_name: str, ascii_only: bool = False) -> str:
    """The one-cell mark for a host as the player sees it. Unknown types get a
    neutral dot rather than nothing, so the column never goes ragged."""
    pair = HOST_GLYPHS.get(display_name)
    if pair is None:
        return '.' if ascii_only else '·'
    return pair[1] if ascii_only else pair[0]



# --------------------------------------------------------------------------
# services
# --------------------------------------------------------------------------

#: family -> which skill and program category answer it. This is the whole
#: reason a build carrying only breakers hits a wall at the vault door.
FAMILIES: dict[str, tuple[str, str]] = {
    'access': ('intrusion', 'breaker'),
    'crypto': ('cryptography', 'breaker'),
    'identity': ('subterfuge', 'forger'),
    'physical': ('hardware', 'breaker'),
}


@dataclass(frozen=True, slots=True)
class Service:
    key: str
    name: str
    family: str
    #: Base difficulty at posture 50, before scaling.
    difficulty: tuple[int, int]
    blurb: str
    #: Noise multiplier for cracking this specifically.
    noise: float = 1.0


SERVICES: tuple[Service, ...] = (
    Service('shell', 'remote shell', 'access', (2, 4),
            'An interactive session, if you can get one.'),
    Service('rpc', 'management rpc', 'access', (3, 5),
            'Administrative endpoints that were never meant to face anything.'),
    Service('webapp', 'web application', 'access', (1, 3),
            'Written in a hurry, four years ago, by somebody who has left.',
            noise=0.8),
    Service('share', 'file share', 'access', (2, 3),
            'Open to more of the organisation than anybody intended.',
            noise=0.9),
    Service('vpn', 'tunnel endpoint', 'crypto', (4, 6),
            'Cryptographically sound and operationally hopeless.'),
    Service('keystore', 'key store', 'crypto', (5, 7),
            'Where the keys live. Naturally it is also a service.',
            noise=1.2),
    Service('cipher', 'encrypted volume', 'crypto', (4, 7),
            'Sealed properly. This one is going to take a while.'),
    Service('sso', 'identity provider', 'identity', (4, 6),
            'Trusts a badge. The badge is the attack surface.'),
    Service('directory', 'directory service', 'identity', (3, 5),
            'Knows who everybody is, which is more useful than it sounds.',
            noise=0.9),
    Service('badge', 'badge reader', 'physical', (2, 4),
            'A door with an opinion. Physically present, digitally naive.',
            noise=0.7),
    Service('bms', 'building management', 'physical', (3, 5),
            'Runs the lights, the doors, and the air. Nobody patches it.',
            noise=1.1),
    Service('queue', 'message queue', 'access', (3, 4),
            'Everything the network says to itself, in order, with retries.',
            noise=0.85),
    Service('sign', 'signing service', 'crypto', (5, 8),
            'Vouches for other things. Break it and the network vouches for '
            'you.',
            noise=1.3),
    Service('roster', 'staff roster', 'identity', (2, 4),
            'Who is on shift, and therefore who is not going to be missed.',
            noise=0.8),
    Service('scada', 'process control', 'physical', (4, 6),
            'Runs something with moving parts. Written in a decade that did '
            'not have a threat model.',
            noise=1.2),
)

SERVICE_BY_KEY: dict[str, Service] = {s.key: s for s in SERVICES}


def services_for(node_type: str) -> list[Service]:
    """Which services plausibly run on which node type.

    Hard-coded rather than random because a badge reader on a fileserver reads
    as a bug even when it is not, and plausibility is most of what makes a
    generated network feel authored.
    """
    table = {
        'gateway': ('webapp', 'vpn', 'shell', 'queue'),
        'relay': ('shell', 'rpc', 'queue'),
        'workstation': ('shell', 'share', 'webapp', 'badge', 'roster'),
        'fileserver': ('share', 'cipher', 'shell', 'queue'),
        'controller': ('rpc', 'bms', 'badge', 'shell', 'scada'),
        'auth': ('sso', 'directory', 'keystore', 'rpc', 'roster', 'sign'),
        'vault': ('cipher', 'keystore', 'share', 'sign'),
        'honeypot': ('shell', 'share', 'webapp', 'rpc', 'roster'),
    }
    return [SERVICE_BY_KEY[k] for k in table.get(node_type, ('shell',))]


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DataKind:
    key: str
    name: str
    #: Base value in credits at posture 50.
    value: tuple[int, int]
    #: Whether it needs a Cryptography check on top of node access.
    encrypted: bool
    blurb: str


DATA_KINDS: tuple[DataKind, ...] = (
    DataKind('personnel', 'personnel records', (200, 600), False,
             'Names, addresses, and who reports to whom. Sells to everybody.'),
    DataKind('financial', 'financial ledgers', (600, 1600), True,
             'What was actually spent, as opposed to what was reported.'),
    DataKind('research', 'research data', (1200, 3200), True,
             'The thing they are for. Buyers are specific and they pay.'),
    DataKind('schematics', 'hardware schematics', (900, 2400), True,
             'How the thing is built, which is worth more than the thing.'),
    DataKind('correspondence', 'internal correspondence', (300, 900), False,
             'People being honest in writing, which they should know better than.'),
    DataKind('credentials', 'credential cache', (400, 1100), True,
             'Keys to somewhere else. Sometimes worth more as a door.'),
    DataKind('surveillance', 'surveillance archive', (500, 1400), False,
             'Who was where. Fixers and gangs both pay well for this.'),
    DataKind('contracts', 'contract archive', (700, 1900), True,
             'Who is being paid to do what to whom.'),
)

DATA_BY_KEY: dict[str, DataKind] = {d.key: d for d in DATA_KINDS}


# --------------------------------------------------------------------------
# names
# --------------------------------------------------------------------------

#: Hostname parts. Corporate networks are named by committee and it shows.
HOST_PREFIX = (
    'ap', 'bk', 'cn', 'dx', 'ed', 'fl', 'gm', 'hd', 'ix', 'jr',
    'kp', 'lm', 'nv', 'or', 'pq', 'rs', 'tv', 'wx',
)
HOST_ROLE = (
    'app', 'db', 'fs', 'auth', 'ctl', 'gw', 'rly', 'ops', 'lab', 'arc',
    'mail', 'bld', 'sec', 'net', 'dev', 'prd',
)
#: Who names the machines, and what that sounds like (D73).
#:
#: A corporation runs an asset register and its hosts are entries in it.
#: Everybody else names a box the way people name a thing they have to
#: live with, and what they reach for says what they are: a gang uses the
#: names it shouts across a room, the docks use the language of the rota,
#: the Chorus uses the hours of the office, Static uses the print floor,
#: Nightwatch uses the register, Switchboard is a telephone exchange and
#: has never pretended otherwise, and whatever Deepwater is, it is not
#: made of offices.
#:
#: One pool per faction kind. Anything without a pool gets the corporate
#: scheme, which is the register.
HOST_NAMES: dict[str, tuple[str, ...]] = {
    'gang': (
        'tommy', 'vic', 'nan', 'bishop', 'hatchet', 'tallboy', 'mule',
        'tenner', 'knuckle', 'cousin', 'jackdaw', 'tooth', 'remy',
        'backhand', 'bruiser', 'dodger', 'weasel', 'muggins', 'nutmeg',
        'sixer',
    ),
    'collective': (
        'berth', 'muster', 'tally', 'quorum', 'picket', 'shanty',
        'longshore', 'deckhand', 'purser', 'bosun', 'hawser', 'jetty',
        'slipway', 'chandler', 'mess', 'nightgang', 'tideboard',
        'dunnage', 'crewroom', 'ropewalk',
    ),
    'cult': (
        'matins', 'lauds', 'compline', 'litany', 'cantor', 'censer',
        'novice', 'antiphon', 'kyrie', 'sexton', 'narthex', 'chancel',
        'oblate', 'plainsong', 'introit', 'canticle', 'sanctus',
        'thurible', 'precentor', 'cloister',
    ),
    'press': (
        'carrier', 'mast', 'dial', 'lede', 'galley', 'splice', 'offcut',
        'bulletin', 'nightdesk', 'byline', 'deadline', 'pressroom',
        'proof', 'slug', 'spike', 'masthead', 'kicker', 'standfirst',
        'deadair', 'cutaway',
    ),
    'law': (
        'docket', 'ward', 'warrant', 'custody', 'remand', 'exhibit',
        'caution', 'summons', 'bailiff', 'casefile', 'chargesheet',
        'watchhouse', 'cellblock', 'register', 'incident', 'disposal',
        'callsign', 'nightturn', 'holdingroom', 'sergeant',
    ),
    'broker': (
        'patch', 'trunk', 'extension', 'operator', 'tieline', 'junction',
        'exchange', 'ringdown', 'switchroom', 'dialtone', 'crossbar',
        'handset', 'subscriber', 'toll', 'party', 'relayroom', 'splitter',
        'tandem', 'terminus', 'loopback',
    ),
    'construct': (
        'fathom', 'trench', 'silt', 'drift', 'hadal', 'nekton', 'anemone',
        'gulper', 'viperfish', 'isopod', 'brine', 'thermocline',
        'midwater', 'scattering', 'deadzone', 'downwelling', 'halocline',
        'sounding', 'abyssal', 'marianas',
    ),
}

#: And where a faction's own character is sharper than its kind's. The
#: Sixes and Carrion are both gangs and do not sound alike: one is six
#: blocks that grew, and the other is organised around chrome the way a
#: cult is organised around a god, and names its machines accordingly.
HOST_NAMES_BY_FACTION: dict[str, tuple[str, ...]] = {
    'carrion': (
        'gristle', 'donor', 'sawbones', 'graft', 'stump', 'splint',
        'cadaver', 'tourniquet', 'meathook', 'ossuary', 'scrapheap',
        'spares', 'harvest', 'transplant', 'rejection', 'necrosis',
        'sepsis', 'triage', 'coldstore', 'offcuts',
    ),
}

