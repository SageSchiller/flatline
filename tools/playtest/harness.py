"""Play-test harness: a real session, everything logged, nothing touching the
player's real profile (D144).

Import this before anything from `flatline`: it sets XDG_DATA_HOME to a
directory under tools/playtest/data/ first, so a persona's saves and profile
counters never reach ~/.local/share/flatline. Set PT_DATA before importing
to pick the directory (each persona uses its own).

Two automatic ways of playing, both the ones `now` recommends: `auto_city`
does the first thing `city_steps` says, `auto_run` does what the run brief
says. Everything else is a persona typing.
"""
import io, os, re, sys, traceback, collections
_here = os.path.dirname(os.path.abspath(__file__))
os.environ['XDG_DATA_HOME'] = os.environ.get('PT_DATA') or os.path.join(_here, 'data', 'default')
os.makedirs(os.environ['XDG_DATA_HOME'], exist_ok=True)
os.environ['NO_COLOR'] = '1'
sys.path.insert(0, os.path.dirname(os.path.dirname(_here)))
from flatline.ui import Console, Caps, ColorLevel, GlyphLevel
from flatline import theme
from flatline.session import Session
from flatline.game import Game
from flatline.model.character import Character
from flatline import commands  # noqa
from flatline.content import attributes as A, skills as S
from flatline.commands import city as city_cmd
from flatline.world import story as story_world

_ANSI = re.compile(r'\033\[[0-9;?]*[A-Za-z]')
NOFIGHT = ('run', 'talk', 'careful', 'pay', 'bolt', 'break', 'yes', 'take')
FIGHTER = ('fight', 'finish', 'strike', 'yes', 'take')


class Play:
    def __init__(self, name, origin='gutter', seed=2468, handle='Tester', log=None,
                 prefer=NOFIGHT, slot='ptest'):
        caps = Caps(ColorLevel.NONE, GlyphLevel.UNICODE, 80, theme.NEUTRAL)
        self.con = Console(caps, stream=io.StringIO())
        self.sess = Session(console=self.con, slot=slot)
        char = Character.from_origin(origin, handle)
        char.points = A.CREATION_POINTS
        char.xp = S.CREATION_XP
        self.sess.game = Game.new(char, seed=seed)
        self.log = log or sys.stdout
        self.name = name
        self.prefer = prefer
        self.errors = []
        self.turns = 0
        self.seen = collections.Counter()   # notable lines, counted
        self.runs_done = 0
        self.runs_tried = 0
        self.log.write(f'\n{"="*78}\n=== {name} ({origin}, seed {seed})\n{"="*78}\n')

    @property
    def g(self):
        return self.sess.game

    def do(self, cmd, note=''):
        self.turns += 1
        self.con.start_capture()
        try:
            self.sess.execute(cmd)
        except Exception as e:
            self.errors.append((cmd, repr(e), traceback.format_exc()[-800:]))
            self.con.end_capture()
            self.log.write(f'\n>>> {cmd}\n!!! CRASH {e!r}\n{traceback.format_exc()[-800:]}\n')
            return ''
        out = _ANSI.sub('', self.con.end_capture()).rstrip()
        prompt = ''
        if self.sess.pending is not None:
            prompt = f'   [waiting: {self.sess.pending.prompt.strip()}]'
        self.log.write(f'\n>>> {cmd}{("   # " + note) if note else ""}\n{out}{prompt}\n')
        for needle in ('the record', 'They have started saying it', 'Every line of',
                       'Afterwards', 'unlocked', 'Deepwater', 'What Deepwater Is',
                       'the water', 'On the board:'):
            if needle in out:
                self.seen[needle] += 1
        return out

    def settle(self, prefer=None, limit=24):
        prefer = prefer or self.prefer
        n = 0
        while self.sess.pending is not None and n < limit:
            n += 1
            ch = list(self.sess.pending.choices)
            pick = next((p for p in prefer if p in ch), None)
            if pick is None:
                pick = ch[0] if ch else ''
            self.do(pick)

    # -- the two automatic ways of playing, the same ones `now` recommends --
    def auto_run(self, cap=80):
        """Inside a run: do what the brief says until it is done or hopeless."""
        n = 0
        self.runs_tried += 1
        while self.sess.run is not None and n < cap:
            n += 1
            b = self.sess.run.brief()
            if b.done:
                self.runs_done += 1
                self.do('jack out'); self.settle(); break
            if not b.steps:
                self.do('job'); self.do('jack out'); self.settle(); break
            step = b.steps[0]
            if '<' in step:
                self.do('jack out'); self.settle(); break
            self.do(step)
            self.settle()
        if self.sess.run is not None:
            self.do('jack out'); self.settle()

    def drive_run(self, cap=60):
        """Play a run toward its objective the way a competent runner would:
        scan, enumerate reachable hosts, crack what is closed, move toward the
        objective node, and do the objective verb when standing on it. Bails
        out when the trace is high or nothing can be done. Returns True if the
        objective was met."""
        run = self.sess.run
        if run is None:
            return False
        for _ in range(cap):
            run = self.sess.run
            if run is None:
                break
            if run.objective_met():
                self.do('jack out'); self.settle(); return True
            # too hot to continue
            if getattr(run, 'trace_pct', 0) > 0.85:
                self.do('jack out'); self.settle(); break
            b = run.brief()
            # follow a concrete brief step if it names a real move
            if b.steps:
                step = b.steps[0]
                head = step.split()[0]
                if head in ('observe', 'pull', 'push', 'wipe', 'brace',
                            'mask', 'scrub', 'jack') and '<' not in step:
                    self.do(step); self.settle()
                    continue
                if head == 'jack':
                    self.do('jack out'); self.settle(); break
            # otherwise, open the network up
            self.do('scan')
            run = self.sess.run
            if run is None:
                break
            here = run.here
            obj = run.net.objective_node
            moved = False
            for uid, node in list(run.net.nodes.items()):
                if self.sess.run is None:
                    break
                if not getattr(node, 'known', False):
                    continue
                if uid == here:
                    continue
                if uid not in run.node.edges:
                    continue
                if not getattr(node, 'mapped', False):
                    self.do(f'probe {uid}')
                if self.sess.run is None:
                    break
                closed = [sv for sv in getattr(node, 'services', [])
                          if not getattr(sv, 'cracked', False)]
                if closed:
                    self.do(f'crack {uid} {closed[0].key}')
                if self.sess.run is None:
                    break
                if getattr(node, 'open', False) and (uid == obj or not moved):
                    self.do(f'connect {uid}')
                    moved = True
                    break
            if not moved and self.sess.run is not None:
                # on the objective with the door open: do the job
                if run.here == obj:
                    b = self.sess.run.brief()
                    if b.steps and '<' not in b.steps[0]:
                        self.do(b.steps[0]); self.settle()
                    else:
                        self.do('observe'); self.settle()
                else:
                    self.do('scan')
            self.settle()
        if self.sess.run is not None:
            self.do('jack out'); self.settle()
        return False

    def auto_city(self, k=1, stop_at_run=True):
        """Outside a run: do the first thing `now` says, k times."""
        done = []
        for _ in range(k):
            if self.g is None or self.g.over:
                break
            if self.sess.run is not None:
                if stop_at_run:
                    break
                self.auto_run(); continue
            steps = city_cmd.city_steps(self.g)
            if not steps:
                break
            cmd = steps[0][0]
            self.do(cmd, note=f'now says: {steps[0][1][:70]}')
            self.settle()
            done.append(cmd)
        return done

    def play_job(self, city_cap=14):
        """One job the way `now` would have you do it. True if a run finished."""
        before = self.g.char.runs
        for _ in range(city_cap):
            if self.g.over:
                return False
            if self.sess.run is not None:
                self.drive_run()
                break
            steps = city_cmd.city_steps(self.g)
            if not steps:
                # nothing to do: `now` has no job. Read the board and take the softest.
                self.do('board')
                if self.g.city.board and self.g.city.current is None:
                    soft = min(self.g.city.board, key=lambda c: c.posture)
                    self.do(f'take {soft.cid}'); self.settle()
                    continue
                self.do('rest'); self.settle()
                continue
            self.do(steps[0][0], note=f'now says: {steps[0][1][:70]}')
            self.settle()
        return self.g.char.runs > before

    def rest(self, n=1):
        for _ in range(n):
            if self.g.over: break
            self.do('rest'); self.settle()

    def present(self):
        return [n.key for n in story_world.present(self.g, self.g.story)]

    def choose_open(self, pick=None):
        """Answer an open story choice, by key or the first one."""
        found = self.g.story.open_choice()
        if found is None:
            return None
        thread, stage = found
        keys = [c.key for c in stage.choices]
        key = pick if pick in keys else keys[0]
        self.do('choose')
        self.do(f'choose {key}')
        self.settle()
        return f'{thread.key}.{stage.key}:{key}'

    def answer_choices(self, table=None, limit=6):
        """Answer every open story decision: `table` maps 'thread.stage' to
        a choice key; anything else takes the first. Returns what was chosen."""
        table = table or {}
        out = []
        for _ in range(limit):
            found = self.g.story.open_choice()
            if found is None:
                break
            thread, stage = found
            out.append(self.choose_open(table.get(f'{thread.key}.{stage.key}')))
        return out

    def shortcut(self, what):
        """A thing the harness did that a player could not, said in the log."""
        self.log.write(f'\n!!! HARNESS SHORTCUT: {what}\n')

    def state(self):
        g = self.g; c = g.char
        return (f'shift {g.city.shift} ({g.city.phase}) in {g.city.district.name} | '
                f'{c.credits:,}c | int {c.integrity}/{c.integrity_max} | xp {c.xp} | '
                f'runs {c.runs} | diss {c.dissonance} | viol {c.skill("violence")} '
                f'intr {c.skill("intrusion")} | weapon {c.weapon or "-"} | '
                f'pit {g.city.pit.get("rank", 0)} | threads {len(g.story.reached)} | '
                f'flags {len(g.story.flags)} | over={bool(g.over)}')

    def mark(self, text):
        self.log.write(f'\n--- {text}\n    STATE: {self.state()}\n')

    def finish(self, label):
        self.log.write(f'\n\n=== {label}: {self.turns} turns, ERRORS: {len(self.errors)}\n')
        for cmd, err, tb in self.errors:
            self.log.write(f'  CRASH on {cmd!r}: {err}\n{tb}\n')
        self.log.write(f'  notable: {dict(self.seen)}\n')
