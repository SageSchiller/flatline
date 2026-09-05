"""Test X: form a partner bond by PLAY. Crew a runner and run jobs beside
them until they decide about you. Measure shifts/jobs to the bond."""
import os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'X2')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
log = open(os.path.join(HERE, 'logs', 'px_bond.log'), 'w')
p = Play('BOND: somebody decides about me', origin='protege', seed=161, handle='Twine', log=log)
g = p.g; p.do('spend'); p.settle()
p.do('boost logic'); p.do('train intrusion')
p.do('who')
target = min([r for r in g.city.rivals if r.alive], key=lambda r: getattr(r.data,'hire_price',9999) if hasattr(r,'data') else 9999)
key = target.key
p.mark(f'the runner is {target.name} ({key}); crew up and run beside them')
trace = []
for j in range(40):
    if g.over: break
    r = g.city.rival(key)
    if r is None or not r.alive:
        p.mark('runner gone'); break
    if r.bond:
        p.mark(f'BOND {r.bond} after {j} jobs at shift {g.city.shift}, disposition {r.disposition}, jobs {r.jobs}'); break
    # earn to afford hiring
    if 'siphon' not in g.char.library and 'siphon' not in g.char.deck.loaded and g.char.credits > 2500:
        p.do('market program'); p.do('buy siphon')
    # crew them if we can, else hire per job
    if not g.city.crew:
        o = p.do(f'crew take {key}')
        if o.lstrip().startswith('✗'):
            p.do(f'hire {key}'); p.settle(prefer=('yes',))
            if g.city.hired != key:
                p.do(f'hire {key} --confirm'); p.settle(prefer=('yes',))
    p.play_job(); p.answer_choices()
    r = g.city.rival(key)
    trace.append((g.city.shift, r.disposition, r.jobs, r.bond or '-', 'crew' if g.city.crew else ('hired' if g.city.hired==key else '-')))
    if j % 6 == 5:
        p.do(f'who {key}'); p.do('crew')
r = g.city.rival(key)
log.write(f'\n### (shift, disposition, rival.jobs, bond, with): {trace}\n')
p.mark(f'END: {target.name} bond={r.bond or "-"} disposition={r.disposition} jobs={r.jobs}')
if r.bond:
    p.do(f'who {key}'); p.do('record people')
p.finish('bond')
log.close()
print(f"X: {target.name} bond={r.bond or '-'} disp={r.disposition} rival.jobs={r.jobs} "
      f"after shift {g.city.shift} | char.runs {g.char.runs} turns {p.turns} errors {len(p.errors)}")
