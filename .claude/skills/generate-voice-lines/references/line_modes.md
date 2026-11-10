# Line modes: the kind of line decides the delivery

Every line is generated with Chatterbox's **English model** from the character's one calm Kokoro
reference clip (one exception: **laughs**, which use the Turbo model, see "Laughs"). The mode only changes the settings and how the text is written. The intensity is
added **once**, here, never in the reference.

## Modes

| Mode | Kinds of line | exaggeration | cfg_weight (pace) | Status |
|---|---|---|---|---|
| **speech** | greeting, farewell, dialogue, shop, idle chatter, blessing, lore told by the character | 0.5 (0.45 formal / prayer-like, 0.65 friendly / welcoming) | 0.4 (0.35 slower, more solemn) | tested: very good |
| **battle** | spell call, battle cry, command in combat, rallying shout | 1.1 | 0.3 | tested: good, 1-2 good takes in 5 |
| **laugh** | a laugh (happy, hearty, giggle) | - (**Turbo model**: it ignores exaggeration and cfg) | - | tested twice: deep laugh alone 1 good in 5; a giggle only worked inside a sentence, cut out |

`temperature` stays at the default; lower it to 0.6-0.7 only if takes keep sounding odd or synthetic.

**Do not use** Turbo style tags for the mode (`[dramatic]`, `[angry]`): they have no intensity dial,
and `[dramatic]` made a line sound silly. Turbo's sound tags (`[gasp]`, `[sigh]`) are fine when a
line needs a sound. **Do not go above exaggeration ~1.2**: the voice drifts away (to ~350 Hz,
shrill, unstable between takes).

### Kinds not tested yet

Hurt, death, fear, whisper, victory, sad, sarcastic... Start from the matching row of the Chatterbox
skill's `references/game_voice_styles.md` (English model columns), still from the calm reference,
make 5 takes, and write what worked in the Chatterbox folder's `AGENTS.md` (Findings). When a kind
works reliably, propose adding it as a mode here (ask the user: this file is shared between projects).

## Writing the text

The text steers the delivery as much as the settings.

**Speech**
- Write like the reference clip: similar words and rhythm, **balanced sentences joined by commas**.
  The best test lines echoed the clip ("Welcome, traveler, and peace be with you...").
- A line that opens with a short command and then changes tone moves around in pitch.
- `!` makes it warmer and more energetic ("Welcome to the city, stranger!"); a plain `.` keeps it calm.

**Battle**
- **Chains of short phrases** work ("Stand behind me! Light, shield us!"). A long flowing sentence
  ("...hear my prayer... and burn away the shadows!") sounded ridiculous, like ordering from a menu.
- **CAPITALS on one strong word** for the shouted peak ("Let there be LIGHT!"). Never on a short
  final word: "be GONE" came out as "be joe" / "be ju on".
- Write compound words as one word ("begone", not "be gone": "be" became its own stressed word).
- If one word sounds synthetic in every take ("gone"), change the wording rather than generating
  more ("Begone, shadows!", "Shadows, away!").

## Short lines: also generate them inside a longer phrase

Lines of about 5 words or fewer give the model little context, so it guesses the stress. For short
**battle** lines generate both, 5 takes each:

1. **short**: the line on its own;
2. **long + cut**: the line at the end of 2-3 in-character battle phrases, with `...` before it
   ("Stand behind me, all of you! By the holy light, I call upon you... let there be LIGHT!"), then
   `check_takes.py --keep "<the line>"` cuts it out.

In the first test the best take was a short one, and the cut ones were not judged yet. Record in the
Chatterbox `AGENTS.md` Findings which of the two the user picks; once a project shows a clear winner,
generate only that.

## Laughs

A laugh is a sound, not words, so the English model cannot act it: "Ha ha ha!" at exaggeration 0.9 /
cfg 0.3 gave only short, thin 0.5-1.1 s "ha-ha"s. The **Turbo** model has a `[laugh]` sound tag and
gives full laughs (1.5-1.8 s), still cloned from the same calm reference.

- **Text:** the laugh written out, then the tag: `"Ha ha ha! [laugh]"` (a tag alone may come back
  short or odd). This worked for a deep, hearty man's laugh.
- **Light or high laughs (a giggle, a young woman's laugh): put the laugh inside a sentence** that
  gives it a reason, ending with the tag, e.g. `"Don't be silly! [laugh]"`, then cut the words away
  with `cut_take.py --start <time in the pause after the last word>`. A giggle on its own (20 Turbo
  takes, with `[laugh]` and `[chuckle]`, with and without written "hehe") came out shrill or odd
  every time; the sentence version gave a usable giggle in 1 of 5. Find the end of the words with
  the loudness print (Whisper does not transcribe the laugh, so it hears only the words).
- **Do not write the laugh for the English model** ("..., hehehe!" or "..., haha!"): it reads the
  letters out instead of laughing. The kind of laugh (deep, hearty, a chuckle) cannot be set: Turbo has no intensity
  dial, so make 5 takes and let the user pick the one that fits. `[chuckle]` exists for a softer one
  (tried once for a giggle, on its own: not better than `[laugh]`).
- **Batch entry:** `"model": "turbo"`, no `exaggeration` / `cfg_weight` (ignored), `"takes": 5`.
- **Checking:** the Whisper word check is **not useful** for laughs: "hahaha" written as one word,
  or "heh heh heh", is flagged WORDS / FAIL but can be a good laugh. Report length and pitch only:
  pitch 0 Hz means an unvoiced, breathy laugh (normal); over ~1.7x the reference is a squeak (in the
  test one take reached 5.5x): list it as probably bad. A longer, lower take is more likely "deep and
  hearty" (the chosen take was the longest and the lowest, 0.84x).
- **Two laughs in one take:** a take can hold two laughs with a short silence between them. If the
  user wants only one, cut it with `cut_take.py`: run it on the take to print its loudness every
  20 ms, pick a time inside the silence, then `cut_take.py <take> --start 0 --end <time>` writes
  `<take>_cut.wav` with a short fade. **Cut only when the user asks.** Record the cut (take, start,
  end) in the master's `.md`.

## Takes and lengths

- **5 takes per line**, always. Expect 1-2 good ones for battle lines, 2-3 for speech.
- In-game lines can be any length (barks of 1.5-2.5 s are normal). Only the reference clip has the
  6-8 s rule.
- A take much shorter than its siblings may have dropped words; the word check will say.
