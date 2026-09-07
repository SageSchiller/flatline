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

Eight axes, 86 pieces:

- **palette** is the colour scheme, and the one people care about most.
- **frame** is the box-drawing: rules, headers, table lines.
- **bars** is what a meter is made of.
- **marks** is bullets, arrows, ticks and crosses.
- **prompt** is the shape of the line you type at, which is the single most
  riced object in the entire practice.
- **banner** is the wordmark on the cold start. Twelve of them, four
  generated from the block bitmap rather than drawn: the slant is a row
  shift, the shadow is an offset copy in a second character, the glitch is a
  fixed tear, and the braille one repacks the same pixels at two by four
  dots per cell.
- **hud** is whether a line of readout follows every action that spends a
  tick inside a run (D59). Five states, all yours from the start (the panel
  is earned): a preference about how much the stream tells you, not a
  reward, and the prompt carries the trace whichever you choose.
- **render** is how a faction's cyberspace and your own icon arrive on
  connect (D102, D105): a picture two pixels to a cell where the terminal
  can, the text mark where it cannot, or nothing.

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
KINDS = ('palette', 'prompt', 'frame', 'bars', 'marks', 'banner', 'hud',
         'render', 'reveal')

#: How a faction's cyberspace arrives on connect (D102). The text mark
#: beside the words, which is the default (D182); a picture, two pixels a
#: cell in the faction's own colours, where the terminal can and the player
#: asked; or nothing.
RENDER_MODES = ('picture', 'wide', 'mark', 'none')

#: How a picture arrives on screen (D109). Cosmetic and visible only where
#: the terminal can animate; the finished picture is identical either way.
REVEAL_STYLES = ('dissolve', 'scan', 'wipe', 'flash', 'instant')

#: The two states of the run readout (D59). A table rather than two
#: literals, so `validate.py` can hold the catalogue to it.
HUD_MODES = ('line', 'bar', 'terse', 'quiet', 'panel')

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
    'errands': 'errands_done',
    'spine': 'spine_finished',
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
             'inside of not knowing looks like, and it is the one thing on '
             'this list you cannot reach by going further in: you have to '
             'have gone and found out (D143).',
             needs=('spine', 1),
             hint='Carry the thing about the water to one of its ends.'),
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
    Cosmetic('midnight', 'palette', 'Midnight',
             'Everything turned down. For running at three in the morning '
             'with the lights off, which is when most of this happens '
             'anyway.',
             needs=('runs', 6),
             hint='Six contracts.'),
    Cosmetic('nightwatch', 'palette', 'Nightwatch',
             'Institutional navy and steel, costed by somebody upstairs and '
             'signed off by somebody above them.',
             needs=('districts', 8),
             hint='Set foot in eight of the twelve districts.'),
    Cosmetic('sixes', 'palette', 'Sixes',
             'Bruised purple and a sick green. Nothing in it was chosen by '
             'anybody who had a choice.',
             needs=('clean', 6),
             hint='Six runs nobody ever knew about.'),
    Cosmetic('aoyama', 'palette', 'Aoyama',
             'Clinical, well-lit, and staffed by people who slept well. The '
             'aftercare really is excellent, which is how they keep the rest '
             'of it quiet.',
             needs=('drift', 40),
             hint='Reach 40 Dissonance. They will be interested by then.'),
    Cosmetic('paper', 'palette', 'Paper',
             'A light scheme, for daylight and for the one person who runs a '
             'light terminal. The only palette here that assumes anything '
             'about the background it lands on.',
             needs=('characters', 3),
             hint='Make a third character. However the first two went.'),

    Cosmetic('sendai', 'palette', 'Sendai',
             'Black, white, and one red. The palette of a company that '
             'renders you at high resolution and lets you work out why.',
             needs=('blackice', 1),
             hint='Meet black ICE and come back to describe it.'),
    Cosmetic('meridian', 'palette', 'Meridian',
             'Ink and gold. A ledger you are on the wrong side of, made '
             'legible.',
             needs=('credits', 25000),
             hint='Hold twenty-five thousand credits at once.'),
    Cosmetic('chorus', 'palette', 'Chorus',
             'Violet and lavender and a line of gold, the light of a hall '
             'that feeds people and files them.',
             needs=('threads', 5),
             hint='Carry five storylines somewhere.'),
    Cosmetic('freeport', 'palette', 'Freeport',
             'Sea, rust, and ochre: a working port that answers to a vote '
             'and a crane.',
             needs=('errands', 20),
             hint='Twenty pieces of street work. The Freeport way.'),
    Cosmetic('ember', 'palette', 'Ember',
             'Red on black, and everything else a ghost of it. What the '
             'name of this game looks like as a colour scheme.',
             needs=('runs', 15),
             hint='Fifteen contracts. You will have earned the red.'),
    Cosmetic('void', 'palette', 'Void',
             'One blue, a long way down. For somebody who has seen the '
             'whole city and wants the terminal to get out of the way.',
             needs=('districts', 12),
             hint='Set foot in all twelve districts.'),

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
             hint='Set foot in six of the twelve districts.'),
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

    Cosmetic('caret', 'prompt', 'Caret',
             'Angle brackets, one bar per fact. Older than everything else '
             'in this list and it has outlasted all of them.',
             needs=('runs', 5),
             hint='Five contracts.'),
    Cosmetic('json', 'prompt', 'Structured',
             'The state as a record. Somebody built this deck for machines '
             'to read and never got round to changing it.',
             needs=('clean', 8),
             hint='Eight runs nobody ever knew about.'),
    Cosmetic('angle', 'prompt', 'Angle',
             'Guillemets, and the trace inside them. Compact.',
             needs=('runs', 4),
             hint='Four contracts.'),
    Cosmetic('tag', 'prompt', 'Tag',
             'Place, hour and account as labels, the way a log line reads.',
             needs=('errands', 8),
             hint='Eight pieces of street work.'),
    Cosmetic('rail', 'prompt', 'Rail',
             'Segments divided by an upright, like a rack readout.',
             needs=('clean', 4),
             hint='Four runs nobody ever knew about.'),

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

    Cosmetic('bracket', 'frame', 'Bracket',
             'Corner marks only, floating off the ends of the rule.',
             needs=('runs', 9),
             hint='Nine contracts.'),
    Cosmetic('rail', 'frame', 'Rail',
             'A double horizontal on single uprights. Reads like a printed '
             'form somebody has been made to fill in.',
             needs=('threads', 1),
             hint='Carry one storyline somewhere.'),
    Cosmetic('slab', 'frame', 'Slab',
             'Half-blocks. Heavier than heavy, and the only frame with any '
             'weight below the line.',
             needs=('credits', 25000),
             hint='Hold twenty-five thousand credits at once.'),
    Cosmetic('quiet', 'frame', 'Quiet',
             'No rule at all. Headings become whitespace and the output has '
             'to hold itself together on its own, which it mostly does.',
             needs=('runs', 16),
             hint='Sixteen contracts. By then you can read it without help.'),

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

    Cosmetic('pipe', 'bars', 'Pipe',
             'Uprights, filled and dotted. The narrowest fill here.',
             needs=('runs', 4),
             hint='Four contracts.'),
    Cosmetic('sharp', 'bars', 'Sharp',
             'Filled and hollow squares, with a gap between them.',
             needs=('districts', 3),
             hint='Three districts.'),
    Cosmetic('arrows', 'bars', 'Arrows',
             'Pointed, and all pointing the way the number is going.',
             needs=('standing', 35),
             hint='Get somebody to think well of you.'),
    Cosmetic('braille', 'bars', 'Braille',
             'Dots at four times the vertical resolution of anything else '
             'here, which a meter does not need and looks excellent anyway.',
             needs=('runs', 11),
             hint='Eleven contracts.'),

    # ------------------------------------------------------------------ marks
    Cosmetic('plain', 'marks', 'Plain',
             'A bullet, an arrow, a tick and a cross. The default.'),
    Cosmetic('angular', 'marks', 'Angular',
             'Sharper. Points at things rather than sitting beside them.',
             needs=('runs', 3),
             hint='Three contracts.'),
    Cosmetic('kerbside', 'marks', 'Kerbside',
             'The marks a courier chalks on a wall for the next courier: '
             'a corner, an arrow, a number. Nobody who has not carried '
             'anything can read them.',
             needs=('errands', 12),
             hint='Twelve pieces of street work.'),
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

    Cosmetic('ticks', 'marks', 'Ticks',
             'Single angles and a clean tick. Quieter than plain, which '
             'takes some doing.',
             needs=('runs', 7),
             hint='Seven contracts.'),
    Cosmetic('stars', 'marks', 'Stars',
             'Four-pointed throughout. The only genuinely decorative thing '
             'in this entire catalogue.',
             needs=('credits', 15000),
             hint='Hold fifteen thousand credits at once.'),
    Cosmetic('medical', 'marks', 'Clinical',
             'A trace line for a bullet and a caduceus for a cross. Somebody '
             'ported this from a monitoring rig and never took it off.',
             needs=('blackice', 1),
             hint='Meet black ICE and be in a condition to remember it.'),

    # ----------------------------------------------------------------- banner
    Cosmetic('block', 'banner', 'Block',
             'The full wordmark, six rows of it, with the trace underneath.'),
    Cosmetic('thin', 'banner', 'Thin',
             'One-cell strokes instead of two, a third narrower, and the '
             'quietest of the big ones.'),
    Cosmetic('outline', 'banner', 'Outline',
             'The same letters, hollow. Lighter, and it holds a gradient '
             'better.',
             needs=('runs', 4),
             hint='Four contracts.'),
    Cosmetic('shadow', 'banner', 'Shadow',
             'Solid, with a lighter copy of itself behind it. The shadow is '
             'drawn in a second character rather than a second colour, so it '
             'survives being piped somewhere.',
             needs=('runs', 7),
             hint='Seven contracts.'),
    Cosmetic('slant', 'banner', 'Slant',
             'The block mark, leaning. Generated by shifting each row against '
             'the one below it rather than cut by hand.',
             needs=('clean', 3),
             hint='Three runs nobody ever knew about.'),
    Cosmetic('wire', 'banner', 'Wire',
             'Drawn in rules rather than filled: a schematic of the word '
             'instead of the word.',
             needs=('districts', 5),
             hint='Five of the twelve districts.'),
    Cosmetic('terminal', 'banner', 'Window',
             'Inside a drawn frame with a device node for a title. The one '
             'banner that uses your frame set, so two axes visibly compose.',
             needs=('standing', 30),
             hint='Get somebody to think reasonably well of you.'),
    Cosmetic('glitch', 'banner', 'Glitch',
             'Torn sideways, with noise in the tears. The same tear every '
             'time: an intro that came out differently on each boot would '
             'read as a fault rather than as a style.',
             needs=('bounty', 1),
             hint='Have somebody put a number on your name.'),
    Cosmetic('braille', 'banner', 'Braille',
             'The same bitmap packed into braille at two by four dots per '
             'character. A third of the width, half the height, and not one '
             'stroke lost.',
             needs=('runs', 14),
             hint='Fourteen contracts.'),
    Cosmetic('stack', 'banner', 'Stack',
             'One letter per line, down the left, on a rule. The only one '
             'taller than it is wide.',
             needs=('threads', 2),
             hint='Carry two storylines somewhere.'),
    Cosmetic('small', 'banner', 'Small',
             'One line. For a small terminal, or for somebody who has seen '
             'the big one enough times.',
             needs=('runs', 10),
             hint='Ten contracts.'),
    Cosmetic('none', 'banner', 'Bare',
             'No wordmark. Straight to the tagline and the prompt.',
             needs=('runs', 18),
             hint='Eighteen contracts. By then you know what it says.'),

    # -------------------------------------------------------------------- hud
    Cosmetic('line', 'hud', 'Readout',
             'One dim line after anything that spends a tick: the trace as a '
             'bar, the noise here, the tick, the alert. For anybody who does '
             'not read the prompt, which is most people, at first.'),
    Cosmetic('bar', 'hud', 'Bar',
             'The trace as a bar and nothing else. The one number that ends '
             'the character, on its own line, after every tick.'),
    Cosmetic('terse', 'hud', 'Terse',
             'The numbers without the bar: trace, noise, tick, alert, in one '
             'dim line. For a narrow terminal, or a wide one you would rather '
             'keep for the network.'),
    Cosmetic('quiet', 'hud', 'Quiet',
             'No readout. The prompt still carries the trace, because it '
             'always does; everything else is one `status` away.'),
    Cosmetic('panel', 'hud', 'Panel',
             'Two lines of instrument after every tick: the trace as a meter '
             'coloured cool to hot by how far along it is, the noise here, '
             'the alert in its own colour, the tick and the focus.',
             needs=('runs', 2),
             hint='Two contracts. By then you know what the numbers are.'),

    # ----------------------------------------------------------------- render
    Cosmetic('picture', 'render', 'Picture',
             'Their cyberspace as a picture, two pixels a cell, in their '
             'own colours, arriving row by row. Forty cells by eight. Also '
             'the portrait on `char`, the icon you wear, and the ICE as '
             'it wakes. Off unless you turn it on: the words were always '
             'the real render.'),
    Cosmetic('wide', 'render', 'Wide',
             'The same picture at half again the width and height, for a '
             'terminal with the room.',
             needs=('runs', 5),
             hint='Five contracts. Somebody\'s render is worth a bigger '
                  'window by then.'),
    Cosmetic('mark', 'render', 'Mark',
             'The eleven-by-four mark beside the name, and the words. The '
             'default, and what every terminal gets when it cannot do the '
             'picture.'),
    Cosmetic('none', 'render', 'Bare',
             'No picture and no mark. The name, the doctrine, and the job.'),

    # ----------------------------------------------------------------- reveal
    Cosmetic('dissolve', 'reveal', 'Dissolve',
             'A picture arrives as rows of noise in its own colours, settling '
             'top to bottom. The default.'),
    Cosmetic('scan', 'reveal', 'Scan',
             'A bright line sweeps down and the picture is behind it, the way '
             'a sensor builds an image one row at a time.',
             needs=('runs', 5),
             hint='Five contracts.'),
    Cosmetic('wipe', 'reveal', 'Wipe',
             'Row by row, no noise. Clean, and quick.',
             needs=('clean', 3),
             hint='Three runs nobody ever knew about.'),
    Cosmetic('flash', 'reveal', 'Flash',
             'A dim flicker, and then the whole picture at once.',
             needs=('runs', 10),
             hint='Ten contracts.'),
    Cosmetic('instant', 'reveal', 'Instant',
             'No animation. The picture, straight away, for people who have '
             'seen enough of them.'),

)

BY_KEY: dict[tuple[str, str], Cosmetic] = {(c.kind, c.key): c for c in COSMETICS}
BY_KIND: dict[str, tuple[Cosmetic, ...]] = {
    kind: tuple(c for c in COSMETICS if c.kind == kind) for kind in KINDS
}

#: What a fresh install is wearing.
DEFAULTS: dict[str, str] = {
    'palette': 'cyberpunk-neon', 'prompt': 'classic', 'frame': 'single',
    'bars': 'blocks', 'marks': 'plain', 'banner': 'block', 'hud': 'line',
    'render': 'mark',
    'reveal': 'dissolve',
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
