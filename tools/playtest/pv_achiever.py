"""Test V: a completionist. Play broad and long, measure how many of the 25
record lines fall by play, and whether the reckoner (record:15 then 20)
actually opens."""
import os, sys, io, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'V2')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.world import record as RW
from flatline.content import record as RC, districts as D
from flatline.world import street as WS
from flatline import save as save_mod
save_mod.write_meta(dict(save_mod.META_DEFAULT))
log = open(os.path.join(HERE, 'logs', 'pv_achiever.log'), 'w')
p = Play('ACHIEVER: do the lot', origin='gutter', seed=141, handle='Sum', log=log)
g = p.g; p.do('spend'); p.settle()
p.do('boost logic'); p.do('train intrusion'); p.do('train cryptography')

def earned():
    return len(RW.earned(RW.counts(g, save_mod.read_meta())))
def lines():
    c = RW.counts(g, save_mod.read_meta())
    return {e.key: (c.get(e.counter,0), e.target) for e in RC.ENTRIES if c.get(e.counter,0) < e.target}

track = []
places = [d.key for d in D.DISTRICTS]
for cyc in range(60):
    if g.over: break
    if 'siphon' not in g.char.library and 'siphon' not in g.char.deck.loaded and g.char.credits > 2500:
        p.do('market program'); p.do('buy siphon')
    p.play_job(); p.answer_choices()
    # explore
    p.do(f'walk {places[cyc % len(places)]}'); p.settle(prefer=('run','pay','talk','yes'))
    p.do('look')
    for key in p.present():
        p.do(f'talk {key}'); p.settle()
        for t in list(__import__('flatline.content.npcs',fromlist=['BY_KEY']).BY_KEY[key].topics)[:3]:
            p.do(f'ask {key} {t}'); p.answer_choices()
    out = p.do('visit')
    for row in re.findall(r'^\s+(\d+)\s+', out, re.M)[:6]:
        p.do(f'visit {row}'); p.settle(prefer=('run','pay','talk','yes'))
    # errands
    if cyc % 2 == 0:
        p.do('errands'); offers = WS.errands_here(g)
        pick = next((i for i,j in enumerate(offers,1) if j['kind'] in ('courier','collect','watch')), None)
        if pick and not g.city.errand: p.do(f'errands take {pick}'); p.settle()
    if cyc % 4 == 3:
        p.do('rumours')
    p.answer_choices()
    if cyc % 5 == 0:
        track.append((cyc, g.city.shift, earned()))
    if 'reckoner' in g.story.reached:
        p.mark(f'RECKONER opened at cycle {cyc}, {earned()} lines')
p.mark(f'campaign end: {earned()}/25 record lines; reckoner {"reached" if "reckoner" in g.story.reached else "NOT reached"}')
p.mark(f'lines still short: {lines()}')
log.write(f'\n### earned over time (cycle, shift, lines): {track}\n')
p.do('record'); p.do('called'); p.do('char')
p.finish('achiever')
log.close()
print(f"V: {earned()}/25 record lines | reckoner {'YES' if 'reckoner' in g.story.reached else 'no'} | "
      f"runs {g.char.runs} shift {g.city.shift} turns {p.turns} errors {len(p.errors)}")
print(f"   short: {list(lines().keys())}")
