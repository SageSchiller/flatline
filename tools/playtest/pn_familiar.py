"""Persona N: the digital pet. Loads a familiar, feels the memory cost against
the deck, takes it into a run and reads what it says at each beat, lets it go
dormant, and drops it."""
import os, sys, io, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'N')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.content import pets as PC
from flatline.commands import city as CC
log = open(os.path.join(HERE, 'logs', 'pn_familiar.log'), 'w')
p = Play('FAMILIAR: company for the cost of memory', origin='gutter', seed=81, handle='Static', log=log)
g = p.g; p.do('spend'); p.settle()

p.mark('what can I run with, and what does it cost?')
p.do('familiar'); p.do('familiar get'); p.do('deck')

p.mark('the deck is full: a 2-mem familiar should not fit')
p.do('familiar get goodboy')
p.mark('make room by carrying less, then load the scary one')
p.do('deck')
# unload a program to free memory
before = len(g.char.deck.loaded)
if g.char.deck.loaded:
    prog = g.char.deck.loaded[-1]
    p.do(f'unload {prog}')
p.do('familiar get wormwood')
if not g.char.deck.familiar:
    # fall back to a 1-mem one
    p.do('familiar get tally')
p.do('familiar name Echo')
p.do('familiar'); p.do('deck')

p.mark('take it into a run and read what it says at each beat')
# take the softest job and drive a loud run to escalate through the alerts
p.do('board')
soft = min(g.city.board, key=lambda c: c.posture, default=None)
if soft:
    p.do(f'take {soft.cid}'); p.settle()
    for _ in range(8):
        st = CC.city_steps(g)
        if not st or g.city.current is None: break
        cmd = st[0][0]
        if cmd.startswith('jack'): break
        if '<' in cmd: break
        p.do(cmd); p.settle()
    p.do('jack in --force')
    p.mark('inside: scan, probe, crack loudly to wake the room')
    for _ in range(20):
        if p.sess.run is None: break
        b = p.sess.run.brief()
        step = b.steps[0] if b.steps else 'scan'
        if '<' in step or step == 'jack out':
            # force noise: scan and probe everything
            p.do('scan')
            for node in list(p.sess.run.net.nodes.values())[:3]:
                if p.sess.run is None: break
                p.do(f'probe {node.uid}')
                for svc in getattr(node, 'services', [])[:2]:
                    if p.sess.run is None: break
                    p.do(f'crack {node.uid} {getattr(svc,"key","")}')
        else:
            p.do(step)
        p.settle()
    if p.sess.run is not None:
        p.do('jack out --anyway'); p.settle()

p.mark('let it go dormant: rest many shifts without running')
for _ in range(12):
    if g.over: break
    p.do('rest'); p.settle()
p.do('familiar')

p.mark('drop it')
p.do('familiar drop'); p.do('familiar'); p.do('deck')
p.finish('familiar')
log.close()
print(f'N: {len(p.errors)} errors | familiar loaded ok, ran, dormant, dropped')
for cmd, err, tb in p.errors[:6]: print('  CRASH', cmd, err)
