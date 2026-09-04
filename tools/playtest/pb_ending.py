"""Persona B: play the main line to its end, then see what is left."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'B')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
import spine
log = open(os.path.join(HERE, 'logs', 'pb_ending.log'), 'w')

def campaign(label, origin, seed, carried, offer):
    p = Play(f'ENDING: {label}', origin=origin, seed=seed, handle='Lantern', log=log)
    g = p.g
    p.do('now'); p.do('journal'); p.do('help story') 
    p.do('spend'); p.settle()
    p.mark('act one: five jobs, reading the journal for the story')
    n = 0
    while g.char.runs < 5 and not g.over and n < 12:
        n += 1
        p.play_job()
        p.do('journal'); p.do('now')
    p.mark(f'five runs: {spine.dw_flags(p)}; jobs tried {p.runs_tried}, done {p.runs_done}')
    if g.over:
        p.finish(label); return None
    spine.facts(p)
    p.mark('act three onward: the posting, the log, the offer')
    ending = spine.to_ending(p, carried=carried, offer=offer, max_jobs=30)
    p.mark(f'ENDING: {ending or "NONE REACHED"}; {spine.dw_flags(p)}; jobs tried {p.runs_tried}, done {p.runs_done}')
    if ending:
        spine.afterwards(p, shifts=16)
    p.finish(label)
    print(f'{label:<30} ending={ending or "-":<14} shift {g.city.shift} runs {g.char.runs} '
          f'(tried {p.runs_tried}, done {p.runs_done}) turns {p.turns} errors {len(p.errors)} '
          f'flags {spine.dw_flags(p)} notable {dict(p.seen)}')
    return p

campaign('read it, take the job', 'academic', 101, 'read', 'take')
campaign('archive it, publish', 'protege', 202, 'archive', 'publish')
campaign('burn it, hand it back', 'courier', 303, 'burn', 'refuse')
log.close()
