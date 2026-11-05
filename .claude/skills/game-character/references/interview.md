# Interview: the questions to ask

How to fill a character bible and a type's lists by asking the user. The goal is a bible complete enough to generate consistent images, sounds and lines from it, and to rebuild the character's look and voice later.

## How to ask

- **A few questions at a time** (one question block, 2-4 questions), one bible section per round. Never a wall of twenty questions.
- **Always offer concrete options**, drawn from what is already decided: the game idea, the type's other characters, `docs/style/`. "Rotting farmer in torn work clothes / plague victim in a shroud / armoured knight risen from a grave?" beats "What does it look like?".
- **Skip what is known**: read the bible and the design docs first, and only ask for what is empty or vague.
- **Accept "you decide" and "later"**: write a proposal marked `(proposed)`, or leave the placeholder and mark it **(open)**. Say what you did.
- **Ask for the distinguishing thing**: what makes this character readable at a glance (silhouette, colour, one prop). Small phone screens and small portraits need one strong feature.
- **Check against the type's other characters**: point out clashes ("the Orc Warrior is also green: make the zombie grey-green?").
- Write each answer into the bible right away, in plain prose for people; put generation phrasing only in the prompt keywords line.

## Types (set up, or a new type)

Ask once per type, when the type is created:

- "Which characters belong to this type, roughly?" (to name the type: `heroes`, `mobs`, `bosses`, `player`, `npcs`)
- "The bible has Appearance, Voice and Background by default. Does this type need all three, or something more?" (a silent mob may drop Voice and keep its sounds under Appearance; a boss may add Story role or Behaviour)
- "What 2D graphics does one of them need in the game?" Offer: face portrait (info card, dialogue), half portrait (head and torso: selection screen, dialogue, story scenes), full-body art, in-game 2D sprite or cut-out (HUD figure), state variants (blink, hurt, casting), icon.
- "Is it a 3D model in the game? Its own or from a pack? Which animations?" (idle, walk, attack, hurt, death, victory)
- "Does it speak?" → voice reference + which lines (greeting, battle cry, hurt, death line, victory, barks). "Or only sounds?" → creature sounds (death, hurt, attack grunt, idle growl).
- "Any sounds besides its voice?" (footsteps, wing flaps, armour clanks)
- "How many variants of each sound?" (sounds heard often need 2-4 for a randomizer)
- For each resource: "Where does it show in the game, and how big?" (fills the spec: on-screen size, aspect, transparent or not).

## Bible sections

The default bible has three sections. Keep each short: a few sentences or bullets a person reads in a minute. Ask in this order; Appearance first, because the first images are made from it.

### Appearance
How the character looks. Ask, with options:
- "Age and sex? Human, orc, undead, animal...?"
- "Build: tall, short, thin, bulky, hunched?"
- "Hair colour and style (or helmet, hood, horns)? Face: scars, eyes, expression?"
- "What does it wear, and in what state (new, worn, torn)? Two or three main colours?"
- "What does it carry (weapon, staff, lantern)?"
- "What should a player recognise it by at a glance?" (one strong feature for small phone screens)
- "Any image that shows what you mean?" → saved in the bible folder as `<name>_ref_<desc>.png`, with where it came from.
Then write the **prompt keywords** line: the look as one comma-separated phrase, reused word for word in every image prompt so all images show the same character. Show it to the user.

### Voice
How the character talks. Ask, with options:
- "High or low pitch? Young or old sounding?"
- "Energetic or calm? Happy, grim, nervous, proud?"
- "An accent or way of speaking: formal, crude, old-fashioned, few words?"
- "Favourite words or a catchphrase?"
- "What does it say when greeting or being chosen?" Offer 2-3 lines in its personality.
- "Where should the voice reference come from: a Chatterbox take we generate, your own recording, a licensed clip?" (the rights are written next to it)
- A mob that does not speak: "What sounds does it make: groans, snarls, clicks, silence?" (write it here, or under Appearance if the type has no Voice section)

### Background
Who the character is. Ask, with options:
- "Three words for its personality?" (moody, cheerful, proud, cruel...)
- "Where does it come from?" ("a knight from a royal family", "a farmer raised from the dead")
- "What does it want, and why is it in this game?"
- Only if the user wants more: its history, a secret, who it knows among the other characters.

### Extra sections
A type can add sections (Story role, Behaviour, Relationships). Ask for them the same way: a few questions with options, a short answer.

## Updating

- Vague change ("make him scarier"): ask what exactly changes, with options ("darker colours / bigger and bulkier / a skull mask / sharper teeth?").
- After the change, list the resources it makes outdated and ask which to regenerate.
