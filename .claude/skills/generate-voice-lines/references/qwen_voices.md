# Qwen3-TTS - designing the default reference and cloning lines

Read this before making a Qwen reference or lines. Facts here come from the first tests (a wizard
character, RTX 5070 Laptop 8 GB); where something is not tested it says so.

## What the two models do

| Model | Does | Does not |
|---|---|---|
| **VoiceDesign** (`Qwen3-TTS-12Hz-1.7B-VoiceDesign`) | Makes a voice from a text description (`instruct`) and speaks a text in it. | Keep the voice: **every call samples a new voice** from the description. Same description + same text = a similar person, not the same one. |
| **Base** (`Qwen3-TTS-12Hz-1.7B-Base`) | **Clones** a voice from a reference clip + its transcript, then speaks any text in it. The voice prompt is built once and reused for every line. | Take an emotion setting or tags. The delivery follows the reference clip and the wording. |

So a character is: **design once (VoiceDesign) -> pick one clip -> clone every line from it (Base)**.
The same reference gives the same character in all lines. Both models are ~4 GB and download into
the `qwen-hf-cache` volume on first use (a few minutes); each run loads a model (~40 s once cached),
so put lines in one batch.

Resources: the image is ~19 GB; a 1.7B model in bf16 ran on an 8 GB GPU. A machine without an NVIDIA
GPU, or with little disk or VRAM, should use the Kokoro route (SKILL.md "Lightweight route").

## The default reference

One per character: the character in their **normal, resting tone** (not their most intense one -
intensity is a separate reference, see SKILL.md "When the emotion does not come through").

1. **Write the description (`--instruct`)** from the game-character Voice section: age, gender, pitch
   and texture, accent, pace, mood, and a "like ..." comparison. Concrete beats poetic. Example that
   was chosen for a wizard: *"An elderly American man, a scholarly wizard, with a deep, gravelly,
   raspy voice weathered by age. Speaks slowly and deliberately in the manner of Deckard Cain, with a
   tired, irritated edge, like a professor annoyed at being interrupted."* A second description with
   a different mood (crisp, clipped, pedantic) gave a clearly different voice - offer the user 2-3
   descriptions when the character is new.
2. **Write the reference text**: two calm sentences in the character's way of talking, 6-10 s when
   spoken (Qwen needs ~3 s at least; 6-10 s is comfortable). The same text for every candidate.
3. **Generate 3 candidates**, open them, let the user choose:
   ```
   docker compose -f <qwen>/docker/compose.yaml run --rm qwen python .claude/skills/generate-voice-lines/assets/scripts/qwen_voice.py design --instruct "<description>" --takes 3 -o <qwen>/output/references/<name>/<name>_ref "<reference text>"
   ```
   Each candidate gets a `.json` with the description, text and seed.
4. **Check the words** of the chosen clip (SKILL.md section 5) - the transcript saved with the
   reference must match what is actually said, because cloning uses it.

## Cloning lines

```
docker compose -f <qwen>/docker/compose.yaml run --rm qwen python .claude/skills/generate-voice-lines/assets/scripts/qwen_voice.py clone --ref <qwen>/voices/<name>.wav --out <qwen>/output/<name> --batch lines.json
```

`lines.json`: `[{"name": "wizard_greet", "text": "Welcome, how may I be at service?", "takes": 3}]`.
An entry can name another reference with `"ref"` (a tone reference) and a `"seed"`. Takes are
`<out>/<name>/<name>-<nr>.wav` with a `.json` (text, reference, transcript, seed); numbers count up,
nothing is overwritten. Default 3 takes per line (each ~5 s to make); the takes of one line differ
in delivery and sometimes in pitch, so the user chooses by ear.

Writing the text: plain sentences, punctuation for rhythm (`,` short pause, `!` more energy,
`...` hesitation). A very short line ("What do you want?") comes out ~1 s; check it is not clipped.

## Emotion

The clone call has **no emotion setting and no tags**. The delivery is borrowed from the reference
clip, and the wording and punctuation add a little. Stage directions typed into the text
(`*hahaha*`, `(irritated)`) are not a documented control: do not rely on them, and if the user wants
to try them, record the result in the Qwen folder's Findings.

What does carry emotion: a **tone reference** - a reference clip that is already in that tone (an
irritated clip makes irritated lines). Making one is a Chatterbox job (SKILL.md "When the emotion
does not come through"). Not yet judged: how well a Chatterbox-made tone reference carries over
into Qwen lines; the user decides by ear, and the result goes in Findings.

## Checks and known behavior

- `check_takes.py <folder> --ref <reference.wav>` (in the same container, CPU) prints each take's
  length, pitch against the reference and the words Whisper heard. In the first test one of two
  takes of the same line was flagged at 1.8x the reference pitch with the words correct: Qwen takes
  can drift in pitch, so look at the PITCH flags and listen.
- Seeds: a take's seed is in its `.json`; the same seed, text and reference reproduce it.
- English is the tested language (`--language English`); Qwen lists others, untested here.
