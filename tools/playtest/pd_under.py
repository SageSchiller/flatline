"""Persona D: says yes to everyone. Reads the log, lets the Archivist have
theirs, keeps Lark alive, and takes the other door. Nobody has."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'D')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
import spine
log = open(os.path.join(HERE, 'logs', 'pd_under.log'), 'w')
TABLE = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse',
         'lark.resolve': 'vance', 'archive.yours': 'yes', 'sparrow.deck': 'teach'}

def campaign(label, seed, final):
    p = Play(f'UNDER: {label}', origin='academic', seed=seed, handle='Fathom', log=log)
    g = p.g
    table = dict(TABLE); table['deepwater.under'] = final
    p.do('spend'); p.settle()
    p.mark('act one: five jobs')
    n = 0
    while g.char.runs < 5 and not g.over and n < 12:
        n += 1; p.play_job(); p.answer_choices(table); p.do('journal')
    p.mark(f'five runs: {spine.dw_flags(p)}')
    p.mark('Lark, early, before anything else')
    spine.meet(p, 'lark', 'shambles', waits=4); p.answer_choices(table)
    p.mark('the Archivist')
    for d in spine.FENCE:
        if spine.meet(p, 'archivist', d, waits=4):
            break
    p.answer_choices(table); p.do('journal')
    p.mark(f'the posting, until it is done: {spine.dw_flags(p)}')
    tries = 0
    while ('did:deepwater.posting' not in g.story.flags and tries < 7
           and not g.over and p.turns < 900):
        tries += 1
        story = [c for c in g.city.board if c.story == 'deepwater.posting']
        cur = g.city.current
        if cur is not None and cur.story == 'deepwater.posting':
            p.auto_city(12); 
            if p.sess.run is not None: p.auto_run()
        elif story and cur is None:
            p.mark(f'taking the posting, attempt {tries}')
            spine.run_contract(p, story[0].cid)
        else:
            p.play_job()
        p.answer_choices(table); p.do('journal'); p.do('look'); p.settle()
    p.mark(f'the posting: {"done" if "did:deepwater.posting" in g.story.flags else "NOT DONE after " + str(tries)}; {spine.dw_flags(p)}')
    p.mark('Lark again, and the Archivist again: the two consents')
    for _ in range(3):
        if g.over: break
        spine.go(p, 'shambles'); p.do('look'); p.settle(); p.answer_choices(table)
        p.do('rest'); p.settle(); p.answer_choices(table)
        if 'lark_saved' in g.story.flags: break
    for _ in range(3):
        if g.over or 'archive_consented' in g.story.flags: break
        for d in spine.FENCE:
            if spine.meet(p, 'archivist', d, waits=3): break
        p.answer_choices(table); p.do('rest'); p.settle(); p.answer_choices(table)
    p.mark(f'consents: {sorted(f for f in g.story.flags if f in ("lark_saved","lark_dead","archive_consented","archive_refused","dw_read","dw_offer"))}')
    p.mark('the offer, then the other door')
    for i in range(24):
        if g.over: break
        if 'dw_under' in g.story.flags or 'dw_stayed' in g.story.flags: break
        p.do('rest'); p.settle(); p.do('look'); p.settle()
        p.answer_choices(table)
        if i % 4 == 3: p.do('journal'); p.do('journal deepwater'); p.do('now')
    p.mark(f'END: over={g.over!r}; {spine.dw_flags(p)}')
    for c in ('journal', 'record', 'rice palette', 'char', 'log', 'career', 'characters', 'now'):
        p.do(c)
    if not g.over:
        spine.afterwards(p, shifts=10)
    p.finish(label)
    # the next character, made the real way, to see what arrives
    q = Play(f'UNDER: after {label}, the next one', origin='gutter', seed=seed + 1, handle='Sounding', log=log)
    q.sess.game = None
    q.do(f'new Sounding --origin gutter --seed {seed + 1}'); q.settle(prefer=('yes',))
    for c in ('characters', 'record', 'char', 'journal', 'now', 'news'):
        q.do(c)
    q.finish(f'after {label}')
    print(f'{label:<8} over={g.over!r:<14} shift {g.city.shift} runs {g.char.runs} turns {p.turns} errors {len(p.errors)+len(q.errors)} flags {spine.dw_flags(p)}')

campaign('go', 401, 'go')
campaign('stay', 402, 'stay')
log.close()
