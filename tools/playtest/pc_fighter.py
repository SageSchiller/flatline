"""Persona C: starts as a fighter, ends on the main line."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'C')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER
import spine
from flatline.content import pit as P
from flatline.world import fight as F, street as WS
log = open(os.path.join(HERE, 'logs', 'pc_fighter.log'), 'w')

p = Play('FIGHTER, THEN THE MAIN LINE', origin='expolice', seed=43, handle='Brick', log=log, prefer=FIGHTER)
g = p.g
p.mark('night one: I want to fight for a living. What does the game say?')
p.do('now'); p.do('spend'); p.settle()
p.do('train violence'); p.do('skills'); p.do('help street'); p.do('help fight')
p.mark('gear')
p.do('market weapon')
out = p.do('buy 1'); p.settle()
p.do('carry'); p.do('market armour'); p.do('buy 2'); p.settle(); p.do('wear')
p.mark('to the Shambles, and a fighter\'s life')
advice = []
def pit_night():
    mine = F.strike_damage(g.char)
    rank = int(g.city.pit.get('rank', 0))
    beat = g.city.pit.get('beaten', [])
    best = None
    for f in sorted(P.FIGHTERS, key=lambda f: -f.rung):
        pool = F.FOE_POOL[f.tier] + f.pool_bonus
        lo, hi = F.FOE_HIT[f.tier]
        rounds = pool / max(1, mine - F.FOE_ARMOUR.get(f.tier, 0))
        taking = rounds * ((lo + hi) / 2 - F.armour_of(g.char))
        if taking < g.char.integrity * 0.8 and (f.rung > rank or f.key in beat):
            best = f; break
    if best is None:
        p.do('rest'); p.settle(); return
    p.do(f'pit {best.key} 0'); p.settle()
    if p.sess.pending is None and g.city.phase == 'night':
        p.do('rest'); p.settle()

for turn in range(44):
    if g.over: break
    if turn % 6 == 0:
        out = p.do('now')
        advice.append((g.city.shift, re.findall(r'^\s+(?:next|then)\s+(\S+(?: \S+)?)', out, re.M)[:3]))
    if g.city.where != P.WHERE:
        spine.go(p, P.WHERE); continue
    if g.char.integrity < g.char.integrity_max // 2:
        p.do('clinic patch'); p.settle()
    if g.city.phase == 'night':
        pit_night()
    elif turn % 2 == 0:
        p.do('errands')
        offers = WS.errands_here(g)
        pick = next((i for i, j in enumerate(offers, 1) if j['kind'] in ('muscle', 'job')), None)
        if pick and not g.city.errand:
            p.do(f'errands take {pick}'); p.settle()
        else:
            p.do('rest'); p.settle()
    else:
        p.do('rest'); p.settle()
    if g.story.open_choice() is not None:
        p.choose_open()
    if turn % 11 == 10:
        p.mark(f'fighter, turn {turn}'); p.do('record floor'); p.do('journal'); p.do('mail')
p.mark(f'the fighter, forty-odd turns in. what `now` said each time: {advice}')
p.do('char'); p.do('record'); p.do('journal'); p.do('skills')
fighter_state = p.state()

p.mark('the pivot: the fighter tries the net')
p.do('now'); p.do('board'); p.do('deck'); p.do('load')
n = 0
while g.char.runs < 5 and not g.over and n < 14:
    n += 1
    p.play_job()
    p.do('journal')
p.mark(f'five runs as a fighter: tried {p.runs_tried} done {p.runs_done}; {spine.dw_flags(p)}')
p.do('now'); p.do('char')
ending = ''
if not g.over:
    spine.facts(p)
    ending = spine.to_ending(p, carried='burn', offer='refuse', max_jobs=30)
    p.mark(f'ENDING: {ending or "NONE REACHED"}; {spine.dw_flags(p)}')
    if ending:
        spine.afterwards(p, shifts=16)
        p.do('record'); p.do('pit')
p.finish('fighter to the main line')
log.close()
print(f'C fighter phase: {fighter_state}')
print(f'C end: {p.state()} | ending={ending or "-"} | turns {p.turns} | errors {len(p.errors)} | runs tried {p.runs_tried} done {p.runs_done}')
print(f'   notable {dict(p.seen)} | advice {advice}')
