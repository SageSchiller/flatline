"""Keeping a pet alive (D152). The state lives on the city as a plain dict so
it round-trips with the save; this is the logic that ages it, cares for it,
and, when nobody did, loses it. Nothing here reaches a run or a fight: a pet
is the part of the game that is not about the work."""

from __future__ import annotations

from ..content import pets as pet_content


def has_pet(city) -> bool:
    return bool(city.pet)


def adopt(city, key: str, name: str = '') -> dict:
    """Take an animal on. The stats start full; a thing you just took in is
    not already neglected."""
    animal = pet_content.BY_KEY[key]
    city.pet = {
        'key': key,
        'name': name or animal.name,
        'food': pet_content.FULL,
        'water': pet_content.FULL,
        'play': pet_content.FULL,
        'feed': 0,
        'neglect': 0,
        'since': int(city.shift),
    }
    return city.pet


def care(city, stat: str, amount: int = pet_content.FULL) -> None:
    """Top a stat back up, and forgive the neglect streak once something has
    been done: a fed animal is not a lost one, even if it was close."""
    pet = city.pet
    if not pet:
        return
    pet[stat] = min(pet_content.FULL, int(pet.get(stat, 0)) + amount)
    if min(pet['food'], pet['water'], pet['play']) >= pet_content.LOW_AT:
        pet['neglect'] = 0


def advance(city, shifts: int = 1) -> list[str]:
    """Age the pet by the shifts that passed, and say what it did or what
    happened to it. Telegraphed all the way down: a hungry animal tells you
    for a long time before it stops being yours."""
    pet = city.pet
    if not pet:
        return []
    animal = pet_content.BY_KEY.get(pet.get('key', ''))
    if animal is None:
        city.pet = {}
        return []
    told: list[str] = []
    before = _vital(pet)
    played = pet['play']
    for _ in range(max(1, shifts)):
        for stat, rate in animal.decay.items():
            pet[stat] = max(0, int(pet.get(stat, 0)) - int(rate))
        # Food and water are what a thing lives on; play is what it lives
        # for. A starving animal is lost; a bored one is only unhappy. So the
        # neglect that ends it counts the vital needs at nothing, not play.
        if _vital(pet) <= 0:
            pet['neglect'] = int(pet.get('neglect', 0)) + 1
        else:
            pet['neglect'] = 0
        if pet['neglect'] >= pet_content.LOST_AFTER:
            told.append(f'[err]{_lost_line(animal, pet)}[/]')
            city.pet = {}
            return told
    after = _vital(pet)
    streak = int(pet.get('neglect', 0))
    # Telegraphed: the last-warning line once a vital need has been at nothing
    # long enough that the next stretch of not-coming-home is the end of it;
    # otherwise a line when it crosses into a worse band on the way down; and,
    # failing either, a quiet line for a fed animal nobody has played with.
    if streak == pet_content.WARN_AFTER:
        told.append(f'[warn]{animal.failing}[/]')
    elif _band(after) < _band(before):
        told.append(f'[warn]{_state_line(animal, pet)}[/]')
    elif pet['play'] <= 0 < played and animal.low:
        told.append(f'[dim]{animal.low[0]}[/]')
    return told


def _vital(pet: dict) -> int:
    """The lower of food and water: what the animal actually lives on."""
    return min(int(pet.get('food', 0)), int(pet.get('water', 0)))


def _band(value: int) -> int:
    if value >= pet_content.CONTENT_AT:
        return 2
    if value >= pet_content.LOW_AT:
        return 1
    return 0


def _state_line(animal, pet) -> str:
    m = pet_content.mood(pet)
    if m in ('low', 'failing') and animal.low:
        # Deterministic in the shift, so the same day says the same thing.
        idx = int(pet.get('since', 0) + pet['food']) % len(animal.low)
        return animal.low[idx]
    return animal.failing or (animal.low[0] if animal.low else '')


def _lost_line(animal, pet) -> str:
    name = pet.get('name', animal.name)
    lead = animal.failing
    return (f'{lead} And then a shift came when it was not there, and the '
            f'flat is a flat again. {name} is gone.')


def greeting(city) -> str:
    """What the pet is doing when you come home (a `rest` or an arrival), by
    mood. Deterministic in the shift so it is steady rather than a slot
    machine."""
    pet = city.pet
    if not pet:
        return ''
    animal = pet_content.BY_KEY.get(pet.get('key', ''))
    if animal is None:
        return ''
    m = pet_content.mood(pet)
    if m == 'content' and animal.happy:
        return animal.happy[int(city.shift) % len(animal.happy)]
    if m == 'ok':
        return animal.happy[0] if animal.happy else ''
    if m == 'low' and animal.low:
        return animal.low[int(city.shift) % len(animal.low)]
    if m == 'failing':
        return animal.failing
    return ''


def ending_coda(city) -> str:
    """One line for the epilogue: what became of the pet. A pet that was kept
    to the end reads differently from one that was lost, and the record of
    which is whether it is still on the city when the character ends."""
    pet = city.pet
    if not pet:
        return ''
    animal = pet_content.BY_KEY.get(pet.get('key', ''))
    if animal is None:
        return ''
    name = pet.get('name', animal.name)
    kept = animal.kept_coda or f'{name} outlived you, which is the deal.'
    return kept
