"""Networks with memory (D179).

The city has always remembered what you did. The networks, where the
player spends most of their minutes, forgot you the moment you jacked out:
every run was a fresh puzzle against a target that had never met you. This
is the target's side of the ledger, kept per faction on the city and
serialised with it:

- `doors`: services you cracked and left cracked, by zone, host type and
  service, which the next network of theirs comes up with still open,
  until the faction patches them, which is news.
- `seen`: techniques you were seen using, counted, which retune their
  networks against you once they have seen one twice. A trail you scrubbed
  teaches nothing; a trail you left teaches everything.
- `nights`, `runs`, `last`, `patched`: the arithmetic of a history.
- `routes`: a route you found with `backdoor`, which is still there next
  time, or has been closed.

Pure functions on plain dicts, so `test.py` can hold every rule without a
network in front of it. The commands and the tick call these.
"""

from __future__ import annotations

#: How many doors a faction remembers you leaving open, at most.
DOORS_KEPT = 8
#: Chance per shift that a faction patches one open door, before heat.
PATCH_BASE = 0.03
#: A technique seen this many times is expected.
EXPECTED_AT = 2
#: What expecting a technique costs its check.
EXPECTED_PENALTY = 2
#: How many nights are kept for the dossier.
NIGHTS_KEPT = 10


def blank() -> dict:
    return {'doors': [], 'seen': {}, 'nights': [], 'runs': 0, 'last': -1,
            'patched': 0, 'routes': [], 'traps': 0}


def of(city, faction: str) -> dict:
    """The faction's memory of you, creating it blank."""
    mem = city.memory.setdefault(faction, blank())
    for key, value in blank().items():
        mem.setdefault(key, value if not isinstance(value, (list, dict)) else type(value)())
    return mem


def door_key(node, svc) -> tuple[str, str, str]:
    return (node.zone, node.type, svc.key)


def remember_run(city, faction: str, net, used: set[str], residue: int,
                 shift: int) -> dict:
    """What the night left them (D179). Doors stay cracked whether or not
    you scrubbed; what they learn about *how* you work needs a trail."""
    mem = of(city, faction)
    have = {(d['zone'], d['type'], d['service']) for d in mem['doors']}
    for node in net.nodes.values():
        for svc in node.services:
            if svc.cracked and door_key(node, svc) not in have:
                mem['doors'].append({'zone': node.zone, 'type': node.type,
                                     'service': svc.key, 'since': int(shift)})
                have.add(door_key(node, svc))
    mem['doors'] = mem['doors'][-DOORS_KEPT:]
    if residue > 0:
        for tech in sorted(used):
            mem['seen'][tech] = int(mem['seen'].get(tech, 0)) + 1
    mem['runs'] = int(mem.get('runs', 0)) + 1
    mem['last'] = int(shift)
    mem['nights'] = (list(mem.get('nights', [])) + [int(shift)])[-NIGHTS_KEPT:]
    return mem


def expected(mem: dict) -> set[str]:
    return {t for t, n in (mem.get('seen') or {}).items() if int(n) >= EXPECTED_AT}


def apply(net, mem: dict) -> tuple[list[str], set[str]]:
    """Bring a fresh network of theirs up the way they left it: the doors
    you left open still open (the host known, the service cracked, the
    host held), and a route you found still there. Returns the lines to
    say and the techniques they expect."""
    said: list[str] = []
    opened = 0
    taken: set[str] = set()
    for door in list(mem.get('doors') or []):
        # The same door on the same kind of host in the same zone; failing
        # that, the same door on the same kind of host; failing that, the
        # same door anywhere. A network is generated fresh each night, and
        # what they left open is a service, not a serial number.
        for match in ((door['zone'], door['type']), (None, door['type']), (None, None)):
            hit = None
            for node in net.nodes.values():
                if node.uid in taken:
                    continue
                if match[0] is not None and node.zone != match[0]:
                    continue
                if match[1] is not None and node.type != match[1]:
                    continue
                svc = next((s for s in node.services if s.key == door['service'] and not s.cracked), None)
                if svc is not None:
                    hit = (node, svc)
                    break
            if hit is not None:
                node, svc = hit
                svc.cracked = True
                node.known = True
                node.open = True
                taken.add(node.uid)
                opened += 1
                break
    if opened:
        said.append(f'{opened} door{"s" if opened != 1 else ""} you left open '
                    f'{"are" if opened != 1 else "is"} still open. They have not '
                    f'read that log yet.')
    routed = 0
    for route in list(mem.get('routes') or [])[:2]:
        a = next((n for n in net.nodes.values() if (n.zone, n.type) == tuple(route['from'])), None)
        b = next((n for n in net.nodes.values() if (n.zone, n.type) == tuple(route['to']) and n is not a), None)
        if a is not None and b is not None and b.uid not in a.edges:
            a.edges.append(b.uid); b.edges.append(a.uid)
            routed += 1
    if routed:
        said.append('The route you found last time is still there. There was '
                    'always going to be.')
    exp = expected(mem)
    if exp:
        names = ', '.join(sorted(exp))
        said.append(f'They have seen you {names} here before. Every door reads it.')
    return said, exp


def patch_tick(city, rng, heat_of) -> list[str]:
    """Each shift, a faction with doors you left open closes one, sometimes,
    and more often the hotter you are with them. Told, and put on the wire,
    and pinged to a watch on the faction."""
    told: list[str] = []
    for faction, mem in list(city.memory.items()):
        doors = list(mem.get('doors') or [])
        if not doors:
            continue
        chance = PATCH_BASE + max(0, int(heat_of(faction))) / 500.0
        if not rng.chance(chance):
            continue
        door = doors[0]
        mem['doors'] = doors[1:]
        mem['patched'] = int(mem.get('patched', 0)) + 1
        line = (f'{_short(faction)} patched the {door["service"]} on their '
                f'{door["type"].replace("_", " ")} in the {door["zone"]}. '
                f'Somebody read the log.')
        told.append(f'[dim]{line}[/]')
        city.news.append(f'[dim]{line}[/]')
        if faction in city.watches:
            mem.setdefault('pings', []).append(line)
    return told


def dossier(city, faction: str, shift: int) -> list[tuple[str, str]]:
    """What they know about you, as rows for `render`."""
    mem = city.memory.get(faction)
    if not mem or not int(mem.get('runs', 0)):
        return []
    rows = [('nights', f'{mem.get("runs", 0)}, the last on shift {mem.get("last", -1)}')]
    doors = mem.get('doors') or []
    if doors:
        rows.append(('doors open', ', '.join(f'{d["service"]} on a {d["type"].replace("_", " ")} ({d["zone"]})'
                                             for d in doors[:4]) + (' and more' if len(doors) > 4 else '')))
    else:
        rows.append(('doors open', 'none they have not patched'))
    seen = mem.get('seen') or {}
    if seen:
        exp = expected(mem)
        rows.append(('seen you', ', '.join(f'{t} x{n}' + (' (expected)' if t in exp else '')
                                          for t, n in sorted(seen.items(), key=lambda kv: -kv[1]))))
    if int(mem.get('patched', 0)):
        rows.append(('patched', str(mem['patched'])))
    if mem.get('routes'):
        rows.append(('routes', f'{len(mem["routes"])} you found, still there'))
    if int(mem.get('traps', 0)):
        rows.append(('traps', f'{mem["traps"]} way back in they left open for you'))
    return rows


def _short(faction: str) -> str:
    from ..content import factions
    f = factions.BY_KEY.get(faction)
    return f.short if f else faction
