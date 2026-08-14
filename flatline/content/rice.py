"""The shell you type into, and how you earn the right to change it.

Everything in this game costs you something. Chrome costs Dissonance, work
costs heat, a face worth remembering costs anonymity. This is the one system
in it that costs nothing and takes nothing, and it exists for exactly that
reason: after four hours of a city that does not care whether you live, a
player has earned a colour scheme.

**It lives in meta, not in the save.** The deck's interface is the player's,
not the character's, and it survives a flatline. That is the whole point of
putting it here rather than in `Character`: you lose everything else, and the
terminal you spent a week getting right is still yours when you sit down with
somebody new. The city takes the runner. It does not get the shell.

Six axes, forty-two pieces:

- **palette** is the colour scheme, and the one people care about most.
- **frame** is the box-drawing: rules, headers, table lines.
- **bars** is what a meter is made of.
- **marks** is bullets, arrows, ticks and crosses.
- **prompt** is the shape of the line you type at, which is the single most
  riced object in the entire practice.
- **banner** is the wordmark on the cold start.

**Nothing here is allowed to affect play**, and `validate.py` enforces it in
two directions: no cosmetic carries an effects dict, and no unlock condition
can be satisfied by anything other than having played. A cosmetic that changed
a number would stop being a reward and start being a build decision, and a
cosmetic you could buy with credits at level one would stop being a reward at
all.

`--theme` on the command line ignores all of this and always has. That is
deliberate and it is not a hole: this is a single-player game and the
catalogue is a reward channel, not a licence check. Somebody who would rather
type a flag than earn Phosphor has not broken anything, and refusing them
would be the game taking itself more seriously than it has any right to.

The conditions are deliberately spread across very different kinds of playing.
Some want persistence, some want a specific bad night, some want you to have
gone somewhere. Nobody should be able to unlock the set by doing one thing
forty times.
"""

from __future__ import annotations

from dataclasses import dataclass

#: The axes. Order is the order `rice` lists them in.
KINDS = ('palette', 'prompt', 'frame', 'bars', 'marks', 'banner')

#: Every condition kind, and the meta counter it reads. Declared as a table so
#: `validate.py` can check that the engine actually maintains each one: an
#: unlock keyed to a counter nothing increments is a cosmetic nobody can ever
#: earn, which is this project's oldest bug in party clothes.
COUNTERS: dict[str, str] = {
    'always': '',
    'runs': 'runs_completed',
    'clean': 'clean_runs',
    'flatlines': 'flatlines',
    'blackice': 'black_ice_survived',
    'drift': 'deepest_drift',
    'credits': 'best_credits',
    'districts': 'districts_seen',
    'bounty': 'bounties_taken',
    'threads': 'threads_closed',
    'standing': 'best_standing',
    'characters': 'characters_created',
}


@dataclass(frozen=True, slots=True)
class Cosmetic:
    key: str
    kind: str
    name: str
    blurb: str
    #: (condition, threshold). See `COUNTERS`.
    needs: tuple[str, int] = ('always', 0)
    #: What to tell somebody who has not got it yet. Written so it reads as a
    #: thing to go and do rather than as a number to grind.
    hint: str = ''


COSMETICS: tuple[Cosmetic, ...] = (

    # ---------------------------------------------------------------- palette
    Cosmetic('cyberpunk-neon', 'palette', 'Cyberpunk Neon',
             'What the deck shipped with. Somebody had opinions and most of '
             'them were about cyan.'),
    Cosmetic('neutral', 'palette', 'Neutral',
             'Duller on purpose, and the safe answer on a terminal whose '
             'background you did not choose.'),
    Cosmetic('ansi', 'palette', 'Inherit',
             'Sixteen colours, all of them somebody else\'s. Whatever your '
             'terminal already does, this does.'),
    Cosmetic('amber', 'palette', 'Amber',
             'One phosphor and eleven brightnesses. The specific warmth of a '
             'tube that has been on since before you were born.',
             needs=('runs', 3),
             hint='Three finished contracts. Any three.'),
    Cosmetic('phosphor', 'palette', 'Phosphor',
             'The other tube. Colder, harsher, and what most people picture '
             'when they picture this.',
             needs=('runs', 8),
             hint='Eight contracts. You will have opinions about ICE by then.'),
    Cosmetic('kagawa', 'palette', 'Kagawa House',
             'Cold, correct, and entirely without opinions. Wearing the '
             'interface of people whose networks you break into is a specific '
             'kind of joke.',
             needs=('standing', 45),
             hint='Get any faction to think well of you. Genuinely well: 45.'),
    Cosmetic('carrion', 'palette', 'Carrion',
             'Wet reds and the colour of bone, and no attempt at comfort.',
             needs=('bounty', 1),
             hint='Have somebody put a number on your name and live in a city '
                  'where that is true.'),
    Cosmetic('deepwater', 'palette', 'Deepwater',
             'Nobody has established what Deepwater is. This is what the '
             'inside of not knowing looks like.',
             needs=('drift', 50),
             hint='Reach Submerged. You will know when.'),
    Cosmetic('static', 'palette', 'Static',
             'Pirate broadcast, and the harshest thing on this list by a '
             'distance.',
             needs=('threads', 3),
             hint='See three storylines through to something that resembles '
                  'an end.'),
    Cosmetic('ash', 'palette', 'Ash',
             'Almost no colour at all, and one thin red line for the only '
             'number that ever really mattered.',
             needs=('flatlines', 1),
             hint='Lose somebody. This is not a thing to aim for.'),
    Cosmetic('paper', 'palette', 'Paper',
             'A light scheme, for daylight and for the one person who runs a '
             'light terminal. The only palette here that assumes anything '
             'about the background it lands on.',
             needs=('characters', 3),
             hint='Make a third character. However the first two went.'),

    # ----------------------------------------------------------------- prompt
    Cosmetic('classic', 'prompt', 'Classic',
             'Everything spelled out, separated by the bullet you chose.'),
    Cosmetic('minimal', 'prompt', 'Minimal',
             'The same facts in the fewest characters that can carry them.'),
    Cosmetic('bracket', 'prompt', 'Bracket',
             'Segmented. Reads fast once your eye knows which bracket is '
             'which.',
             needs=('runs', 2),
             hint='Two contracts.'),
    Cosmetic('path', 'prompt', 'Path',
             'The city as a filesystem, which is either a joke about '
             'netrunners or the most honest thing in this game.',
             needs=('districts', 6),
             hint='Set foot in six of the nine districts.'),
    Cosmetic('powerline', 'prompt', 'Powerline',
             'Segments with pointed separators, the way everybody\'s terminal '
             'looked for about four years.',
             needs=('clean', 3),
             hint='Three runs where nobody ever knew you were there.'),
    Cosmetic('terse', 'prompt', 'Terse',
             'For people who have played enough that the prompt is furniture.',
             needs=('runs', 20),
             hint='Twenty contracts. At that point you have earned the right '
                  'to stop reading it.'),

    # ------------------------------------------------------------------ frame
    Cosmetic('single', 'frame', 'Single',
             'One line. The default, and correct.'),
    Cosmetic('rounded', 'frame', 'Rounded',
             'Softened corners. Very slightly kinder than this game deserves.'),
    Cosmetic('heavy', 'frame', 'Heavy',
             'Thicker rules. Reads as more serious, which is a lie your eye '
             'believes anyway.',
             needs=('runs', 4),
             hint='Four contracts.'),
    Cosmetic('double', 'frame', 'Double',
             'Two lines. Institutional, in the way a form is institutional.',
             needs=('standing', 25),
             hint='Get on decent terms with anybody.'),
    Cosmetic('dotted', 'frame', 'Dotted',
             'Broken rules, for people who find a solid line too much of a '
             'commitment.',
             needs=('clean', 2),
             hint='Two runs nobody noticed.'),
    Cosmetic('wire', 'frame', 'Wire',
             'Crossed corners. Schematic rather than decorative.',
             needs=('districts', 4),
             hint='Four districts.'),
    Cosmetic('rule', 'frame', 'Rule',
             'No corners at all. Just the line, which is all a rule ever '
             'needed to be.',
             needs=('runs', 12),
             hint='Twelve contracts.'),
    Cosmetic('scan', 'frame', 'Scan',
             'Dashed and thin, like something drawn by a machine that was '
             'not sure the drawing mattered.',
             needs=('drift', 25),
             hint='Reach Drifting. It will happen on its own.'),

    # ------------------------------------------------------------------- bars
    Cosmetic('blocks', 'bars', 'Blocks',
             'Solid and hollow. The default.'),
    Cosmetic('shaded', 'bars', 'Shaded',
             'Softer fill. Easier on a low-contrast terminal.'),
    Cosmetic('solid', 'bars', 'Solid',
             'Fill and nothing. The bar is only where the bar is.',
             needs=('runs', 2),
             hint='Two contracts.'),
    Cosmetic('dots', 'bars', 'Dots',
             'Discrete rather than continuous, which is closer to what the '
             'numbers actually are.',
             needs=('runs', 6),
             hint='Six contracts.'),
    Cosmetic('line', 'bars', 'Line',
             'A single rule that fills. Very flat, very quiet.',
             needs=('clean', 4),
             hint='Four clean runs.'),
    Cosmetic('ladder', 'bars', 'Ladder',
             'Segmented uprights. Reads as a gauge rather than a fill.',
             needs=('blackice', 1),
             hint='Meet black ICE and be in a condition to remember it.'),
    Cosmetic('wave', 'bars', 'Wave',
             'Rounded segments, and the only cheerful thing in this list.',
             needs=('credits', 40000),
             hint='Have forty thousand credits at once, however briefly.'),
    Cosmetic('ascii', 'bars', 'ASCII',
             'Hash and dot. What the ASCII rung uses anyway, available to '
             'everybody who wants it on purpose.',
             needs=('characters', 2),
             hint='Start a second character.'),

    # ------------------------------------------------------------------ marks
    Cosmetic('plain', 'marks', 'Plain',
             'A bullet, an arrow, a tick and a cross. The default.'),
    Cosmetic('angular', 'marks', 'Angular',
             'Sharper. Points at things rather than sitting beside them.',
             needs=('runs', 3),
             hint='Three contracts.'),
    Cosmetic('minimal', 'marks', 'Minimal',
             'ASCII marks in a Unicode terminal, which is a whole aesthetic '
             'and you know whether it is yours.',
             needs=('runs', 5),
             hint='Five contracts.'),
    Cosmetic('geometric', 'marks', 'Geometric',
             'Filled shapes throughout. Heavier, and unmistakable at a '
             'glance in a wall of scrollback.',
             needs=('clean', 5),
             hint='Five runs nobody ever knew about.'),
    Cosmetic('runic', 'marks', 'Runic',
             'Older glyphs, for no reason anybody has been able to establish.',
             needs=('drift', 75),
             hint='Reach Dissolved. Please do not.'),

    # ----------------------------------------------------------------- banner
    Cosmetic('block', 'banner', 'Block',
             'The full wordmark, six rows of it, with the trace underneath.'),
    Cosmetic('outline', 'banner', 'Outline',
             'The same letters, hollow. Lighter, and it holds a gradient '
             'better.',
             needs=('runs', 5),
             hint='Five contracts.'),
    Cosmetic('small', 'banner', 'Small',
             'One line. For a small terminal, or for somebody who has seen '
             'the big one enough times.',
             needs=('runs', 10),
             hint='Ten contracts.'),
    Cosmetic('none', 'banner', 'None',
             'No wordmark. Straight to the tagline and the prompt.',
             needs=('runs', 15),
             hint='Fifteen contracts. By then you know what it says.'),
)

BY_KEY: dict[tuple[str, str], Cosmetic] = {(c.kind, c.key): c for c in COSMETICS}
BY_KIND: dict[str, tuple[Cosmetic, ...]] = {
    kind: tuple(c for c in COSMETICS if c.kind == kind) for kind in KINDS
}

#: What a fresh install is wearing.
DEFAULTS: dict[str, str] = {
    'palette': 'cyberpunk-neon', 'prompt': 'classic', 'frame': 'single',
    'bars': 'blocks', 'marks': 'plain', 'banner': 'block',
}


def met(cosmetic: Cosmetic, stats: dict) -> bool:
    """Whether this is earned, given the meta counters."""
    kind, threshold = cosmetic.needs
    if kind == 'always':
        return True
    counter = COUNTERS.get(kind)
    if not counter:
        return False
    return float(stats.get(counter) or 0) >= threshold


def unlocked(stats: dict) -> list[Cosmetic]:
    """Everything currently earned, in catalogue order."""
    return [c for c in COSMETICS if met(c, stats)]


def newly_earned(stats: dict, already: set[str]) -> list[Cosmetic]:
    """What has become available that the player has not been told about.

    Keyed by `kind:key` rather than by key alone, because `minimal` is both a
    prompt and a mark set and they are unlocked by different things.
    """
    return [c for c in unlocked(stats) if f'{c.kind}:{c.key}' not in already]


def progress(cosmetic: Cosmetic, stats: dict) -> str:
    """How close somebody is, as a line. Empty for anything already earned."""
    kind, threshold = cosmetic.needs
    if kind == 'always' or met(cosmetic, stats):
        return ''
    counter = COUNTERS.get(kind, '')
    have = int(float(stats.get(counter) or 0))
    return f'{have}/{threshold}'
