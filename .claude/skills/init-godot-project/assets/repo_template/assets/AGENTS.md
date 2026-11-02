# AGENTS.md

The source resources of the game: the chosen masters of every image, model
and sound, each with a record of where it came from. This folder is the
source of truth; the files in the Godot project are exported from it.

`assets/` only describes the resources themselves. Which file the game uses,
where, and how it is converted is in
[prototype/asset_map/](../prototype/asset_map/AGENTS.md). Never point Godot
at this folder directly.

## Layout

Organized by type, then by subject. Names are `snake_case`.

```
assets/
  2d/                        images (portraits/<unit>/, icons/, ...)
  3d/
    third_party/<pack>/      files taken out of the pack (original names and paths),
                             License.txt (the raw zips stay in downloads/)
    third_party/sources.md   download page and license of every pack
  audio/
    music/                   tracks + sources.md (tool, prompt, link)
    sfx/<category>/<owner>_<event>/  chosen takes of a sound effect + .md each
                             (prompt, seed) + <owner>_<event>_workflow.json
```

Add a folder when its first resource arrives, and describe it here.

## Rules

- **Only chosen resources.** Work in progress (every generated take, test
  renders) stays in the workshop, `{{WORKSHOP}}/` at the repo root
  (git-ignored). Copy a take here once it is picked for the game.
- **No raw downloads.** Zips and files as downloaded stay in `downloads/`
  (git-ignored); only the files the game uses are copied here. Material that
  only shows what we want (a drawing style) goes to
  [docs/references/](../docs/references/AGENTS.md), not here.
- **Keep the best version.** Store the highest-quality file you have
  (largest image, lossless or original audio); the asset map's profile makes
  the game-ready version.
- **Provenance next to the file.** A generated resource keeps the per-take
  `.md` from the workshop (prompt, model, seed) renamed to match it, and the
  reloadable ComfyUI workflow as `<name>_workflow.json`. A vendor resource
  keeps its pack's `License.txt`, and the pack is listed in
  `3d/third_party/sources.md`. Never edit the resource itself; changes are
  new takes.
- **New takes replace the master in place**: same file names, with the new
  take's `.md`. Takes reviewed and not wanted are listed in the master's
  `.md` as `Rejected: <take file>, ...`; `tools/check_sync.py` reports any
  newer, unlisted take in the workshop.
- **No game usage here.** No Godot paths, `.import` files or game data in
  this folder; those belong in `prototype/` and `godot/`.
- Resources by hand (bought, made in an editor) follow the same rules: the
  `.md` says where they came from and under what license.

## Current contents

| Folder | Contents |
|---|---|
| (empty) | No resources yet. |
