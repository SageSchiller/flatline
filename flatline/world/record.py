"""Reading the record (D142).

Counts live in the profile (`save.META`) rather than the save, because
these are "has this player ever" questions and the answer has to survive a
flatline the way the terminal does. The live game is read for the lines
that are about right now.
"""

from __future__ import annotations

from ..content import record as record_content


def counts(game, meta: dict) -> dict:
    """Every counter the record reads, live game first, profile behind."""
    out = {k: int(meta.get(k) or 0) for k in record_content.COUNTERS}
    if game is None:
        return out
    story, city, char = game.story, game.city, game.char
    flags = story.flags
    live = {
        'runs_completed': char.runs,
        'districts_seen': len(city.visited),
        'places_stood': sum(1 for f in flags if f.startswith('visited:')),
        'relics_found': sum(1 for f in flags if f.startswith('found:')),
        'nights_seen': sum(1 for f in flags if f.startswith('night:')),
        'watch_hits': int(city.messaged.get('watch_hits', 0)),
        'people_met': len(story.met),
        'topics_asked': sum(1 for f in flags if f.startswith('asked:')),
        'bonds_formed': sum(1 for r in city.rivals if getattr(r, 'bond', '')),
        'decisions_made': sum(1 for f in flags if f.startswith('chose:')),
        'threads_closed': sum(1 for v in story.reached.values() if v),
        'errands_done': int(getattr(city, 'errands_done', 0)),
        'best_credits': char.credits,
        'deepest_drift': char.dissonance,
        'fights_won': int(getattr(city, 'fights_won', 0)),
        'pit_rank': int(city.pit.get('rank', 0)),
        'pit_champion': 1 if 'pit:champion' in flags else 0,
        'factions_fought': sum(1 for f in flags if f.startswith('fought:')),
        'doorways_held': int(getattr(city, 'doorways', 0)),
        'kills_done': 1 if 'killer' in flags else 0,
        'bounties_taken': 1 if city.bounties else 0,
        'black_ice_survived': 1 if 'black_ice' in char.marks else 0,
    }
    for key, value in live.items():
        if key in out:
            out[key] = max(out[key], int(value))
    return out


def earned(counts_now: dict) -> list:
    """Every entry whose line is done."""
    return [e for e in record_content.ENTRIES
            if counts_now.get(e.counter, 0) >= e.target]


def newly_earned(counts_now: dict, already) -> list:
    said = set(already or ())
    return [e for e in earned(counts_now) if e.key not in said]


def sections_done(counts_now: dict) -> list[str]:
    got = {e.key for e in earned(counts_now)}
    return [k for k in record_content.SECTION_KEYS
            if all(e.key in got for e in record_content.BY_SECTION[k])]


def titles(counts_now: dict, recorded=None) -> list[str]:
    """What the city calls you, newest last.

    `recorded` is the profile's list of lines in the order they landed
    (D144). It used to be catalogue order, so the name on `char` was
    whichever earned line sat latest in the list: "who asks" through six
    later names, and "on the wall" after "who went and looked". A line
    earned but not yet announced is newer than any that has been.
    """
    got = earned(counts_now)
    if recorded:
        order = {k: i for i, k in enumerate(recorded)}
        got.sort(key=lambda e: order.get(e.key, len(order)))
    out = [e.title for e in got if e.title]
    for k in sections_done(counts_now):
        out.append(record_content.SECTION_TITLE[k])
    if len(earned(counts_now)) == len(record_content.ENTRIES):
        out.append(record_content.COMPLETE)
    return out


def extra_earned(game) -> list:
    """The flavoured titles (D151) whose deed has been done: read against the
    live game, since they are earned by doing one thing rather than by a
    count the profile keeps."""
    if game is None:
        return []
    return [t for t in record_content.TITLES
            if game.story.satisfied(t.rule, game)]


def all_titles(counts_now: dict, meta: dict) -> list[str]:
    """Every title this profile can wear: the record\'s, newest last, then
    the extra titles it has earned (D151). Used by `called` and by the pin,
    so both draw on the same pool."""
    out = list(titles(counts_now, (meta or {}).get('recorded')))
    for key in (meta or {}).get('titles') or ():
        entry = record_content.TITLE_BY_KEY.get(key)
        if entry is not None and entry.name not in out:
            out.append(entry.name)
    return out


def title_of(counts_now: dict, recorded=None, meta=None) -> str:
    """What the city calls you now: the one you have pinned if it is still
    earned, otherwise the newest (D151). `meta` carries the pin and the
    earned extra titles; `recorded` is kept for the callers that have only
    that."""
    pool = all_titles(counts_now, meta if meta is not None
                      else {'recorded': recorded})
    if meta:
        chosen = meta.get('called') or ''
        if chosen and chosen in pool:
            return chosen
    return pool[-1] if pool else ''
