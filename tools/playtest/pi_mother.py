"""Persona I: the top of the wall. Trains Violence to four the way `now` now
says to, buys the best blade the street sells, and takes Mother."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'I')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER
import spine
from flatline.content import pit as P
from flatline.world import fight as F, street as WS
log = open(os.path.join(HERE, 'logs', 'pi_mother.log'), 'w')
p = Play('MOTHER: the wall held', origin='expolice', seed=801, handle='Anvil', log=log, prefer=FIGHTER)
g = p.g
p.do('spend'); p.settle()
spine.go(p, 'shambles')
p.do('market weapon'); p.do('market armour')
def buy_best():
    out = p.do('market weapon')
    best = None
    for line in out.splitlines():
        import re
        m = re.match(r'\s*(\d+)\s+(\S+(?: \S+)?)\s+weapon\s+\+(\d+) a hit, (quiet|loud)', line)
        if m and m.group(4) == 'quiet' and (best is None or int(m.group(3)) > best[1]):
            best = (m.group(1), int(m.group(3)))
    if best: p.do(f'buy {best[0]}'); p.settle()
buy_best(); p.do('buy vest'); p.settle(); p.do('carry'); p.do('wear')
wins = 0; attempts = []
for turn in range(90):
    if g.over: break
    if turn % 8 == 0:
        p.do('now'); p.auto_city(1)   # the training step, when it is there
    if g.city.where != P.WHERE:
        spine.go(p, P.WHERE); continue
    if g.char.integrity < g.char.integrity_max * 0.6:
        p.do('clinic patch'); p.settle()
    if g.city.phase != 'night':
        if turn % 2 == 0:
            p.do('errands'); offers = WS.errands_here(g)
            pick = next((i for i, j in enumerate(offers, 1) if j['kind'] in ('muscle', 'job')), None)
            p.do(f'errands take {pick}') if pick and not g.city.errand else p.do('rest'); p.settle()
        else:
            p.do('rest'); p.settle()
        p.answer_choices(); continue
    rank = int(g.city.pit.get('rank', 0))
    viol = g.char.skill('violence')
    if viol >= 4 and rank >= 4 and 'pit:champion' not in g.story.flags:
        p.mark(f'taking Mother: violence {viol}, integrity {g.char.integrity}/{g.char.integrity_max}, weapon {g.char.weapon}')
        out = p.do('pit mother 0'); p.settle()
        attempts.append((g.city.shift, 'won' if 'pit:champion' in g.story.flags else 'lost'))
        if 'pit:champion' in g.story.flags:
            p.mark('THE WALL HELD'); p.do('carry'); p.do('carry eightfold'); p.do('inspect eightfold'); p.do('record floor'); p.do('char'); p.do('pit'); p.do('mail'); p.do('news')
            break
        if len(attempts) >= 8: p.mark('eight tries at Mother, no'); break
        continue
    # climb: the best name I can take, p8-style
    mine = F.strike_damage(g.char); beat = g.city.pit.get('beaten', []); best = None
    for f in sorted(P.FIGHTERS, key=lambda f: -f.rung):
        if f.key == 'mother': continue
        pool = F.FOE_POOL[f.tier] + f.pool_bonus; lo, hi = F.FOE_HIT[f.tier]
        rounds = pool / max(1, mine - F.FOE_ARMOUR.get(f.tier, 0))
        if rounds * ((lo + hi) / 2 - F.armour_of(g.char)) < g.char.integrity * 0.8 and (f.rung > rank or f.key in beat):
            best = f; break
    if best is None or viol < 4 and rank >= 4:
        p.do('rest'); p.settle(); p.answer_choices(); continue
    p.do(f'pit {best.key} 0'); p.settle(); p.answer_choices()
    if p.sess.pending is None and g.city.phase == 'night':
        p.do('rest'); p.settle()
p.mark('menace, on the street')
g.city.shift += 0
for _ in range(6):
    if g.over: break
    p.do('walk ninth'); 
    if p.sess.pending is not None and 'menace' in p.sess.pending.choices:
        p.mark('a menace option'); p.do('menace'); p.settle(); break
    p.settle(); p.do('walk shambles'); p.settle()
p.mark(f'END: {p.state()}; attempts at Mother {attempts}')
p.do('record'); p.do('char'); p.do('skills')
p.finish('mother')
log.close()
print(f'I: {p.state()} | Mother {attempts} | champion={"pit:champion" in g.story.flags} | errors {len(p.errors)}')
