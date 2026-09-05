"""Test Y: does money stay a constraint? A long campaign that also keeps a
pet, a familiar, an arrangement and a debt, logging credits over time."""
import os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'Y2')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.world import pets as PW
log = open(os.path.join(HERE, 'logs', 'py_balance.log'), 'w')
p = Play('BALANCE: does money stay tight', origin='gutter', seed=171, handle='Ledger', log=log)
g = p.g; p.do('spend'); p.settle()
p.do('boost logic'); p.do('train intrusion')
# take on the upkeep: safehouse, pet, familiar
g.city.safehouse = {'key': 'x', 'district': g.city.where}
credits = []
sinks = {'feed': 0, 'clinic': 0}
for cyc in range(50):
    if g.over: break
    if 'siphon' not in g.char.library and 'siphon' not in g.char.deck.loaded and g.char.credits > 2500:
        p.do('market program'); p.do('buy siphon')
    p.play_job(); p.answer_choices()
    if cyc == 3 and not g.city.pet:
        spine_ok = True
        for _ in range(3):
            if g.city.where == 'ninth': break
            p.do('walk ninth'); p.settle(prefer=('run','pay','talk','yes'))
        p.do('pet get cat'); p.do('pet name Interest')
        if g.char.deck.memory_free >= 1:
            g.char.deck.loaded = g.char.deck.loaded[:-1] if g.char.deck.memory_free < 1 else g.char.deck.loaded
            p.do('familiar get pixelcat')
    # keep the pet
    if g.city.pet:
        if int(g.city.pet.get('feed', 0)) <= 1:
            b = g.char.credits; p.do('pet feed buy'); sinks['feed'] += b - g.char.credits
        p.do('pet feed'); p.do('pet water'); p.do('pet play')
    # heal at a clinic sometimes
    if g.char.integrity < g.char.integrity_max // 2:
        b = g.char.credits; p.do('clinic patch'); sinks['clinic'] += max(0, b - g.char.credits)
    credits.append((g.city.shift, g.char.credits))
    if cyc % 10 == 0:
        p.mark(f'cycle {cyc}: {g.char.credits}c, pet {"kept" if g.city.pet else "lost"}')
lo = min(c for _,c in credits); hi = max(c for _,c in credits); end = credits[-1][1] if credits else 0
log.write(f'\n### credits (shift, c): {credits}\n### sinks: {sinks}\n')
p.mark(f'balance: low {lo}c, high {hi}c, end {end}c over {g.city.shift} shifts; sinks {sinks}')
p.do('record'); p.do('char')
p.finish('balance')
log.close()
broke_shifts = sum(1 for _,c in credits if c < 500)
print(f"Y: end {end}c | range {lo}-{hi}c | {broke_shifts}/{len(credits)} cycles under 500c | "
      f"sinks {sinks} | runs {g.char.runs} turns {p.turns} errors {len(p.errors)}")
