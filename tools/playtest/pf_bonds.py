"""Persona F: wants somebody to decide about them. Two ways: hire the same
runner every job until they are a partner; sell one out and race them until
they are a nemesis. Measured: shifts and jobs to a bond, across seeds."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'F')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
log = open(os.path.join(HERE, 'logs', 'pf_bonds.log'), 'w')

def campaign(label, seed, way, jobs=26):
    p = Play(f'BONDS: {label}', origin='protege', seed=seed, handle='Cinder', log=log)
    g = p.g; p.do('spend'); p.settle()
    p.do('who')
    alive = [r for r in g.city.rivals if r.alive]
    target = min(alive, key=lambda r: getattr(r.data, 'hire_price', 0) if hasattr(r, 'data') else 0)
    key = target.key
    p.mark(f'{way}: the runner is {target.name} ({key})')
    p.do(f'who {key}')
    trace = []
    if way == 'nemesis':
        p.do(f'betray {key}'); p.settle(prefer=('yes',))
        p.do(f'betray {key} --confirm'); p.settle(prefer=('yes',))
        p.do(f'who {key}'); p.do('news')
    for j in range(jobs):
        if g.over: break
        r = g.city.rival(key)
        if r is None or not r.alive:
            p.mark('the runner is dead or gone'); break
        if r.bond:
            p.mark(f'BOND {r.bond} after {j} jobs, shift {g.city.shift}'); break
        if way == 'partner':
            p.do(f'hire {key}'); p.settle(prefer=('yes',))
            if g.city.hired != key:
                p.do(f'hire {key} --confirm'); p.settle(prefer=('yes',))
        p.play_job(); p.answer_choices()
        r = g.city.rival(key)
        trace.append((g.city.shift, r.disposition, r.jobs, r.bond or '-', g.city.hired or '-'))
        if j % 5 == 4:
            p.do(f'who {key}'); p.do('crew'); p.do('news')
    r = g.city.rival(key)
    log.write(f'\n### {label}: (shift, disposition, rival.jobs, bond, hired): {trace}\n')
    p.finish(label)
    print(f'{label:<24} bond={r.bond or "-":<8} disp {r.disposition:+4} rival.jobs {r.jobs:2} after shift {g.city.shift:3} runs {g.char.runs:2} turns {p.turns} errors {len(p.errors)}')

campaign('partner, seed 11', 11, 'partner')
campaign('partner, seed 12', 12, 'partner')
campaign('nemesis, seed 21', 21, 'nemesis')
campaign('nemesis, seed 22', 22, 'nemesis')
log.close()
