"""Persona K: the face. Never cracks a hard door; talks, pays, arranges,
knows everyone. Does the social build have story, and does the tone hold
when the game is played by talking rather than running?"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'K')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline.content import districts as D, npcs as N
log = open(os.path.join(HERE, 'logs', 'pk_face.log'), 'w')
p = Play('FACE: I talk my way through', origin='protege', seed=1001, handle='Silk', log=log)
g = p.g; p.do('spend'); p.settle()
met = set()
for cycle in range(20):
    if g.over: break
    # meet everyone, ask everyone everything
    for d in [D.DISTRICTS[cycle % len(D.DISTRICTS)]]:
        for _ in range(3):
            if g.over or g.city.where==d.key: break
            p.do(f'walk {d.key}'); p.settle(prefer=('talk','pay','run','yes'))
    p.do('look')
    for key in p.present():
        if g.over: break
        p.do(f'talk {key}'); p.settle(prefer=('talk','pay','yes'))
        for topic in list(N.BY_KEY[key].topics):
            p.do(f'ask {key} {topic}'); p.answer_choices()
        met.add(key)
    # take a talk-your-way-in job
    if g.city.current is None:
        soft = min(g.city.board, key=lambda c: c.posture, default=None)
        if soft: p.do(f'take {soft.cid}'); p.settle()
    if g.city.current is not None:
        p.do('approach'); p.do('approach social'); p.settle(prefer=('yes',))
        p.play_job()
    p.answer_choices()
    if cycle % 4 == 3:
        p.do('arrange'); p.do('who'); p.do('journal'); p.do('rep')
p.mark(f'the face, played: met {len(met)} people, {len(g.story.reached)} threads')
p.do('journal'); p.do('record people'); p.do('who'); p.do('char')
p.finish('face')
log.close()
print(f'K: met {len(met)} | threads {len(g.story.reached)} | {p.state()} | errors {len(p.errors)}')
print(f'   threads: {sorted(g.story.reached)}')
