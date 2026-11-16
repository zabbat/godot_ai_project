# Changelog

Versions of the `godot-ai` plugin (`.claude-plugin/plugin.json`). Newest first; one line per
change, naming the skill or agent. Bump rules: see [AGENTS.md](AGENTS.md).

## 1.3.0 - 2026-11-16

- `godot-3d-models-and-animations`: ponytails and hair as well as cloaks in `cloaks-and-cloth.md`
  (spring bones centred on the skeleton, a push while walking, reading results in `skeleton_updated`);
  new scripts `split_part.py`, `add_bone_chains.py`, `spring_chains.gd`, `spring_measure.gd`.

## 1.2.0 - 2026-11-16

- `godot-3d-models-and-animations`: new `references/cloaks-and-cloth.md` (why auto-rigs skin a cloak
  to the arms, how games handle it, its own bone chains with `SpringBoneSimulator3D` and capsule
  colliders, how to check it); `ai-models-and-mixamo.md` gains checking the auto-rig's weights
  (feet, loose cloth) and splitting parts out of the one mesh; verify from behind and in front.
- `godot-shader-effects`: vertex shaders on skinned parts (posed `VERTEX`, baked vertex-colour masks,
  `material_override` only while running), `pow` of a negative, tweening shader parameters,
  back-face normals on double-sided cloth.

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
