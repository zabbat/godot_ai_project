# Changelog

Versions of the `godot-ai` plugin (`.claude-plugin/plugin.json`). Newest first; one line per
change, naming the skill or agent. Bump rules: see [AGENTS.md](AGENTS.md).

## 1.1.1 - 2026-11-15

- `comfy-ui-images`, `game-character`: concept sheet is now 720x1280 in a two by two grid, with
  neutral A-pose front, back and side views, and loose parts (a cape) on their own sheet.

## 1.1.0 - 2026-11-15

- `comfy-ui-images`: new "concept sheet" command and `references/concept-sheet.md` (one image
  with a character in four views).
- `game-character`: "Concept sheet" resource, made first for every new character.

## 1.0.0 - 2026-11-15

- First plugin release: skills and agents moved from `.claude/` to `.agents/` and published as
  the `godot-ai` plugin (marketplace `godot-ai-project`); projects enable it instead of copying.
- `godot-3d-models-and-animations` (renamed from `glb-3d-model-and-animations`).
- Descriptions shortened to the Agent Skills limit (1024 characters).
