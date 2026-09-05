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
        p.do_step(f'walk {district}'); p.settle()
    return p.g.city.where == district

def meet(p, key, district, waits=5):
    """Go where somebody is, wait for their hours, talk, ask them everything."""
    go(p, district)
    npc = NPC.BY_KEY[key]
    for _ in range(waits):
        if p.g.over:
            return False
        if key in p.present():
            break
        p.do('look')
        if npc.at:
            # Somebody who keeps to one place is found there, not in the street.
            p.do(f'visit {npc.at}'); p.settle()
            if key in p.present():
                break
        p.do('rest'); p.settle()
    if key not in p.present():
        p.do('look')
        return False
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
    if p.g.city.current is None or p.g.city.current.cid != cid:
        p.do(f'take {cid}'); p.settle()
    try:
        import campaign
        campaign.ensure_payload(p)
    except Exception:
        pass
    for _ in range(14):
        if p.g.over or p.sess.run is not None:
            break
        steps = city_cmd.city_steps(p.g)
        if not steps:
            break
        p.do_step(steps[0][0], note=f'now says: {steps[0][1][:70]}'); p.settle()
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
        if found is not None and p.sess.run is not None:
            # `choose` is a city command; a run left open is the harness's
            # fault, not a decision that cannot be answered.
            p.do('jack out'); p.settle()
            if p.sess.run is not None:
                p.do('jack out --anyway'); p.settle()
        if found is not None:
            thread, stage = found
            table = getattr(p, 'table', None) or {}
            pick = ({'carried': carried, 'offer': offer}.get(stage.key)
                    or table.get(f'{thread.key}.{stage.key}'))
            p.mark(f'a decision is open: {thread.key}.{stage.key}, choosing {pick or "the first"}')
            p.choose_open(pick)
            again = p.g.story.open_choice()
            if again is not None and again[1] is stage:
                # It did not close. Try every other answer once, then stop:
                # a decision no answer closes is a finding, not a loop.
                for c in stage.choices:
                    if c.key == pick:
                        continue
                    p.choose_open(c.key)
                    if p.g.story.open_choice() is None or p.g.story.open_choice()[1] is not stage:
                        break
                else:
                    p.mark(f'FINDING: {thread.key}.{stage.key} stays open whatever is chosen')
                    break
            continue
        dw = board_deepwater(p)
        cur = p.g.city.current
        if dw and cur is not None and cur.cid != dw[0].cid and 'Four Hundred' in dw[0].title:
            # The posting with your name in it outranks whatever half-done
            # board job is still accepted; a player drops that for this.
            p.do('drop'); p.settle()
            cur = p.g.city.current
        if dw and cur is None:
            p.mark(f'a Deepwater job on the board: {dw[0].title} ({dw[0].cid}); {dw_flags(p)}')
            run_contract(p, dw[0].cid); jobs += 1
        elif dw and cur is not None and cur.cid == dw[0].cid:
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
