# AGENTS.md

What each character needs in the game and where its files are: one resource
sheet per character (`<type>/<name>.md`). Who the characters are is in
[docs/characters/](../../docs/characters/AGENTS.md); their exact game data is
in [game_data.md](../game_data.md).

Managed with the `game-character` skill. A type's `AGENTS.md` is its
resource set: every resource its characters have, with spec, tool, master
and Godot paths, and what each depends on in the bible.

## Status values

| Status | Means |
|---|---|
| `missing` | needed, nothing made yet |
| `takes` | takes exist in a tool's `output/`, none chosen yet (named in Notes) |
| `chosen` | master copied to `assets/` with its record, not in the game yet |
| `in game` | mapped in the asset map, exported, and used by the Godot files |
| `outdated` | exists, but the bible part it depends on changed after it was made (Notes say what) |
| `not needed` | this character skips a resource its type has (Notes say why) |

Types:

- (none yet) Add each type here: one link per type folder to its `AGENTS.md` (its resource set and characters).
