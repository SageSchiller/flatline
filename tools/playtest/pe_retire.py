"""Persona E: plays for the door. Reads `retire` from the first week, plays a
career, and walks out on purpose. Then somebody else sits down."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'E')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
log = open(os.path.join(HERE, 'logs', 'pe_retire.log'), 'w')
p = Play('RETIRE: I want out, on my terms', origin='courier', seed=501, handle='Tallis', log=log)
g = p.g
p.mark('week one: is the door signposted?')
for c in ('now', 'help retire', 'retire', 'ambitions', 'retire --confirm'):
    p.do(c); p.settle(prefer=('no',))
p.do('spend'); p.settle()
n = 0
while g.char.runs < 14 and not g.over and n < 30:
    n += 1; p.play_job(); p.answer_choices()
    if g.char.runs in (3, 8, 12):
        p.mark(f'{g.char.runs} runs: how far off?'); p.do('retire'); p.do('debt'); p.do('chem'); p.do('char')
p.mark(f'a career played: {p.state()}')
p.do('retire')
if g.over:
    p.finish('retire (died first)'); log.close(); sys.exit(0)
if g.char.credits < 45000:
    p.shortcut(f'credits {g.char.credits} -> 45000 (the stake is the grind, the door is the test)')
    g.char.credits = 45000
p.do('retire')
# clear what the gates want, by play where it is cheap
if g.debt.owed:
    p.do('debt'); p.do('debt pay all'); p.settle(prefer=('yes',)); p.do('retire')
if g.city.bounties:
    p.mark('a bounty on the name: what does the door say?'); p.do('retire'); p.do('burn --confirm'); p.settle(prefer=('yes',)); p.do('retire')
shifts = 0
while shifts < 14 and 'All four' not in p.do('retire') and not g.over:
    shifts += 1; p.do('rest'); p.settle(); p.answer_choices()
p.mark('the door, open')
p.do('retire --confirm'); p.settle(prefer=('yes',))
p.mark(f'after: over={g.over!r}')
for c in ('now', 'char', 'log', 'career', 'characters', 'record', 'rice palette', 'journal', 'rest', 'board', 'switch Tallis'):
    p.do(c)
p.finish('retire')
q = Play('RETIRE: the next one', origin='gutter', seed=502, handle='Second', log=log)
q.sess.game = None
q.do('new Second --origin gutter --seed 502'); q.settle(prefer=('yes',))
for c in ('characters', 'record', 'char', 'news', 'now', 'career'):
    q.do(c)
q.finish('retire, the next one')
log.close()
print(f'E: over={g.over!r} shift {g.city.shift} runs {g.char.runs} credits {g.char.credits} turns {p.turns} errors {len(p.errors)+len(q.errors)}')
