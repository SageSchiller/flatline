"""Persona J: the explorer. Walks every district, stands in every place,
finds what there is to find, reads what the city says. Does any story ever
answer the walking?"""
import os, sys, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'J')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.content import districts as D, spots
log = open(os.path.join(HERE, 'logs', 'pj_explorer.log'), 'w')
p = Play('EXPLORER: I want to know the whole city', origin='courier', seed=901, handle='Cartographer', log=log)
g = p.g; p.do('spend'); p.settle()
# a couple of runs for money and to open the world
for _ in range(3):
    if g.over: break
    p.play_job(); p.answer_choices()
p.mark('now the walking: every district, every quarter, every place')
visited = set(); found_before = 0
for d in D.DISTRICTS:
    if g.over: break
    for _ in range(4):
        if g.over or g.city.where == d.key: break
        p.do(f'walk {d.key}'); p.settle(prefer=('run','pay','talk','bolt','yes'))
    if g.city.where != d.key: continue
    p.mark(f'in {d.name}')
    p.do('look'); p.do('district')
    out = p.do('visit')
    rows = re.findall(r'^\s+(\d+)\s+', out, re.M)
    for row in rows[:8]:
        if g.over: break
        vo = p.do(f'visit {row}'); p.settle(prefer=('run','pay','talk','yes'))
        visited.add((d.key, row))
        # read anybody here, in case standing about is a social act
        for name in re.findall(r'\b([A-Z][a-z]{3,})\b', vo)[:2]:
            pass
    p.do('journal'); p.do('record city')
found = sum(1 for f in g.story.flags if f.startswith('found:'))
stood = sum(1 for f in g.story.flags if f.startswith('visited:'))
p.mark(f'stood in {stood} places, found {found} one-of-a-kind things, {len(g.story.reached)} threads')
p.mark('did any thread ever answer the walking? the journal in full:')
p.do('journal')
for k in list(g.story.reached):
    p.do(f'journal {k}')
p.mark('the record, and what is left for an explorer')
p.do('record'); p.do('record city'); p.do('ambitions'); p.do('world')
# keep going: more finds, deeper drift-by-walking
p.mark('another pass, hunting the one-of-a-kind things by rumour')
for d in D.DISTRICTS:
    if g.over: break
    for _ in range(3):
        if g.over or g.city.where==d.key: break
        p.do(f'walk {d.key}'); p.settle(prefer=('run','pay','talk','bolt','yes'))
    out = p.do('visit')
    for row in re.findall(r'^\s+(\d+)\s+', out, re.M)[:8]:
        if g.over: break
        p.do(f'visit {row}'); p.settle(prefer=('run','pay','talk','yes'))
    p.do('rest'); p.settle(); p.answer_choices()
found2 = sum(1 for f in g.story.flags if f.startswith('found:'))
stood2 = sum(1 for f in g.story.flags if f.startswith('visited:'))
p.mark(f'END: stood {stood2}, found {found2}, threads {len(g.story.reached)}: {sorted(g.story.reached)}')
p.do('record'); p.do('char'); p.do('rice palette')
p.finish('explorer')
log.close()
print(f'J: stood {stood2}/60, found {found2}, threads touched {len(g.story.reached)} | {p.state()} | errors {len(p.errors)}')
print(f'   threads: {sorted(g.story.reached)}')
