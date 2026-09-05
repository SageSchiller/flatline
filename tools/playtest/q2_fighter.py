"""Q2: the fighter. The wall, the street, a dog, a crew, and the burn ending."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q2_fighter')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER, NOFIGHT
import campaign as C
from campaign import act
log = open(os.path.join(HERE, 'logs', 'q2_fighter.log'), 'w')
p = Play('Q2: the fighter. The wall, the street, a dog, a crew, and the burn ending.', origin='expolice', seed=1102, handle='Brick', log=log, prefer=FIGHTER)
p.table = {'deepwater.carried': 'burn', 'deepwater.offer': 'refuse', 'lark.resolve': 'pay'}
g = p.g

act(p, C.setup, train=("violence",), boost="body")
act(p, C.street, fighter=True, nights=10)
act(p, C.money); act(p, C.pets, animal="dog", name="Sarge", familiar="goodboy", fname="Rex")
act(p, C.jobs, n=6, approach="breach")
act(p, C.street, fighter=True, nights=8); act(p, C.heat_and_names)
act(p, C.crew, jobs_n=6); act(p, C.people)
act(p, C.record_and_titles)
act(p, C.story_end, carried="burn", offer="refuse")
act(p, C.street, fighter=True, nights=4); act(p, C.record_and_titles)
p.finish('q2_fighter')
print(C.summary(p, 'q2_fighter'))
log.close()
