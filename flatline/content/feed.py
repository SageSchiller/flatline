"""The deck, in the city (D135): what it says when you are not jacked in.

Mail from the people who would actually message you, a search that knows
where things are sold, a watch that tells you when they land, a line to
the other runners, and the ads. The ads are the thesis in another key:
everything you do is loud and the city remembers, and so the ads *know*.
They are targeted by what you actually did, in the absurd register the
tone budget already allows, and every one of them is on the nose on
purpose.

Every feature here has a mechanical hook, or it would be a drawer of
toys: search finds real stock, mail moves standing and points at real
work, a watch saves a shift, a message moves a disposition, an ad reads
your state.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Predicates the world layer evaluates for an ad or a message. Listed so
#: the validator can hold content to them.
WHEN = ('any', 'shot_at', 'hurt', 'drift', 'habit', 'loud', 'killer',
        'veteran', 'debt', 'champion', 'blooded', 'hot', 'broke', 'rich',
        'chromed', 'clean')


@dataclass(frozen=True, slots=True)
class Ad:
    key: str
    #: Who is paying for it.
    sponsor: str
    #: The ad. Deadpan. It may address you.
    text: str
    #: A predicate from `WHEN`. Specific ones are shown before `any`.
    when: str = 'any'
    tone: str = 'absurd'


ADS: tuple[Ad, ...] = (
    Ad('plating', 'Kohler-Reyes',
       'You were recently shot at. We noticed, because we were listening. '
       'Have you considered plating? Our plating has considered you.',
       when='shot_at'),
    Ad('clinic_hurt', 'A clinic near you',
       'You are hurt. We can tell from here. A clinic near you is open, and '
       'would like to say that the slow way of healing is also a way, but '
       'not one we recommend to anybody we would like to see again.',
       when='hurt'),
    Ad('drift', 'Kohler-Reyes',
       'A message for the person who is more machine than they were last '
       'month: it is fine. Many of our best customers are. Some of them are '
       'products.', when='drift'),
    Ad('vending', 'The Concourse Vending Association',
       'The machines on the concourse have a position on your habit, and the '
       'position is that they stock it. This message was printed by a '
       'machine that is not judging you, in a font that is.', when='habit'),
    Ad('nightwatch_psa', 'Nightwatch Community Relations',
       'A reminder, addressed to you specifically, that discharging a firearm '
       'in a public walkway is a matter for the Nightwatch, that we have your '
       'serial, and that we hope you are having a pleasant evening.',
       when='loud', tone='wry'),
    Ad('lawyer', 'Abernathy, Abernathy & Blank',
       'Have you recently ended somebody? Our clients often have. Consultations '
       'are discreet, our offices are in the Vertical, and the first hour is '
       'free because the second one is not.', when='killer', tone='wry'),
    Ad('veteran', 'Sendai Precision',
       'Runners like you have been in the net for a while. Runners like you '
       'have a tell, and the tell is that you are still reading this instead '
       'of skipping it. Sendai Precision: for the ones who read to the end.',
       when='veteran'),
    Ad('lender', 'A lender who prefers not to be named',
       'You owe money. This is not an advertisement. It is a reminder that '
       'the advertisement you are about to see was paid for with what you '
       'owe, and that we would like it back.', when='debt', tone='wry'),
    Ad('champion', 'Carrion, in a personal capacity',
       'The wall in the pit under the fence has a new name on it, and it is '
       'yours, and the house would like to sponsor you, which means it would '
       'like to put its name on your back and a small cut on your purse.',
       when='champion'),
    Ad('blooded', 'A tailor in the Row',
       'You have started standing in doorways a certain way. We make a coat '
       'for that. It is not armour. It is the way it hangs when you stand '
       'like that, which is the whole of what people see.', when='blooded',
       tone='wry'),
    Ad('hot', 'Freeport Cranes & Rebuild',
       'Somebody is looking for you, according to a source we are not going '
       'to name because it is the same source you use. Freeport has cranes, '
       'a tide, and a policy of not knowing who is in the container.',
       when='hot', tone='wry'),
    Ad('broke', 'The Hall',
       'You have no money. The Hall has soup. This is not a business '
       'relationship and the Hall would like to be very clear about that, '
       'and about the soup, which is mostly lentils.', when='broke'),
    Ad('rich', 'Meridian Row, collectively',
       'You have money. The Row would like to sell you something that is '
       'the same as the thing you have, at a price that is not, on the '
       'grounds that the difference is the point.', when='rich'),
    Ad('chromed', 'A clinic in the Glasshouse',
       'You have a lot in you. Not a judgement. We are asking because at a '
       'certain point the question of who is servicing whom becomes '
       'interesting, and we have an interest.', when='chromed'),
    Ad('clean', 'Nobody, apparently',
       'This slot was bought by a company that has since stopped existing. '
       'The ad is for a product that was never made. Please enjoy the '
       'silence, which the company would like you to associate with it.',
       when='clean'),
    Ad('energy', 'The energy drink',
       'The energy drink. You know the one. It has been on the billboard '
       'since before you were born and it will be there after, and it '
       'would like you to know that the sorry was sincere.'),
    Ad('optimism', 'The Kagawa Vertical',
       'The Kagawa Vertical is monitored by systems that care. This is a '
       'statement of fact and also a threat and also, we think, rather '
       'lovely.'),
    Ad('umbrella', 'A man with umbrellas',
       'It is going to rain. It is always going to rain. A man on the '
       'Freeport gate has umbrellas and no opinion about where you got the '
       'money, which is a rarer thing to sell than umbrellas.'),
)

AD_BY_KEY: dict[str, Ad] = {a.key: a for a in ADS}

#: Mail. Each pool is picked from by the day, `{name}` and the rest fill.
PARTNER_MAIL = (
    '"Still here. Still around. If you go into somewhere with a door I '
    'do not like the look of, say, and I will stand outside it."',
    '"Heard you were in {district}. I was near. You did not call. That '
    'is fine. It is not fine. Call."',
    '"Job on the board with your shape on it. I am not taking it. Take it, '
    'and tell me where, and I will be there before you are."',
)
NEMESIS_MAIL = (
    '"I know where you sleep. I have not done anything about it. I would '
    'like you to notice the second half of that sentence, tonight, for as '
    'long as it lasts."',
    '"Every job you take, I take the one next to it. You will find that '
    'out the night it matters."',
    '"You are going to hear my name in a room where you did not expect it. '
    'That is not a threat. It is a schedule."',
)
FIXER_MAIL = (
    '"I have something physical. Not a run. Somebody who needs a bad night '
    'and a place that needs standing in front of. You know where I am."',
    '"Two things that need doing with hands. I thought of yours."',
)
WORK_MAIL = (
    '"There is a job I am not putting on the board, because the board '
    'is where people read things. Come and be handed it."',
)
LENDER_MAIL = (
    '"{amount}c. You know the terms. This message is a courtesy, and the '
    'next one will not be a message."',
    '"A reminder about the {amount}c, from somebody who does not send '
    'reminders twice."',
)
PIT_MAIL = (
    '"The wall has your name at rung {rank}. {next} is asking about you. '
    'Asking is what {next} does before the other thing."',
)
BOUNTY_MAIL = (
    '"There is a number against your name with {faction}. This message '
    'is from somebody who would like you to know that they know, and '
    'that knowing has a price, and that they are not the only one."',
)
WATCH_MAIL = '{item} is on a shelf in {district}: {price}c this cycle.'
STORY_MAIL = 'Something you are in the middle of: {short}'

#: Replies to a message, by the other runner's opinion of you.
REPLIES: dict[str, tuple[str, ...]] = {
    'will sell you': (
        '"Received." That is the whole of it, and it was sent to two '
        'people.',
    ),
    'hostile': (
        '"Do not message me."',
        '"I read it. I am not going to say what I did with it."',
    ),
    'cold': (
        '"Busy."',
        '"What do you want." There is no question mark.',
    ),
    'neutral': (
        '"Sure." A minute later: "What was that about?"',
        '"Heard you. Working. Talk at the Hall sometime."',
    ),
    'friendly': (
        '"Good to hear from you. I am on something in {district}; it is '
        'going the way they go. Yours?"',
        '"Message me when you are done, and I will tell you what I heard '
        'about the place you are going."',
    ),
    'owes you': (
        '"Anything. Say the word. I have not forgotten."',
        '"You messaged. Good. I was going to. I am in {district} and the '
        'thing there is worse than the board says; if you are near, do '
        'not be."',
    ),
    'partner': (
        '"Here. Where?"',
        '"I am two districts away and moving. Whatever it is, it is ours."',
    ),
    'nemesis': (
        '"I was wondering when you would."',
        'No reply. The message shows as read, and then, an hour later, '
        'as read again.',
    ),
}
NO_REPLY_YET = '{name} has not answered the last one. They will, or they will not.'
NO_LINE = '{name} is dead, and the deck does not know that yet, and sends it.'

#: What the search says.
SEARCH_NONE = ('The net does not know where that is this cycle, which '
               'means nobody is selling it or nobody is saying.')
SEARCH_RELIC = ('The net does not sell that. It is one of a kind, and the '
                'people who ask about it in {district} stop asking, which '
                'is where you should ask.')
SEARCH_RELIC_FAR = ('The net does not sell that. There is a rumour, and '
                    'the rumour is careful about districts.')
SEARCH_LOUD = 'A search for a gun is a record. Nightwatch attention +1.'
