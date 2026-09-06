"""Q8: one life per origin. Twelve characters, twenty shifts each, each
following the thread only their origin has: meet who it asks for, run what
it asks for, answer it, and say how far it got. The seven origin threads
were the last content verified by state rather than by play."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q8_origins')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, NOFIGHT
import campaign as C
from campaign import act
import spine
from flatline.content import origins as ORI, threads as TC, npcs as NPC
log = open(os.path.join(HERE, 'logs', 'q8_origins.log'), 'w')
p = Play('Q8: one life per origin', origin='gutter', seed=1108, handle='First', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse'}
results = {}
first = True
for okey in ORI.BY_KEY:
    thread = next((t for t in TC.THREADS if any(r == f'origin:{okey}' for r in t.stages[0].requires)), None)
    handle = 'Or' + okey[:6].capitalize()
    if first:
        # The first character is the one Play made; become the origin instead.
        first = False
    o = p.do(f'new {handle} --origin {okey}'); p.settle(prefer=('yes', 'no'))
    g = p.g
    if g is None or g.char.handle != handle:
        results[okey] = 'could not become them: ' + ' '.join(o.split())[:100]; continue
    p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse'}
    p.mark(f'{okey}: {thread.key if thread else "no origin thread"} ({thread.name if thread else ""})')
    p.do('spend'); p.settle(prefer=C.SAFE); p.do('techniques'); p.do('journal')
    p.shortcut('intrusion 3 and 6,000c: the thread is the test, not the first week')
    g.char.base_skills['intrusion'] = max(3, g.char.base_skills.get('intrusion', 0)); g.char.credits = max(g.char.credits, 6000)
    if thread is None:
        results[okey] = 'no origin thread'; continue
    first_stage = thread.stages[0]
    needs = list(first_stage.requires) + list(first_stage.any_of[:1])
    # what the opener asks for, by play where play can do it
    for rule in needs:
        if rule.startswith('met:'):
            npc = NPC.BY_KEY.get(rule[4:])
            if npc is not None and npc.where:
                spine.meet(p, npc.key, npc.where, waits=4)
        elif rule.startswith('runs:'):
            want = int(rule[5:])
            n = 0
            while g.char.runs < want and n < want + 4 and not g.over:
                n += 1; C.run_job(p)
        elif rule.startswith('shift:'):
            while g.city.shift < int(rule[6:]) and not g.over:
                p.do('rest'); p.settle(prefer=C.SAFE)
        elif rule.startswith(('diss:', 'heat:', 'credits:', 'debt:', 'rep:')):
            p.shortcut(f'{rule}: set by hand, the twenty shifts cannot earn it')
            kind, _, value = rule.partition(':')
            if kind == 'diss': g.char.dissonance = int(value)
            elif kind == 'credits': g.char.credits = int(value)
            elif kind == 'heat': g.alias.add_heat('sixes', int(value) + 5)
            elif kind == 'debt': g.debt.amount = int(value) + 1; g.debt.lender = 'sixes'
    if first_stage.where:
        C.go(p, first_stage.where)
    # then live until the thread has said everything it will, or twenty shifts
    start = g.city.shift
    reached = lambda: list(g.story.reached.get(thread.key, []))
    for i in range(60):
        if g.over or g.city.shift - start > 30: break
        # Stand where the next scene happens, if it happens somewhere.
        nxt = next((st for st in thread.stages if st.key not in reached()), None)
        if nxt is not None and nxt.where and g.city.where != nxt.where and g.city.current is None:
            C.go(p, nxt.where)
        p.do('look'); p.settle(prefer=C.SAFE)
        found = g.story.open_choice()
        if found is not None:
            if found[0].key == thread.key:
                p.do('choose')
            p.answer_choices(p.table)
        if len(reached()) >= len(thread.stages) and g.story.open_choice() is None:
            break
        # A scene that posts a job advances only when that job is done:
        # take the thread's own posting over anything softer.
        posting = next((c for c in g.city.board if (c.story or '').startswith(thread.key + '.')), None)
        cur = g.city.current
        if cur is not None and (cur.story or '').startswith(thread.key + '.'):
            # accepted and not yet done: again, and the second time as an inside job
            if not (cur.approach or {}).get('kind'):
                p.do('approach inside --confirm'); p.settle(prefer=('yes',))
            # A posting that has beaten this life once gets a stronger one:
            # the thread is the test, not the run.
            p.shortcut('intrusion, stealth and cryptography 4, and a mask, for the thread posting')
            for sk in ('intrusion', 'stealth', 'cryptography'):
                g.char.base_skills[sk] = max(4, g.char.base_skills.get(sk, 0))
            g.char.credits = max(g.char.credits, 8000)
            if not g.char.deck.has_category('mask'):
                p.do('market programs')
                for mk in ('understair', 'quietcastle'):
                    o = p.do(f'buy {mk}')
                    if '✗' not in o:
                        C.ensure_payload(p); p.do(f'load {mk}'); break
            spine.run_contract(p, cur.cid)
        elif posting is not None and g.city.current is None:
            spine.run_contract(p, posting.cid)
        elif i % 3 == 2:
            C.run_job(p)
        else:
            p.do('rest'); p.settle(prefer=C.SAFE)
    p.do('journal ' + thread.key)
    results[okey] = f'{thread.key}: stages {reached()} of {[s.key for s in thread.stages]}, decided {[c for st, c in g.story.decided(thread.key)] if hasattr(g.story, "decided") else "?"}'
    p.mark(f'{okey} -> {results[okey]}')
    if g.over:
        p.mark(f'{okey}: over={g.over!r}')
p.finish('q8_origins')
for k, v in results.items():
    print(f'{k:10} {v}'[:220])
print(C.summary(p, 'q8_origins'))
log.close()
