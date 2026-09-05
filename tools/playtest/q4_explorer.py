"""Q4: the explorer. Walks everything, hunts the finds, pins a title, saves and restores, retires."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q4_explorer')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER, NOFIGHT
import campaign as C
from campaign import act
log = open(os.path.join(HERE, 'logs', 'q4_explorer.log'), 'w')
p = Play('Q4: the explorer. Walks everything, hunts the finds, pins a title, saves and restores, retires.', origin='courier', seed=1104, handle='Cartog', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse'}
g = p.g

act(p, C.setup, train=("streetwise", "signal"), boost="reflex")
act(p, C.walk_all, visits=4)
act(p, C.jobs, n=8, legwork="perimeter")
act(p, C.pets, animal="pigeon", name="Sextant", familiar="chatterbird", fname="Herald")
act(p, C.walk_all, visits=4); act(p, C.city_deck); act(p, C.appearance)
act(p, C.jobs, n=8, approach="inside", legwork="tap")
act(p, C.walk_all, visits=3); act(p, C.people); act(p, C.money)
act(p, C.record_and_titles); act(p, C.save_restore, slot="q4")
act(p, C.jobs, n=6)
act(p, C.walk_all, visits=3); act(p, C.record_and_titles)
act(p, C.retire_end)
p.finish('q4_explorer')
print(C.summary(p, 'q4_explorer'))
log.close()
