# Templates

Copied into a project by the `game-character` skill, with the placeholders filled:

| Placeholder | Value |
|---|---|
| `{{TYPE}}` | the type folder name, `snake_case` plural (`mobs`) |
| `{{TYPE_TITLE}}` | the type for people (`Mobs`) |
| `{{NAME}}` | the character's `snake_case` name (`orc_warrior`) |
| `{{DISPLAY_NAME}}` | the character's name for people (`Orc Warrior`) |
| `{{DATE}}` | today, `YYYY-MM-DD` |

| Template | Becomes |
|---|---|
| `docs/characters/AGENTS.md` | `docs/characters/AGENTS.md` (once) |
| `docs/characters/TYPE/AGENTS.md` | `docs/characters/<type>/AGENTS.md` (per type; its bible sections) |
| `docs/characters/TYPE/NAME/NAME.md` | `docs/characters/<type>/<name>/<name>.md` (per character; keep only the type's sections) |
| `prototype/characters/AGENTS.md` | `prototype/characters/AGENTS.md` (once) |
| `prototype/characters/TYPE/AGENTS.md` | `prototype/characters/<type>/AGENTS.md` (per type; its resource set) |
| `prototype/characters/TYPE/NAME.md` | `prototype/characters/<type>/<name>.md` (per character; one row per resource of the type) |

Keep the wording generic: no game-specific content in these files.
