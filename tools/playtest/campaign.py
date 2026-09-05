"""Full-campaign acts (task after D157): the pieces of a long life in the
city, each one typing the real commands, so five personas can compose a
whole career in five different orders and the transcript shows every system
answering. Every act is guarded: a persona bug is logged as a PERSONA ERROR
and the campaign goes on, because the finding is in the game's transcript,
not in the script that drives it."""
import re, traceback
import flatline.content.threads  # break the arcs/threads import cycle first
from flatline.content import (districts, npcs as NPC, hardware, mods as MODS,
                              safehouses as SH, cyberware as CW, programs as PR,
                              pit as PIT, rivals as RV, pets as PETS, spots as SPOTS)
from flatline.commands import city as city_cmd
import spine

SAFE = ('give', 'talk', 'run', 'pay', 'bolt', 'yes', 'take', 'careful', 'break')


def act(p, fn, *a, **kw):
    """Run one act; a persona-side exception is a note in the log, not the
    end of the campaign."""
    try:
        return fn(p, *a, **kw)
    except Exception as e:
        p.log.write(f'\n!!! PERSONA ERROR in {fn.__name__}: {e!r}\n{traceback.format_exc()[-900:]}\n')
        p.errors.append((fn.__name__, repr(e), traceback.format_exc()[-800:]))
        return None


def go(p, district):
    """Walk somewhere, taking the street's outs when it refuses."""
    for _ in range(8):
        if p.g.city.where == district or p.g.over or p.sess.run is not None:
            break
        p.do_step(f'walk {district}'); p.settle(prefer=SAFE)
    return p.g.city.where == district


def cheapest(coll, attr='price', where=None):
    items = [x for x in coll.values() if int(getattr(x, attr, 10**9) or 0) > 0]
    if where is not None:
        items = [x for x in items if where(x)]
    return min(items, key=lambda x: int(getattr(x, attr, 10**9))) if items else None


#: `now` steps that only read; a follower that types them for ever is stuck.
READ_ONLY = {'status', 'board', 'char', 'job', 'now', 'look', 'skills', 'market'}


def ensure_payload(p):
    """Carry what the contract needs, the way a player who read `jack in`
    would: buy the cheapest program of the needed category, make room,
    load it."""
    from flatline.world.contracts import OBJECTIVE_PROGRAM
    c = p.g.city.current
    if c is None:
        return
    need = OBJECTIVE_PROGRAM.get(c.objective, '')
    deck = p.g.char.deck
    if not need or deck.has_category(need):
        return
    owned = [k for k in p.g.char.library if k in PR.BY_KEY and PR.BY_KEY[k].category == need]
    if not owned:
        buyable = sorted((x for x in PR.BY_KEY.values() if x.category == need and not x.unique),
                         key=lambda x: (x.memory, x.price))
        for prog in buyable[:3]:
            if p.g.char.credits < prog.price:
                continue
            p.do('market programs')
            o = p.do(f'buy {prog.key}'); p.settle(prefer=('yes',))
            if '✗' not in o:
                owned = [prog.key]; break
    if not owned:
        return
    key = owned[0]
    for _ in range(3):
        ok, _why = deck.can_load(key)
        if ok:
            break
        loaded = [k for k in deck.loaded if PR.BY_KEY.get(k) and PR.BY_KEY[k].category != 'breaker']
        if not loaded:
            break
        p.do(f'unload {loaded[-1]}')
    if not deck.can_load(key)[0] and deck.familiar:
        # A player keeps the familiar until the job needs the room.
        p.do('familiar drop', note='the job needs the memory')
    if deck.can_load(key)[0]:
        p.do(f'load {key}')
    p.do('load')


def buy_rows(p, listing_cmd, rows=(1,), settle=('yes',)):
    """Buy by row from a shelf just listed, which is what a player does."""
    out = p.do(listing_cmd)
    have = re.findall(r'^\s*(\d+)\s{2}', out, re.M)
    bought = []
    for r in rows:
        if str(r) in have:
            o = p.do(f'buy {r}'); p.settle(prefer=settle)
            if '✗' not in o:
                bought.append(r)
    return bought


# -- acts -----------------------------------------------------------------

def setup(p, train=(), boost='', reads=()):
    p.mark('night one: who am I, and what does the game say to read')
    p.do('now'); p.do('tutorial skip'); p.do('spend'); p.settle(prefer=SAFE)
    for sk in train:
        p.do(f'train {sk}')
    if boost:
        p.do(f'boost {boost}')
    for c in ('skills', 'techniques', 'char --effects', 'char --attributes', 'self',
              'help', 'help topics', 'help commands', 'trait', 'ambitions', 'world',
              'district', 'map', 'look', 'people', 'board', 'deck', 'chem', 'debt',
              'safehouse', 'home', 'pet', 'familiar', 'record', 'called', 'rice',
              'icon', 'career', 'history 5', 'log 5', 'news', 'mail', 'ads') + tuple(reads):
        p.do(c); p.settle(prefer=SAFE)


def deck_life(p):
    """The deck as a thing with a body: name it, fit a component, a mod, the
    bench, and the four city-side deck commands."""
    p.mark('the deck as a thing you own')
    p.do('deck'); p.do('deck name Ferryman'); p.do('deck')
    p.do('market components'); p.do('market ware'); p.do('market programs')
    comp = cheapest(hardware.BY_KEY)
    if comp is not None:
        p.do(f'buy {comp.key} --why'); p.do(f'buy {comp.key}'); p.settle(prefer=('yes',))
        p.do(f'fit {comp.key}'); p.settle(prefer=('yes',))
    p.do('mod')
    mod = cheapest(MODS.BY_KEY)
    if mod is not None:
        p.do(f'mod {mod.key}'); p.do(f'mod {mod.key} --confirm'); p.settle(prefer=('yes',))
    p.do('repair'); p.do('repair --confirm'); p.settle(prefer=('yes',))
    p.do('tune'); p.do(f'tune {p.g.city.where}'); p.do('sweep'); p.do(f'sweep {p.g.city.where}')
    other = next((d.key for d in districts.DISTRICTS if d.key != p.g.city.where), 'ninth')
    p.do(f'route {other}'); p.do('load'); p.do('salvage'); p.do('deck'); p.do('inspect 1')


def city_deck(p):
    """The deck as a thing you live with: mail, search, watch, message, ads."""
    p.mark('the deck in the city: what is it saying tonight')
    for c in ('mail', 'mail all', 'news 5', 'ads', 'world', 'log 8', 'rep', 'who',
              'people', 'rumours', 'district', 'map --flat', 'watch'):
        p.do(c)
    p.do('search deepwater'); p.do('search kagawa'); p.do('watch deepwater'); p.do('watch')
    riv = next((r for r in p.g.city.rivals if r.alive), None)
    if riv is not None:
        p.do(f'who is {riv.key}'); p.do(f'who {riv.key}'); p.do(f'search {riv.key}')
        p.do(f'message {riv.key} you working tonight'); p.do(f'watch {riv.key}')
        p.do(f'render {riv.key}')
    p.do('render'); p.do('render deepwater'); p.do('watch drop deepwater'); p.do('mail')


DROPPED = set()


def take_softest(p):
    p.do('board')
    choices = [c for c in p.g.city.board if c.cid not in DROPPED] or list(p.g.city.board)
    if choices and p.g.city.current is None:
        soft = min(choices, key=lambda c: c.posture)
        p.do(f'board {soft.cid}'); p.do(f'take {soft.cid}'); p.settle(prefer=SAFE)
        return soft
    return None


def run_job(p, approach='', legwork='', hire=False, extra=()):
    """One job, typed the long way: take, legwork, approach, hire, walk,
    jack in, the run's own reading commands, then the brief to the end."""
    before = p.g.char.runs
    if p.g.city.current is None and take_softest(p) is None:
        p.do('rest'); p.settle(prefer=SAFE); return False
    c = p.g.city.current
    if legwork:
        p.do('legwork'); p.do(f'legwork {legwork}'); p.settle(prefer=SAFE)
    if approach:
        p.do('approach'); p.do(f'approach {approach}'); p.settle(prefer=('yes',))
    if hire and p.g.char.credits > 6000:
        p.do('hire')
        riv = min([r for r in p.g.city.rivals if r.alive],
                  key=lambda r: r.disposition * -1, default=None)
        if riv is not None:
            p.do(f'hire {riv.key} --confirm'); p.settle(prefer=('yes',))
    p.do('job'); p.do('load')
    ensure_payload(p)
    last = ''
    for _ in range(16):
        if p.g.over or p.sess.run is not None or p.g.city.current is None:
            break
        steps = city_cmd.city_steps(p.g)
        if not steps or '<' in steps[0][0]:
            break
        step = steps[0][0]
        if step.startswith('jack') or step.split()[0] in READ_ONLY or step == last:
            break
        if step == 'drop':
            # `now` says drop because the walk is hot. A player who wants
            # the money takes the priced walk the reason names, or the
            # arrangement or the burn if `now` lists one; dropping is last.
            alt = next((v for v, _ in steps[1:] if v.startswith(('arrange', 'burn'))), '')
            m = re.search(r'`(\w+ \w+ --anyway)`', steps[0][1])
            if m:
                p.do_step(m.group(1), note='now says drop; walking into it priced'); p.settle(prefer=SAFE)
                last = m.group(1); continue
            if alt:
                p.do(alt, note='now says drop; taking its other out'); p.settle(prefer=('yes',))
                last = alt; continue
            p.do('drop'); DROPPED.add(c.cid); break
        p.do_step(step, note=f'now says: {steps[0][1][:70]}'); p.settle(prefer=SAFE)
        last = step
    if p.sess.run is None and p.g.city.current is not None:
        o = p.do('jack in')
        m = re.search(r'`((?:travel|walk) \w+)`', o)
        for _ in range(3):
            if '✗' not in o or not m:
                break
            p.do_step(m.group(1)); p.settle(prefer=SAFE)
            o = p.do('jack in')
            m = re.search(r'`((?:travel|walk) \w+)`', o)
        if '✗' in o and 'shift' not in o:
            p.do('jack in --force')
    if p.sess.run is not None:
        for c in ('here', 'status', 'job', 'map', 'scan', 'listen', 'chart', 'playbook',
                  'techniques', 'odds') + tuple(extra):
            p.do(c)
        p.drive_run()
    p.answer_choices(p.table)
    return p.g.char.runs > before


def jobs(p, n=8, approach='', legwork='', hire=False, extra=()):
    p.mark(f'{n} jobs the long way (approach={approach or "breach"}, legwork={legwork or "none"}, hire={hire})')
    done = 0
    for i in range(n):
        if p.g.over:
            break
        if run_job(p, approach=approach if i % 2 == 0 else '',
                   legwork=legwork if i % 3 == 0 else '', hire=hire and i % 2 == 1,
                   extra=extra if i == 0 else ()):
            done += 1
        if i % 3 == 2:
            p.do('journal'); p.do('salvage'); p.do('record work'); p.do('rep')
        p.do('look'); p.settle(prefer=SAFE)
    p.mark(f'jobs: {done}/{n} finished, runs {p.g.char.runs}, credits {p.g.char.credits}')
    return done


def people(p, limit=6):
    """Everyone here: talk, ask them everything, a favour, a deal."""
    p.mark('the people in the room')
    p.do('people'); p.do('look'); p.do('rumours')
    met = 0
    for key in p.present()[:limit]:
        npc = NPC.BY_KEY.get(key)
        if npc is None:
            continue
        p.do(f'talk {key}'); p.settle(prefer=SAFE)
        for t in list(npc.topics)[:3]:
            p.do(f'ask {key} {t}'); p.settle(prefer=SAFE)
        p.do(f'ask {key} favour'); p.settle(prefer=SAFE)
        p.do(f'inspect {key}')
        met += 1
    p.do('deal'); p.settle(prefer=SAFE)
    riv = next((r for r in p.g.city.rivals if r.alive), None)
    if riv is not None:
        p.do(f'deal {riv.key} work'); p.settle(prefer=SAFE)
    p.answer_choices(p.table)
    p.do('journal'); p.do('record people')
    p.mark(f'people: talked to {met}, threads open {len(p.g.story.reached)}')


def safehouse(p):
    if p.g.city.safehouse:
        return True
    p.mark('a place to keep things: buy a safehouse')
    p.do('safehouse')
    for house in sorted(SH.BY_KEY.values(), key=lambda h: h.price):
        if p.g.char.credits < house.price:
            p.shortcut(f'credits {p.g.char.credits} -> {house.price + 2000} for the safehouse')
            p.g.char.credits = house.price + 2000
        go(p, house.where)
        p.do(f'safehouse buy {house.key}'); p.settle(prefer=('yes',))
        if p.g.city.safehouse:
            break
    p.do('safehouse'); p.do('home')
    return bool(p.g.city.safehouse)


def pets(p, animal='cat', name='Ledger', familiar='pixelcat', fname='Echo'):
    """Both kinds: the animal at the safehouse, the familiar on the deck."""
    if safehouse(p):
        p.mark(f'a {animal} called {name}')
        go(p, 'ninth'); p.do('pet get')
        p.do(f'pet get {animal}'); p.settle(prefer=('yes',))
        if not p.g.city.pet:
            for a in PETS.ANIMALS:
                p.do(f'pet get {a.key}'); p.settle(prefer=('yes',))
                if p.g.city.pet:
                    break
        p.do(f'pet name {name}'); p.do('pet')
        p.do('pet feed buy'); p.do('pet feed'); p.do('pet water'); p.do('pet play'); p.do('pet')
        p.do('home')
    p.mark(f'a familiar called {fname}')
    p.do('familiar'); p.do('familiar get')
    o = p.do(f'familiar get {familiar}')
    if '✗' in o:
        loaded = list(p.g.char.deck.loaded)
        for prog in loaded[::-1][:2]:
            p.do(f'unload {prog}')
        p.do(f'familiar get {familiar}')
    p.do(f'familiar name {fname}'); p.do('familiar'); p.do('deck'); p.do('familiar tend'); p.do('home')


def pet_care(p):
    """Between acts: keep what you keep alive."""
    if p.g.city.pet:
        p.do('pet')
        if int(p.g.city.pet.get('feed', 0)) <= 0:
            p.do('pet feed buy')
        p.do('pet feed'); p.do('pet water'); p.do('pet play')
    if p.g.char.deck.familiar:
        p.do('familiar tend')


def money(p):
    """Debt, the lenders, the tables, the fence, the stash."""
    p.mark('money: the lender, the tables, the fence, the stash')
    p.do('debt'); p.do('borrow'); p.do('borrow 800'); p.do('borrow 800 --confirm'); p.settle(prefer=('yes',))
    p.do('debt'); p.do('debt pay 200'); p.do('debt pay all'); p.settle(prefer=('yes',)); p.do('debt')
    p.do('cards'); p.do('cards 50'); p.settle(prefer=SAFE)
    p.do('dice'); p.do('dice 50 high'); p.settle(prefer=SAFE); p.do('dice 50 seven'); p.settle(prefer=SAFE)
    spare = [k for k in p.g.char.library if k not in p.g.char.deck.loaded]
    if spare:
        p.do(f'sell {spare[0]}'); p.settle(prefer=('yes',))
    if p.g.city.safehouse:
        p.do('safehouse money 200'); p.do('safehouse')
        loaded = list(p.g.char.deck.loaded)
        if loaded:
            p.do(f'unload {loaded[-1]}'); p.do(f'safehouse stash {loaded[-1]}')
            p.do('safehouse'); p.do(f'safehouse take {loaded[-1]}'); p.do(f'load {loaded[-1]}')
    p.do('char'); p.do('record')


def street(p, fighter=False, nights=6):
    """The meat side: errands, the clinic, the pit, what you carry."""
    p.mark(f'the street{" as a fighter" if fighter else ""}: errands, clinic, the pit')
    p.do('market weapons'); p.do('market armour')
    if fighter:
        from flatline.content import weapons as W, armour as A
        w = cheapest(W.BY_KEY); a = cheapest(A.BY_KEY)
        if w: p.do(f'buy {w.key}'); p.settle(prefer=('yes',)); p.do(f'carry {w.key}')
        if a: p.do(f'buy {a.key}'); p.settle(prefer=('yes',)); p.do(f'wear {a.key}')
    p.do('carry'); p.do('wear')
    go(p, PIT.WHERE)
    p.do('pit'); p.do('clinic')
    for i in range(nights):
        if p.g.over:
            break
        p.do('errands')
        if not p.g.city.errand:
            p.do('errands take 1'); p.settle(prefer=SAFE)
        if fighter and p.g.city.phase == 'night':
            p.do('pit next 0'); p.settle(prefer=p.prefer)
        if p.g.char.integrity < p.g.char.integrity_max // 2:
            p.do('clinic patch'); p.settle(prefer=('yes',))
        p.do('rest'); p.settle(prefer=SAFE)
        p.answer_choices(p.table)
    p.do('errands drop'); p.do('record floor'); p.do('pit'); p.do('char')


def chrome_and_chem(p, wares=2, drug='redline', doses=4):
    """Chrome to the first band of drift, a habit, and coming off it."""
    p.mark(f'chrome ({wares} pieces) and a {drug} habit')
    go(p, 'glasshouse'); p.do('clinic'); p.do('chrome'); p.do('market ware')
    if p.g.char.credits < 6000:
        p.shortcut(f'credits {p.g.char.credits} -> 9000 for the chrome')
        p.g.char.credits = 9000
    put = 0
    before = set(getattr(p.g.char, 'cyberware', []) or [])
    for row in range(1, 1 + wares):
        out = p.do('market ware')
        rows = re.findall(r'^\s*(\d+)\s{2}', out, re.M)
        if str(row) not in rows:
            break
        o = p.do(f'buy {row}'); p.settle(prefer=('yes',))
        m = re.search(r'\u2713 (.+?) (?:is yours|bought)', o)
        p.do('chrome')
        p.do('install'); p.settle(prefer=('yes',))
        p.do('rest'); p.settle(prefer=SAFE); p.answer_choices(p.table)
    p.do('chrome'); p.do('char'); p.do('ground'); p.do('rice palette')
    go(p, 'shambles'); p.do('chem')
    for _ in range(doses):
        out = p.do('market drugs')
        m = re.search(r'^\s*(\d+)\s{2}' + re.escape(drug.replace('_', ' ').title()), out, re.M | re.I)
        row = m.group(1) if m else (re.findall(r'^\s*(\d+)\s{2}', out, re.M) or ['1'])[0]
        p.do(f'buy {row}'); p.settle(prefer=('yes',))
        held = [k for k in getattr(p.g.char, 'chem', {}).get('held', {}) ] if isinstance(getattr(p.g.char, 'chem', None), dict) else []
        p.do(f'dose {drug}'); p.settle(prefer=SAFE)
        p.do('rest'); p.settle(prefer=SAFE); p.answer_choices(p.table)
    p.do('chem'); p.do(f'chem {drug}'); p.do('detox'); p.do(f'detox {drug} --confirm'); p.settle(prefer=('yes',))
    p.do('rest'); p.settle(prefer=SAFE); p.do('chem'); p.do('char --effects')


def walk_all(p, visits=3):
    """Every district, the places in it, the finds the walking turns up."""
    p.mark('the walking: every district and what is in it')
    stood = 0
    for d in districts.DISTRICTS:
        if p.g.over:
            break
        if not go(p, d.key):
            continue
        p.do('look'); p.do('district'); p.do('rumours')
        out = p.do('visit')
        rows = re.findall(r'^\s*(\d+)\s', out, re.M)[:visits]
        for row in rows:
            p.do(f'visit {row}'); p.settle(prefer=SAFE); stood += 1
        pet_care(p)
        p.answer_choices(p.table)
    p.do('journal'); p.do('record city'); p.do('world')
    p.mark(f'walked {len(p.g.city.visited)} districts, stood in {stood} places, finds {finds_of(p)}')


def record_and_titles(p):
    p.mark('the record, and what the city calls you')
    for c in ('record', 'record work', 'record city', 'record people', 'record floor',
              'called', 'called auto', 'title', 'title --still', 'ambitions', 'rep',
              'rice', 'rice palette', 'rice marks', 'icon', 'career', 'char', 'self'):
        p.do(c)
    titles = earned_titles()
    if titles:
        p.do(f'called {titles[0]}'); p.do('record'); p.do('char')
    p.do('called auto')


def save_restore(p, slot='camp'):
    p.mark('save it, restore it, is everything still there')
    def snap():
        g = p.g
        return (g.city.shift, bool(g.city.pet), (g.city.pet or {}).get('toy', ''),
                bool(g.char.deck.familiar), (g.char.deck.familiar or {}).get('runs', 0), g.char.runs)
    before = snap()
    p.do(f'save {slot}'); p.do('characters'); p.do(f'restore {slot}'); p.settle(prefer=('yes',))
    after = snap()
    p.mark(f'save/restore: before {before} after {after} {"SAME" if before == after else "DIFFERENT"}')


def appearance(p):
    p.mark('who I look like: icon, self, the deck name')
    p.do('icon'); p.do('self'); p.do('self --roll'); p.do('self')
    from flatline.content import icons as IC
    ic = cheapest(IC.BY_KEY)
    if ic is not None:
        p.do(f'icon buy {ic.key}'); p.settle(prefer=('yes',)); p.do(f'icon wear {ic.key}'); p.do('icon')


def heat_and_names(p):
    p.mark('heat: an arrangement, an alias, and what burning a name costs')
    p.do('arrange'); p.do('alias'); p.do('rep')
    fac = getattr(districts.BY_KEY.get(p.g.city.where), 'controller', '')
    if fac:
        p.do(f'arrange {fac}'); p.settle(prefer=('yes',)); p.do('arrange'); p.do(f'arrange stop {fac}')
    p.do('burn'); p.do('char')


def crew(p, jobs_n=4):
    p.mark('somebody beside you: crew a runner and work')
    p.do('crew')
    riv = max([r for r in p.g.city.rivals if r.alive], key=lambda r: r.disposition, default=None)
    if riv is None:
        return
    o = p.do(f'crew take {riv.key}')
    if 'retainer' in o and '✗' not in o:
        if p.g.char.credits < 12000:
            p.shortcut(f'credits {p.g.char.credits} -> 14000 for the retainer')
            p.g.char.credits = 14000
        p.do(f'crew take {riv.key} --confirm'); p.settle(prefer=('yes',))
    for _ in range(jobs_n):
        if p.g.over:
            break
        run_job(p, hire=not p.g.city.crew)
    p.do('crew'); p.do(f'who {riv.key}'); p.do('journal')
    p.mark(f'crew: {riv.name} disposition {riv.disposition} bond {riv.bond or "-"}')


def story_end(p, carried='read', offer='take', max_jobs=30, after=12):
    p.mark(f'the main line to an end (carried={carried}, offer={offer})')
    spine.facts(p)
    ending = spine.to_ending(p, carried=carried, offer=offer, max_jobs=max_jobs)
    p.mark(f'ENDING: {ending or "NONE REACHED"}; {spine.dw_flags(p)}')
    if ending:
        spine.afterwards(p, shifts=after)
    p.do('record'); p.do('journal'); p.do('called'); p.do('home')
    return ending


def retire_end(p):
    p.mark('the door: retire')
    p.do('retire'); p.do('debt pay all'); p.settle(prefer=('yes',))
    n = 0
    while n < 14 and 'All four' not in p.do('retire') and not p.g.over:
        n += 1; p.do('rest'); p.settle(prefer=SAFE); p.answer_choices(p.table)
    o = p.do('retire --confirm'); p.settle(prefer=('yes',))
    if 'bounty' in o and not p.g.over:
        # A number on the name closes the door: end the name, then go.
        p.do('burn --confirm'); p.settle(prefer=('yes',))
        n = 0
        while n < 10 and 'All four' not in p.do('retire') and not p.g.over:
            n += 1; p.do('rest'); p.settle(prefer=SAFE); p.answer_choices(p.table)
        p.do('retire --confirm'); p.settle(prefer=('yes',))
    p.mark(f'after the door: over={p.g.over!r}')
    for c in ('journal', 'record', 'career', 'characters', 'history 10'):
        p.do(c)


def earned_titles():
    from flatline import save as save_mod
    try:
        return list(save_mod.read_meta().get('titles') or [])
    except Exception:
        return []


def finds_of(p):
    return sorted(f[6:] for f in p.g.story.flags if f.startswith('found:'))


def summary(p, label):
    hit, missed = p.coverage()
    p.log.write(f'\n### COVERAGE {label}: typed {len(hit)} of {len(hit) + len(missed)} commands\n'
                f'### never typed: {" ".join(missed)}\n')
    return (f'{label}: shift {p.g.city.shift} runs {p.g.char.runs} credits {p.g.char.credits} '
            f'over={p.g.over!r} threads {len(p.g.story.reached)} titles {earned_titles()} finds {len(finds_of(p))} '
            f'turns {p.turns} errors {len(p.errors)} coverage {len(hit)}/{len(hit) + len(missed)}')
