# AGENTS.md

The tools the project uses, one folder per tool. Each tool folder holds its
own settings, its own scripts, its `AGENTS.md` and, for generators, an
`output/` folder with every generated take (git-ignored). Working files
keep their own folder names (for example Blender's `models/`). A chosen take
is copied to [assets/](../assets/AGENTS.md); nothing in `tools/` is used by
the game directly.

A tool's skill creates its folder the first time it is set up; the paths
are in the "Project paths" table of the root [AGENTS.md](../AGENTS.md).
Removing a tool is removing its folder (and its row there).

- [godot-sync/](godot-sync/AGENTS.md) — Generic scripts: export `assets/`
  into Godot through the asset map, and check where Godot and the docs
  disagree.
