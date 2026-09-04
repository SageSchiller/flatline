"""Persona A: an achiever. Plays for the record. Does the record play back?"""
import os, sys, re, collections
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'A')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.content import districts, record as RC, npcs as NPC
from flatline.world import record as RW, street as WS
from flatline import save as save_mod
log = open(os.path.join(HERE, 'logs', 'pa_record.log'), 'w')

p = Play('ACHIEVER: I play for the record', origin='courier', seed=61, handle='Tally', log=log)
g = p.g
def snapshot():
    return RW.counts(g, save_mod.read_meta())

p.mark('night one: is there a record, and does anything point me at it?')
for c in ('now', 'help', 'help record', 'char', 'record', 'record floor', 'record nonsense', 'records'):
    p.do(c)
start = snapshot()
p.mark(f'lines already done at creation: {[e.key for e in RW.earned(start)]}')
p.do('spend'); p.settle()
hist = [(0, snapshot())]
places = [d.key for d in districts.DISTRICTS]
asked = set()
watched = False
for cycle in range(22):
    if g.over:
        break
    p.mark(f'cycle {cycle}: a job')
    p.play_job()
    if g.over:
        break
    # the explorer half: a different district every other cycle, everybody in
    # it talked to and asked things, every place in it stood in
    if cycle % 2 == 0:
        p.do(f'walk {places[(cycle // 2) % len(places)]}'); p.settle()
    if g.over:
        break
    p.do('look')
    for key in p.present():
        if g.over: break
        p.do(f'talk {key}'); p.settle()
        for topic in list(NPC.BY_KEY[key].topics)[:3]:
            if (key, topic) in asked:
                continue
            asked.add((key, topic))
            p.do(f'ask {key} {topic}'); p.settle()
    out = p.do('visit')
    for row in re.findall(r'^\s+(\d+)\s{2}', out, re.M)[:5]:
        if g.over: break
        p.do(f'visit {row}'); p.settle()
    if g.over:
        break
    if cycle % 3 == 1:
        p.do('errands')
        offers = WS.errands_here(g)
        pick = next((i for i, j in enumerate(offers, 1) if j['kind'] in ('courier', 'collect', 'watch')), None)
        if pick and not g.city.errand:
            p.do(f'errands take {pick}'); p.settle()
            to = (g.city.errand or {}).get('to')
            for _ in range(4):
                if not g.city.errand or g.over: break
                if to and to != g.city.where:
                    p.do(f'walk {to}'); p.settle()
                else:
                    p.do('rest'); p.settle()
    if not watched and g.char.credits > 400:
        p.do('watch kick'); p.do('watch jacket'); p.do('watch blade'); watched = True
    if g.story.open_choice() is not None:
        p.choose_open()
    if cycle % 3 == 2:
        p.mark('reading the record')
        p.do('record'); p.do('char')
    hist.append((cycle + 1, snapshot()))

p.mark('the campaign, read back')
p.do('record'); p.do('record work'); p.do('record city'); p.do('record people'); p.do('record floor'); p.do('char'); p.do('journal')
final = snapshot()
log.write('\n### counters over the campaign (cycle: value) and when each line landed\n')
for e in RC.ENTRIES:
    series = [(c, s[e.counter]) for c, s in hist]
    landed = next((c for c, s in hist if s[e.counter] >= e.target), None)
    moved = final[e.counter] != start[e.counter]
    log.write(f'  {e.key:<10} {e.counter:<20} start {start[e.counter]:>6} end {final[e.counter]:>6} target {e.target:>6} '
              f'{"LANDED cycle " + str(landed) if landed is not None else ("moving" if moved else "NEVER MOVED")}\n')
log.write(f'  earned: {[e.key for e in RW.earned(final)]}\n  titles: {RW.titles(final)}\n')
p.mark('the profile after this character: a second character sits down')
p.finish('achiever')
q = Play('ACHIEVER, second character, same terminal', origin='gutter', seed=62, handle='Tally II', log=log)
q.do('record'); q.do('char'); q.do('now')
q.finish('achiever, second character')
log.close()
never = [e.key for e in RC.ENTRIES if final[e.counter] == start[e.counter]]
print(f'A: {p.state()} | turns {p.turns} | errors {len(p.errors)} | runs tried {p.runs_tried} done {p.runs_done}')
print(f'   earned {[e.key for e in RW.earned(final)]}')
print(f'   never moved: {never}')
print(f'   second character sees: {q.do("record").splitlines()[1][:80]!r}')
