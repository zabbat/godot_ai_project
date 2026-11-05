# Designing a voice with Kokoro

Read this before making a voice reference clip.

## What Kokoro can and cannot do

Kokoro-82M is a small text-to-speech model (Apache-2.0) with 54 fixed built-in voices. It runs in
about a second per line (also on CPU).

- **Can:** pick a voice, **blend voices** (weighted average of their style vectors, which gives a new,
  stable voice), set the speed, and read text clearly and naturally.
- **Cannot:** act. No emotion settings, no voice cloning. Every line comes out as a calm narrator.
  CAPITALS do nothing. A `.` between sentences gives only a short, unnatural pause.

That is why Kokoro only makes the **calm reference clip**, and Chatterbox does the acting.

## Choosing voices for a blend

Blend 2-4 voices towards the character's description. A blend lands between its voices in pitch
and tone; quality drops towards the weakest voice, so **anchor every blend with a good voice**
(grade B- or better) at 40-60 %.

Grades are the model author's (quality and amount of training data; `VOICES.md` in
`hexgrad/Kokoro-82M`). Descriptions are measurements of one test line (median pitch, how much the
pitch moves, brightness, breathiness), not listening notes; let the user listen before deciding.

### US English (`a`)

| Voice | Grade | Pitch | Measured character |
|---|---|---|---|
| **af_heart** | **A** | 204 Hz | warm, bright, slightly breathy, natural pace; the best all-rounder |
| **af_bella** | **A-** | 207 Hz | very bright and clear, steady, confident |
| af_nicole | B- | 166 Hz | very breathy, almost a whisper, slow: secrets, ghosts, intimate |
| af_sarah | C+ | 195 Hz | bright, slightly breathy, clean narrator |
| af_aoede | C+ | 180 Hz | neutral, steady, fairly flat: calm and formal |
| af_kore | C+ | 144 Hz | low for a woman, lively: mature |
| af_nova | C | 156 Hz | darker, expressive |
| af_alloy | C | 146 Hz | dark, crisp, low |
| af_sky | C- | 163 Hz | dark, plain |
| af_jessica | D | 214 Hz | highest, crisp, quick: young |
| af_river | D | 179 Hz | neutral, fast, monotone |
| am_michael | C+ | 116 Hz | bright, slow, deliberate: hero, narrator |
| am_fenrir | C+ | 135 Hz | bright, firm, slow |
| am_puck | C+ | 108 Hz | low, playful, expressive |
| am_onyx | D | 87 Hz | deepest, very dark, flat: giants, bosses, gravitas |
| am_echo | D | 107 Hz | low, dark, clean |
| am_liam | D | 121 Hz | neutral, young adult |
| am_eric | D | 158 Hz | high for a man, fastest: young, nervous |
| am_santa | D- | 168 Hz | jolly, slow: novelty |
| am_adam | F+ | 117 Hz | worst rated: avoid |

### UK English (`b`) - grades only, not measured

bf_emma **B-**, bf_isabella C, bf_alice D, bf_lily D · bm_george C, bm_fable C, bm_lewis D+, bm_daniel D

Other languages (es, fr, it, pt, hi, ja, zh) exist but are weak and need extra packages
(espeak-ng; misaki[ja]/[zh]). English only unless the user insists.

### Recipes

- **Male voices are weak** (best C+). Blend `am_michael` / `am_fenrir` / `am_puck` and add `am_onyx`
  for depth (e.g. `am_michael:0.6,am_onyx:0.4`). Expect to rely on Chatterbox for character.
- **Mature woman, calm and formal:** `af_heart:0.5,af_aoede:0.3,af_kore:0.2` (warm + steady + lower;
  measured ~185 Hz). Used for a priestess; the spell lines made from it were the best of the test.
- Softer / mystical: add 20-30 % `af_nicole`. Darker / commanding: `af_kore` + `af_alloy`.
- Younger: lean on `af_bella` / `af_jessica`; older or deeper: `af_kore`, `af_alloy`, `am_onyx`.

## Auditions (optional)

If the user wants to hear candidates first, render one in-character line in the candidate voices
and blends with `kokoro_samples.py` (e.g. `"af_heart;af_aoede;af_kore;af_heart:0.5,af_aoede:0.3,af_kore:0.2"`)
and let them pick. Skip it when the user says "you decide".

## The reference clip

The clip is what Chatterbox clones for **every** line, so it fixes the voice for good.

- **6-8 s**, one speaker, clean, **no effects** (reverb or pitch shift on the clip is copied into
  every line).
- **Two sentences, ~16 words**, that the character would say **in their normal, calm tone**. Pick
  words Kokoro reads in the right tone by default: sincere, calm, in the character's way of talking
  (their favourite phrases are ideal). Never an emotional line: Kokoro cannot act it, and a calm clip
  is what lets Chatterbox add intensity once.
- **Render each sentence as its own part** with an explicit pause after it (`"text|speed|0.5"`);
  the last part gets pause 0.
- **Speed 0.82-0.85** for calm and formal; up to 0.95 for a brisk character.
- Make **two takes with different text** (same blend and speeds) so the user can pick. If one is
  outside 6-8 s, change the text or speed and render again; never pad with silence.
- Example (priestess, 7.0 s):
  `"Peace be with you, traveler.|0.85|0.5" "May the light shine on you, and may God bless your path.|0.82|0"`

## Why the reference must come straight from Kokoro

Every round of cloning loses quality. In the test, lines generated from the Kokoro clip (first
generation) were the best; lines cloned from a Chatterbox take (second generation) were worse; and
a Chatterbox take that was already intense, used as the reference for intense lines, sounded
mechanical and sped up (intensity applied twice). So: **one calm Kokoro clip per character, and
every line is generated from it.**
