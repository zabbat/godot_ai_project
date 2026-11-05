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
| Voice reference | Voice | generate-voice-lines | `audio/voice/<name>/<name>_voice_reference.wav` + `.md` | - (not in the game) | 6-8 s, calm, clean, one speaker; Kokoro recipe or source and rights in the `.md` |
| Greeting line | Voice, Background | generate-voice-lines (speech) | `audio/voice/<name>/<name>_greeting/` | (agree at set-up) | 5 takes, 2-3 variants kept |
| Death sound | Voice | comfy-ui-sound-effects or generate-voice-lines | `audio/sfx/characters/<name>_death/` | (agree at set-up) | 2-4 variants, short, trimmed |

## Characters

- (none yet) one link per character sheet (`<name>.md`), with one line on its state, e.g. "portraits in game, voice missing".
