"""Persona H: gets a number put on their name, on purpose, then does only
what `now` says. Does the advice walk a hunted runner out of it?"""
import os, sys, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'H')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
log = open(os.path.join(HERE, 'logs', 'ph_hunted.log'), 'w')
p = Play('HUNTED: a number on my name', origin='gutter', seed=701, handle='Marrow', log=log)
g = p.g; p.do('spend'); p.settle()
p.mark('loud work against one outfit until they put a number on me')
n = 0
while not g.city.bounties and not g.over and n < 10:
    n += 1
    carrion = [c for c in g.city.board if c.target == 'carrion'] or [c for c in g.city.board if c.target in ('sixes', 'kagawa')]
    if carrion and g.city.current is None:
        p.do(f'take {carrion[0].cid}'); p.settle()
    p.play_job(); p.answer_choices()
    p.do('heat'); p.do('status')
if not g.city.bounties:
    p.shortcut('heat with Carrion set to 70 (the bounty is the test, not the wait)')
    g.alias.add_heat('carrion', 70)
    for _ in range(3):
        p.do('rest'); p.settle()
        if g.city.bounties: break
p.mark(f'hunted: bounties {dict(g.city.bounties)}; {p.state()}')
p.do('heat'); p.do('status'); p.do('help bounty'); p.do('board'); p.do('now')
p.mark('now on, I do what `now` says and nothing else')
first = collections.Counter(); refused = 0; walked = 0
for turn in range(30):
    if g.over: break
    from flatline.commands import city as city_cmd
    steps = city_cmd.city_steps(g)
    head = steps[0][0].split()[0] if steps else '(none)'
    first[head] += 1
    done = p.auto_city(1)
    if p.sess.run is not None: p.auto_run()
    p.answer_choices()
    tail = p.log  # noqa
    if turn % 6 == 5:
        p.mark(f'turn {turn}: bounties {dict(g.city.bounties)}'); p.do('now'); p.do('heat')
p.mark(f'END: bounties {dict(g.city.bounties)}; {p.state()}')
log.write(f'\n### first steps `now` gave, counted: {dict(first)}\n')
p.do('now'); p.do('heat'); p.do('status'); p.do('char')
p.finish('hunted')
log.close()
print(f'H: {p.state()} | now said {dict(first)} | bounties {dict(g.city.bounties)} | errors {len(p.errors)}')
