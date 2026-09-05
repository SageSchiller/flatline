"""Test U: reach the under ending by PLAY, not by setting flags. Say yes to
everyone, meet the people, finish the posting, take the other door."""
import os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'U2')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
import spine
log = open(os.path.join(HERE, 'logs', 'pu_under.log'), 'w')
TABLE = {'deepwater.carried': 'read', 'deepwater.offer': 'refuse',
         'deepwater.under': 'go',
         'lark.resolve': 'pay', 'archive.yours': 'yes', 'sparrow.deck': 'gear'}
p = Play('UNDER by play: yes to everyone', origin='academic', seed=131, handle='Fathom', log=log)
g = p.g
# a capable build so runs can actually be finished
p.do('spend'); p.settle()
p.do('boost logic'); p.do('train intrusion'); p.do('train cryptography')
p.mark('earn a living and the runs the spine needs')
n = 0
while g.char.runs < 7 and not g.over and n < 20:
    n += 1
    # buy a payload if we can, so exfil jobs are doable
    if 'siphon' not in g.char.library and 'siphon' not in g.char.deck.loaded and g.char.credits > 2500:
        p.do('market program'); p.do('buy siphon')
    p.play_job(); p.answer_choices(TABLE)
    if g.char.xp >= 7:
        p.do('train intrusion')
p.mark(f'{g.char.runs} runs, credits {g.char.credits}: {spine.dw_flags(p)}')
p.mark('meet Lark (pay the surgeon), the Archivist (consent), read everyone')
spine.meet(p, 'lark', 'shambles', waits=5); p.answer_choices(TABLE)
for d in spine.FENCE:
    if spine.meet(p, 'archivist', d, waits=4): break
p.answer_choices(TABLE)
# remnant, for dw_name (a fact)
spine.meet(p, 'remnant', 'glasshouse', waits=4); p.answer_choices(TABLE)
p.mark(f'after the people: {spine.dw_flags(p)} | consents {sorted(f for f in g.story.flags if f in ("lark_saved","archive_consented","dw_read"))}')
p.mark('run the posting until it is DONE (this is the hard part)')
tries = 0
while 'did:deepwater.posting' not in g.story.flags and tries < 10 and not g.over and p.turns < 1500:
    tries += 1
    story = [c for c in g.city.board if c.story == 'deepwater.posting']
    if g.city.current is not None and g.city.current.story == 'deepwater.posting':
        # travel to it and run it with the strong driver
        for _ in range(4):
            from flatline.commands import city as CC
            st = CC.city_steps(g)
            if not st or g.city.current is None or st[0][0].startswith('jack'): break
            if '<' in st[0][0]: break
            p.do(st[0][0]); p.settle()
        o = p.do('jack in')
        if o.lstrip().startswith('✗'): p.do('jack in --force')
        if p.sess.run is not None:
            p.drive_run()
    elif story:
        p.do(f'take {story[0].cid}'); p.settle()
    else:
        p.play_job()
    p.answer_choices(TABLE); p.do('journal')
p.mark(f'posting {"DONE" if "did:deepwater.posting" in g.story.flags else "NOT DONE after "+str(tries)}: {spine.dw_flags(p)}')
p.mark('now the offer and the other door, by resting and answering')
for i in range(30):
    if g.over: break
    if g.story.flags & {'dw_under', 'dw_stayed'}: break
    p.answer_choices(TABLE)
    p.do('rest'); p.settle(); p.do('look'); p.settle()
p.mark(f'END by play: over={g.over!r} | {spine.dw_flags(p)}')
p.do('journal'); p.do('record'); p.do('char')
p.finish('under by play')
log.close()
print(f"U: over={g.over!r} | deepest {sorted(f for f in g.story.flags if f.startswith('dw_'))} | "
      f"posting {'done' if 'did:deepwater.posting' in g.story.flags else 'NOT done'} | "
      f"runs {g.char.runs} turns {p.turns} errors {len(p.errors)}")
