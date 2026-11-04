# AGENTS.md

Blender work for this project, done by Claude through the sandboxed Blender MCP
(the `blender-3d-modeling` skill). Blender runs in Docker with no network and sees
only the folders listed in [config/sandbox.toml](config/sandbox.toml).

- [models/](models/) — `.blend` work files, one folder per subject (`models/<subject>/<subject>.blend`), previews in `models/_previews/`. Shared with the sandbox as `/models` (read-write).
- [config/](config/) — sandbox settings. **Never shared** with the sandbox, so Blender code cannot change what it can access.
  - [config/sandbox.toml](config/sandbox.toml) — shared folders (host path ↔ sandbox path, access), image, memory.

## Conventions

- Units: metric, 1 unit = 1 m. Up +Z in Blender (glTF export converts to +Y up).
- Name every object, mesh, material and action (no `Cube.001`). Looping clips end in `-loop`.
- Exports: <where finished .glb files go, e.g. assets/3d/ — must be a shared folder>

## Gotchas

<findings from working in Blender on this project>
