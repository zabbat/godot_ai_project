# The default resource set

The resources a character usually needs in the game. A type's resource set (`prototype/characters/<type>/AGENTS.md`) starts from this list at set-up; the user drops what the type does not need and adds what it does. Paths below are defaults: if the project's `assets/AGENTS.md` or `prototype/godot_structure.md` already has a pattern, use that and write it into the type's resource set.

`<name>` is the character's `snake_case` name. Master paths are relative to `assets/`.

| Resource | Depends on | Tool skill | Master (default) | Spec (default) |
|---|---|---|---|---|
| Face portrait | Appearance | `comfy-ui-images` | `2d/portraits/<name>/<name>_portrait.png` | square, 720x720 or more, face centered, nothing important in the corners |
| Half portrait | Appearance | `comfy-ui-images` (+ cut out if transparent) | `2d/portraits/<name>/<name>_half_portrait.png` | head and torso, 2:3 portrait, 720x1080 or more |
| 3D model | Appearance | `blender-3d-modeling` (own) or a vendor pack (`glb-3d-model-and-animations`) | own: `3d/characters/<name>/<name>.glb`; vendor: the pack's file in `3d/third_party/<pack>/` | budget and scale from `docs/style/3d_style.md`; animations listed |
| Voice reference | Voice | `chatterbox-text-to-speech` (or the user's recording) | `docs/characters/<type>/<name>/<name>_voice.wav` (a reference, not an asset) | 6-15 s, one speaker, clean, no music; source and rights recorded |
| Greeting line | Voice, Background | `chatterbox-text-to-speech` with the voice reference | `audio/voice/<name>/<name>_greeting/` | 2-3 variants, the text from the bible's Voice (Greeting) |
| Death sound | Voice (or Appearance for creatures) | `comfy-ui-sound-effects` (creatures, monsters), `chatterbox-text-to-speech` (human cries with the voice) | `audio/sfx/characters/<name>_death/` | 2-4 variants, short, trimmed |

"Depends on" is what makes a resource `outdated` when that bible section changes.

Common extras to offer at set-up:

| Resource | Depends on | Tool skill | Master (default) |
|---|---|---|---|
| Portrait states (blink, hurt, casting...) | Appearance | `comfy-ui-images` (image-to-image from the portrait) | `2d/portraits/<name>/<name>_portrait_<state>.png` |
| In-game 2D figure / sprite / HUD cut-out | Appearance | `comfy-ui-images` + cut out | `2d/characters/<name>/<name>_<desc>.png` |
| Full-body art | Appearance | `comfy-ui-images` | `2d/portraits/<name>/<name>_full.png` |
| More spoken lines (battle cry, hurt, victory, barks) | Voice | `chatterbox-text-to-speech` | `audio/voice/<name>/<name>_<line>/` |
| Hurt / attack / idle sounds | Voice or Appearance | `comfy-ui-sound-effects` | `audio/sfx/characters/<name>_<event>/` |
| Animations (for a vendor rig) | Appearance (movement) | `glb-3d-model-and-animations` / `blender-3d-modeling` | with the model |

The Godot path of each resource is project-specific (for example `entities/<type>/<name>/<name>_portrait.png`): agree it at set-up from `prototype/godot_structure.md` and write it into the type's resource set. The asset map entry and its profile follow the architecture skill.

## Tips per resource

### Face portrait
- Make it first: it fixes the character's look, and later images use it as reference.
- Prompt = the style doc's style keywords + the bible's Appearance **prompt keywords** + framing ("close-up face portrait, face fills most of the frame, three-quarter view") + background from the style doc.
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
- Made once per speaking character, before any of its lines. Every line uses it (`--voice <name>`), so all lines sound like one person.
- From a Chatterbox take: generate a 10-15 s neutral line with the built-in voice and settings matching the bible's Voice section; when the user likes a take, save it as the reference. Or the user records or licenses one.
- It lives in the bible folder (committed, it is a design reference) and is copied to `<cbx>/voices/<name>.wav` for Chatterbox. A clip of a real person is committed only if the user has the rights and says so.
- Changing the voice makes every spoken line `outdated`.

### Greeting line and other spoken lines
- The text comes from the bible's Voice section (Greeting, favourite words); the delivery (style, exaggeration) from Voice and Background (personality). Lines beyond the greeting are listed under Voice too. Read the Chatterbox skill's style reference before choosing settings.
- 2-3 takes per variant; lines heard often need several variants (different wordings).

### Death sound and other creature sounds
- Monsters and creatures: `comfy-ui-sound-effects` ("zombie death groan, wet gurgle, collapse"), built from the bible's Appearance and Voice.
- Humans: a Chatterbox cry with the voice reference sounds like the same person; a sound effect is the fallback.
- 2-4 variants so the game can randomize (the Godot side is a randomizer, `godot-development`).
