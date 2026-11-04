# Game voice styles: how to get the performance you want

Read this when the user asks for a character, an emotion or a type of line. Chatterbox
has no "emotion dropdown". Delivery comes from four things, strongest first:

1. **The reference voice** (`--voice`). Its accent, age, pitch and energy are inherited. A calm
   clip gives calm output no matter what else you set. Record or pick clips that already
   sound like the character (see "Reference clips").
2. **The model.** Turbo reacts to tags; English/Multilingual react to `exaggeration`/`cfg_weight`.
3. **The text itself.** Wording, punctuation and length steer delivery in every model.
4. **Seed and temperature.** The same settings give different takes. Generate 3-5 takes and pick.

## Turbo and Nano: tags

Tags are typed into the text. **Style tags** (set the whole delivery; put one at the start):
`[angry]` `[fear]` `[surprised]` `[whispering]` `[dramatic]` `[narration]` `[advertisement]`
`[happy]` `[crying]` `[sarcastic]`

**Sound tags** (a vocal event; put them where they happen in the line):
`[laugh]` `[chuckle]` `[sigh]` `[gasp]` `[groan]` `[cough]` `[clear throat]` `[sniff]` `[shush]`

```
[angry] You think you can stand against ME?
[fear] No... no, don't leave me down here. [gasp]
[happy] Oh, that's wonderful! [chuckle] Come in, come in.
[sigh] Another day, another shift on the wall.
[dramatic] And so the last king fell. [sigh] But the crown did not.
```

Practical rules (from Resemble's examples, not exhaustive; judge by ear and adjust):
- One style tag per line, at the start. Mixing two style tags is unpredictable.
- Put sound tags where the sound happens: between words or at the end ("Fine. [sigh]"). A line
  that is only a sound tag may come back short or odd; combine it with a word ("Ha! [laugh]").
- Tags are real tokens in Turbo's vocabulary (listed above); a tag spelled any other way, like
  `[sad]`, is just text and may be read aloud. Use the exact names.
- There is no `[sad]` or `[tired]` style tag: get those from `[crying]` at low intensity, a
  `[sigh]`, slow wording ("..."), and a weary reference voice.
- Turbo **ignores** `exaggeration` and `cfg_weight` (it logs a warning). Do not tune them for
  Turbo; tune the text, tag, voice and temperature instead.

## English and Multilingual: exaggeration and cfg_weight

| Want | exaggeration | cfg_weight | Notes |
|---|---|---|---|
| Neutral / narrator | 0.4-0.5 | 0.5 | defaults; good for most lines |
| Warm, friendly | 0.6-0.7 | 0.4 | |
| Angry, shouting | 0.9-1.3 | 0.2-0.3 | high exaggeration speeds speech up; low cfg slows it back down |
| Whisper, intimate | 0.3-0.4 | 0.5 | keep text short and lowercase |
| Sad, weary | 0.3-0.4 | 0.6 | slow pacing |
| Dramatic villain | 0.8-1.0 | 0.2-0.25 | |
| Fast reference speaker sounds rushed | any | ~0.3 | lowers pace |
| Accent leaks across languages | any | 0 | multilingual with a reference in another language |

Go above exaggeration 1.3 only for short barks; long lines get unstable and may glitch.
`temperature` 0.6-0.7 = steady, 0.9-1.0 = livelier but risks artifacts.

## Writing text that performs

The same sentence reads very differently depending on how it is typed.

| Technique | Example | Effect |
|---|---|---|
| Short sentences | "No. Not again." | punchy, tense, clipped |
| Ellipses | "I... I don't know." | hesitation, fear, grief |
| Dashes | "Wait-- what was that?" | interruption, alarm |
| `!` and `?` | "You dare?!" | raises energy and pitch |
| CAPITALS (one word) | "I said GET OUT." | stress on that word. Whole lines in caps get shouted, sometimes garbled |
| Repeated letters | "Nooooo!" | stretches the sound; use sparingly |
| Interjections | "Hah", "Ugh", "Hm", "Oh" | the model speaks them as sounds, good for barks |
| Commas for breath | "Well, now, what have we here" | slower, more deliberate |
| No end punctuation | "Hold the line" | flatter, trailing |

Length: **1 to 25 words per line is the sweet spot.** Over ~40 words the model drifts, rushes or
repeats. Split long speeches into sentences (one line each, same seed base and voice) and
join them in the engine or with ffmpeg. Very short lines (one word) can come back with
padding or oddities: use 2-3 words or keep several takes.

Spell out what must be read exactly: numbers ("two hundred"), acronyms ("S O S"),
and unusual names (respell phonetically: "Zy-ra" for Zyra). Keep a respelling list
for recurring names in `chatterbox/AGENTS.md` so every line pronounces them the same.

## Line types for a game

| Type | Style preset | Text length | Tips |
|---|---|---|---|
| Combat bark (attack, charge) | `battle-cry` | 1-4 words | `--takes 5`, trim on. "HAAA!" "For the king!" |
| Hit / pain reaction | `pain` | 1-3 words | "Ugh!" "Argh--" |
| Death | `dying` | 3-8 words | "I... can't... [sigh]" |
| Taunt / enemy callout | `angry` or `sarcastic` | 4-12 words | pair with a harsh voice clip |
| Boss monologue | `villain` or `dramatic` | 15-30 words, split | slow voice clip |
| NPC greeting | `happy` / `neutral` | 5-15 words | make 3-5 variants, randomise in-engine |
| Shopkeeper | `happy`, `sarcastic` | 5-15 words | |
| Idle chatter | `tired`, `neutral` | 5-15 words | many variants, keep volume low |
| Fear / panic | `fear`, `terrified` | 2-8 words | broken phrases, ellipses |
| Companion banter | `sarcastic`, `excited` | 5-20 words | |
| Narration, lore | `narration` | 20-40 words, split per sentence | |
| Tutorial / announcer | `announcer` | 5-20 words | clear, no tags inside |
| Whispered secret / stealth | `whisper` | 3-12 words | |
| Victory / defeat | `excited` / `sad` | 3-10 words | |

**Variety is the point in games.** For anything players hear often, generate 4-8 variants
(different wording *and* different seeds) and group them as one folder; the Godot side can
use an `AudioStreamRandomizer`. One take repeated 50 times is the most noticeable flaw.

## Characters from a few voices

You only need a handful of reference clips; vary the character with style:

- One calm voice + `villain` (slow, low exaggeration/cfg) = menacing; the same voice + `happy` = the friendly version.
- Pitch/age/size come from the reference, not from settings. For a monster or a child, use a clip that is already like that. Post-process (ffmpeg `asetrate`, `atempo`, `aecho`) for creatures, robots, radios, if needed.
- For a "chorus" of NPCs, mix 3-4 clips with different pitch and gender and rotate them by NPC id.

## Reference clips (`chatterbox/voices/`)

- 6-15 s, one speaker, **clean** (no music, no echo, no background talk), mono or stereo
  WAV/MP3/FLAC. Turbo needs more than 5 s.
- The clip should itself be in the target emotion range: an expressive read cloned with
  `neutral` still sounds lively; a monotone read stays flat.
- Match the clip language to `--language` on the multilingual model, or set `cfg_weight` 0.
- Only use voices you have the rights to (your own, a hired actor, a licensed set). Do not
  clone real people without permission. Every file Chatterbox writes carries Resemble's
  PerTh watermark; that is built in and fine for game use.
- `voices/` is git-ignored. If the team needs to share clips, put them in `assets/` and
  copy or link them here.

## Judging and fixing a take

| Problem | Fix |
|---|---|
| Flat, no emotion | add/strengthen the tag (Turbo) or raise `exaggeration` (English); use a more expressive clip; shorten the line |
| Too fast | lower `cfg_weight` to 0.25-0.3; add commas; (English) lower `exaggeration` |
| Mumbling / garbled | lower `temperature` to 0.6-0.7; shorten; respell hard words; try another seed |
| Repeats or runs on after the line | shorten; `repetition_penalty` 1.3; trim is on by default |
| Tag spoken aloud | not an exact tag name (see list above), or the model is English/Multilingual, which have no tags and read them as text |
| Clicks / metallic | another seed; cleaner reference clip |
| Accent wrong | reference clip decides it; for cross-language set `cfg_weight` 0 |
| Level differs between lines | keep `peak_db` at -1 for all; loudness-match in the engine |
