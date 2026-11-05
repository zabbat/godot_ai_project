# AGENTS.md

The resource set of {{TYPE_TITLE}}: every resource a character of this type
has in the game. Each character's sheet has one row per resource below
(`not needed` if it skips one). Change the set here first, then add or mark
the rows in every sheet.

Master paths are relative to `assets/`, Godot paths to the Godot project.
"Depends on" names the bible section that makes the resource `outdated`
when it changes.

## Resource set

| Resource | Depends on | Tool | Master | In Godot | Spec |
|---|---|---|---|---|---|
| Face portrait | Appearance | comfy-ui-images | `2d/portraits/<name>/<name>_portrait.png` | (agree at set-up) | square, 720x720+, face centered; shown at (size) in (screen) |
| Half portrait | Appearance | comfy-ui-images | `2d/portraits/<name>/<name>_half_portrait.png` | (agree at set-up) | head and torso, 2:3, 720x1080+; transparent or not |
| 3D model | Appearance | blender-3d-modeling or a vendor pack | `3d/characters/<name>/<name>.glb` or a pack file | (agree at set-up) | budget from `docs/style/3d_style.md`; animations: idle, walk, attack, hurt, death |
| Voice reference | Voice | chatterbox-text-to-speech | `docs/characters/{{TYPE}}/<name>/<name>_voice.wav` (a reference, not an asset) | - | 6-15 s, clean, one speaker; source and rights in the bible |
| Greeting line | Voice, Background | chatterbox-text-to-speech | `audio/voice/<name>/<name>_greeting/` | (agree at set-up) | 2-3 variants |
| Death sound | Voice | comfy-ui-sound-effects or chatterbox-text-to-speech | `audio/sfx/characters/<name>_death/` | (agree at set-up) | 2-4 variants, short, trimmed |

## Characters

- (none yet) one link per character sheet (`<name>.md`), with one line on its state, e.g. "portraits in game, voice missing".
