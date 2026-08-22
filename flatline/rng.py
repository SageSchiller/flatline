"""Determinism, per D3. Nothing in this game calls `random` directly.

Two ideas here earn their keep.

**Named streams.** Every system draws from its own generator, derived from the
world seed and a name. Network generation cannot perturb contract generation,
so adding a die roll to one system does not silently rewrite every other
system's output in existing saves. Without this, D3 holds for exactly as long
as nobody edits any code, which is not a useful guarantee.

**Stable derivation.** Child seeds come from blake2b, not from `hash()`, whose
string hashing is randomised per process by default. A world seeded 8829 has to
be the same world tomorrow, on another machine, under another Python.
"""

from __future__ import annotations

import hashlib
import random
from typing import Iterable, Mapping, Sequence, TypeVar

from .config import SEED_MAX

T = TypeVar('T')


def derive(seed: int, name: str) -> int:
    """A stable 64-bit child seed from a world seed and a stream name."""
    h = hashlib.blake2b(f'{seed}:{name}'.encode(), digest_size=8)
    return int.from_bytes(h.digest(), 'big')


class Stream:
    """One named generator. Thin wrapper, but the helpers are the point.

    The helpers exist so that call sites read as intent rather than as
    arithmetic: `rng.chance(0.3)` says what it means, and `rng.spread(10, 0.2)`
    keeps the "give me this number, fuzzed" pattern in one place instead of
    scattered `int(n * (1 + r.uniform(...)))` across forty content files.
    """

    __slots__ = ('name', '_r')

    def __init__(self, name: str, seed: int) -> None:
        self.name = name
        self._r = random.Random(seed)

    # -- primitives --------------------------------------------------------

    def random(self) -> float:
        return self._r.random()

    def chance(self, p: float) -> bool:
        """True with probability p. The most-called method in the codebase."""
        return self._r.random() < p

    def int(self, lo: int, hi: int) -> int:
        """Inclusive on both ends, because every call site wants that."""
        return self._r.randint(lo, hi)

    def roll(self, dice: int, sides: int) -> int:
        return sum(self._r.randint(1, sides) for _ in range(dice))

    def pick(self, seq: Sequence[T]) -> T:
        return seq[self._r.randrange(len(seq))]

    def sample(self, seq: Sequence[T], k: int) -> list[T]:
        k = max(0, min(k, len(seq)))
        return self._r.sample(list(seq), k)

    def shuffled(self, seq: Iterable[T]) -> list[T]:
        out = list(seq)
        self._r.shuffle(out)
        return out

    def weighted(self, options: Mapping[T, float]) -> T:
        """Pick a key with probability proportional to its weight.

        Non-positive weights are dropped rather than clamped, which lets
        content express "this is unavailable right now" as a zero without a
        separate filtering pass at every call site.
        """
        items = [(k, w) for k, w in options.items() if w > 0]
        if not items:
            raise ValueError(f'weighted() with no positive weights: {list(options)}')
        total = sum(w for _, w in items)
        x = self._r.random() * total
        for k, w in items:
            x -= w
            if x <= 0:
                return k
        return items[-1][0]

    def spread(self, base: float, frac: float = 0.15) -> int:
        """`base`, fuzzed by up to `frac` either way, rounded, never below zero.

        The standard way this game turns a designed number into an observed
        one, so that two runs against the same posture are not identical.
        """
        lo, hi = base * (1 - frac), base * (1 + frac)
        return max(0, int(round(self._r.uniform(lo, hi))))

    def curve(self, lo: int, hi: int, bias: float = 0.5) -> int:
        """Triangular distribution over an inclusive range.

        For anything where the extremes should be rare: node counts, ICE
        ratings, contract payouts. `bias` is where the peak sits, 0 to 1.
        """
        if hi <= lo:
            return lo
        mode = lo + (hi - lo) * max(0.0, min(1.0, bias))
        return int(round(self._r.triangular(lo, hi, mode)))

    # -- persistence -------------------------------------------------------

    def getstate(self) -> list:
        """JSON-safe. `random`'s state is nested tuples, which JSON flattens
        to lists; `setstate` needs them back as tuples, hence the pairing."""
        version, internal, gauss = self._r.getstate()
        return [version, list(internal), gauss]

    def setstate(self, state) -> None:
        version, internal, gauss = state
        self._r.setstate((version, tuple(internal), gauss))


class Rng:
    """The seeded world. One per session, threaded everywhere.

    Streams are created lazily on first use and remembered, so a system that
    has never run has no state and costs nothing in the save file.
    """

    #: Every stream name the game uses. Declared rather than discovered so
    #: `validate.py` can assert that nothing draws from an undeclared stream,
    #: which is how a typo like `rng('netowrk')` would otherwise become an
    #: invisible second universe that quietly reruns from scratch each load.
    STREAMS = (
        'world',      # city layout, faction seeding, one-time at creation
        'contracts',  # the board
        'network',    # run topology and node contents
        'ice',        # countermeasure placement and behaviour
        'combat',     # per-action resolution inside a run
        'market',     # stock and prices
        'rivals',     # NPC runner decisions
        'names',      # generated proper nouns
        'events',     # city events between shifts
        # Its own stream rather than borrowing one, because `self --roll` is a
        # player-initiated convenience they may use twenty times in a row, and
        # drawing that from a shared stream would mean the number of times you
        # rerolled your haircut changed which contracts appeared on the board.
        'appearance',
        # Tonight's condition inside a network (D61). Forked on the contract
        # and never drawn from the network stream, so the network a contract
        # generates is the same network whether or not anybody looked at the
        # weather: legwork regenerates it to read it and must get the same one.
        'condition',
        # Same reason as `appearance`, and more so: a player can roll dice
        # forty times in a row for their own entertainment, and drawing that
        # from a shared stream would mean an evening's gambling silently
        # reshuffled the contract board and every network in the city.
        'games',
    )

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self._streams: dict[str, Stream] = {}

    def __call__(self, name: str) -> Stream:
        if name not in self.STREAMS:
            raise KeyError(f'undeclared rng stream {name!r}; add it to Rng.STREAMS')
        s = self._streams.get(name)
        if s is None:
            s = Stream(name, derive(self.seed, name))
            self._streams[name] = s
        return s

    def fork(self, name: str, key: str | int) -> Stream:
        """A throwaway stream keyed to a specific thing.

        Used where an object needs stable randomness independent of when it is
        generated: a network for contract 41 must look the same whether you
        run it now or three shifts from now, and whether or not you looked at
        contract 40 first. Not persisted, because it is reproducible from the
        key alone. That is the whole point of it.
        """
        if name not in self.STREAMS:
            raise KeyError(f'undeclared rng stream {name!r}; add it to Rng.STREAMS')
        return Stream(f'{name}:{key}', derive(self.seed, f'{name}:{key}'))

    # -- persistence -------------------------------------------------------

    def getstate(self) -> dict:
        return {'seed': self.seed,
                'streams': {n: s.getstate() for n, s in self._streams.items()}}

    @classmethod
    def fromstate(cls, state: dict) -> Rng:
        r = cls(int(state['seed']))
        for name, st in (state.get('streams') or {}).items():
            if name in cls.STREAMS:
                s = Stream(name, derive(r.seed, name))
                s.setstate(st)
                r._streams[name] = s
        return r


def random_seed() -> int:
    """A fresh world seed. The only place the game touches system entropy."""
    return random.SystemRandom().randint(0, SEED_MAX)
