"""What you look like, and why the city cares.

This is the seventh customisation axis and the first one that is about the
meat rather than the work. It exists because a character who is only a
statblock is somebody else's character, and because a game that asks you to
build a person should let you decide what the person looks like when they walk
into a room.

It is not a paper doll. Every feature moves two numbers:

**Memorable.** How easily a stranger could describe you afterwards. This is
deliberately two-sided and is the whole design of the system. Being striking
means fixers remember your work and pay accordingly, and it also means the
woman behind the counter can tell Nightwatch exactly who came in. High
memorable earns more reputation per job and converts more residue into heat.
Low memorable is safe and forgettable, and forgettable people get offered
forgettable work.

**Presence.** How much weight you carry in a conversation. Feeds pretext, and
therefore feeds everything social: asking around, hiring, talking your way past
something that expected a badge.

**Chrome sets a floor under memorable and you cannot get back under it.** Past
about forty Dissonance there is no such thing as an unremarkable netrunner:
whatever you have had done shows, in the way you hold still and the way you do
not, and no haircut fixes it. This is the appearance layer paying the same rent
as everything else in this game. You do not get the benefits of the hardware
and the anonymity of not having it.

Four features are permanent, set at creation, changed afterwards only on a
clinic table for real money. Four are yours to change whenever you like, which
makes changing your look the cheap half of going to ground: it will not clear a
bounty, but it buys back a little of what the bounty is worth.

Marks are the exception to both. You do not choose them. They accumulate.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Feature:
    slot: str
    key: str
    name: str
    #: How it reads in the assembled description. Written to follow the
    #: sentence stem in `SLOTS`, so it starts lowercase and does not repeat
    #: the subject.
    look: str
    #: How easy you are to describe to somebody who is writing it down.
    memorable: int = 0
    #: How much room you take up in a conversation.
    presence: int = 0
    #: Rare, and small. Most features are social, not mechanical.
    effects: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Slot:
    key: str
    name: str
    #: Whether the player can change it without surgery.
    fixed: bool
    #: Sentence stem the feature text completes, for the assembled paragraph.
    stem: str
    #: One line explaining what this slot is, for `look --options`.
    blurb: str


SLOTS: tuple[Slot, ...] = (
    Slot('build', 'Build', True, 'You are',
         'Height and frame. What somebody sees at forty metres.'),
    Slot('face', 'Face', True, 'Your face is',
         'Bones and what a life has done to them.'),
    Slot('eyes', 'Eyes', True, 'Your eyes are',
         'The first thing anybody checks for chrome.'),
    Slot('hair', 'Hair', False, 'You wear your hair',
         'The cheapest thing about you to change, and it shows.'),
    Slot('marks', 'Marks', True, 'You carry',
         'Scars, ink, and the things the work has left on you.'),
    Slot('dress', 'Dress', False, 'You dress',
         'What you have decided to tell people before you speak.'),
    Slot('bearing', 'Bearing', False, 'You hold yourself',
         'How you occupy a room you have no business being in.'),
    Slot('voice', 'Voice', False, 'You speak',
         'What people remember when they did not see your face.'),
)

SLOT_BY_KEY: dict[str, Slot] = {s.key: s for s in SLOTS}
SLOT_KEYS: tuple[str, ...] = tuple(SLOT_BY_KEY)
FIXED_SLOTS: tuple[str, ...] = tuple(s.key for s in SLOTS if s.fixed)
FREE_SLOTS: tuple[str, ...] = tuple(s.key for s in SLOTS if not s.fixed)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

FEATURES: tuple[Feature, ...] = (
    Feature('build', 'slight', 'Slight',
            'small and narrow through the shoulders, and have spent your '
            'whole life being underestimated by people who should know '
            'better',
            memorable=-1, presence=-1),
    Feature('build', 'wiry', 'Wiry',
            'thin in the way that comes from doing without rather than from '
            'training for anything',
            memorable=0, presence=-1),
    Feature('build', 'tall', 'Tall',
            'tall enough that doorways in the Ninth are a running argument, '
            'and you have learned to stand in a way that apologises for it',
            memorable=2, presence=1),
    Feature('build', 'heavy', 'Heavy',
            'broad and heavy, and take up the amount of room you take up '
            'without discussing it',
            memorable=2, presence=2),
    Feature('build', 'soft', 'Soft',
            'soft in a city that reads softness as either wealth or '
            'surrender, and you have been mistaken for both',
            memorable=0, presence=-1),
    Feature('build', 'compact', 'Compact',
            'short and solidly put together, and have never once been the '
            'first person in a room somebody looks at',
            memorable=-1, presence=0),
    Feature('build', 'stooped', 'Stooped',
            'bent slightly forward from twenty years of leaning into a deck, '
            'and it no longer straightens out',
            memorable=1, presence=-1),
    Feature('build', 'rangy', 'Rangy',
            'long-limbed and badly proportioned for furniture, which you have '
            'stopped taking personally',
            memorable=1, presence=0),
    Feature('build', 'gaunt', 'Gaunt',
            'thin past the point where anybody polite mentions it, and the '
            'clinics have opinions you have decided not to hear',
            memorable=2, presence=0),
    Feature('build', 'blocky', 'Blocky',
            'built like the loading equipment in Freeport, and about as '
            'interested in being moved',
            memorable=1, presence=2),
    Feature('build', 'unremarkable', 'Unremarkable',
            'the exact average height and the exact average width of the '
            'people around you, which is the most useful thing about you',
            memorable=-2, presence=-1),
    Feature('build', 'asymmetric', 'Asymmetric',
            'put back together at least once by somebody working fast, and '
            'one side of you sits lower than the other',
            memorable=2, presence=0),

    # ----------------------------------------------------------------------
    # face
    # ----------------------------------------------------------------------
    Feature('face', 'plain', 'Plain',
            'the kind nobody describes successfully. Witnesses agree on the '
            'hair and then run out',
            memorable=-2, presence=-1),
    Feature('face', 'sharp', 'Sharp',
            'all angles, and it lands somewhere between handsome and a '
            'warning depending on the light',
            memorable=1, presence=1),
    Feature('face', 'broad', 'Broad',
            'wide and open and honest-looking, which has been worth more to '
            'you than any program you have ever run',
            memorable=0, presence=2),
    Feature('face', 'scarred', 'Scarred',
            'been through something. It healed clean but it healed obvious',
            memorable=3, presence=1),
    Feature('face', 'young', 'Young',
            'younger than the rest of you, and people keep addressing the '
            'face instead of the person behind it',
            memorable=0, presence=-2),
    Feature('face', 'worn', 'Worn',
            'a decade older than you are, and the decade was not free',
            memorable=1, presence=1),
    Feature('face', 'burned', 'Burned',
            'carried a feedback burn down one side since the first deck you '
            'could afford, which was the first deck that could afford you',
            memorable=3, presence=0),
    Feature('face', 'still', 'Still',
            'does not move much. People find this restful or unbearable and '
            'there is no third option',
            memorable=1, presence=1),
    Feature('face', 'kind', 'Kind',
            'built to be trusted, entirely by accident, and you have never '
            'been able to stop trading on it',
            memorable=0, presence=2),
    Feature('face', 'unfinished', 'Unfinished',
            'the result of reconstructive work somebody stopped paying for '
            'partway through',
            memorable=3, presence=-1),
    Feature('face', 'severe', 'Severe',
            'gives nothing away and never has, and children in the Terraces '
            'have opinions about it',
            memorable=1, presence=2),
    Feature('face', 'lopsided', 'Lopsided',
            'slightly wrong in a way people cannot place, and they spend the '
            'whole conversation placing it',
            memorable=2, presence=0),

    # ----------------------------------------------------------------------
    # eyes
    # ----------------------------------------------------------------------
    Feature('eyes', 'brown', 'Brown',
            'brown, original, and yours, which past a certain income bracket '
            'is its own statement',
            memorable=-1, presence=0),
    Feature('eyes', 'grey', 'Grey',
            'a flat grey that people mistake for optics until they look '
            'twice, and by then you have what you needed',
            memorable=0, presence=1),
    Feature('eyes', 'tired', 'Tired',
            'red-rimmed and permanently underslept. The net does this. '
            'Everybody in the trade has them and nobody mentions it',
            memorable=-1, presence=-1),
    Feature('eyes', 'mismatched', 'Mismatched',
            'mismatched: one you were born with and one that was cheaper '
            'than the matching pair',
            memorable=3, presence=0),
    Feature('eyes', 'optics', 'Visible Optics',
            'obviously not eyes. The housings are flush but the ring of scar '
            'tissue is not, and the aperture is audible in a quiet room',
            memorable=3, presence=1),
    Feature('eyes', 'blackout', 'Blackout',
            'solid black from lid to lid, which is a fashion in the Shambles '
            'and a diagnosis anywhere else',
            memorable=4, presence=1),
    Feature('eyes', 'pale', 'Pale',
            'pale enough to look through, and you have been told this in '
            'both a good and a bad way',
            memorable=2, presence=1),
    Feature('eyes', 'shielded', 'Shielded',
            'behind smoked lenses you do not take off indoors, which everyone '
            'assumes is affectation and half of them are wrong',
            memorable=2, presence=1),
    Feature('eyes', 'flickering', 'Flickering',
            'fine until the driver drops a frame, and then for a quarter of a '
            'second there is nobody home',
            memorable=3, presence=-1),
    Feature('eyes', 'warm', 'Warm',
            'the only warm thing about you, which several people have said '
            'out loud and one of them meant kindly',
            memorable=1, presence=2),
    Feature('eyes', 'narrow', 'Narrow',
            'narrow and hard to read, and you have been playing that hand '
            'since before you understood you were holding it',
            memorable=0, presence=1),
    Feature('eyes', 'reconstructed', 'Reconstructed',
            'grown rather than made, on a corporate warranty that expired '
            'while you were still asleep',
            memorable=1, presence=0),

    # ----------------------------------------------------------------------
    # hair
    # ----------------------------------------------------------------------
    Feature('hair', 'cropped', 'Cropped',
            'short, badly, and cut it yourself over a basin every few weeks',
            memorable=-1, presence=0),
    Feature('hair', 'shaved', 'Shaved',
            'shaved to the scalp, which shows the interface ports and saves '
            'a conversation later',
            memorable=1, presence=1),
    Feature('hair', 'long', 'Long',
            'long and tied back out of the way of the jack, which is a runner '
            'tell to anybody who has met one',
            memorable=1, presence=0),
    Feature('hair', 'bleached', 'Bleached',
            'bleached to straw and going brittle at the ends',
            memorable=2, presence=0),
    Feature('hair', 'dyed', 'Dyed',
            'in a colour that does not occur, and reapply it the night before '
            'anything that matters',
            memorable=3, presence=1),
    Feature('hair', 'greying', 'Greying',
            'grey at the temples and have stopped doing anything about it',
            memorable=0, presence=1),
    Feature('hair', 'locked', 'Locked',
            'in locks past your shoulders, gathered up before you jack in',
            memorable=2, presence=1),
    Feature('hair', 'undercut', 'Undercut',
            'long on top and shaved to the skin at the sides, which was '
            'fashionable four years ago and you have not been told',
            memorable=2, presence=0),
    Feature('hair', 'thinning', 'Thinning',
            'in retreat and do not comment on it',
            memorable=0, presence=-1),
    Feature('hair', 'braided', 'Braided',
            'braided tight to the skull in a pattern that takes somebody else '
            'four hours and means something to about two hundred people',
            memorable=2, presence=1),
    Feature('hair', 'wig', 'Wig',
            'differently every time you go out, and none of it is yours',
            memorable=-2, presence=0),
    Feature('hair', 'unkempt', 'Unkempt',
            'like somebody who has not left the flat in nine days, because '
            'the work does not care what you look like',
            memorable=0, presence=-1),
    Feature('hair', 'severe', 'Severe',
            'scraped back so tightly it reads as a policy decision',
            memorable=1, presence=2),
    Feature('hair', 'none', 'None',
            'not at all. Whatever they gave you for the nerve damage took it '
            'and did not give it back',
            memorable=2, presence=0),

    # ----------------------------------------------------------------------
    # marks
    # ----------------------------------------------------------------------
    Feature('marks', 'clean', 'Clean',
            'nothing on your skin worth writing down, which at this point in '
            'your career is either luck or a very short career',
            memorable=-2, presence=0),
    Feature('marks', 'ports', 'Port Scarring',
            'the ring of raised tissue around a cervical port that never '
            'quite settled, and you stopped wearing collars that hide it',
            memorable=1, presence=0),
    Feature('marks', 'ink', 'Ink',
            'work up both forearms, done over years by four different people, '
            'two of whom are dead',
            memorable=2, presence=1),
    Feature('marks', 'gang', 'Gang Ink',
            'a Sixes crew mark on the inside of your wrist, from a year you '
            'do not talk about and a crew that mostly is not around to '
            'confirm it',
            memorable=3, presence=1),
    Feature('marks', 'corporate', 'Corporate Tattoo',
            'an employee number under your collarbone in a typeface Kagawa '
            'still uses, which is a problem in about three districts',
            memorable=2, presence=1),
    Feature('marks', 'burns', 'Burns',
            'feedback burns up the inside of both arms, tracking the nerve '
            'the way lightning tracks a tree',
            memorable=3, presence=0),
    Feature('marks', 'surgical', 'Surgical Scars',
            'the ladder of scars down your sternum from work done cheaply and '
            'more than once',
            memorable=2, presence=0),
    Feature('marks', 'brand', 'Brand',
            'a debt brand on the back of your hand. It is not legal and it is '
            'not enforceable and it is still there',
            memorable=4, presence=0),
    Feature('marks', 'subdermal', 'Subdermal Work',
            'ridged patterning under the skin of your forearms, which cost '
            'more than a deck and does nothing at all',
            memorable=3, presence=2),
    Feature('marks', 'faded', 'Faded Work',
            'the ghost of something removed, in the specific mottled grey of '
            'a laser that was not quite good enough',
            memorable=1, presence=0),
    Feature('marks', 'religious', 'Devotional',
            'a small mark behind your ear that four thousand people in this '
            'city would recognise and nobody else would notice',
            memorable=1, presence=1),
    Feature('marks', 'tally', 'Tally',
            'a line inked on your ribs for every runner you have known who '
            'did not come back, and you ran out of ribs',
            memorable=2, presence=1),
    Feature('marks', 'clinic', 'Clinic Marks',
            'the puncture grid of somebody who has been through a Shambles '
            'clinic often enough to have a preferred chair',
            memorable=2, presence=-1),
    Feature('marks', 'none_visible', 'Nothing Visible',
            'whatever you carry under your clothes and have never given '
            'anybody a reason to ask about',
            memorable=-2, presence=0),
)


# Marks the world gives you. Not choosable at creation: `EARNED` entries are
# awarded by the engine when the thing that causes them happens.
EARNED: tuple[Feature, ...] = (
    Feature('marks', 'flatline_scar', 'Flatline Scar',
            'the burn where the trode net cooked into your scalp the time '
            'your heart stopped, which the clinic wrote up as a good outcome',
            memorable=4, presence=1),
    Feature('marks', 'black_ice', 'Black ICE Burn',
            'the fern pattern black ICE leaves when it goes through a nervous '
            'system and does not finish the job',
            memorable=4, presence=2),
    Feature('marks', 'bounty_mark', 'A Bad Night',
            'the mark from the night somebody collected on you and only got '
            'part of the way through it',
            memorable=3, presence=1),
    Feature('marks', 'drift_pallor', 'Drift',
            'the colour of somebody whose body has stopped believing the '
            'reports it is getting from itself',
            memorable=3, presence=-1),
)

EARNED_BY_KEY: dict[str, Feature] = {f.key: f for f in EARNED}


FEATURES = FEATURES + (
    # ----------------------------------------------------------------------
    # dress
    # ----------------------------------------------------------------------
    Feature('dress', 'grey', 'Grey',
            'in whatever was on the top of the pile, in the colours that a '
            'camera gives up on',
            memorable=-2, presence=-1),
    Feature('dress', 'workwear', 'Workwear',
            'like somebody with a shift to get to, in Freeport canvas that '
            'has been repaired more often than washed',
            memorable=-1, presence=0),
    Feature('dress', 'corporate', 'Corporate',
            'one tier above your actual station, in a cut that Kagawa middle '
            'management wore two seasons ago, which is exactly right for '
            'somebody who is not being paid enough to keep up',
            memorable=0, presence=3,
            effects={'pretext_bonus': 1}),
    Feature('dress', 'armoured', 'Armoured',
            'in a weave-lined coat that stops nothing but is very obvious '
            'about being willing to try',
            memorable=2, presence=2),
    Feature('dress', 'street', 'Street',
            'in whatever the Ninth is wearing this year, which is whatever '
            'the Ninth was wearing last year with the logos taken off',
            memorable=0, presence=1),
    Feature('dress', 'clinical', 'Clinical',
            'in clinic whites you have no right to, and nobody has stopped '
            'you yet',
            memorable=1, presence=2,
            effects={'pretext_bonus': 1}),
    Feature('dress', 'expensive', 'Expensive',
            'in one genuinely expensive thing and nothing else that matches '
            'it, which fools about half the people it needs to',
            memorable=3, presence=2),
    Feature('dress', 'layered', 'Layered',
            'in four thin layers you can lose one at a time, which is a habit '
            'from a specific night you do not describe',
            memorable=-1, presence=0),
    Feature('dress', 'devotional', 'Devotional',
            'in the plain dark of one of the city\'s smaller faiths, which '
            'gets you left alone by roughly everybody for entirely different '
            'reasons',
            memorable=2, presence=1),
    Feature('dress', 'salvage', 'Salvage',
            'in pieces of at least three uniforms, none of which you were '
            'ever issued',
            memorable=2, presence=0),
    Feature('dress', 'immaculate', 'Immaculate',
            'in clothes that are always clean, in a city where that is a '
            'more expensive claim than the clothes',
            memorable=2, presence=3),
    Feature('dress', 'nothing', 'Whatever',
            'like getting dressed is a solved problem you solved badly once '
            'and have not revisited',
            memorable=0, presence=-2),
    Feature('dress', 'nightwatch', 'Surplus',
            'in Nightwatch surplus with the flashes unpicked, which is either '
            'very cheap or very stupid depending on the district',
            memorable=2, presence=1),
    Feature('dress', 'bright', 'Bright',
            'in something no camera is going to lose, on the theory that '
            'people who are hiding do not do this',
            memorable=4, presence=2),

    # ----------------------------------------------------------------------
    # bearing
    # ----------------------------------------------------------------------
    Feature('bearing', 'still', 'Still',
            'very still, and people find themselves filling the silence you '
            'left, which is usually all you needed',
            memorable=1, presence=2),
    Feature('bearing', 'restless', 'Restless',
            'like there is somewhere else you should be, because there '
            'usually is',
            memorable=0, presence=-1),
    Feature('bearing', 'grey_man', 'Unnoticed',
            'like furniture, deliberately, and have practised it',
            memorable=-3, presence=-2),
    Feature('bearing', 'open', 'Open',
            'loose and unguarded, which reads as either confidence or a very '
            'good imitation of it',
            memorable=0, presence=2),
    Feature('bearing', 'coiled', 'Coiled',
            'like you are about to be asked to leave and have already decided '
            'how that goes',
            memorable=2, presence=2),
    Feature('bearing', 'formal', 'Formal',
            'correctly, in a way that belongs to a building you no longer '
            'have access to',
            memorable=1, presence=2),
    Feature('bearing', 'apologetic', 'Apologetic',
            'slightly folded, taking up less room than you are entitled to, '
            'which has been underestimated by better people than you',
            memorable=-2, presence=-2),
    Feature('bearing', 'watchful', 'Watchful',
            'with your back to something solid and your eyes on the door, '
            'every time, without deciding to',
            memorable=1, presence=1),
    Feature('bearing', 'exhausted', 'Exhausted',
            'like the day has been going on for eleven years',
            memorable=0, presence=-1),
    Feature('bearing', 'imperious', 'Imperious',
            'as though the room is running late for you',
            memorable=3, presence=3),
    Feature('bearing', 'twitchy', 'Twitchy',
            'badly. Something in the wiring fires when it should not and you '
            'have stopped explaining it',
            memorable=2, presence=-2),
    Feature('bearing', 'amiable', 'Amiable',
            'like somebody who is pleased to be here, which is a lie you tell '
            'with your whole body and tell well',
            memorable=0, presence=2),

    # ----------------------------------------------------------------------
    # voice
    # ----------------------------------------------------------------------
    Feature('voice', 'quiet', 'Quiet',
            'quietly enough that people lean in, which you noticed worked and '
            'never stopped doing',
            memorable=1, presence=2),
    Feature('voice', 'flat', 'Flat',
            'without inflection, which unsettles people who have not met many '
            'runners and reassures the ones who have',
            memorable=1, presence=1),
    Feature('voice', 'fast', 'Fast',
            'faster than people can follow, and repeat yourself constantly '
            'and resent it every time',
            memorable=1, presence=-1),
    Feature('voice', 'rough', 'Rough',
            'through damage. Something went through your throat and the '
            'repair was structural rather than cosmetic',
            memorable=3, presence=1),
    Feature('voice', 'accented', 'Accented',
            'with the vowels of somewhere three thousand kilometres from here '
            'that no longer exists in the form you remember',
            memorable=3, presence=1),
    Feature('voice', 'ninth', 'Ninth Ward',
            'like the Ninth, which opens exactly as many doors as it closes '
            'and never the same ones',
            memorable=1, presence=0),
    Feature('voice', 'corporate', 'Corporate',
            'in the flattened everywhere-accent of corporate training, which '
            'you got honestly and have never been able to put down',
            memorable=0, presence=2),
    Feature('voice', 'synthetic', 'Synthetic',
            'through a larynx that is not the one you were issued, and it is '
            'good work but the consonants land a fraction early',
            memorable=3, presence=0),
    Feature('voice', 'warm', 'Warm',
            'like somebody worth telling things to, which has been the most '
            'profitable thing about you',
            memorable=1, presence=3),
    Feature('voice', 'clipped', 'Clipped',
            'in the fewest words that will do, and let the gap after them do '
            'the rest',
            memorable=1, presence=2),
    Feature('voice', 'rambling', 'Rambling',
            'at length, around the subject, and arrive eventually, and people '
            'have stopped waiting',
            memorable=1, presence=-2),
    Feature('voice', 'unremarkable', 'Unremarkable',
            'in a voice nobody has ever described, which took work and which '
            'nobody has ever complimented',
            memorable=-2, presence=0),
)


BY_SLOT: dict[str, tuple[Feature, ...]] = {
    s.key: tuple(f for f in FEATURES if f.slot == s.key) for s in SLOTS
}
#: Slot-qualified lookup. Keys repeat across slots on purpose: 'severe' is a
#: face and a hairstyle and they are different features.
BY_KEY: dict[tuple[str, str], Feature] = {(f.slot, f.key): f for f in FEATURES}
ALL_BY_KEY: dict[tuple[str, str], Feature] = {
    **BY_KEY, **{(f.slot, f.key): f for f in EARNED}}


# --------------------------------------------------------------------------
# derived numbers
# --------------------------------------------------------------------------

#: Dissonance at which the chrome floor starts biting, and how fast it climbs.
#: Past this you cannot be forgettable however you dress, because the thing
#: people notice is not something you are wearing.
FLOOR_FROM = 25
FLOOR_STEP = 18

#: Memorable is reported on this scale rather than raw, so the player has a
#: word rather than a number to reason about.
BANDS: tuple[tuple[int, str, str], ...] = (
    (-99, 'forgettable',
     'Nobody can describe you afterwards. Fixers do not remember your last '
     'job either.'),
    (0, 'ordinary',
     'You look like the city. Descriptions of you fit about nine thousand '
     'people.'),
    (6, 'noticeable',
     'Somebody who saw you once could pick you out of three. That cuts both '
     'ways and it is starting to.'),
    (12, 'distinctive',
     'You are a description that fits one person. Your work is remembered '
     'and so is your face.'),
    (20, 'unmistakable',
     'There is nobody else in this city who looks like you, and everybody '
     'who wants you knows exactly what to circulate.'),
)


def floor_from_chrome(dissonance: int) -> int:
    """The memorable score you cannot get below, given what is in you."""
    if dissonance < FLOOR_FROM:
        return 0
    return 1 + (dissonance - FLOOR_FROM) // FLOOR_STEP


def score(look: dict[str, str], marks: list[str] | None = None,
          dissonance: int = 0) -> tuple[int, int]:
    """(memorable, presence) for an assembled appearance.

    `look` maps slot to feature key. `marks` are earned marks on top of the
    chosen one, which is why marks are the only slot that can stack.
    """
    memorable = presence = 0
    for slot, key in (look or {}).items():
        feature = ALL_BY_KEY.get((slot, key))
        if feature is None:
            continue
        memorable += feature.memorable
        presence += feature.presence
    for key in marks or ():
        feature = EARNED_BY_KEY.get(key)
        if feature is not None:
            memorable += feature.memorable
            presence += feature.presence
    # The floor only binds when there is chrome to enforce it. Applying it
    # unconditionally would clamp a deliberately forgettable build up to zero
    # and delete the entire bottom half of the scale, which is the half that
    # people who do not want to be found are buying.
    floor = floor_from_chrome(dissonance)
    return (max(memorable, floor) if floor else memorable), presence


def band(memorable: int) -> tuple[str, str]:
    """(name, explanation) for a memorable score."""
    name, why = BANDS[0][1], BANDS[0][2]
    for threshold, label, text in BANDS:
        if memorable >= threshold:
            name, why = label, text
    return name, why


#: How memorable converts into the two things it touches. Both are deliberately
#: gentle: appearance should be a thumb on the scale, not a build decision that
#: dominates skills and chrome.
HEAT_PER_POINT = 0.02
REP_PER_POINT = 0.015


def heat_mult(memorable: int) -> float:
    """Residue converts to faction heat faster when they know who to look for."""
    return max(0.6, 1.0 + memorable * HEAT_PER_POINT)


def rep_mult(memorable: int) -> float:
    """Work is remembered as yours when you are worth remembering."""
    return max(0.7, 1.0 + memorable * REP_PER_POINT)


def effects(look: dict[str, str], marks: list[str] | None = None) -> dict:
    """The (rare) mechanical effects the chosen features carry."""
    from . import effects as fx
    parts = []
    for slot, key in (look or {}).items():
        feature = ALL_BY_KEY.get((slot, key))
        if feature is not None and feature.effects:
            parts.append(feature.effects)
    return fx.merge(*parts)


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------


def default() -> dict[str, str]:
    """The blank everybody starts from before they touch anything."""
    return {'build': 'unremarkable', 'face': 'plain', 'eyes': 'tired',
            'hair': 'cropped', 'marks': 'ports', 'dress': 'grey',
            'bearing': 'watchful', 'voice': 'flat'}


def roll(rng) -> dict[str, str]:
    """A complete appearance, for a player who does not want to pick eight."""
    return {s.key: rng.pick([f.key for f in BY_SLOT[s.key]]) for s in SLOTS}


def describe(look: dict[str, str], marks: list[str] | None = None) -> list[str]:
    """The assembled description, one sentence per slot.

    Returned as a list rather than a paragraph so the console can wrap each
    one and so `look` can put the earned marks last, where they read as
    accumulation rather than choice.
    """
    out: list[str] = []
    for slot in SLOTS:
        key = (look or {}).get(slot.key)
        feature = ALL_BY_KEY.get((slot.key, key))
        if feature is None:
            continue
        out.append(f'{slot.stem} {feature.look}.')
    for key in marks or ():
        feature = EARNED_BY_KEY.get(key)
        if feature is not None:
            out.append(f'You also carry {feature.look}.')
    return out


def summary(look: dict[str, str]) -> str:
    """The one-line version, for a character sheet header."""
    bits = [ALL_BY_KEY[(s.key, look[s.key])].name.lower()
            for s in SLOTS if look.get(s.key)
            and (s.key, look[s.key]) in ALL_BY_KEY]
    return ', '.join(bits)
