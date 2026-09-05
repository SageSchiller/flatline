"""Persona L: earns titles across the three registers, pins one, checks the
city calls you what you chose, that it survives the character, and that the
displayed name is never a surprise."""
import os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ['PT_DATA'] = os.path.join(HERE, 'data', 'L')
sys.path.insert(0, HERE); os.makedirs(os.path.join(HERE, 'logs'), exist_ok=True)
from harness import Play
from flatline import save as save_mod
from flatline.world import record as RW
from flatline.content import record as RC
save_mod.write_meta(dict(save_mod.META_DEFAULT))
log = open(os.path.join(HERE, 'logs', 'pl_titles.log'), 'w')
p = Play('TITLES: what the city calls me', origin='gutter', seed=61, handle='Verdict', log=log)
g = p.g; p.do('spend'); p.settle()

p.mark('nothing earned yet: what does called say?')
p.do('called'); p.do('char')

p.mark('earn a heroic, a vile, and an amusing title by deed')
g.story.flags.add('lark_saved')      # bloodprice (heroic)
g.story.flags.add('killer')          # crossed (vile)
g.story.flags.add('asked:vending:war')  # veteran (amusing)
g.char.runs = 12                     # a working runner (record)
p.sess.record_progress()
p.mark('the announcements should have fired above; now the board')
p.do('called')

p.mark('the newest name shows by default; pin the heroic one')
p.do('char')
p.do('called blood')
p.do('char')
p.do('record')

p.mark('pin a vile one, then an amusing one, then auto')
p.do('called cross'); p.do('char')
p.do('called war'); p.do('char')
p.do('called auto'); p.do('char')

p.mark('a name not earned is refused')
p.do('called who holds the wall')
p.do('called nonsense')

p.mark('earn more, check the pin sticks if still earned')
p.do('called blood')
g.story.flags.add('betrayed')        # judas (vile)
g.story.flags.add('dw_refused')      # unbought (heroic)
p.sess.record_progress()
p.do('called'); p.do('char')

p.mark('does it survive the character? make a second runner')
meta = save_mod.read_meta()
p.mark(f'profile titles: {meta.get("titles")}, pinned: {meta.get("called")!r}')
p.finish('titles')
q = Play('TITLES: the next runner', origin='courier', seed=62, handle='Second', log=log)
q.sess.game = None
q.do('new Second --origin courier --seed 62'); q.settle(prefer=('yes',))
q.do('called'); q.do('char')
q.finish('titles, the next runner')
log.close()
earned = RW.all_titles(RW.counts(None, save_mod.read_meta()), save_mod.read_meta())
print(f'L: {len(p.errors)} errors | profile titles {save_mod.read_meta().get("titles")}')
print(f'   pinned {save_mod.read_meta().get("called")!r}')
print(f'   all earned names: {earned}')
