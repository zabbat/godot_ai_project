# AGENTS.md

The bridge between the game design in [docs/](../docs/AGENTS.md) and the
Godot project in `godot/{{GODOT_PROJECT}}/`. These documents say how each feature is
built, the exact data the game uses, the rules the build decided, and where
every file goes. Together with `docs/` and `assets/`, they must be enough to
rebuild the Godot project from scratch.

Keep them in sync with Godot: a change on one side updates the other in the
same step.

Below is a short description of each document/subfolder in this folder.

- [godot_structure.md](godot_structure.md) — Map of the Godot project: project folder, engine version and executable, main scene, and what each folder holds with its key files. Look Godot paths up here; update it whenever folders or key files change.
- [game_data.md](game_data.md) — The exact game data (stats, rules, constants, content lists). Rebuild the Godot data from this.
- [asset_map/](asset_map/AGENTS.md) — Which file in `assets/` becomes which file in Godot, converted how (TOML entries and conversion profiles).
