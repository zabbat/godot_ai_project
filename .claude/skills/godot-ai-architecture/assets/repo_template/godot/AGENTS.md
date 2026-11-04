# AGENTS.md

The Godot side of the repo. `{{GODOT_PROJECT}}/` is the Godot 4 project
(`project.godot`, {{RENDERER_NAME}} renderer, {{VIEWPORT_W}}x{{VIEWPORT_H}}). GDScript only.

This folder is built from the AI side and can be rebuilt from it:

- **What to build**: the design in [docs/](../docs/AGENTS.md) and the build
  notes, exact game data and file conventions in
  [prototype/](../prototype/AGENTS.md).
- **Resources**: exported from [assets/](../assets/AGENTS.md) through the
  [asset map](../prototype/asset_map/AGENTS.md). Exported files in
  `{{GODOT_PROJECT}}/` are never edited or replaced here; change the master or
  the map instead. Godot's `.import` and `.uid` files next to them belong to
  this side.
- **Where things are**: [godot_structure.md](../prototype/godot_structure.md)
  maps every folder and key file. Update it when you add, move or remove
  one.
- **Conventions**: the `godot-development` skill (layout, scenes, Resources,
  shaders, audio) and, for 3D models, the `glb-3d-model-and-animations`
  skill. How the repo feeds this folder: the `godot-ai-architecture` skill.

When you change game data or behavior here (a `.tres`, a scene property, a
constant, a rule in a script), update `prototype/` in the same step,
especially [game_data.md](../prototype/game_data.md). The
`godot-resource-manager` agent checks this and updates the docs from Godot.

Raw downloads never go inside the Godot project; they live in the repo's
`downloads/` folder (git-ignored).
