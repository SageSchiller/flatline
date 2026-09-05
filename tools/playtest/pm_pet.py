"""Persona M: the real-world pet. Adopts one, names it, lives the care loop,
lets one starve to the telegraphed loss, adopts another and keeps it, and
takes it into the ending."""
import os, sys, io, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'M')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.content import pets as PC
log = open(os.path.join(HERE, 'logs', 'pm_pet.log'), 'w')
p = Play('PET: something soft in a hard city', origin='courier', seed=71, handle='Kettle', log=log)
g = p.g; p.do('spend'); p.settle(); g.char.credits = 20000

p.mark('no safehouse: can I even keep a pet?')
p.do('pet'); p.do('pet get')
p.mark('get a safehouse first')
# find a safehouse district and buy
from flatline.content import districts as D
for d in D.DISTRICTS:
    if 'safehouse' in d.services:
        for _ in range(3):
            if g.city.where == d.key: break
            p.do(f'walk {d.key}'); p.settle(prefer=('run','pay','talk','yes'))
        break
out = p.do('safehouse')
# buy the first offered key
m = re.search(r'safehouse buy (\w+)', out) or re.search(r'\b(\w+)\b.*\d+c', out)
p.do('safehouse buy ' + (m.group(1) if m else ''))
if not g.city.safehouse:
    p.shortcut('forced a safehouse (buy flow varies by district)')
    g.city.safehouse = {'key': 'x', 'district': g.city.where}

p.mark('go where strays are and see the choices')
for _ in range(3):
    if g.city.where == 'ninth': break
    p.do(f'walk ninth'); p.settle(prefer=('run','pay','talk','yes'))
p.do('pet get')
p.mark('adopt the dog (needs the most care), name it')
p.do('pet get cat') if not any(a.key=='dog' for a in __import__('flatline.commands.city',fromlist=['_pets_here'])._pets_here(g)) else p.do('pet get dog')
p.do('pet name Biscuit')
p.do('pet')

p.mark('the care loop: buy feed, feed, water, play')
p.do('pet feed'); p.do('pet feed buy'); p.do('pet feed'); p.do('pet water'); p.do('pet play')
p.do('pet')

p.mark('come home and be greeted (rest at the safehouse district)')
for _ in range(3):
    if g.city.where == g.city.safehouse.get('district'): break
    p.do(f"walk {g.city.safehouse.get('district')}"); p.settle(prefer=('run','pay','talk','yes'))
p.do('rest'); p.settle()

p.mark('now neglect it: rest away, do not feed, watch it be lost')
lost = False
for i in range(30):
    if g.over: break
    p.do('rest'); p.settle()
    if not g.city.pet:
        p.mark(f'LOST at shift {g.city.shift}'); lost = True; break
    if i % 3 == 0:
        p.do('pet')
p.mark(f'pet after neglect: {"gone" if not g.city.pet else "still here"}')

p.mark('adopt another and keep it well, then let it go on purpose')
for _ in range(3):
    if g.city.where == 'ninth': break
    p.do('walk ninth'); p.settle(prefer=('run','pay','talk','yes'))
p.do('pet get cat'); p.do('pet name Sequel')
p.do('pet feed buy'); p.do('pet feed'); p.do('pet water'); p.do('pet play')
p.do('pet let go'); p.do('pet let go --confirm')
p.do('pet')

p.mark('adopt a keeper for the ending, then retire to see the coda')
for _ in range(3):
    if g.city.where == 'ninth': break
    p.do('walk ninth'); p.settle(prefer=('run','pay','talk','yes'))
p.do('pet get cat'); p.do('pet name Ledger')
# fake the retire gates to see the epilogue coda
p.shortcut('forced the retire gates to reach the ending and read the pet coda')
g.char.credits = 60000
from flatline.content import legacy
g.alias.established = g.city.shift - legacy.NAME_HOLDS - 1
p.do('retire'); p.do('retire --confirm'); p.settle(prefer=('yes',))
p.mark(f'over={g.over!r}')
p.finish('pet')
log.close()
print(f'M: {len(p.errors)} errors | lost telegraphed: {lost} | over={g.over!r}')
for cmd, err, tb in p.errors[:6]: print('  CRASH', cmd, err)
