# The default resource set

The resources a character usually needs in the game. A type's resource set (`prototype/characters/<type>/AGENTS.md`) starts from this list at set-up; the user drops what the type does not need and adds what it does. Paths below are defaults: if the project's `assets/AGENTS.md` or `prototype/godot_structure.md` already has a pattern, use that and write it into the type's resource set.

`<name>` is the character's `snake_case` name. Master paths are relative to `assets/`.

| Resource | Depends on | Tool skill | Master (default) | Spec (default) |
|---|---|---|---|---|
| Face portrait | Appearance | `comfy-ui-images` | `2d/portraits/<name>/<name>_portrait.png` | square, 720x720 or more, face centered, nothing important in the corners |
| Half portrait | Appearance | `comfy-ui-images` (+ cut out if transparent) | `2d/portraits/<name>/<name>_half_portrait.png` | head and torso, 2:3 portrait, 720x1080 or more |
| 3D model | Appearance | `blender-3d-modeling` (own) or a vendor pack (`glb-3d-model-and-animations`) | own: `3d/characters/<name>/<name>.glb`; vendor: the pack's file in `3d/third_party/<pack>/` | budget and scale from `docs/style/3d_style.md`; animations listed |
| Voice reference | Voice | `generate-voice-lines` (Kokoro; or the user's recording) | `audio/voice/<name>/<name>_voice_reference.wav` + `.md` (not exported to the game) | 6-8 s, calm, one speaker, clean, no effects; recipe or source and rights in the `.md` |
| Greeting line | Voice, Background | `generate-voice-lines` (speech mode) | `audio/voice/<name>/<name>_greeting/` | 5 takes generated, 2-3 variants kept, the text from the bible's Voice (Greeting) |
| Death sound | Voice (or Appearance for creatures) | `comfy-ui-sound-effects` (creatures, monsters), `generate-voice-lines` (human cries with the voice) | `audio/sfx/characters/<name>_death/` | 2-4 variants, short, trimmed |

"Depends on" is what makes a resource `outdated` when that bible section changes.

Common extras to offer at set-up:

| Resource | Depends on | Tool skill | Master (default) |
|---|---|---|---|
| Portrait states (blink, hurt, casting...) | Appearance | `comfy-ui-images` (image-to-image from the portrait) | `2d/portraits/<name>/<name>_portrait_<state>.png` |
| In-game 2D figure / sprite / HUD cut-out | Appearance | `comfy-ui-images` + cut out | `2d/characters/<name>/<name>_<desc>.png` |
| Full-body art | Appearance | `comfy-ui-images` | `2d/portraits/<name>/<name>_full.png` |
| More spoken lines (spell calls, battle cry, hurt, victory, barks) | Voice | `generate-voice-lines` | `audio/voice/<name>/<name>_<line>/` |
| Hurt / attack / idle sounds | Voice or Appearance | `comfy-ui-sound-effects` | `audio/sfx/characters/<name>_<event>/` |
| Animations (for a vendor rig) | Appearance (movement) | `glb-3d-model-and-animations` / `blender-3d-modeling` | with the model |

The Godot path of each resource is project-specific (for example `entities/<type>/<name>/<name>_portrait.png`): agree it at set-up from `prototype/godot_structure.md` and write it into the type's resource set. The asset map entry and its profile follow the architecture skill.

## Tips per resource

### Face portrait
- Make it first: it fixes the character's look, and later images use it as reference.
- Start from the template the style doc names for portraits (`comfy-ui-images`, "The project's style doc"). Prompt = the style doc's style keywords + the bible's Appearance **prompt keywords** + framing ("close-up face portrait, face fills most of the frame, three-quarter view") + background from the style doc.
- Generate 3-4 takes with different seeds; the user picks one.

### Half portrait
- The same face, hair, outfit and colours as the face portrait: use the same prompt keywords and seed range, and use the face portrait as an image reference (image-to-image / reference workflow) when the ComfyUI graph has one.
- Framing: "half-body portrait, head and torso, hands visible if holding a prop".
- If the game shows it over the scene, cut it out (transparent PNG), as the `comfy-ui-images` skill describes.

### 3D model
- Vendor model first if the project uses a pack: pick the closest model, then record in Notes what differs from the bible (colours can often be changed with a material).
- Own model: build from the portraits (front and side) in Blender; check the budget in `3d_style.md`; export GLB with the Blender skill's checks.
- List the animations it needs in the resource spec (idle, walk, attack, hurt, death...).

### Voice reference
- Made once per speaking character, before any of its lines, with the `generate-voice-lines` skill: a blend of Kokoro voices chosen from the bible's Voice section, rendered as one **calm** 6-8 s clip. Every line is generated from it, so all lines sound like one person. Or the user records or licenses one.
- Its master is a resource, so it lives in `assets/` (`audio/voice/<name>/<name>_voice_reference.wav`, committed, with the Kokoro recipe in its `.md`), never in `docs/`. It has no asset map entry (not in the game). Chatterbox uses a copy at `<cbx>/voices/<name>.wav`. A clip of a real person is committed only if the user has the rights and says so.
- The bible's Voice section links it and names the blend in one line.
- Changing the voice makes every spoken line `outdated`.

### Greeting line and other spoken lines
- Made with `generate-voice-lines`: the text comes from the bible's Voice section (Greeting, favourite words, spell calls), the delivery from the **kind of line** (speech for greetings and dialogue, battle for spell calls and battle cries) and the personality. Lines beyond the greeting are listed under Voice too.
- 5 takes per line, word-checked automatically; the user keeps the good ones. Lines heard often need several variants (different wordings).

### Death sound and other creature sounds
- Monsters and creatures: `comfy-ui-sound-effects` ("zombie death groan, wet gurgle, collapse"), built from the bible's Appearance and Voice.
- Humans: a cry made with `generate-voice-lines` from the voice reference sounds like the same person; a sound effect is the fallback.
- 2-4 variants so the game can randomize (the Godot side is a randomizer, `godot-development`).
