"""Persona G: goes too far in. Chrome until the net answers back, a habit
through Ninety Seconds, the clinic on the way down, and what the city says
at each band."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'G')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
import spine
log = open(os.path.join(HERE, 'logs', 'pg_drift.log'), 'w')
p = Play('DRIFT: further in than out', origin='protege', seed=601, handle='Halyard', log=log)
g = p.g
p.do('spend'); p.settle()
p.mark('a few jobs first, for the money and the runs')
n = 0
while g.char.runs < 6 and not g.over and n < 12:
    n += 1; p.play_job(); p.answer_choices()
p.mark('the ladder: what does the game say about drift before I climb it?')
for c in ('help dissonance', 'char', 'self', 'clinic'):
    p.do(c)
p.shortcut(f'credits {g.char.credits} -> 60000 (the chrome is the test, not the grind)')
g.char.credits = 60000
spine.go(p, 'glasshouse'); p.do('clinic'); p.do('market chrome'); p.do('market cyberware')
bands = []
for ware in ('gorilla', 'spinal_bus', 'breaker_hand', 'deep_jack', 'threadpuller', 'mourner', 'lamprey'):
    if g.over: break
    before = g.char.dissonance
    out = p.do(f'install {ware}'); p.settle(prefer=('yes',))
    if out.lstrip().startswith('✗'):
        p.do('market'); continue
    p.do('rest'); p.settle(); p.answer_choices()
    now = g.char.dissonance
    bands.append((ware, before, now, g.char.dissonance_band[1]))
    p.mark(f'{ware}: dissonance {before} -> {now} ({g.char.dissonance_band[1]})')
    p.do('char'); p.do('now'); p.do('look'); p.settle()
    if now >= 50 and 'submerged' not in [b for b in bands if b == 'x']:
        p.do('world'); p.do('rice palette'); p.do('board'); p.do('clinic')
    if now >= 75:
        p.mark('Dissolved'); p.do('self'); p.do('rice marks'); p.do('news'); p.do('journal'); p.do('mail')
        break
log.write(f'\n### the climb: {bands}\n')
p.mark(f'at the top: {p.state()}')
p.do('help ground'); p.do('ground'); p.do('ground --confirm'); p.settle(prefer=('yes',)); p.do('char')
p.mark('a habit: Redline, then Numb, then Pell')
spine.go(p, 'shambles'); p.do('market drug'); p.do('market drugs')
for i in range(10):
    if g.over: break
    p.do('buy redline'); p.settle(); p.do('dose redline'); p.settle()
    p.do('chem')
    p.do('rest'); p.settle(); p.answer_choices({'ninety.offer': 'stop'})
    if i % 3 == 2:
        p.do('look'); p.settle(); p.do('talk pell'); p.settle(); p.do('ask pell habit'); p.answer_choices({'ninety.offer': 'stop'})
    from flatline.content import drugs as DR
    if DR.habit(g.char.chem, 'redline') >= 2 and i >= 5:
        break
from flatline.content import drugs as DR
p.mark(f'habit redline {DR.habit(g.char.chem, "redline")}; ninety flags {sorted(f for f in g.story.flags if f.startswith("ninety"))}')
for _ in range(8):
    if g.over: break
    p.do('rest'); p.settle(); p.answer_choices({'ninety.offer': 'stop'})
    if 'ninety_closed' in g.story.flags: break
p.do('journal ninety'); p.do('chem'); p.do('retire')
p.mark('coming off it')
p.do('help detox'); p.do('detox'); p.do('detox redline --confirm'); p.settle(prefer=('yes',))
for _ in range(6):
    p.do('rest'); p.settle(); p.do('chem')
p.mark(f'END: {p.state()}')
p.do('char'); p.do('record'); p.do('retire')
p.finish('drift')
log.close()
print(f'G: {p.state()} | climb {bands} | errors {len(p.errors)}')
