"""Q9: the regular. Somebody who works one faction's networks night after
night, with a watch on them, and reads what they know about them each time:
the doors left open, the techniques they have seen, the patches, the way
back in that turns out to be a trap. The finding is whether the memory shows
up where a player would look for it, and never in a way that loops."""
import collections
import os
import re
import sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q9_memory')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, NOFIGHT
import campaign as C
from campaign import act, SAFE
from flatline.content import skills as S

log = open(os.path.join(HERE, 'logs', 'q9_memory.log'), 'w')
p = Play('Q9: the regular, one faction ten nights running', origin='academic',
         seed=1109, handle='Regular', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse'}
g = p.g

act(p, C.setup, train=('intrusion', 'cryptography'), boost='logic')
p.shortcut('rank 4 in the deck skills, so backdoor, ghost and quiet are on the table')
for sk in S.SKILLS:
    g.char.base_skills[sk.key] = max(g.char.base_skills.get(sk.key, 0), 4)
p.do('techniques'); p.do('render')


def against(fac):
    return [c for c in g.city.board if c.target == fac and c.objective != 'escort']


def pick_faction():
    p.do('board')
    counts = collections.Counter(c.target for c in g.city.board if c.objective != 'escort')
    return counts.most_common(1)[0][0] if counts else None


fac = pick_faction()
p.mark(f'the faction: {fac}')
p.do(f'watch {fac}'); p.do('watch'); p.do(f'render {fac}')
seen = collections.Counter()
nights = 0
for night in range(10):
    if g.over:
        break
    jobs = against(fac)
    tries = 0
    while not jobs and tries < 8 and not g.over:
        p.do('rest'); p.settle(prefer=SAFE); p.do('board'); jobs = against(fac); tries += 1
    if not jobs:
        p.mark(f'night {night}: nothing against {fac} on the board after {tries} rests')
        continue
    if g.city.current is None:
        soft = min(jobs, key=lambda c: c.posture)
        p.do(f'take {soft.cid}'); p.settle(prefer=SAFE)
    p.do(f'render {fac}')
    ok = C.run_job(p, extra=('render', 'status') if night == 0 else ())
    nights += 1 if ok else 0
    out = p.do(f'render {fac}')
    for needle in ('what they know about you', 'doors open', 'seen you', '(expected)',
                   'routes', 'traps', 'patched', 'Nothing. You have never been in'):
        if needle in out:
            seen[needle] += 1
    p.do('news'); p.do('mail'); p.do('watch'); p.settle(prefer=SAFE)
    p.mark(f'night {night}: runs {g.char.runs}, finished {nights}, memory {dict(g.city.memory.get(fac, {}).get("seen", {}))}, doors {len(g.city.memory.get(fac, {}).get("doors", []))}')

p.mark(f'the dossier after {nights} finished nights: {dict(seen)}')
p.do(f'render {fac}'); p.do('log'); p.do('record work'); p.do('journal')
p.do(f'watch {fac}'); p.do('watch')
act(p, C.record_and_titles)
p.finish('q9_memory')
print(C.summary(p, 'q9_memory'))
log.close()
