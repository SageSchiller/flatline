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
NOFIGHT = ('give', 'pay', 'run', 'talk', 'careful', 'bolt', 'break', 'yes', 'take')
FIGHTER = ('fight', 'finish', 'strike', 'give', 'yes', 'take')


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
        self.verbs = collections.Counter()
        self.seen = collections.Counter()   # notable lines, counted
        self.runs_done = 0
        self.runs_tried = 0
        self.log.write(f'\n{"="*78}\n=== {name} ({origin}, seed {seed})\n{"="*78}\n')

    @property
    def g(self):
        return self.sess.game

    def do(self, cmd, note=''):
        self.turns += 1
        self.verbs[_verb(cmd)] += 1
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

    def drive_run(self, cap=80):
        """Play a run the way the game's own brief says to: do its first
        concrete step every time. The brief already knows the route, the
        door, the objective verb and the sealed-pull fallback; a driver that
        second-guesses it finishes fewer runs than one that trusts it. Bails
        only when the brief itself says out, or the trace is spent with no
        finishing move in hand. Returns True if the objective was met."""
        run = self.sess.run
        if run is None:
            return False
        for _ in range(cap):
            run = self.sess.run
            if run is None:
                break
            b = run.brief()
            if b.done or run.objective_met():
                self.do('jack out'); self.settle(); return True
            step = b.steps[0] if b.steps else ''
            on_obj = run.here == run.net.objective_node
            if getattr(run, 'trace_pct', 0) > 0.9 and not (step and on_obj):
                self.do('jack out'); self.settle(); break
            if not step or '<' in step:
                self.do('scan'); self.settle(); continue
            if step == 'jack out':
                self.do('jack out'); self.settle(); break
            self.do(step); self.settle()
        if self.sess.run is not None:
            self.do('jack out'); self.settle()
        if self.sess.run is not None:
            self.do('jack out --anyway'); self.settle()
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

    def do_step(self, step, note=''):
        """Do a city step the way a player would: if the street refuses it
        for heat, take the out the refusal names (an arrangement if they
        will take the money, otherwise going anyway), then carry on."""
        out = self.do(step, note=note)
        if '\u2717' in out and '--anyway' in out:
            m = re.search(r'`arrange (\w+)`', out)
            if m and self.g.char.credits >= 400:
                o2 = self.do(f'arrange {m.group(1)} --confirm'); self.settle()
                if '\u2717' not in o2:
                    out = self.do(step, note='after arranging')
                    if '\u2717' not in out:
                        return out
            m = re.search(r'`(travel \w+ --anyway)`', out)
            if m:
                out = self.do(m.group(1), note='heat: going anyway'); self.settle()
        return out

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
            self.do_step(steps[0][0], note=f'now says: {steps[0][1][:70]}')
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
        a choice key; anything else takes the first. A refused answer (it
        costs what you do not have) falls through to the next one, the way
        a player reads "another option" and picks it. Returns what was chosen."""
        table = table or {}
        out = []
        for _ in range(limit):
            found = self.g.story.open_choice()
            if found is None:
                break
            if self.sess.run is not None:
                self.do('jack out'); self.settle()
                if self.sess.run is not None:
                    self.do('jack out --anyway'); self.settle()
            thread, stage = found
            keys = [c.key for c in stage.choices]
            want = table.get(f'{thread.key}.{stage.key}')
            order = ([want] if want in keys else []) + [k for k in keys if k != want]
            self.do('choose')
            chosen = ''
            for key in order:
                o = self.do(f'choose {key}')
                self.settle()
                if '\u2717' not in o:
                    chosen = key
                    break
            out.append(f'{thread.key}.{stage.key}:{chosen or "REFUSED ALL"}')
            if not chosen:
                break
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

    def coverage(self):
        """(hit, missed): the commands this persona typed at least once, and
        the ones it never did, out of everything the game registers."""
        names = all_verbs()
        hit = sorted(v for v in self.verbs if v in names)
        return hit, sorted(names - set(hit))

    def finish(self, label):
        self.log.write(f'\n\n=== {label}: {self.turns} turns, ERRORS: {len(self.errors)}\n')
        for cmd, err, tb in self.errors:
            self.log.write(f'  CRASH on {cmd!r}: {err}\n{tb}\n')
        self.log.write(f'  notable: {dict(self.seen)}\n')

def _verb(cmd):
    w = cmd.split()
    if not w:
        return ''
    if len(w) > 1 and w[0] in ('jack', 'who'):
        return f'{w[0]} {w[1]}'
    return w[0]


def all_verbs():
    """Every command the game registers, by name, so a persona can say what
    it never typed."""
    import importlib, pkgutil
    import flatline.commands as CM
    for m in pkgutil.iter_modules(CM.__path__):
        importlib.import_module(f'flatline.commands.{m.name}')
    from flatline.shell import REGISTRY
    names = set()
    for k, c in REGISTRY.commands.items():
        names.add(getattr(c, 'name', k))
    return names

