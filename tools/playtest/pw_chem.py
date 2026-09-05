"""Test W: build a habit and go deep. Buy Redline, dose to a habit, play the
Ninety thread with Pell, detox, and climb Dissonance with chrome to the
bands. Measure habit, ninety flags, drift band."""
import os, sys, io, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'W2')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
import spine
from flatline.content import drugs as DR
log = open(os.path.join(HERE, 'logs', 'pw_chem.log'), 'w')
p = Play('CHEM: further in than out', origin='protege', seed=151, handle='Wick', log=log)
g = p.g; p.do('spend'); p.settle()
for _ in range(4):
    if g.over: break
    p.play_job(); p.answer_choices()

p.mark('a habit: find where Redline is sold, buy and dose repeatedly')
def buy_redline():
    for cmd in ('market drug', 'market'):
        out = p.do(cmd)
        if 'redline' in out.lower():
            p.do('buy redline'); return True
    return False
spine.go(p, 'shambles')
got = 0
for i in range(18):
    if g.over: break
    if buy_redline():
        p.do('dose redline'); p.settle(); got += 1
    else:
        # try other drug districts
        for d in ('marrow','freeport'):
            spine.go(p, d)
            if buy_redline(): p.do('dose redline'); p.settle(); got += 1; break
        spine.go(p, 'shambles')
    p.do('chem')
    p.do('rest'); p.settle(); p.answer_choices({'ninety.offer':'stop'})
    if DR.habit(g.char.chem, 'redline') >= 2:
        p.mark(f'redline habit reached 2 after {got} doses'); break
p.mark(f'habit redline={DR.habit(g.char.chem,"redline")} numb={DR.habit(g.char.chem,"numb")} | doses {got}')
p.mark('meet Pell and play Ninety')
spine.meet(p, 'pell', 'shambles', waits=5); p.answer_choices({'ninety.offer':'stop'})
for _ in range(10):
    if g.over or 'ninety_closed' in g.story.flags: break
    spine.go(p, 'shambles'); p.do('look'); p.settle()
    p.do('rest'); p.settle(); p.answer_choices({'ninety.offer':'stop'})
p.mark(f'ninety flags: {sorted(f for f in g.story.flags if f.startswith("ninety"))}')
p.mark('detox off it')
p.do('help detox'); p.do('detox redline'); p.do('detox redline --confirm'); p.settle(prefer=('yes',))
for _ in range(6): p.do('rest'); p.settle(); p.do('chem')
p.mark(f'after detox: redline habit {DR.habit(g.char.chem,"redline")}')
p.mark('climb the drift with chrome to the bands')
p.shortcut('credits topped to buy chrome (the drift climb is the test, not the grind)')
g.char.credits = 80000
spine.go(p, 'glasshouse')
bands = []
p.do('market ware')
import re as _re
for _ in range(10):
    if g.over: break
    out = p.do('market ware')
    m = _re.findall(r'^\s*\d+\s+(\S+(?: \S+)*?)\s+ware', out, _re.M)
    bought = False
    for name in m:
        o = p.do(f'buy {name.split()[0].lower()}')
        if not o.lstrip().startswith('✗') and 'install' in o.lower():
            key = None
            o2 = p.do('char')
            # install what we just bought
            for w in ['gorilla','muscle','doorman','spinal','breaker','deep','mourner','lamprey']:
                oi = p.do(f'install {w}')
                if not oi.lstrip().startswith('✗'):
                    bought = True; break
            if bought: break
    p.do('rest'); p.settle()
    band = g.char.dissonance_band[1]
    bands.append((g.char.dissonance, band))
    if g.char.dissonance >= 50: p.do('self'); p.do('char')
    if g.char.dissonance >= 75: p.mark('DISSOLVED'); p.do('self'); break
    if not bought and g.char.dissonance < 25: break
p.mark(f'drift climb: {bands} | final {g.char.dissonance} ({g.char.dissonance_band[1]})')
p.do('char'); p.do('record'); p.do('help chemistry')
p.finish('chem')
log.close()
print(f"W: redline habit {DR.habit(g.char.chem,'redline')} | ninety {sorted(f for f in g.story.flags if f.startswith('ninety'))} | "
      f"drift {g.char.dissonance} ({g.char.dissonance_band[1]}) | turns {p.turns} errors {len(p.errors)}")
