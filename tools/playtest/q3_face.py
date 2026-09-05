"""Q3: the face. Talks to everybody, arranges, hires, keeps a cat, takes the offer."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q3_face')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER, NOFIGHT
import campaign as C
from campaign import act
log = open(os.path.join(HERE, 'logs', 'q3_face.log'), 'w')
p = Play('Q3: the face. Talks to everybody, arranges, hires, keeps a cat, takes the offer.', origin='protege', seed=1103, handle='Vell', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'take', 'lark.resolve': 'pay', 'archive.yours': 'yes', 'sparrow.deck': 'gear'}
g = p.g

act(p, C.setup, train=("persuasion", "streetwise"), boost="presence")
act(p, C.people); act(p, C.city_deck)
act(p, C.jobs, n=5, approach="social", legwork="employee")
act(p, C.heat_and_names); act(p, C.people)
act(p, C.pets, animal="cat", name="Minister", familiar="chatterbird", fname="Gossip")
act(p, C.jobs, n=5, approach="social", hire=True)
act(p, C.walk_all, visits=2); act(p, C.people)
act(p, C.crew, jobs_n=5); act(p, C.money); act(p, C.appearance)
act(p, C.record_and_titles)
act(p, C.story_end, carried="read", offer="take")
act(p, C.people); act(p, C.record_and_titles)
p.finish('q3_face')
print(C.summary(p, 'q3_face'))
log.close()
