"""Q7: the long life. Two hundred shifts, every act in rotation, the main
line somewhere in the middle, and the door at the end. The question is
whether the late game is still deciding anything: what `now` says at shift
150, whether the record and the titles keep landing, whether anything
loops, stalls or reads stale once the story has run out."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q7_long')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, NOFIGHT
import campaign as C
from campaign import act
log = open(os.path.join(HERE, 'logs', 'q7_long.log'), 'w')
p = Play('Q7: the long life', origin='courier', seed=1107, handle='Tenure', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'take', 'lark.resolve': 'pay',
           'archive.yours': 'yes', 'paper.taken': 'front', 'quiet.berth': 'stay'}
g = p.g
act(p, C.setup, train=('intrusion', 'streetwise'), boost='logic')
act(p, C.pets, animal='dog', name='Tenure', familiar='pixelcat', fname='Echo')
ROTATION = [
    lambda: act(p, C.jobs, n=4, legwork='intel'),
    lambda: act(p, C.people),
    lambda: act(p, C.walk_all, visits=2),
    lambda: act(p, C.money),
    lambda: act(p, C.street, fighter=False, nights=3),
    lambda: act(p, C.city_deck),
    lambda: act(p, C.jobs, n=4, approach='inside'),
    lambda: act(p, C.record_and_titles),
]
i = 0
ending = ''
while g.city.shift < 200 and not g.over and p.turns < 9000:
    ROTATION[i % len(ROTATION)](); i += 1
    act(p, C.pet_care)
    if g.city.shift % 25 < 3 and i % len(ROTATION) == 0:
        p.mark(f'shift {g.city.shift}: {p.state()}')
        p.do('now'); p.do('journal'); p.do('record'); p.do('home'); p.do('who')
    if not ending and g.city.shift >= 60 and 'dw_posting' in g.story.flags:
        ending = act(p, C.story_end, carried='read', offer='take', max_jobs=20, after=6) or ''
        p.mark(f'ENDING at shift {g.city.shift}: {ending or "NONE"}')
p.mark(f'late game: shift {g.city.shift}, runs {g.char.runs}, credits {g.char.credits}, threads {len(g.story.reached)}')
for c in ('now', 'journal', 'record', 'called', 'who', 'home', 'board', 'rumours', 'news 10'):
    p.do(c)
act(p, C.retire_end)
p.finish('q7_long')
print(C.summary(p, 'q7_long'))
log.close()
