"""Procedural network generation.

Networks are grown in four concentric **zones** rather than as a random graph.
That single choice does most of the work of making a generated network feel
authored: depth is legible, chokepoints are meaningful, and a player can always
answer "how deep am I and what did it cost" without a map.

Everything here is driven by one `rng.Stream`, forked per contract, so a given
contract's network is identical whether you run it now or eight shifts from
now, and whether or not you looked at another contract first. That property is
load-bearing for legwork: intel bought on shift 3 has to still be true on
shift 6, and it is only true because generation never touches shared state.

**Posture** is the difficulty dial and it comes from the city layer. Everything
scales off it: node counts, service difficulty, ICE density and rating. A
faction you have robbed four times generates a visibly meaner network, and that
is the main channel through which the persistent layer is felt during a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..content import factions, ice as ice_content, nodes as node_content
from ..rng import Stream
from .. import ui

#: Access tier required per zone. The player's tier starts at 0.
ZONE_TIER = {'perimeter': 0, 'interior': 1, 'restricted': 2, 'core': 3}


@dataclass(slots=True)
class ServiceInstance:
    key: str
    difficulty: int
    cracked: bool = False

    @property
    def data(self) -> node_content.Service:
        return node_content.SERVICE_BY_KEY[self.key]

    @property
    def family(self) -> str:
        return self.data.family


@dataclass(slots=True)
class IceInstance:
    uid: str
    key: str
    rating: int
    #: dormant -> awake -> locked, or dead. Traps go dormant -> sprung.
    state: str = 'dormant'
    #: Set when a tell has been printed and the strike is due next tick.
    telegraphed: bool = False
    #: Ticks it has held the strike back since the tell, for `tell_lead`.
    warned: int = 0
    damage_taken: int = 0
    #: True once the player has identified it (probe, Auspex, or ex-cop eye).
    known: bool = False

    @property
    def data(self) -> ice_content.IceType:
        return ice_content.BY_KEY[self.key]

    @property
    def behaviour(self) -> str:
        return self.data.behaviour

    @property
    def alive(self) -> bool:
        return self.state != 'dead'

    @property
    def hp(self) -> int:
        return self.rating * 4


@dataclass(slots=True)
class DataAsset:
    uid: str
    kind: str
    value: int
    encrypted: bool
    taken: bool = False
    #: Set when the contract is about this specific asset.
    objective: bool = False
    #: What a scene called it, when it did. Overrides the kind's name
    #: everywhere the asset is named (D52).
    label: str = ''

    @property
    def data(self) -> node_content.DataKind:
        return node_content.DATA_BY_KEY[self.kind]

    @property
    def name(self) -> str:
        return self.label or self.data.name


@dataclass(slots=True)
class Node:
    uid: str
    type: str
    zone: str
    services: list[ServiceInstance] = field(default_factory=list)
    ice: list[IceInstance] = field(default_factory=list)
    data: list[DataAsset] = field(default_factory=list)
    edges: list[str] = field(default_factory=list)

    # -- live state --------------------------------------------------------
    #: Seen on a scan. Type is known, contents are not.
    known: bool = False
    #: Services and data enumerated.
    mapped: bool = False
    #: Access obtained. You can stand here.
    open: bool = False
    #: Local suspicion, decays each tick.
    noise: int = 0
    #: Evidence left here, per D5. Survives the run.
    residue: int = 0
    #: True for honeypots the player has not yet identified as such.
    disguised: bool = True

    @property
    def data_type(self) -> node_content.NodeType:
        return node_content.BY_KEY[self.type]

    @property
    def tier(self) -> int:
        return ZONE_TIER[self.zone]

    @property
    def display_type(self) -> str:
        """What the player sees. A honeypot lies until it is identified."""
        if self.type == 'honeypot' and self.disguised:
            return 'workstation'
        return self.data_type.name

    @property
    def live_ice(self) -> list[IceInstance]:
        return [i for i in self.ice if i.alive]

    def service(self, key: str) -> ServiceInstance | None:
        return next((s for s in self.services if s.key == key), None)

    @property
    def cracked_all(self) -> bool:
        return all(s.cracked for s in self.services)


#: The shapes a network can take (D64 a), and what each does to the edges.
#: A layered net is the standard four concentric zones; a spine is one long
#: corridor; a ring closes each zone into a loop with two ways round; a hub
#: hangs each zone off one host, which is where the wardens stand; a mesh is
#: everything joined to everything near it; a split forks the deep zones
#: into two wings, and the job is in one of them. Which shapes a faction
#: builds is doctrine (`SHAPE_WEIGHTS`), so a Sixes phone tree is a hub and
#: Deepwater is a mesh nobody drew.
SHAPES: dict[str, str] = {
    'layered': 'layered, four rings deep',
    'spine': 'a spine, one long corridor in',
    'ring': 'a ring, two ways round every zone',
    'hub': 'a hub and spokes, everything through one host per zone',
    'mesh': 'a mesh, joined every way it could be',
    'split': 'split, two wings past the interior',
}

SHAPE_WEIGHTS: dict[str, dict[str, float]] = {
    'corp': {'layered': 3.0, 'spine': 1.2, 'ring': 0.8, 'split': 1.0},
    'law': {'layered': 2.0, 'ring': 2.0, 'hub': 0.6},
    'broker': {'hub': 2.5, 'layered': 1.0},
    'collective': {'ring': 2.0, 'mesh': 1.5, 'layered': 1.0},
    'gang': {'hub': 3.0, 'spine': 1.0, 'mesh': 0.8},
    'cult': {'hub': 2.0, 'spine': 1.5, 'layered': 0.8},
    'press': {'mesh': 3.0, 'ring': 1.0},
    'construct': {'mesh': 3.0, 'split': 1.5},
}
SHAPE_BY_FACTION: dict[str, dict[str, float]] = {
    'aoyama': {'split': 3.0, 'layered': 1.5, 'ring': 0.5},
    'meridian': {'spine': 3.0, 'layered': 1.0},
    'sendai': {'spine': 2.0, 'layered': 2.0, 'split': 0.8},
}


@dataclass(slots=True)
class Network:
    faction: str
    posture: int
    nodes: dict[str, Node] = field(default_factory=dict)
    entry: str = ''
    #: Which of `SHAPES` this one is.
    shape: str = 'layered'

    @property
    def crowd(self) -> float:
        """Trace multiplier from the size of the place (D66)."""
        n = len(self.nodes)
        return max(CROWD_FLOOR,
                   min(CROWD_CEILING, 1.0 - (n - CROWD_AT) * CROWD_PER_HOST))
    #: uid of the asset the contract is about, when there is one.
    objective_asset: str = ''
    objective_node: str = ''

    def node(self, uid: str) -> Node | None:
        return self.nodes.get(uid)

    def neighbours(self, uid: str) -> list[Node]:
        n = self.nodes.get(uid)
        return [self.nodes[e] for e in (n.edges if n else []) if e in self.nodes]

    def find_asset(self, uid: str) -> tuple[Node, DataAsset] | None:
        for node in self.nodes.values():
            for asset in node.data:
                if asset.uid == uid:
                    return node, asset
        return None


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------

#: Nodes per zone at posture 50, before scaling. Perimeter is deliberately
#: narrow: a wide front door makes the opening of every run identical.
ZONE_SIZE = {
    'perimeter': (2, 3),
    'interior': (3, 5),
    'restricted': (2, 4),
    'core': (1, 2),
}

#: How much of a contract's size reaches each zone (D66). A bigger job is a
#: bigger *front*: more ways in, more hosts that are not the job, more to
#: find. It is not a deeper one. Depth is ticks and ticks are trace, and
#: measuring it showed what that costs: a large job at corporate posture
#: finished nought times in twenty-four, because the only thing size did
#: was add a fifth of the run to the walk. Breadth is choices; depth is a
#: countdown.
SIZE_REACH = {
    'perimeter': 1.0,
    'interior': 1.0,
    'restricted': 0.4,
    'core': 0.0,
}

#: Trace per tick is scaled by how much traffic there is to be lost in
#: (D66). Ten thousand legitimate sessions is the best mask money cannot
#: buy, and the manual has said so for months; this is the number under it.
#: A twenty-host network runs the clock about a fifth slower than an
#: eight-host one, which is what makes a big job worth the walk.
CROWD_AT = 10
CROWD_PER_HOST = 0.018
CROWD_FLOOR = 0.78
CROWD_CEILING = 1.10


def generate(rng: Stream, faction: str, posture: int,
             objective: str = 'exfiltrate', size_mod: float = 1.0) -> Network:
    """Build a network. Deterministic given `rng`, `faction`, and `posture`."""
    fac = factions.BY_KEY[faction]
    scale = posture / 50.0
    net = Network(faction=faction, posture=posture)

    informal = fac.kind in ('gang', 'collective')
    used_names: set[str] = set()

    def hostname() -> str:
        for _ in range(50):
            if informal:
                name = rng.pick(node_content.INFORMAL_HOSTS)
                if rng.chance(0.4):
                    name = f'{name}{rng.int(1, 9)}'
            else:
                name = (f'{rng.pick(node_content.HOST_PREFIX)}-'
                        f'{rng.pick(node_content.HOST_ROLE)}'
                        f'{rng.int(1, 29):02d}')
            if name not in used_names:
                used_names.add(name)
                return name
        # Exhausting the space is not a real risk at these sizes, but a
        # generator that can loop forever is a generator that eventually will.
        name = f'node{len(used_names):03d}'
        used_names.add(name)
        return name

    # -- nodes by zone -----------------------------------------------------
    by_zone: dict[str, list[Node]] = {}
    for zone in node_content.ZONES:
        lo, hi = ZONE_SIZE[zone]
        # Size reaches the front of a network and barely reaches the back.
        reach = 1.0 + (size_mod - 1.0) * SIZE_REACH[zone]
        count = max(1, int(round(rng.curve(lo, hi, 0.5) * reach
                                 * (0.85 + 0.3 * scale))))
        candidates = [n for n in node_content.NODE_TYPES if zone in n.zones]
        zone_nodes: list[Node] = []
        for _ in range(count):
            weights = {n.key: 1.0 for n in candidates}
            # Honeypots scale hard with posture: a paranoid target invests in
            # them, a gang does not.
            if 'honeypot' in weights:
                weights['honeypot'] = 0.8 * scale if fac.kind == 'corp' else 0.2
            if 'vault' in weights:
                # Aoyama's doctrine: a lot of small vaults (D63 b).
                weights['vault'] = ((2.5 if zone == 'core' else 0.6)
                                    * fac.style.get('vaults', 1.0))
            pick = rng.weighted(weights)
            zone_nodes.append(Node(uid=hostname(), type=pick, zone=zone))
        by_zone[zone] = zone_nodes
        for n in zone_nodes:
            net.nodes[n.uid] = n

    # -- edges -------------------------------------------------------------
    # The shape decides the edges (D64 a). Layered is the standard: within a
    # zone a spanning path plus a few extras, between zones one or two
    # chokepoints. The others bend that.
    net.shape = _pick_shape(rng, fac)
    _wire(rng, net.shape, by_zone, scale)

    # -- entry -------------------------------------------------------------
    perimeter = by_zone['perimeter']
    entry = next((n for n in perimeter if n.type == 'gateway'), perimeter[0])
    net.entry = entry.uid
    entry.known = True
    entry.open = True
    entry.mapped = True

    # -- services ----------------------------------------------------------
    for node in net.nodes.values():
        pool = node_content.services_for(node.type)
        lo, hi = node.data_type.services
        count = min(len(pool), rng.curve(lo, hi, 0.5))
        for svc in rng.sample(pool, count):
            dlo, dhi = svc.difficulty
            # D67: posture decides how well the thing is actually built,
            # and the old curve barely bent. At a gang's posture it came
            # out at 0.96, so the Sixes' vault ran the same signing
            # service as Kagawa's, which is not what "a phone tree with
            # delusions" means and made the first job in the game one a
            # starting deck could not open. Now a gang is genuinely soft
            # and a bank is genuinely not.
            diff = rng.int(dlo, dhi) * (0.45 + 0.78 * scale)
            if svc.family == 'crypto':
                # Meridian's doctrine: the keys are the thing (D63 b).
                diff *= fac.style.get('crypto', 1.0)
            diff = max(1, int(round(diff)))
            node.services.append(ServiceInstance(key=svc.key, difficulty=diff))
        # The entry node is already yours; its services are not a puzzle.
        if node.uid == net.entry:
            for s in node.services:
                s.cracked = True

    # -- ice ---------------------------------------------------------------
    # Density is the main thing that makes one faction's networks feel unlike
    # another's, so it is driven by doctrine as well as by posture. A gang at
    # posture 22 has to read as genuinely empty next to a corp at 45, or the
    # faction descriptions are writing cheques the generator does not honour.
    uid = 0
    kind_density = {
        'corp': 1.15,
        'law': 1.0,
        'broker': 0.9,
        'collective': 0.8,
        'gang': 0.55,
        # A cult defends devotionally: fewer constructs, and the ones there
        # are do not leave.
        'cult': 0.75,
        # A pirate press has almost nothing worth defending and knows it.
        'press': 0.4,
        # Deepwater is not defended, it is inhabited.
        'construct': 1.3,
    }[fac.kind]
    style = fac.style
    for node in net.nodes.values():
        if node.uid == net.entry:
            continue
        chance = (node.data_type.ice_chance * (0.35 + 0.95 * scale)
                  * kind_density * style.get('density', 1.0))
        # Deeper zones are meaner regardless of posture.
        chance *= {'perimeter': 0.6, 'interior': 0.9,
                   'restricted': 1.15, 'core': 1.4}[node.zone]
        count = 0
        while count < 3 and rng.chance(min(0.9, chance)):
            count += 1
            chance *= 0.35
        for _ in range(count):
            behaviour = _pick_behaviour(rng, node, scale, style)
            pool = ice_content.available(behaviour, faction)
            if not pool and behaviour == 'black':
                # D63 b: seven factions have no lethal construct of their
                # own, and the fallback used to hand them everybody else's.
                # A Sixes vault does not get an Undertow; it gets a hunter.
                behaviour = 'hunter'
                pool = ice_content.available(behaviour, faction)
            if not pool:
                pool = ice_content.by_behaviour(behaviour)
            it = rng.pick(pool)
            lo, hi = it.rating
            rating = max(1, int(round(rng.int(lo, hi) * (0.75 + 0.5 * scale))))
            uid += 1
            node.ice.append(IceInstance(uid=f'{it.key}-{uid}', key=it.key,
                                        rating=rating))

    # -- wardens on chokepoints -------------------------------------------
    # A boundary node with no warden is a boundary that does not read as one.
    for outer, inner in zip(node_content.ZONES, node_content.ZONES[1:]):
        for node in by_zone[inner]:
            if not any(net.nodes[e].zone == outer for e in node.edges
                       if e in net.nodes):
                continue
            if any(i.behaviour == 'warden' for i in node.ice):
                continue
            # Not every boundary is guarded. A gang's "restricted zone" is a
            # back room with a door on it, and putting a Chamberlain on it
            # would make every faction's network feel like the same network.
            warden_chance = (min(0.95, 0.25 + 0.6 * scale) * kind_density
                             * style.get('wardens', 1.0))
            if inner == 'interior':
                warden_chance *= 0.55  # the first boundary is often soft
            if not rng.chance(warden_chance):
                continue
            pool = ice_content.available('warden', faction)
            it = rng.pick(pool)
            lo, hi = it.rating
            rating = max(1, int(round(rng.int(lo, hi) * (0.75 + 0.5 * scale))))
            uid += 1
            node.ice.append(IceInstance(uid=f'{it.key}-{uid}', key=it.key,
                                        rating=rating))

    # -- data --------------------------------------------------------------
    asset_uid = 0
    for node in net.nodes.values():
        if not rng.chance(node.data_type.data_chance):
            continue
        depth = {'perimeter': 0.55, 'interior': 0.85,
                 'restricted': 1.2, 'core': 1.8}[node.zone]
        count = 2 if (node.type == 'vault' and rng.chance(0.5)) else 1
        for _ in range(count):
            kind = rng.weighted(_data_weights(node, fac))
            dk = node_content.DATA_BY_KEY[kind]
            lo, hi = dk.value
            value = int(round(rng.int(lo, hi) * depth * (0.8 + 0.5 * scale)))
            asset_uid += 1
            node.data.append(DataAsset(uid=f'asset-{asset_uid}', kind=kind,
                                       value=value, encrypted=dk.encrypted))

    # -- objective ---------------------------------------------------------
    _place_objective(rng, net, objective)
    _ensure_ladder(rng, net, scale)
    _signature(rng, net, fac)
    return net


#: What each faction's network *is*, past the knobs (D67). A style value
#: makes a network denser or quieter; these change its shape or its rules,
#: which is the difference between a faction that reads different and one
#: that is. Each is one sentence of doctrine the generator or the run
#: honours literally, and `check_factions` holds every declared signature
#: to being implemented.
SIGNATURES: dict[str, str] = {
    'deepwater': 'no perimeter: you arrive already inside it',
    'freeport': 'audited in public: the whole topology is known from the '
                'first tick',
    'static': 'mirrored: the thing you came for exists twice',
    'meridian': 'everything is sealed: the objective is always encrypted',
    'chorus': 'devotional: what wakes here does not go back to sleep',
    'nightwatch': 'response, not prevention: something arrives when the '
                  'room turns red',
}


def _signature(rng: Stream, net: Network, fac: factions.Faction) -> None:
    """Apply the faction's structural signature.

    The generation half. The run half lives in `RunState` and reads
    `net.faction` for the same keys.
    """
    if fac.key == 'deepwater':
        # No perimeter to speak of: the front of the network is not there
        # and you arrive somewhere that is already inside.
        inside = [n for n in net.nodes.values() if n.zone == 'interior']
        if inside:
            for node in [n for n in net.nodes.values()
                         if n.zone == 'perimeter']:
                node.zone = 'interior'
            entry = rng.pick(inside)
            net.entry = entry.uid
            entry.known = entry.open = entry.mapped = True
    if fac.key == 'freeport':
        # Genuinely open, genuinely audited. You can see all of it. Seeing
        # it and being able to walk it are different things.
        for node in net.nodes.values():
            node.known = True
    if fac.key == 'static':
        # Mirrored eleven times, and one of the mirrors is reachable.
        found = net.find_asset(net.objective_asset)
        if found:
            node, asset = found
            others = [n for n in net.nodes.values()
                      if n.uid != node.uid
                      and n.zone in ('interior', 'restricted')]
            if others:
                twin = rng.pick(others)
                twin.data.append(DataAsset(
                    uid=f'{asset.uid}-mirror', kind=asset.kind,
                    value=asset.value, encrypted=asset.encrypted,
                    objective=True, label=asset.label))
    if fac.key == 'meridian':
        # The keys are the only thing they guard, so the thing you came for
        # is behind one.
        found = net.find_asset(net.objective_asset)
        if found:
            found[1].encrypted = True


def _ensure_ladder(rng: Stream, net: Network, scale: float) -> None:
    """A way up to the tier the job is behind (D64 c).

    Access tiers are a penalty, not a wall: three points on every attempt
    per tier you are short. Against a core objective that is nine, which no
    fresh build passes, and the only route up is a full crack of an auth
    server. A network whose only auth server sits at tier two therefore
    has no ladder at all for somebody standing at tier zero: the brief
    correctly says jack out, and it says it on every run.

    So: any network whose objective is tier two or deeper has an auth
    server at tier one, promoting an interior host if the roll did not
    produce one. Interior rather than perimeter because that is where the
    content says an auth server lives, and one tier short is three points,
    which is a decision rather than a wall.
    """
    objective = net.node(net.objective_node)
    if objective is None or objective.tier < 2:
        return
    if any(n.type == 'auth' and n.tier <= 1 for n in net.nodes.values()):
        return
    pool = [n for n in net.nodes.values()
            if n.zone == 'interior' and n.uid != net.entry
            and n.uid != net.objective_node and n.type != 'honeypot']
    if not pool:
        return
    node = rng.pick(pool)
    node.type = 'auth'
    node.services = []
    kinds = node_content.services_for('auth')
    lo, hi = node_content.BY_KEY['auth'].services
    count = min(len(kinds), rng.curve(lo, hi, 0.5))
    for svc in rng.sample(kinds, count):
        dlo, dhi = svc.difficulty
        node.services.append(ServiceInstance(
            key=svc.key,
            difficulty=max(1, int(round(rng.int(dlo, dhi)
                                        * (0.7 + 0.6 * scale))))))


def _pick_shape(rng: Stream, fac: factions.Faction) -> str:
    weights = dict(SHAPE_WEIGHTS.get(fac.kind, {'layered': 1.0}))
    weights.update(SHAPE_BY_FACTION.get(fac.key, {}))
    return rng.weighted(weights)


def _wire(rng: Stream, shape: str, by_zone: dict, scale: float) -> None:
    """Draw the edges for a shape. Repairs (`_ensure_reachable`) run after
    the objective is placed, so a shape only has to be a shape, not proof
    against its own corners."""
    zones = list(node_content.ZONES)
    hubs: dict[str, Node] = {}
    wings: dict[str, tuple[list, list]] = {}

    for zone in zones:
        group = by_zone[zone]
        if not group:
            continue
        if shape == 'hub':
            hub = rng.pick(group)
            hubs[zone] = hub
            for n in group:
                _link(hub, n)
            continue
        if shape == 'split' and zone in ('restricted', 'core') and len(group) >= 2:
            half = max(1, len(group) // 2)
            left, right = group[:half], group[half:]
            for part in (left, right):
                for a, b in zip(part, part[1:]):
                    _link(a, b)
            wings[zone] = (left, right)
            continue
        # chain
        for a, b in zip(group, group[1:]):
            _link(a, b)
        if shape == 'ring' and len(group) >= 3:
            _link(group[-1], group[0])
        extra = {'spine': 0, 'mesh': len(group) // 2 + 1}.get(shape, len(group) // 3)
        for _ in range(extra):
            a, b = rng.pick(group), rng.pick(group)
            if a is not b:
                _link(a, b)

    for outer, inner in zip(zones, zones[1:]):
        outs, ins = by_zone[outer], by_zone[inner]
        if not outs or not ins:
            continue
        if shape == 'hub':
            # Through the hub, which is where the boundary stands.
            _link(hubs.get(outer, rng.pick(outs)), hubs.get(inner, rng.pick(ins)))
            continue
        if shape == 'split' and inner in wings:
            left, right = wings[inner]
            if outer in wings:
                o_left, o_right = wings[outer]
                _link(rng.pick(o_left), rng.pick(left))
                _link(rng.pick(o_right), rng.pick(right))
            else:
                # Two doors out of the interior, one per wing.
                _link(rng.pick(outs), rng.pick(left))
                _link(rng.pick(outs), rng.pick(right))
            continue
        if shape == 'spine':
            count = 1
        elif shape == 'ring':
            count = 2 if len(ins) > 1 and len(outs) > 1 else 1
        elif shape == 'mesh':
            count = 3 if len(ins) > 2 else 2
        else:
            # Fewer chokepoints as posture rises: a hardened network funnels you.
            count = 2 if (scale < 1.1 and len(ins) > 1 and rng.chance(0.6)) else 1
        for _ in range(count):
            _link(rng.pick(outs), rng.pick(ins))


def _link(a: Node, b: Node) -> None:
    if a is b:
        return
    if b.uid not in a.edges:
        a.edges.append(b.uid)
    if a.uid not in b.edges:
        b.edges.append(a.uid)


def _pick_behaviour(rng: Stream, node: Node, scale: float,
                    style: dict | None = None) -> str:
    """Which kind of countermeasure fits this node.

    Weighted by node type rather than uniform, because a Coffin on a perimeter
    relay is not a difficulty spike, it is a bug the player can feel. The
    faction's style (D63 b) scales each behaviour, which is how Carrion is
    studded with traps and Nightwatch is watched rather than defended.
    """
    style = style or {}
    weights = {
        'sentry': 3.0,
        'probe': 1.4 * style.get('probes', 1.0),
        'hunter': 1.0 * scale * style.get('hunters', 1.0),
        'trap': 1.2 * style.get('traps', 1.0),
        'herder': 0.7 * style.get('herders', 1.0),
        'warden': 0.0,   # placed deliberately at chokepoints, never randomly
        'black': 0.0,
    }
    if node.zone in ('restricted', 'core'):
        weights['hunter'] *= 2.0
        weights['trap'] *= 1.3
        weights['herder'] *= 1.4
    if node.zone == 'core' or node.type == 'vault':
        weights['black'] = 1.1 * scale * style.get('black', 1.0)
    if node.type == 'honeypot':
        # Honeypots are soft on purpose, right up to the part that is not.
        weights = {'sentry': 4.0, 'trap': 2.5, 'probe': 0.5,
                   'hunter': 0.0, 'warden': 0.0, 'herder': 0.0,
                   'black': 0.0}
    return rng.weighted(weights)


def _data_weights(node: Node, fac: factions.Faction) -> dict[str, float]:
    weights = {k: 1.0 for k in node_content.DATA_BY_KEY}
    if fac.kind == 'corp':
        weights['research'] = 2.2
        weights['financial'] = 1.8
        weights['schematics'] = 1.6
        weights['surveillance'] = 0.5
    elif fac.kind == 'press':
        weights['correspondence'] = 2.6
        weights['contracts'] = 2.2
        weights['surveillance'] = 1.8
        weights['schematics'] = 0.2
    elif fac.kind == 'cult':
        weights['personnel'] = 2.4
        weights['research'] = 1.6
        weights['correspondence'] = 1.8
        weights['financial'] = 0.4
    elif fac.kind == 'construct':
        # Whatever Deepwater keeps, it is not keeping it for money.
        weights['research'] = 3.0
        weights['schematics'] = 2.0
        weights['credentials'] = 1.6
        weights['financial'] = 0.2
        weights['personnel'] = 0.3
    elif fac.kind == 'gang':
        weights['surveillance'] = 2.4
        weights['contracts'] = 2.0
        weights['research'] = 0.15
        weights['schematics'] = 0.3
    elif fac.kind == 'law':
        weights['surveillance'] = 2.6
        weights['personnel'] = 2.0
        weights['contracts'] = 1.6
        weights['research'] = 0.2
    if node.type == 'auth':
        weights['credentials'] = 4.0
    if node.type == 'vault':
        weights['research'] = weights.get('research', 1.0) * 2.0
        weights['financial'] = weights.get('financial', 1.0) * 1.6
    if node.type == 'workstation':
        weights['correspondence'] = 2.5
        weights['research'] = 0.4
    return weights


def _place_objective(rng: Stream, net: Network, objective: str) -> None:
    """Pick what the contract is about and make sure it is reachable.

    Reachability is not assumed. A network whose objective sits behind an edge
    the generator never drew is a run the player cannot finish, and that is
    the one generation bug that is completely unacceptable, so it is checked
    here and repaired rather than left to chance.
    """
    deep = [n for n in net.nodes.values() if n.zone in ('core', 'restricted')]
    if not deep:
        deep = list(net.nodes.values())

    if objective in ('exfiltrate', 'corrupt', 'wipe'):
        candidates = [(n, a) for n in deep for a in n.data]
        if not candidates:
            # Force one into existence rather than degrading the contract.
            node = max(deep, key=lambda n: (n.zone == 'core', len(n.services)))
            kind = rng.weighted(_data_weights(node, factions.BY_KEY[net.faction]))
            dk = node_content.DATA_BY_KEY[kind]
            asset = DataAsset(uid='asset-objective', kind=kind,
                              value=int(rng.int(*dk.value) * 1.6),
                              encrypted=dk.encrypted)
            node.data.append(asset)
            candidates = [(node, asset)]
        node, asset = max(candidates, key=lambda pair: pair[1].value)
        asset.objective = True
        net.objective_asset = asset.uid
        net.objective_node = node.uid
    else:
        # implant, surveil, escort: the objective is a place, not a thing.
        node = max(deep, key=lambda n: (n.zone == 'core', len(n.services)))
        net.objective_node = node.uid

    _ensure_reachable(net)
    # After the edges exist, because it walks them.
    _ensure_passable(net)
    _soften_route(net)


#: Wardens that cannot be answered with credentials. A warden is the one kind
#: of countermeasure that guards the *door* rather than the room, so you meet
#: it from the node next to it, and `strike` and `overload` only reach what is
#: on the node you are standing on or what has locked on to you. That leaves
#: exactly two counters to one of these, `pivot` at Intrusion 4 and going
#: round, and a new character has neither.
def _is_wall(node: Node) -> bool:
    return any(i.behaviour == 'warden' and i.alive
               and not i.data.effects.get('credential_check')
               for i in node.ice)


#: The highest rating a credential warden keeps on the one route
#: `_ensure_passable` opens (D63 b).
SOFT_WARDEN = 4


def _ensure_passable(net: Network) -> None:
    """A route to the objective that does not need a technique to walk.

    `_ensure_reachable` guarantees the edges exist. It does not guarantee you
    can use them, and those are different promises: a Gatekeeper on every
    route to the objective is a run that cannot be finished by anybody who has
    not bought Intrusion rank 4, which is every new character and most old
    ones. Before this, seven networks in ten were shaped that way.

    The repair is to open one route rather than to remove every wall. Wardens
    keep the shortcuts, the deep alternatives, and everything that is not the
    one path this walks, so the build that can break them still gets paid for
    it in ticks saved rather than in runs that finish at all.
    """
    objective = net.objective_node
    if not objective or objective not in net.nodes:
        return
    walls = {uid for uid, node in net.nodes.items() if _is_wall(node)}
    if not walls:
        return

    # Breadth-first from the entry, refusing to enter a wall. If that finds
    # the objective, some route is already walkable and nothing needs doing.
    def open_route() -> bool:
        seen = {net.entry}
        queue = [net.entry]
        while queue:
            uid = queue.pop(0)
            for edge in net.nodes[uid].edges:
                if edge in seen or edge not in net.nodes or edge in walls:
                    continue
                if edge == objective:
                    return True
                seen.add(edge)
                queue.append(edge)
        return objective == net.entry or objective in seen

    while not open_route():
        # Take the wall nearest the front door on the shortest path to the
        # objective and stand it down. Nearest rather than any, so the repair
        # opens the route a player would have taken anyway.
        blocking = _first_wall_on_route(net, objective, walls)
        if blocking is None:
            return
        for construct in net.nodes[blocking].ice:
            if (construct.behaviour == 'warden'
                    and not construct.data.effects.get('credential_check')):
                construct.state = 'dead'
        walls.discard(blocking)


def _soften_route(net: Network) -> None:
    """D63 b: the same promise for the builds that cannot present a badge.

    A credential warden at rating 8 is resistance 18, which no fresh runner
    and few old ones beat without a forger, so on the one route a player
    would walk (the shortest one that needs no technique) the wardens are
    capped at `SOFT_WARDEN`: a cheap Handshake answers them, and everything
    off that route keeps its rating."""
    objective = net.objective_node
    if not objective or objective not in net.nodes:
        return
    walls = {uid for uid, node in net.nodes.items() if _is_wall(node)}
    for uid in _route(net, objective, avoid=walls) or _route(net, objective):
        for construct in net.nodes[uid].ice:
            if (construct.behaviour == 'warden' and construct.alive
                    and construct.data.effects.get('credential_check')
                    and construct.rating > SOFT_WARDEN):
                construct.rating = SOFT_WARDEN


def _route(net: Network, objective: str, avoid=()) -> list[str]:
    """The shortest route from the entry to the objective that does not
    pass through `avoid`, as host uids, or [] if there is none."""
    parent: dict[str, str] = {net.entry: ''}
    queue = [net.entry]
    while queue:
        uid = queue.pop(0)
        if uid == objective:
            path = [uid]
            while parent[path[-1]]:
                path.append(parent[path[-1]])
            return path
        for edge in net.nodes[uid].edges:
            if edge in parent or edge not in net.nodes:
                continue
            if edge in avoid and edge != objective:
                continue
            parent[edge] = uid
            queue.append(edge)
    return []


def _first_wall_on_route(net: Network, objective: str,
                         walls: set[str]) -> str | None:
    """The first walled host on the shortest route from the entry."""
    parent: dict[str, str] = {net.entry: ''}
    queue = [net.entry]
    while queue:
        uid = queue.pop(0)
        if uid == objective:
            path = [uid]
            while parent[path[-1]]:
                path.append(parent[path[-1]])
            for step in reversed(path):
                if step in walls:
                    return step
            return None
        for edge in net.nodes[uid].edges:
            if edge in parent or edge not in net.nodes:
                continue
            parent[edge] = uid
            queue.append(edge)
    return None


def _ensure_reachable(net: Network) -> None:
    """Every node must be reachable from the entry. Repair, do not assert."""
    seen = {net.entry}
    frontier = [net.entry]
    while frontier:
        uid = frontier.pop()
        for edge in net.nodes[uid].edges:
            if edge in net.nodes and edge not in seen:
                seen.add(edge)
                frontier.append(edge)

    orphans = [n for uid, n in net.nodes.items() if uid not in seen]
    if not orphans:
        return
    # Attach each orphan to the shallowest reachable node, which keeps the
    # zone shape intact rather than wiring a core node to the front door.
    reachable = [net.nodes[u] for u in seen]
    for orphan in orphans:
        target = min(reachable,
                     key=lambda n: abs(ZONE_TIER[n.zone] - ZONE_TIER[orphan.zone]))
        _link(orphan, target)
        seen.add(orphan.uid)
        reachable.append(orphan)


# --------------------------------------------------------------------------
# drawing
# --------------------------------------------------------------------------


def adjacency(net: Network) -> dict[str, list[str]]:
    """The network as a plain graph, which is all the drawing needs."""
    return {uid: list(node.edges) for uid, node in net.nodes.items()}


def spanning_tree(net: Network, root: str,
                  visible: set[str]) -> tuple[dict[str, list[str]],
                                              dict[str, list[str]]]:
    """The known part of the network, as a tree from `root`. See `ui`."""
    return ui.spanning_tree(adjacency(net), root, visible)


def tree_rows(net: Network, root: str, visible: set[str],
              ascii_only: bool = False) -> list[tuple[str, str]]:
    """(prefix, uid) for every visible host, in drawing order. See `ui`."""
    return ui.tree_rows(adjacency(net), root, visible, ascii_only)
