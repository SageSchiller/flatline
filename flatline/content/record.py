"""What the city can say about you (D142).

Not achievements, and never announced as achievements. The game's thesis
is that the city remembers, and this is the memory made countable: what
you have done, where you have stood, who you know, and what you have put
down. It is the one screen that answers "what is left", which a city with
seventy-two quarters and twenty-five one-of-a-kind things in it owes the
player.

Four sections, because there are four reasons people play: the work, the
city, the people and the floor. Each line is a count against a target,
and crossing one earns a **name** rather than a badge: something the city
starts calling you, kept in the profile so it survives the character, the
way the terminal does.
"""

from __future__ import annotations

from dataclasses import dataclass

SECTIONS = (
    ('work', 'The work', 'What you have done with a deck.'),
    ('city', 'The city', 'Where you have been, and what you found there.'),
    ('people', 'The people', 'Who knows you, and how.'),
    ('floor', 'The floor', 'What you have done without one.'),
)
SECTION_KEYS = tuple(k for k, _, _ in SECTIONS)


@dataclass(frozen=True, slots=True)
class Entry:
    key: str
    section: str
    #: The line, in the second person.
    name: str
    #: What the counter is called in `save.META` or on the game.
    counter: str
    #: What counts as done.
    target: int
    #: What the city calls you for it, or '' when it is only a count.
    title: str = ''
    #: One line, said once, when it lands.
    earned: str = ''


ENTRIES: tuple[Entry, ...] = (
    # -- the work ----------------------------------------------------------
    Entry('runner', 'work', 'Runs finished', 'runs_completed', 12,
          title='a working runner',
          earned='Twelve networks. Somebody in a bar describes a job to '
                 'somebody else and uses your handle as the unit.'),
    Entry('clean', 'work', 'Runs that left nothing behind', 'clean_runs', 6,
          title='quiet',
          earned='Six runs and no residue worth the name. There are people '
                 'whose job is noticing that, and they have.'),
    Entry('black', 'work', 'Black ICE survived', 'black_ice_survived', 1,
          title='still here',
          earned='You have been stopped by the thing that stops people and '
                 'you are still here, which is a sentence about twelve '
                 'people in this city can say.'),
    Entry('haul', 'work', 'Best night, in credits', 'best_credits', 20000,
          title='well paid',
          earned='Twenty thousand in hand at once. It will not last. It was '
                 'still twenty thousand.'),
    Entry('threads', 'work', 'Storylines you carried', 'threads_closed', 10,
          title='in the middle of things',
          earned='Ten stories with you in them. The city has started using '
                 'your name to explain other things that happened.'),
    Entry('spine', 'work', 'The main line, carried to an end',
          'spine_finished', 1,
          title='who went and looked',
          earned='You took the thing about the water all the way to one of '
                 'its ends. Most people who hear the name never find out '
                 'what it is.'),
    Entry('errands', 'work', 'Street work done', 'errands_done', 15,
          earned='Fifteen jobs that needed no deck. Somebody always needs '
                 'something carried, and now they ask for you.'),
    # -- the city ----------------------------------------------------------
    Entry('walked', 'city', 'Districts walked', 'districts_seen', 12,
          title='who has been everywhere',
          earned='All twelve. There is nowhere in this city you would have '
                 'to ask directions to, which is not the same as being '
                 'welcome in it.'),
    Entry('stood', 'city', 'Places stood in', 'places_stood', 30,
          title='who stands about',
          earned='Thirty places that are not on the way to anywhere. You '
                 'have started to have opinions about doorways.'),
    Entry('found', 'city', 'One of a kind, found', 'relics_found', 6,
          title='who finds things',
          earned='Six things there is one of. Every one of them was a '
                 'rumour first, and you were the one who went and looked.'),
    Entry('drift', 'city', 'Deepest drift reached', 'deepest_drift', 60,
          title='further in than out',
          earned='Sixty. The net is not a place you visit any more and you '
                 'have known that for a while.'),
    Entry('nights', 'city', 'Nights the street had weather', 'nights_seen', 5,
          earned='Five nights of the city having its own opinion about '
                 'whether you should be out in it.'),
    Entry('shelf', 'city', 'Things the deck found for you', 'watch_hits', 5,
          earned='Five times you asked the net where something was and went '
                 'and got it. That is what it is for.'),
    # -- the people --------------------------------------------------------
    Entry('known', 'people', 'People met', 'people_met', 20,
          title='who knows people',
          earned='Twenty names who know yours. That is a different city to '
                 'the one you started in.'),
    Entry('asked', 'people', 'Things asked about', 'topics_asked', 25,
          title='who asks',
          earned='Twenty-five questions asked of people who knew the answer. '
                 'Most runners never ask anybody anything.'),
    Entry('bonds', 'people', 'Runners who decided about you', 'bonds_formed', 2,
          title='not working alone',
          earned='Two of the other runners have made their minds up about '
                 'you, one way or the other, and both of those are worth '
                 'having.'),
    Entry('standing', 'people', 'Best standing with anybody', 'best_standing', 40,
          title='vouched for',
          earned='Somebody in this city will say your name in a room you are '
                 'not in, and it will help.'),
    Entry('decided', 'people', 'Decisions taken in a story', 'decisions_made', 12,
          title='who decides',
          earned='Twelve times somebody put it to you and you answered. The '
                 'ending will remember every one of them.'),
    Entry('hunted', 'people', 'Bounties worn', 'bounties_taken', 1,
          earned='Somebody has put a number against your name. It is not a '
                 'good number and it is a number.'),
    # -- the floor ---------------------------------------------------------
    Entry('fights', 'floor', 'Fights won', 'fights_won', 10,
          title='who is not worth it',
          earned='Ten. The word for you on this street is not a compliment '
                 'and it is doing a job that a compliment could not.'),
    Entry('wall', 'floor', 'Rungs of the wall taken', 'pit_rank', 3,
          title='on the wall',
          earned='Three rungs. Your name is on a wall in the Shambles above '
                 'other people\'s names, which is the oldest kind of record '
                 'there is.'),
    Entry('champion', 'floor', 'The wall held', 'pit_champion', 1,
          title='who holds the wall',
          earned='The wall is yours and the blade is yours, and both of '
                 'those were somebody else\'s for nine years.'),
    Entry('stood_up', 'floor', 'Faction people beaten', 'factions_fought', 3,
          title='who does not pay',
          earned='Three different outfits have sent people and got them '
                 'back. They talk to each other, and they have.'),
    Entry('doorways', 'floor', 'Doorways held for somebody', 'doorways_held', 5,
          earned='Five times somebody needed a person in front of them and '
                 'the person was you.'),
    Entry('blooded', 'floor', 'The kind that kills, survived', 'kills_done', 1,
          earned='You have been to the top of the street\'s ladder and come '
                 'back, and it left something in how you stand.'),
)

BY_KEY: dict[str, Entry] = {e.key: e for e in ENTRIES}
BY_SECTION: dict[str, list[Entry]] = {
    k: [e for e in ENTRIES if e.section == k] for k in SECTION_KEYS}
#: Counters the record reads. Every one has to be written by the engine,
#: which `validate` holds it to.
COUNTERS: tuple[str, ...] = tuple(dict.fromkeys(e.counter for e in ENTRIES))

#: What the city calls somebody who has done all of one section.
SECTION_TITLE = {
    'work': 'a name on the board',
    'city': 'who has walked all of it',
    'people': 'known everywhere',
    'floor': 'not somebody you send people to',
}
#: And the whole of it, which almost nobody will do.
COMPLETE = 'who did the lot'
COMPLETE_LINE = (
    'Every line of it. There is a version of this city where somebody did '
    'all of that, and you are standing in it, and it is still raining.')
