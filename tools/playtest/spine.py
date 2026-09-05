"""The main line, played: meet the people, get the posting, choose, live after."""
from flatline.content import districts, npcs as NPC
from flatline.commands import city as city_cmd

ENDINGS = {'dw_employed', 'dw_published', 'dw_refused', 'dw_under', 'dw_stayed'}
FENCE = [d.key for d in districts.DISTRICTS if 'fence' in d.services]

def dw_flags(p):
    return sorted(x for x in p.g.story.flags if x.startswith(('dw_', 'after_', 'did:deepwater')))

def go(p, district):
    for _ in range(8):
        if p.g.city.where == district or p.g.over or p.sess.run is not None:
            break
        p.do(f'walk {district}'); p.settle()
    return p.g.city.where == district

def meet(p, key, district, waits=5):
    """Go where somebody is, wait for their hours, talk, ask them everything."""
    go(p, district)
    for _ in range(waits):
        if p.g.over:
            return False
        if key in p.present():
            break
        p.do('look')
        p.do('rest'); p.settle()
    if key not in p.present():
        p.do('look')
        return False
    npc = NPC.BY_KEY[key]
    out = p.do(f'talk {key}'); p.settle()
    if out.lstrip().startswith('✗'):
        p.do(f'talk {npc.name.split()[-1].lower()}'); p.settle()
    for topic in npc.topics:
        p.do(f'ask {key} {topic}'); p.settle()
    return f'met:{key}' in p.g.story.flags

def board_deepwater(p):
    return [c for c in p.g.city.board
            if c.target == 'deepwater' or 'Four Hundred' in c.title]

def run_contract(p, cid):
    p.do(f'take {cid}'); p.settle()
    for _ in range(14):
        if p.g.over or p.sess.run is not None:
            break
        steps = city_cmd.city_steps(p.g)
        if not steps:
            break
        p.do(steps[0][0], note=f'now says: {steps[0][1][:70]}'); p.settle()
    if p.sess.run is not None:
        p.drive_run()

def facts(p):
    """Act two: the Archivist (fence, afternoon/night, runs 5) and Remnant
    (Glasshouse clinic, runs 3). Returns what the story now holds."""
    p.mark('act two: the Archivist')
    got_a = False
    for d in FENCE:
        if meet(p, 'archivist', d, waits=4):
            got_a = True; break
    p.mark(f'the Archivist: {"met" if got_a else "NOT FOUND"}; {dw_flags(p)}')
    p.mark('act two: Remnant')
    got_r = meet(p, 'remnant', 'glasshouse', waits=4)
    p.mark(f'Remnant: {"met" if got_r else "NOT FOUND"}; {dw_flags(p)}')
    p.do('journal')
    return dw_flags(p)

def to_ending(p, carried='read', offer='take', max_jobs=30):
    """Act three to five, by playing. Returns the ending flag, or ''."""
    jobs = 0
    while jobs < max_jobs and not p.g.over:
        flags = p.g.story.flags
        if flags & ENDINGS:
            break
        found = p.g.story.open_choice()
        if found is not None:
            thread, stage = found
            pick = {'carried': carried, 'offer': offer}.get(stage.key)
            p.mark(f'a decision is open: {thread.key}.{stage.key}, choosing {pick or "the first"}')
            p.choose_open(pick)
            continue
        dw = board_deepwater(p)
        if dw and p.g.city.current is None:
            p.mark(f'a Deepwater job on the board: {dw[0].title} ({dw[0].cid}); {dw_flags(p)}')
            run_contract(p, dw[0].cid); jobs += 1
        else:
            p.play_job(); jobs += 1
        p.do('journal')
        p.do('look'); p.settle()
    flags = p.g.story.flags
    return sorted(flags & ENDINGS)[0] if flags & ENDINGS else ''

def afterwards(p, shifts=16):
    p.mark(f'after the ending: {dw_flags(p)}')
    for i in range(shifts):
        if p.g.over:
            break
        p.do('rest'); p.settle()
        p.do('look'); p.settle()
        if p.g.story.open_choice() is not None:
            p.choose_open()
        p.do('news')
        if i % 4 == 0:
            p.do('journal'); p.do('now')
    p.mark(f'the city afterwards: {dw_flags(p)}')
    for c in ('journal', 'record', 'rice', 'char', 'world', 'board', 'now', 'help deepwater'):
        p.do(c)
