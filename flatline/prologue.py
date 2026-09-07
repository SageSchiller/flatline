"""The cold open (D115, rebuilt as a real run in D186): a first job, before
there is a you.

A text game asks a newcomer to make a character and read a stat sheet before
anything has happened to them, and the best thing in this game (the writing,
the tension, the story) is the last thing they meet. The cold open turns that
around: it drops the player into a short heist as somebody else, already
mid-job, with a voice in their ear and the trace climbing, and then hands
them the question the whole game is really asking: now, who are you?

The first version was a scripted scene. Four words were listened for, any
word advanced it, the trace was four hand-picked percentages, and nothing it
showed carried into the game. It read as a cutscene where the player types
"next". This one is a run: a hand-built network of three hosts, played with
the real verbs, the real dice, the real readout and the real countermeasure,
as the dead runner's own character. Switchboard is the coach in her own
voice, handing over exactly the next command. The crack can fail. The Hunter
is real. The trace can fill, and being cut loose is a scene rather than a
game over. And what happens carries into the runner made afterwards: read
the ledger and the main line knows you have heard the word; get cut loose
and the Sixes start with a shape to look for; get out clean and the street
rounds up.

Nothing of the borrowed runner is kept. The game it runs in is never saved.
"""

from __future__ import annotations

from dataclasses import dataclass

from .game import Game
from .model.character import Character
from .run.network import DataAsset, IceInstance, Network, Node, ServiceInstance
from .run.session import RunState

#: The borrowed deck's world. Nothing of it survives the scene.
SEED = 1177
GATE, DESK, VAULT = 'gw-node00', 'ws-desk02', 'fs-vault07'
SHARE = 'share'
LEDGER = 'asset-objective'
#: Where the trace stands when you come up: the job was hers, and she was
#: halfway through it when she stopped answering.
TRACE_AT_THE_DOOR = 22.0
#: What the scene hands the runner made after it.
CLEAN_BONUS = 250
SEVERED_HEAT = 8

CONTRACT = {'objective': 'exfiltrate', 'title': 'A borrowed job',
            'target': 'sixes', 'posture': 15, 'pay': 0, 'district': 'ninth'}

_SKIP = ('skip', 'new', 'creation')
_READ = ('read', 'read ledger', 'read it', 'read the ledger', 'open ledger',
         'open it')


def _voice(c, text: str) -> None:
    """Switchboard, in your ear. Its own colour, so it reads as a person on
    the line rather than as the game narrating."""
    c.say(f'[accent]Switchboard[/][dim]:[/] [fg]{text}[/]')


# --------------------------------------------------------------------------
# the borrowed runner, and her network
# --------------------------------------------------------------------------

def _runner() -> Character:
    """Her. A gutter runner who was good at it, with a deck that can do
    the job: a breaker, a payload, a hunter's eye, and the memory for all
    three."""
    char = Character.from_origin('gutter', 'Rook')
    char.points = 0
    char.xp = 0
    char.base_attrs['reflex'] = 6
    char.base_attrs['logic'] = 4
    char.base_skills['intrusion'] = 2
    char.deck.parts['memory'] = 'mem_cascade'
    char.deck.loaded = ['sable', 'siphon', 'ledgerhand']
    char.library = list(char.deck.loaded)
    return char


def _network() -> Network:
    """Three hosts, all in the perimeter so nothing needs a badge: the
    gateway you come up on, a desk that is somebody's lunch, and the
    fileserver with the ledger and one light sleeper on it."""
    net = Network(faction='sixes', posture=15, shape='layered')
    gate = Node(uid=GATE, type='gateway', zone='perimeter', edges=[DESK, VAULT])
    desk = Node(uid=DESK, type='workstation', zone='perimeter',
                edges=[GATE, VAULT],
                services=[ServiceInstance('badge', 2), ServiceInstance('roster', 3)],
                data=[DataAsset(uid='asset-desk', kind='correspondence',
                                value=180, encrypted=False)])
    vault = Node(uid=VAULT, type='fileserver', zone='perimeter',
                 edges=[GATE, DESK],
                 services=[ServiceInstance(SHARE, 2), ServiceInstance('cipher', 4)],
                 data=[DataAsset(uid=LEDGER, kind='financial', value=1400,
                                 encrypted=False, objective=True,
                                 label='the ledger')],
                 ice=[IceInstance(uid='scrapper-vault', key='scrapper', rating=2)])
    net.nodes = {GATE: gate, DESK: desk, VAULT: vault}
    net.entry = GATE
    net.objective_node = VAULT
    net.objective_asset = LEDGER
    return net


@dataclass
class Prologue:
    """What the scene has said so far, so it says each thing once."""
    stage: str = ''
    read: bool = False
    warned: bool = False
    struck: bool = False
    held: bool = False
    desk: bool = False


# --------------------------------------------------------------------------
# the scene
# --------------------------------------------------------------------------

def play(sess) -> None:
    """Open the scene, and start the run. Everything after is the real
    dispatcher, with `after` speaking once each command has run."""
    c = sess.console
    from . import anim
    c.blank()
    c.rule('a borrowed deck', role='accent2')
    c.say('[dim]You are not you yet. Tonight you are wearing a dead '
          'runner\'s deck and her name, because the job was hers and she is '
          'not using either any more. The deck smells of Kick and cat. Her '
          'mask is riced to look like a broken television, which was her idea '
          'of funny. A voice you paid for waits on the line. It calls itself '
          'Switchboard.[/]')
    c.blank()
    _voice(c, 'You are on. The Sixes keep a ledger on a fileserver in this '
              'segment and somebody in the Glasshouse is paying to see it. '
              'She got as far as the gateway. Then she stopped answering.')
    c.blank()

    char = _runner()
    game = Game.new(char, seed=SEED)
    sess.game = game
    net = _network()
    state = RunState.begin(net, char, game.rng('combat'), c, contract=CONTRACT)
    state.render_mode = sess.render_mode
    state.trace = TRACE_AT_THE_DOOR
    sess.run = state
    sess.prologue = Prologue()

    anim.connect(c, GATE, quick=False)
    c.blank()
    c.say(f'[dim]You come up on [/][accent]{GATE}[/][dim]: their gateway, '
          f'municipal blue, half its textures missing. The trace is already '
          f'at [/][trace]{int(TRACE_AT_THE_DOOR)}[/][dim] because she spent '
          f'that much of it before she stopped. Every command in here costs '
          f'time, and time is what the trace eats. At 100 they cut you '
          f'loose.[/]')
    c.blank()
    after(sess)


def _stage(state) -> str:
    """Where the job stands, read off the run rather than remembered."""
    vault = state.net.node(VAULT)
    if state.net.objective_asset in state.haul:
        return 'taken'
    if state.here == VAULT:
        return 'stood'
    if vault.open:
        return 'open'
    if vault.mapped:
        return 'mapped'
    if vault.known:
        return 'seen'
    return 'door'


#: Her line when the job moves on to each stage, and the one-liner when it
#: has not.
_LINES = {
    'seen': ('The dark answers. Three shapes resolve out of it, close enough '
             'to touch. The fileserver is the one you want: that is where '
             'the ledger lives. Look at it properly. Type `probe fs-vault07`.',
             '`probe fs-vault07`.'),
    'mapped': ('Two doors on it. The share is the soft one. Break it: '
               '`crack fs-vault07 share`. If you want the sum before you '
               'commit, `odds crack fs-vault07 share` prints it, and it '
               'costs nothing.',
               '`crack fs-vault07 share`.'),
    'open': ('In. It will take a connection now. Stand on it: '
             '`connect fs-vault07`.',
             '`connect fs-vault07`.'),
    'stood': ('The ledger is right there. Take it and nothing else, and do '
              'not read it. Type `pull`.',
              '`pull`.'),
    'taken': ('That woke something. It has your shape now and it is coming '
              'down the wire for it. Do not be here. Type `jack out`.',
              '`jack out`.'),
    'door': ('Half a minute before the log works out your shape. Look '
             'around. Type `scan`.',
             '`scan`.'),
}


def after(sess) -> None:
    """Once per command while the scene runs: her reactions, then the next
    thing to type. Reads the run rather than counting commands, so a wrong
    word, a failed crack or a wander to the desk are all answered with
    where the job actually stands."""
    p = sess.prologue
    state = sess.run
    if p is None or state is None:
        return
    c = sess.console
    vault = state.net.node(VAULT)
    desk = state.net.node(DESK)
    sentry = vault.ice[0] if vault.ice else None

    # Reactions, each once.
    if desk.mapped and not p.desk:
        p.desk = True
        c.say('[dim]The desk: a lunch order, a photo of somebody\'s dog, and '
              'four years of shortcuts. Not that one.[/]')
    if (not vault.open and state.failed.get((VAULT, SHARE), 0) > 0
            and not p.held):
        p.held = True
        _voice(c, 'It held. It will not hold twice. Again.')
    if state.char.integrity < state.char.integrity_max and not p.struck:
        p.struck = True
        _voice(c, 'That is what it does. It will do it again. Out.')
    if state.trace >= 80 and not p.warned:
        p.warned = True
        _voice(c, 'Eighty. Whatever you are doing, finish it in one. Then '
                  'out.')

    stage = _stage(state)
    if stage != p.stage:
        p.stage = stage
        awake = sentry is not None and sentry.state not in ('dormant', 'dead')
        full, _ = _LINES[stage]
        c.blank()
        if stage == 'stood' and awake:
            full = ('The ledger is right there, and so is the thing that '
                    'lives on this host, and it is awake. Take the ledger in '
                    'one and do not read it. Type `pull`.')
        if stage == 'taken':
            if sentry is not None and sentry.state == 'dormant':
                # The one light sleeper on the vault, woken by the ledger
                # leaving: the tell prints on the engine's next tick.
                sentry.state = 'awake'
                sentry.known = True
                c.say('[dim]The ledger comes loose into the deck, warm and '
                      'heavier than a file has any right to be. And the '
                      'network stops pretending it cannot see you.[/]')
            else:
                c.say('[dim]The ledger comes loose into the deck, warm and '
                      'heavier than a file has any right to be.[/]')
                full = ('It has your shape now, and it has the ledger\'s. Do '
                        'not be here. Type `jack out`.')
        _voice(c, full)
        if stage == 'door':
            c.say('[dim]`skip` goes straight to making your own runner.[/]')
        if stage == 'taken':
            c.say('[dim](It is warm. `read` it, one tick, and she would not '
                  'want you to.)[/]')
        return
    _, short = _LINES[stage]
    c.say(f'[accent]Switchboard[/][dim]: {short}[/]')


def intercept(sess, line: str) -> bool:
    """The two words the scene answers itself: `skip`, and `read`."""
    p = sess.prologue
    if p is None:
        return False
    low = line.strip().lower()
    if low in _SKIP:
        c = sess.console
        c.blank()
        c.say('[dim]Straight to it, then.[/]')
        _leave(sess, {})
        return True
    if low in _READ:
        c = sess.console
        state = sess.run
        if state is None or _stage(state) != 'taken':
            c.say('[dim]Nothing in the deck to read yet.[/]')
            return True
        if p.read:
            c.say('[dim]You have read it. The word does not change.[/]')
            return True
        p.read = True
        c.blank()
        c.say('[dim]You open it, because it is warm and because she said '
              'not to. Most of it is numbers. One word is not.[/] '
              '[accent2]Deepwater.[/]')
        c.blank()
        _voice(c, 'I said do not read it. Out. Now.')
        state.advance(1)
        if sess.run is not None and sess.run.running:
            from .commands.run import _hud
            _hud(sess)
        return True
    return False


def finish(sess, state, summary: dict) -> None:
    """The run is over, one way or another: her verdict, what she was, and
    the question. Called by the run's own close-out in place of the city
    consequences, because there is no city yet and nothing here is kept."""
    p = sess.prologue
    c = sess.console
    outcome = summary.get('outcome', 'burned')
    took = state.net.objective_asset in state.haul
    c.blank()
    if outcome == 'severed':
        c.say('[dim]The ceiling of a rented booth. Your own hands. The deck '
              'fans screaming and a taste of copper. Somebody in the Sixes '
              'is looking at a shape on a screen and it is yours.[/]')
        c.blank()
        _voice(c, 'Still there? Good. They have your shape. Not your name: '
                  'they have hers, and she is past minding. That will do '
                  'for a week.')
    elif took:
        c.say('[dim]You rip the connection out by the root. The room lunges, '
              'closes on the place you were, and finds cooling air. Then the '
              'ceiling of a rented booth, and your own hands, and the sweat '
              'cold on the back of your neck.[/]')
        c.blank()
        _voice(c, 'You are out. You are breathing. Not everyone who takes '
                  'that job is, tonight.')
        if p is not None and p.read:
            c.blank()
            c.say('[dim]The ledger sits in the deck with a word in it you '
                  'were not paid to read, and read anyway.[/] '
                  '[accent2]Deepwater.[/]')
            c.say('[dim]Switchboard is quiet for a second longer than a '
                  'machine should be.[/]')
            _voice(c, '"Forget you saw that."')
        else:
            c.blank()
            c.say('[dim]The ledger sits in the deck, unread, which is the '
                  'first sensible thing anybody has done with it.[/]')
    else:
        c.say('[dim]You are out, and empty. The room comes back the same '
              'way it would have with the ledger in the deck, and the '
              'ceiling is the same ceiling.[/]')
        c.blank()
        _voice(c, 'She would have gone back for it. That is why she is not '
                  'here. There is no shame in the door.')

    c.blank()
    c.rule('and now', role='accent2')
    c.say('[dim]That was her deck. Her name. Her job. You gave the name back '
          'the moment you were clear of it, because it was never yours.[/]')
    c.blank()
    c.say('[dim]She kept a cat in a safehouse in the Ninth that nobody has '
          'fed since Tuesday. She had three names under hers on the wall of '
          'the pit beneath the Shambles, and the fourth put her in a clinic. '
          'She owed Auntie Nine, and Auntie Nine does not forget. She lost '
          'this deck at Ninepins twice and won it back twice. She took Kick '
          'to stay sharp, and it is why she is not here. Moth offered to '
          'come in with her on this one, and she said no. The city called '
          'her something once, a name she earned rather than one she was '
          'given, and it will call you something too, when you have done a '
          'thing worth a name.[/]')
    c.blank()
    c.say('[dim]All of it is still there. The cat still needs feeding.[/]')
    c.blank()
    c.say('[fg]The next one is yours. Who are you?[/]')
    c.blank()
    _leave(sess, {'outcome': outcome, 'read': bool(p and p.read), 'took': took})


def _leave(sess, result: dict) -> None:
    """Put the borrowed runner away and start the real one."""
    sess.run = None
    sess.game = None
    sess.prologue = None
    sess.prologue_result = dict(result)
    from .commands import guide
    guide.start_creation(sess)


#: What the scene hands the runner made after it, said once at the end of
#: creation, in the order the flags are checked.
def carry(sess) -> list[str]:
    """Apply the scene's result to the new character. Returns the lines
    that say so."""
    res = getattr(sess, 'prologue_result', None) or {}
    game = sess.game
    if not res or game is None:
        return []
    sess.prologue_result = {}
    said: list[str] = []
    if res.get('read'):
        game.story.flags.add('dw_heard')
        said.append('You have heard the word. Somebody in this city will '
                    'notice that you have, sooner than they would have.')
    if res.get('outcome') == 'severed':
        game.alias.add_heat('sixes', SEVERED_HEAT)
        game.city.news.append('[heat]The Sixes are asking who was on the '
                              'borrowed deck last night. They have a shape, '
                              'not a name.[/]')
        said.append(f'The Sixes have a shape to look for. {SEVERED_HEAT} '
                    f'heat on your name, from a night that was not yours.')
    elif res.get('took'):
        game.char.credits += CLEAN_BONUS
        said.append(f'The street rounds up: {CLEAN_BONUS:,}c, for getting '
                    f'out with it.')
    return said
