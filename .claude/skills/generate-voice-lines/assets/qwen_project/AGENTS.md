# Qwen3-TTS - voice design and cloned voice lines (Docker)

Index and project notes for the default voice engine of the `generate-voice-lines` skill
(`.claude/skills/generate-voice-lines/`; read it before generating). Qwen3-TTS (Apache-2.0) runs
only in Docker, on the NVIDIA GPU.

```
<qwen>/
  AGENTS.md          this file
  .gitignore         ignores voices/, output/
  docker/            Dockerfile + compose.yaml (image qwen3-tts:1, weights in the volume qwen-hf-cache)
  voices/            reference clips used for cloning, each with its <name>.json transcript (git-ignored)
  output/            candidate references and generated lines (git-ignored)
    references/<name>/   VoiceDesign candidates for a default reference
    <name>/              line takes: <line>/<line>-<nr>.wav + .json
```

Run (from the project root):

```
docker compose -f <qwen>/docker/compose.yaml run --rm qwen python .claude/skills/generate-voice-lines/assets/scripts/qwen_voice.py design|clone ...
```

## Voices (fill in as references are chosen)

A reference's transcript lives in the `.json` next to it; cloning reads it from there.

| Voice file | Character | Kind (default / tone) | VoiceDesign description or source | Master |
|---|---|---|---|---|
| _(none yet)_ | | | | |

## Findings

What worked and what did not for this game's voices (emotions that came through, ones that needed
Chatterbox, descriptions that gave a stable voice). Newest first.
