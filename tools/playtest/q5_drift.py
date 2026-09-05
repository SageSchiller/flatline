"""Q5: the drift. Chrome, a habit, a scary familiar, the lender, and the under ending."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q5_drift')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, FIGHTER, NOFIGHT
import campaign as C
from campaign import act
log = open(os.path.join(HERE, 'logs', 'q5_drift.log'), 'w')
p = Play('Q5: the drift. Chrome, a habit, a scary familiar, the lender, and the under ending.', origin='gutter', seed=1105, handle='Hollow', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse', 'deepwater.under': 'go', 'lark.resolve': 'pay', 'archive.yours': 'yes', 'ninety.offer': 'stop'}
g = p.g

act(p, C.setup, train=("intrusion", "hardware"), boost="logic")
act(p, C.jobs, n=6)
act(p, C.chrome_and_chem, wares=3, drug="redline", doses=5)
act(p, C.money)
act(p, C.pets, animal="rat", name="Tithe", familiar="wormwood", fname="Sorrow")
act(p, C.jobs, n=6, approach="inside")
act(p, C.chrome_and_chem, wares=2, drug="numb", doses=3)
act(p, C.people); act(p, C.city_deck); act(p, C.street, fighter=False, nights=4)
act(p, C.record_and_titles)
act(p, C.story_end, carried="read", offer="refuse")
act(p, C.record_and_titles)
p.finish('q5_drift')
print(C.summary(p, 'q5_drift'))
log.close()
