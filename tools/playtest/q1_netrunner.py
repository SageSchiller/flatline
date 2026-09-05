"""Q1: the netrunner. Lives on the deck, in and out of the city, to the read ending."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q1_netrunner')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER, NOFIGHT
import campaign as C
from campaign import act
log = open(os.path.join(HERE, 'logs', 'q1_netrunner.log'), 'w')
p = Play('Q1: the netrunner. Lives on the deck, in and out of the city, to the read ending.', origin='academic', seed=1101, handle='Tessellate', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'take', 'lark.resolve': 'pay', 'archive.yours': 'yes'}
g = p.g

act(p, C.setup, train=("intrusion", "cryptography"), boost="logic")
act(p, C.deck_life); act(p, C.city_deck)
act(p, C.jobs, n=6, legwork="intel", extra=("probe", "here"))
act(p, C.pets, animal="cat", name="Packet", familiar="pixelcat", fname="Echo")
act(p, C.jobs, n=6, approach="inside")
act(p, C.people); act(p, C.money); act(p, C.appearance)
act(p, C.jobs, n=6, hire=True)
act(p, C.record_and_titles); act(p, C.save_restore, slot="q1")
act(p, C.story_end, carried="read", offer="take")
act(p, C.record_and_titles)
p.finish('q1_netrunner')
print(C.summary(p, 'q1_netrunner'))
log.close()
