# Voice generation: what we tried and what worked

Notes from a test (2026-11-04/05) on making a character voice for a game with local, free tools.
It was run in the tower game repo (`games/tower/`). **It is now the `generate-voice-lines` skill**
(`.claude/skills/generate-voice-lines/`); this file is the history behind it. The test installs were
removed from tower; the test audio is backed up in `games/tower-voice-test-backup/`.

## The way of working (current best)

The rest of this file is the log of how we got here; this section is the recipe.

1. **Describe the character** (age, gender, role, how they talk, their main emotional mode).
2. **Design the voice in Kokoro.** Blend 2-4 built-in voices (`blend.py` / `shape.py`) towards the
   description, e.g. a warm A-grade voice + a steady one + a lower one for maturity.
3. **Render ONE calm reference clip of 6-8 s** in Kokoro: 2 sentences the character would say in
   their normal tone, each rendered separately with an explicit 0.5 s pause (`shape.py` parts),
   speed ~0.82-0.85. Words that Kokoro reads in the right tone by default (sincere, calm), since
   Kokoro cannot act. Put it in Chatterbox's `voices/`.
4. **Generate every in-game line in Chatterbox from that one Kokoro clip** (first generation;
   do not clone from Chatterbox's own takes). Use the **English model** and get the mode from the
   settings only:

   | Mode | exaggeration | cfg_weight | Text |
   |---|---|---|---|
   | Normal speech | 0.45-0.65 | 0.35-0.4 | wording and rhythm close to the reference clip; commas, balanced sentences |
   | Battle / spells | 1.1 | 0.3 | short spell phrases; CAPITALS on one strong word ("LIGHT") only; no capitals on short final words; "begone" as one word |

5. **Make 5 takes of every line.** Expect 1-2 good ones; throw the rest away.
6. **Run the word check** (`cut_spell.py`): it drops takes with wrong words ("let there be white")
   before anyone listens. For lines generated inside a longer phrase, the same script cuts the
   wanted part out.
7. **Listen and pick.** The final judgement is always by ear; the numbers only shortlist.

## Lessons learned

- **Kokoro designs the voice, Chatterbox acts it.** Kokoro has no emotional control; Chatterbox
  cannot make a voice from a description.
- **One calm reference, intensity added once, in the settings.** A reference that is already intense
  (a battle take) plus high exaggeration stacks the intensity: sped up, pitch off, mechanical.
- **Every generation of cloning loses quality.** Kokoro clip -> line (1st generation) gave the best
  spell takes; cloning from a Chatterbox take (2nd generation) and then pushing it (3rd) gave the
  worst. Keep calm speech takes as references at most, never pushed ones.
- **5 takes per line**, not 3. Short intense lines hit about 1 good take in 5; calm lines about 2 in 3.
- **Reference clips 6-8 s.** Shorter fails (Turbo needs > 5 s); generate lines long enough for it.
- **Text steers delivery as much as settings.** Speech lines that echo the reference clip's wording
  came out best. Long flowing battle sentences sound silly; chains of short phrases work.
- **Capitals:** good on one strong word ("LIGHT"), bad on a short final word ("GONE" became "joe").
  Kokoro ignores capitals entirely.
- **Exaggeration above ~1.2 drifts away from the voice** (up to ~350 Hz, shrill, unstable).
- **Turbo tags have no intensity dial**; `[dramatic]` made a line sound silly. Use the English model.
- **Some words sound synthetic in any take** ("gone" in "begone"). If one word keeps failing, change
  the wording rather than generating forever.
- **Let a script do the checking, not the ears:** Whisper word timestamps cost a few hundred tokens
  per batch (audio never enters the conversation) and catch wrong words automatically.

## Why two steps

| Tool | Good at | Bad at |
|---|---|---|
| Kokoro-82M | Clean, consistent voices; fast (~1 s per line on the RTX 5070); 54 built-in voices that can be blended into new ones | **No emotional control at all.** Only voice, speed and the text. Capitals do nothing; a single `.` gives a poor pause. Not usable for acted lines. |
| Chatterbox | Acting: emotion via `exaggeration` / `cfg_weight` (English model) or tags (Turbo); clones a voice from a 6-15 s clip | Cannot make a voice from a description; needs a reference clip |

So Kokoro designs the **voice**, Chatterbox does the **acting**.

## Step 1: Kokoro, design the voice

- Installed only as a test in `games/tower/tools/kokoro-temp/` (uv, Python 3.11, torch 2.8 cu128,
  `en-core-web-sm` as a direct dependency because uv venvs have no pip). Git-ignored via
  `games/tower/.git/info/exclude`, not `.gitignore`.
- Scripts there: `try_kokoro.py` (one line), `sample_voices.py` (one line in every voice / several
  speeds), `blend.py` (weighted blends, `--save` a blend as `.pt`), `shape.py` (render a line in
  parts, each `"text|speed|pause_seconds"`, optional reverb), `analyze_voices.py` (pitch, pitch range,
  pace, brightness).
- Voices: official grades are in `VOICES.md` of `hexgrad/Kokoro-82M`. Best: `af_heart` (A),
  `af_bella` (A-). Male voices are weak (best C+: `am_michael`, `am_fenrir`, `am_puck`;
  `am_adam` is F+). Our measured descriptions of all US voices are in the conversation, not here.
- **Pauses:** render each sentence separately and add explicit silence (`shape.py` parts) rather than
  relying on `.` between sentences.
- **Length:** the clip must be 6-8 s, since it is Chatterbox's reference. Two sentences with one
  0.5 s pause at speed ~0.82-0.85 gave exactly 7.0 s.
- **Lines for the clip:** pick text whose natural reading already matches the character (calm,
  formal, sincere). Kokoro reads everything like a calm narrator, so it cannot be pushed into an
  emotion; choose words it will read in the right tone by default.
- Stress markup works in the text (`[word](-2)` removes stress, `[word](/phonemes/)` sets it), but the
  effect is small.

## Step 2: Chatterbox, act the lines

- The Kokoro clip goes in `games/tower/tools/chatterbox/voices/` and is used with `--voice NAME`.
- **Use the English model for both modes**, only changing the settings:

| Mode | model | exaggeration | cfg_weight (pace) | Result |
|---|---|---|---|---|
| Normal speech | english | 0.6 | 0.4 | calm, warm; pitch stays close to the reference (~200 Hz) |
| Battle / spell casting | english | 1.1 | 0.3 | intense, raised pitch (~250-280 Hz), still the same person |

- Lines must be long enough for a **6-8 s take** (about 17-19 words; Chatterbox speaks ~2.5-3 words/s).
  Make 3 takes per line; about 1 in 4 fell outside 6-8 s and was discarded.
- **Write speech lines like the reference clip.** The best speech takes (all three of `speech_2`) used
  wording and rhythm close to the Kokoro clip's text: "Welcome, traveler, and peace be with you. You
  are safe here, and no harm will come to you tonight." Two balanced sentences joined by commas. A
  line that opened with a short command and then changed tone (`speech_1`) moved much more in pitch.
- **Battle lines: chains of short spell phrases** worked ("Stand behind me, all of you! Light, shield
  us! By the holy light, I banish you! Be gone, darkness!"). A long, flowing battle sentence
  ("…hear my prayer… and burn away the shadows!") sounded ridiculous, like ordering from a menu.
  Stress sometimes lands on the wrong word; next time try CAPITALS on the word to stress, or split
  the phrases into separate lines.

### What did not work

- **Turbo with tags** (`[dramatic]`, `[angry]`) keeps the voice's pitch but has no intensity dial;
  `[dramatic]` on a long line sounded silly. Keep Turbo for sound tags (`[gasp]`, `[sigh]`) at most.
- **English model at exaggeration ≥ 1.25** drifted far from the voice (up to ~350 Hz, likely shrill).
  `exaggeration 1.5, cfg 1.0` was unstable between takes.
- **Takes under 5-6 s as references:** too short (Turbo needs > 5 s; the guide says 6-15 s).
- **Separate Kokoro clips for calm and battle:** unnecessary; one calm clip plus settings is enough
  and keeps the character one person.
- **Kokoro alone for acted lines,** even with per-part speeds, pauses, stress markup and reverb.

## The test character: the defender

A priestess in her 20s, fair, casts light magic, good-natured. Voice: mid range for a woman, calm,
slightly formal ("God bless you", "May the light shine on you"). Her main emotional mode is in
battle, intense while casting spells.

- **Kokoro blend:** `af_heart:0.5, af_aoede:0.3, af_kore:0.2` (warm + steady/formal + lower/mature,
  so not girly). Measured ~185 Hz.
- **Kokoro clip:** `kokoro_defender.wav`, 7.0 s:
  `"Peace be with you, traveler.|0.85|0.5" "May the light shine on you, and may God bless your path.|0.82|0"`
- **Chatterbox takes** (in `games/tower/tools/chatterbox/output/temp/defender/`, git-ignored, may be
  deleted):

| Take | Verdict |
|---|---|
| speech_2-1, -2, -3 | all very good: the calm speech voice |
| speech_1-1, -2 | not reviewed in detail; more pitch movement |
| battle_1-2, battle_2-2, battle_2-3 | good; stress sometimes on the wrong word |
| battle_1-1 | bad |

Each take has a `.json` next to it with text, settings and seed, so it can be regenerated.

## Step 3: in-game lines (first try)

Reference clips chosen: `voices/defender-speech.wav` (= speech_2-1) and `voices/defender-battle.wav`
(= battle_2-3), registered in `games/tower/tools/chatterbox/AGENTS.md`. 3 takes per line, in
`games/tower/tools/chatterbox/output/defender/`.

| Line | Reference + settings | Result |
|---|---|---|
| "Welcome to the city, stranger!" | speech, english, ex 0.65, cfg 0.4 | takes 1-2 **amazing** |
| "May the light shine on you." | speech, english, ex 0.45, cfg 0.35 | take 2 **fantastic**; 1 and 3 had weird emphasis |
| "Let there be LIGHT!" | battle, english, ex 1.05, cfg 0.3 | all bad: pitch-corrected, mechanical, sped up, synthetic. The "LIGHT" itself was good in take 1 |
| "Shadows, be GONE!" | battle, english, ex 1.0, cfg 0.3 | all bad: "shadows. bee. gone." with awkward pauses, "be joe", "be ju on", high-pitched |

### What was right

- **Gentle at every stage works:** calm Kokoro clip, then calm Chatterbox take as reference, then
  moderate settings (ex 0.45-0.65). Nothing pushed, so little quality is lost per generation.
- With short lines, 1 good take in 3 is normal variance. Make more takes, don't change settings.

### What was wrong

1. **Intensity applied twice.** The battle reference is already a high-exaggeration take (~280 Hz).
   Adding ex ~1.0 on top pushed the voice further: sped up, pitch off, mechanical. Each generation
   also compounds artifacts (Kokoro -> battle ref -> spell = third generation, all of them pushed).
   **Rule: one calm reference; add intensity once, in the settings.** A reference that is already
   intense needs low exaggeration (~0.5-0.7) or should not be used.
2. **Very short lines (3-4 words) at high exaggeration** give the model no context, so it guesses
   the stress. The good battle takes were 6-8 s chains of phrases.
3. **CAPITALS on a short final word ("GONE") broke pronunciation.** Capitals on "LIGHT" worked.
   "be gone" as two words made "be" its own stressed word ("bee."). Write **"begone"**, one word,
   no capitals.

### How to do battle lines instead

- Speech reference (or the Kokoro clip) + english ex ~1.0-1.1, cfg 0.3: intensity from settings only.
- 5 takes for short barks instead of 3; temperature 0.6-0.7 if takes sound odd or synthetic.
- Or write the spell inside a longer phrase ("By the holy light... let there be LIGHT!") and cut the
  end off afterwards (see below).

Second try (`_v2` takes, speech reference, ex 1.1, cfg 0.3, 5 takes, "Shadows, begone!"): pitch came
down from ~250-285 Hz to mostly ~190-275 Hz, closer to her normal voice. Verdict by ear:

- "Let there be LIGHT!": takes 2 and 3 **great**; the rest had issues; take 5 had a comically
  high-pitched "LIGHT".
- "Shadows, begone!": only take 4 OK; the others were too calm or had odd emotional emphasis.
- So about **1-2 good takes in 5** for short, intense spell lines. **Rule: make at least 5 takes of
  every line** and expect to throw most away.

### Cutting a spell out of a longer line

**Built** as `games/tower/tools/kokoro-temp/cut_spell.py` (faster-whisper `small.en` on CPU, added to
the temp env). Usage: `uv run --project tools/kokoro-temp tools/kokoro-temp/cut_spell.py FOLDER "let
there be light"`. Writes `<take>_cut.wav` + `.json`; prints ok / WARN / FAIL with what Whisper heard.
Whisper writes "begone" as "be gone" sometimes; the script merges them. The word check also works on
short takes: it caught "let there be **white**".

Third try (`output/defender_v3/`, all from the **Kokoro clip directly**, english ex 1.1, cfg 0.3,
5 takes each, short and long+cut). Verdict by ear:

- `light_short`: take 4 **perfect**, the others odd. The best spell take so far. The main difference
  from the second try is the reference: the Kokoro clip (1st generation) instead of the speech take
  (2nd generation). Could also be seed luck; 1 in 5 again.
- "Shadows, begone!": none perfect, take 1 the best. The remaining issue is a synthetic-sounding
  "gone" (try other wording, e.g. "Shadows, away!" or "Begone, shadows!").
- The `_cut` takes from the long lines have not been compared yet, so whether cutting helps is still
  open.

Original plan:

Short lines lack context, so generate the spell inside a longer phrase and keep only the end.
Chosen method: **word timestamps with Whisper** (e.g. `faster-whisper`, small model, ~500 MB,
installed in the temp environment).

1. Generate the long line, e.g. "By the holy light... let there be LIGHT!" (several takes).
2. Run Whisper with word timestamps on each take.
3. **Check the words** against the intended text; drop takes with wrong words (this would have caught
   "be joe" / "be ju on" automatically, before anyone listens).
4. Cut just before the first word of the spell ("Let"), keep a few ms of padding and add a short
   fade-in so there is no click; keep the trailing silence trim as usual.
5. Save the cut take next to the original with its own `.json` (source take, cut time, words found).

Why not silence detection (cut at the last pause): simpler and needs no install, but Chatterbox does
not always pause where `...` is written, so cuts can land in the wrong place, and it cannot check the
words. Token cost of either method is small: the script runs locally and prints one line per take;
the audio is never loaded into the conversation. The result is still judged by ear.

## Next steps (not done)

1. Compare the `_cut` takes in `output/defender_v3/` with the short ones to decide whether cutting
   from longer lines is worth it.
2. Generate the defender's lines from `voices/kokoro_defender.wav` with the recipe at the top.
   `voices/defender-battle.wav` (stacked intensity) should not be used; `voices/defender-speech.wav`
   is only needed if the Kokoro clip ever falls short for speech.
3. If this becomes the workflow: add Kokoro properly (a `kokoro` tool folder or a step in the
   `chatterbox-text-to-speech` skill: "design a voice with Kokoro"), with the blend recipe and
   reference-clip rules above, and record each character's blend in the game's docs.
4. Clean up when done: `games/tower/tools/kokoro-temp/` (~3 GB), its line in
   `games/tower/.git/info/exclude`, and `~/.cache/huggingface/hub/models--hexgrad--Kokoro-82M`
   (~350 MB). `voices/aoede-guide-80.wav` in Chatterbox's voices folder is an older test clip.
