# AGENTS.md

Template repo for Godot AI projects: the shared skills and agents in `.agents/`, published as the Claude Code plugin `godot-ai` (see
[README.md](README.md)). The paths below let the tool skills be tried out in this repo;
their output goes to `tools/` (git-ignored, not part of the template). New game projects get
their own `AGENTS.md` from `.agents/skills/godot-ai-architecture/assets/repo_template/`.

## Changing the skills and agents

Projects install the plugin from GitHub and only receive a change when the version in
`.claude-plugin/plugin.json` goes up (a push without a bump never reaches them). So every
change to `.agents/` (or the plugin files) comes with a version bump and a line in
[CHANGELOG.md](CHANGELOG.md):

- **patch** (1.0.0 → 1.0.1): fixes and wording inside a skill, no change in what it does.
- **minor** (1.0.1 → 1.1.0): a new skill, reference or script, or a new capability of a skill.
- **major** (1.1.0 → 2.0.0): a skill renamed or removed, or a change projects must migrate for
  (new layout, moved files, changed project settings).

One bump per push is enough (use the largest change in it). Keep `version` only in
`plugin.json`, not in `marketplace.json`. After pushing, projects update with
`claude plugin marketplace update godot-ai-project` and
`claude plugin update godot-ai@godot-ai-project`, then `/reload-plugins`.

## Project paths

| What | Path |
|---|---|
| ComfyUI install | `C:\ai\ComfyUI_windows_portable\ComfyUI` (existing, portable; start: `run_nvidia_gpu.bat`) |
| ComfyUI server | `http://127.0.0.1:8188` |
| ComfyUI images output | `tools/comfy-ui/output/images/` |
| ComfyUI image templates | `tools/comfy-ui/templates/images/` |
| ComfyUI sound effects output | `tools/comfy-ui/output/sound-effects/` |
| ComfyUI sound templates | `tools/comfy-ui/templates/sound-effects/` |
| Chatterbox | `tools/chatterbox/` |
| Qwen3-TTS | `tools/qwen3-tts/` |
