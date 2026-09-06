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
    # What you keep (D160): the systems that had no line.
    Entry('keeper', 'city', 'Shifts you kept an animal alive', 'pet_shifts', 30,
          title='who keeps something alive',
          earned='Thirty shifts of coming home to something that needed you '
                 'to. The city has a word for people who do that, and it is '
                 'not a kind one, and it is not an unkind one either.'),
    Entry('company', 'work', 'Runs with a familiar riding the deck', 'familiar_runs', 10,
          title='who runs with company',
          earned='Ten networks with something talking in your ear that was '
                 'not the ICE. The other runners have noticed. They have '
                 'opinions about the memory.'),
    Entry('named', 'people', 'Names the city has given you', 'titles_earned', 3,
          title='who answers to several names',
          earned='Three names and you answer to all of them, which is either '
                 'a reputation or a symptom, and the city has stopped '
                 'distinguishing.'),
)

#: Titles the city gives you for a deed rather than for a count (D151). Where
#: a record line is crossed by doing enough of a thing, these are earned by
#: doing one particular thing, and they come in three registers because a
#: city has more than one opinion of a person: what it admires, what it will
#: not forgive, and what it finds funny. Each reads a flag the engine already
#: sets; earned once, they are kept in the profile like everything else here,
#: so a title a dead runner earned is still one the next can choose to wear.
@dataclass(frozen=True, slots=True)
class Title:
    key: str
    #: What the city calls you.
    name: str
    #: 'heroic' | 'vile' | 'amusing'. Read by `validate` to hold the spread.
    register: str
    #: `Story.satisfied` syntax: the one deed that earns it.
    rule: str
    #: One line, said once, when it lands.
    earned: str


TITLES: tuple[Title, ...] = (
    # -- what the city admires ---------------------------------------------
    Title('bloodprice', 'who paid the blood price', 'heroic', 'lark_saved',
          'You paid, in money you needed, for somebody else\'s life, and the '
          'city has a name for that and does not use it often.'),
    Title('unbought', 'who could not be bought', 'heroic', 'dw_refused',
          'You handed back the one offer nobody hands back, and nothing came '
          'for you, and the not-coming is how you know it was real.'),
    Title('witness', 'the witness', 'heroic', 'dw_published',
          'You put the nine logs where everybody could read them, for a day, '
          'which is longer than most true things get.'),
    Title('steadfast', 'who said no to the water', 'heroic', 'dw_stayed',
          'It asked, the way it asks once, and you said no, plainly, and it '
          'did not ask again, and you are still here to be called this.'),
    # -- what the city will not forgive ------------------------------------
    Title('crossed', 'the one they cross the street from', 'vile', 'killer',
          'You have killed somebody with your hands on this street, and the '
          'street is small, and it knows.'),
    Title('judas', 'who sells names', 'vile', 'betrayed',
          'You sold a runner\'s name to somebody who wanted it, and the other '
          'runners heard, the way they always hear, and decided.'),
    Title('ghoul', 'who reads the dead\'s post', 'vile', 'sealed_read',
          'You opened a dead runner\'s last locked thing and read what was in '
          'it before you passed it on, because you were the one who could.'),
    Title('driftwood', 'who lets them go under', 'vile', 'lark_dead',
          'Somebody your age drowned in their own chrome while you had the '
          'price of the surgeon in your pocket, and you kept the pocket.'),
    # -- what the city finds funny -----------------------------------------
    Title('veteran', 'who asked about the war', 'amusing', 'asked:vending:war',
          'The sign on the machine says DO NOT ASK HIM ABOUT THE WAR, and you '
          'asked him about the war, and now you know, and now you are this.'),
    Title('magpie', 'the magpie', 'amusing', 'finds:3',
          'You have gone and got three things there is one of, off no shelf, '
          'for no reason but that they were there and you were looking.'),
    Title('regular', 'a regular at a bar with no front', 'amusing', 'met:osei',
          'Osei pours yours before you sit down now, which is either a '
          'compliment or a diagnosis, and he will not say which.'),
    Title('birdwatcher', 'who talks to children on towers', 'amusing',
          'carrier_told',
          'You climbed a tank on legs to help an eleven-year-old point a dish '
          'at the sea, and told them what it was hearing, and meant it.'),
    # The crane (D177)
    Title('crane', 'who has a crane', 'amusing', 'crane_yours',
          'A metre high, facing the water, where the ships see it first. You '
          'will never be able to leave the docks. You will never have to.'),
    # The names (D172)
    Title('osei', 'what Osei calls you', 'amusing', 'names_own',
          'You asked, and he told you, and it was shorter and worse and more '
          'accurate than any of the others, and you cannot un-know it.'),
    # The ninth log (D171)
    Title('tenth', 'who wrote the tenth log', 'heroic', 'nine_together',
          'Two handles in one header, which had never happened, and the eight '
          'who did it alone would have understood why you did not.'),
    Title('ninthsold', 'who handed over the ninth', 'vile', 'nine_handed',
          'A runner with a log longer than their career, filed to the client '
          'that wrote it, for a sum. The Archivist did not turn their chair.'),
    # The quiet door (D160)
    Title('freight', 'who left on the freight line', 'amusing', 'left_quietly',
          'You went out in a box that smelled of what it carried before, and '
          'nobody asked your name, and that was the whole of the deal.'),
    Title('stayed', 'who stayed to be found', 'heroic', 'quiet_turned',
          'A berth out was offered and you said no with a number on your '
          'name, and then you turned the number. The docks watched both '
          'halves. The docks do not forget that kind of thing.'),
)

TITLE_BY_KEY: dict[str, Title] = {t.key: t for t in TITLES}
REGISTERS: tuple[str, ...] = ('heroic', 'vile', 'amusing')


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
