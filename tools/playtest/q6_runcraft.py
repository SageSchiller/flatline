"""Q6: run craft. Every technique the game has, typed in a network, in
context, by somebody trained to rank four in everything; and the city-side
commands no campaign ever typed (betray, uninstall, script, bind, new,
switch, delete). The finding is what refuses badly, reads wrong, or
crashes; the transcript is the deliverable."""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'q6_runcraft')
sys.path.insert(0, HERE)
os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play, NOFIGHT
import campaign as C
from campaign import act
from flatline.content import skills as SK, hardware as HW, cyberware as CW, factions as FAC
log = open(os.path.join(HERE, 'logs', 'q6_runcraft.log'), 'w')
p = Play('Q6: run craft, every technique', origin='academic', seed=1106, handle='Craft', log=log, prefer=NOFIGHT)
p.table = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse', 'lark.resolve': 'pay'}
g = p.g

act(p, C.setup, train=('intrusion',))
p.shortcut('every skill to rank 4, and 40,000c, because the techniques are the test')
for sk in SK.SKILLS:
    g.char.base_skills[sk.key] = 4
g.char.credits = 40000
p.do('skills'); p.do('techniques'); p.do('help techniques')

# -- what to type inside, spread over the runs so no one run burns on it --
def hosts(run):
    return [n for n in run.net.nodes.values() if n.known]

def a_service(run, node):
    return node.services[0].key if node.services else ''

def an_ice(run, node):
    return node.ice[0].key if node.ice else ''

BATCHES = [
    ('recon and the readers', lambda r, n, h: [
        'chart', 'listen', 'playbook', 'here', 'map', 'policy', f'policy {h}',
        f'odds crack {h} {a_service(r, n)}', 'odds strike', 'techniques', 'status']),
    ('the quiet doors', lambda r, n, h: [
        f'crack {h} {a_service(r, n)} --quiet', f'crack {h} {a_service(r, n)} --key',
        f'crack {h} {a_service(r, n)} --chain', f'pretext {h} {a_service(r, n)}',
        'sidechannel', 'impersonate', 'vouch', 'firstprinciples', 'intercept']),
    ('the other ways in', lambda r, n, h: [
        f'backdoor {h}', f'backway {h}', f'pivot {h}', f'connect {h} --ghost',
        f'connect {h} --present', f'misdirect {h}', 'overclock 1', 'nullsig', 'steady']),
    ('the defences', lambda r, n, h: [
        'focus', 'mask', 'brace', 'hymn', 'jury', 'native', 'nobody', 'remember',
        'correction', 'signal hold', 'signal move', 'scrub', 'dissociate']),
    ('the loud things', lambda r, n, h: [
        f'strike {an_ice(r, n)}', f'overload {an_ice(r, n)}', 'overload',
        f'falsify {FAC.FACTIONS[0].key}', 'daemon hold', 'daemon noise', 'daemon grind',
        'script list', 'requisition', 'requisition siphon']),
    ('the actions', lambda r, n, h: [
        'observe', 'plant', 'push', 'crash', 'collapse', 'ghost', 'wait 1',
        'hotswap ' + (HW.BY_KEY[next(iter(HW.BY_KEY))].key), 'signal out']),
]

def craft_run(batch_no):
    """One job; inside, one batch of verbs on a probed host, then the brief."""
    if g.city.current is None and C.take_softest(p) is None:
        p.do('rest'); p.settle(prefer=C.SAFE); return
    p.do('load'); C.ensure_payload(p)
    for _ in range(12):
        if g.over or p.sess.run is not None or g.city.current is None: break
        from flatline.commands import city as CC
        st = CC.city_steps(g)
        if not st or '<' in st[0][0] or st[0][0].startswith('jack'): break
        if st[0][0].split()[0] in C.READ_ONLY: break
        p.do_step(st[0][0], note=f'now says: {st[0][1][:60]}'); p.settle(prefer=C.SAFE)
    if p.sess.run is None:
        o = p.do('jack in')
        m = re.search(r'`((?:travel|walk) \w+)`', o)
        for _ in range(3):
            if '✗' not in o or not m: break
            p.do_step(m.group(1)); p.settle(prefer=C.SAFE); o = p.do('jack in')
            m = re.search(r'`((?:travel|walk) \w+)`', o)
        if '✗' in o and 'wrecked' in o:
            m2 = re.search(r'`(travel \w+)`', o)
            if m2:
                p.do_step(m2.group(1)); p.settle(prefer=C.SAFE)
            p.do('repair'); p.do('repair --confirm'); p.settle(prefer=('yes',)); o = p.do('jack in')
        if '✗' in o and 'shift' not in o: p.do('jack in --force')
    run = p.sess.run
    if run is None:
        return
    title, make = BATCHES[batch_no % len(BATCHES)]
    p.mark(f'inside: {title}')
    p.do('scan')
    for n in hosts(run)[:2]:
        p.do(f'probe {n.uid}')
    node = next((n for n in hosts(run) if n.services), None) or run.net.nodes[run.here]
    for cmd in make(run, node, node.uid):
        if p.sess.run is None: break
        p.do(cmd)
    if p.sess.run is not None:
        p.drive_run()
    p.answer_choices(p.table)

p.mark('twelve runs, each with one batch of technique inside')
for i in range(12):
    if g.over: break
    craft_run(i)
    if i % 4 == 3:
        p.do('journal'); p.do('record work'); p.do('char')
        if g.char.integrity < g.char.integrity_max // 2:
            p.do('clinic patch'); p.settle(prefer=('yes',))

p.mark('the city-side commands nobody typed: betray, uninstall, script, bind, new, switch, delete')
riv = next((r for r in g.city.rivals if r.alive), None)
if riv is not None:
    p.do('betray'); p.do(f'betray {riv.key}'); p.do(f'betray {riv.key} --confirm'); p.settle(prefer=('yes',))
    p.do(f'who {riv.key}')
C.go(p, 'glasshouse'); p.do('market ware')
cheap = sorted(CW.BY_KEY.values(), key=lambda w: w.price)
put = ''
for w in cheap[:6]:
    o = p.do(f'buy {w.key}'); p.settle(prefer=('yes',))
    if '✗' in o:
        continue
    o2 = p.do(f'install {w.key}'); p.settle(prefer=('yes',))
    if '✗' not in o2:
        put = w.key; break
p.do('chrome')
if put:
    p.do(f'uninstall {put}'); p.do(f'uninstall {put} --confirm'); p.settle(prefer=('yes',)); p.do('chrome')
p.do('script'); p.do('script help'); p.do('script list'); p.do('script write probe-all scan'); p.do('script show probe-all')
p.do('script save probe-all'); p.do('script run probe-all'); p.do('script drop probe-all')
p.do('bind'); p.do('bind zz scan'); p.do('bind'); p.do('zz')
p.do('characters'); p.do('new Spare --origin gutter'); p.settle(prefer=('yes', 'no'))
p.do('characters'); p.do('switch Craft'); p.settle(prefer=('yes',)); p.do('characters')
p.do('delete Spare'); p.do('delete Spare --confirm'); p.settle(prefer=('yes',)); p.do('characters')
p.do('history 5'); p.do('career'); p.do('title'); p.do('reset'); p.do('help reset')

p.mark('one character per origin, and the verb only that origin has')
ORIGIN_VERB = {'protege': 'vouch', 'bonded': 'requisition siphon', 'burnout': 'remember',
               'defector': 'policy', 'expolice': 'playbook', 'ghost': 'nobody',
               'chromed': 'native', 'chorister': 'hymn', 'gutter': 'jury',
               'printer': 'correction', 'academic': 'firstprinciples', 'courier': 'bolt'}
from flatline.content import origins as ORI
from flatline.commands import city as CC
for okey in ORI.BY_KEY:
    if g.over: break
    handle = 'Rc' + okey[:6].capitalize()
    o = p.do(f'new {handle} --origin {okey}'); p.settle(prefer=('yes', 'no'))
    g = p.g
    if g is None or g.char.handle != handle:
        p.mark(f'{okey}: could not become {handle}: ' + ' '.join(o.split())[:120]); continue
    p.do('spend'); p.settle(prefer=C.SAFE)
    for sk in SK.SKILLS: g.char.base_skills[sk.key] = 4
    g.char.credits = 30000
    p.do('techniques')
    verb = ORIGIN_VERB.get(okey, '')
    if C.take_softest(p) is None:
        p.mark(f'{okey}: no board'); continue
    p.do('load'); C.ensure_payload(p)
    for _ in range(12):
        if g.over or p.sess.run is not None or g.city.current is None: break
        st = CC.city_steps(g)
        if not st or '<' in st[0][0] or st[0][0].startswith('jack'): break
        if st[0][0].split()[0] in C.READ_ONLY: break
        p.do_step(st[0][0], note=f'now says: {st[0][1][:60]}'); p.settle(prefer=C.SAFE)
    if p.sess.run is None:
        o = p.do('jack in')
        m = re.search(r'`((?:travel|walk) \w+)`', o)
        for _ in range(3):
            if '✗' not in o or not m: break
            p.do_step(m.group(1)); p.settle(prefer=C.SAFE); o = p.do('jack in')
            m = re.search(r'`((?:travel|walk) \w+)`', o)
        if '✗' in o and 'shift' not in o: p.do('jack in --force')
    if p.sess.run is not None and verb and verb != 'bolt':
        run = p.sess.run
        p.do('scan')
        for n in hosts(run)[:2]: p.do(f'probe {n.uid}')
        node = next((n for n in hosts(run) if n.services), None) or run.net.nodes[run.here]
        p.mark(f'{okey}: {verb}')
        p.do(verb if verb != 'policy' else f'policy {node.uid}')
        p.do(verb)
        p.drive_run()
    elif verb == 'bolt':
        p.mark(f'{okey}: bolt is a street answer; walk until the street asks')
        if p.sess.run is not None: p.drive_run()
        for d in ('ninth', 'shambles', 'marrow'):
            C.go(p, d)
    p.answer_choices(p.table)
    p.do('char'); p.do('characters'); p.do('switch Craft'); p.settle(prefer=('yes',))
    g = p.g
    p.do(f'delete {handle} --confirm'); p.settle(prefer=('yes',))
p.do('characters')
act(p, C.record_and_titles)
p.finish('q6_runcraft')
print(C.summary(p, 'q6_runcraft'))
log.close()
