---
name: comfy-ui-connection
description: How to talk to ComfyUI through comfy-cli (Comfy-Org's official command line) - finding or installing comfy-cli, choosing the ComfyUI install (an existing one, or a new one in the project's tools folder), checking and starting the server, reading the current setup, running a graph, uploading inputs and downloading outputs, listing models, and fixing failed or stuck runs. Local ComfyUI only (no Comfy Cloud). The base the ComfyUI generation skills (comfy-ui-images, comfy-ui-sound-effects) build on; load it before any of them talks to ComfyUI. Use directly when the user says "init comfy", wants to install or set up comfy-cli or ComfyUI, points the project at a ComfyUI install, or asks whether ComfyUI is running or which models it has.
---

# ComfyUI connection

The single place that knows how to reach ComfyUI. Other skills say *what* to generate and
where to keep it; they get the connection, the run and the files from here, so a change in
how ComfyUI is reached is made once, in this skill.

Bundled: `scripts/comfy_graph.py` - reads the current setup from ComfyUI's history and edits
API-format graphs (set inputs, new seeds, a text preview node). Standard library only.

Tested with comfy-cli 1.25.0 against ComfyUI 0.43.2 (Windows portable build), 2026-11-07.

## Rules for every call

- **Local only.** Comfy Cloud (Comfy-Org's hosted ComfyUI, `--where cloud`) is not supported.
  Never pass `--where cloud`, never run `comfy cloud login` / `set-key`, and never pass
  `--allow-spend` (paid partner-API nodes such as Flux Pro or Ideogram bill a Comfy account
  even from a local ComfyUI). If an envelope says `"where": "cloud"`, stop and tell the user:
  a cloud sign-in or `COMFY_WHERE` would route every command there; `--where local` forces local.
- Run `comfy` with **`--skip-prompt --json`** (no questions, one JSON envelope on stdout:
  `{"ok", "command", "data", "error": {"code", "message", "hint", "details"}}`). Read `ok`
  and `data`; on `ok: false` look up `error.code` in "When something fails", and show the
  user `error.message`. `details` usually says why.
- Set **`PYTHONUTF8=1`** in the environment. Without it comfy-cli crashes on the Windows
  console (`UnicodeEncodeError` in its help and tables). Also set `DO_NOT_TRACK=1`.
- **Never let a command wait on stdin.** `comfy download` without a prompt id reads stdin and
  hangs; always pass the id, and redirect stdin (`< /dev/null` in Git Bash).
- Give long runs a timeout (`--timeout`, and the Bash tool's own timeout).

In Git Bash:

```bash
export PYTHONUTF8=1 DO_NOT_TRACK=1
comfy --skip-prompt --json <command> ... < /dev/null
```

The helper runs with a uv-managed Python (`python` on Windows is often the Store stub):

```bash
uv run --no-project --python 3.12 python -I <this skill>/scripts/comfy_graph.py <cmd> ...
```

## Setup: "init comfy" (or the first ComfyUI task of a session)

### 1. comfy-cli

Check `comfy --version` (also `~/.local/bin/comfy.exe`). If it's missing:

1. Tell the user comfy-cli isn't installed and **ask** before installing it. It is a
   user-wide tool, installed once per machine, not per project:
   ```bash
   uv tool install comfy-cli        # puts comfy.exe in ~/.local/bin
   comfy tracking disable
   ```
2. No `uv`? Offer its installer (Windows:
   `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`), then
   Claude Code needs a restart to see the new PATH. Until then `uvx --from comfy-cli comfy ...`
   runs it without installing.
3. Updating later: `uv tool upgrade comfy-cli`.

Do **not** run `comfy setup` or `comfy skills install`: they install comfy-cli's own agent
skills into Claude Code.

### 2. The ComfyUI install

The project's root `AGENTS.md` "Project paths" table says which ComfyUI to use:

| What | Path |
|---|---|
| ComfyUI install | `C:\ai\ComfyUI_windows_portable\ComfyUI` (existing, portable; start: `run_nvidia_gpu.bat`) |
| ComfyUI server | `http://127.0.0.1:8188` |

If there's no row, **ask the user** (AskUserQuestion):

- **Use an existing install** (recommended when they have one: models are large, never
  duplicate them). Ask for the path of its `ComfyUI` folder (the one with `main.py` and
  `models/`). Look first in likely places (`C:\ai\`, `~\Documents\ComfyUI*`, `~\comfy`) and
  offer what you find. Note how it is started (portable: `run_nvidia_gpu.bat` next to the
  `ComfyUI` folder; desktop app; their own venv).
- **Install a new one into the project** at `tools/comfy-ui/ComfyUI/` (or a folder they name)
  with comfy-cli; see "New install" below.
- **Only a server** (on another machine or port): record its URL; no install row.

Write the rows (create the table if missing) so the question is never asked again. The
install path is on this machine only: if the project moves to another machine and the path
doesn't exist, ask again.

**What comfy-cli may do to an install depends on who made it:**

| Install | comfy-cli may | Never |
|---|---|---|
| **Existing** (portable, desktop app, the user's own) | Server calls: `run`, `upload`, `download`, `jobs`, `system-stats`, `free`, `model list` (read-only) | `launch`, `install`, `update`, `node install/update/uninstall`, `model download/remove` without asking, `stop` |
| **New**, made by comfy-cli in the project | everything | - |

Why: comfy-cli picks Python from `VIRTUAL_ENV` / `CONDA_PREFIX` / a `.venv` in the
workspace, and otherwise (installed with `uv tool`) **creates a new `.venv` inside the
workspace**. It knows nothing about the portable build's `python_embeded`, so `launch` or
`node install` on a portable install would build a second, empty environment inside it.

### 3. The server

```bash
comfy --skip-prompt --json system-stats < /dev/null      # ok=true: running (ComfyUI version, GPU, VRAM)
```

`server_not_running` →

- **Existing install**: ask the user to start ComfyUI the way they usually do (portable:
  `run_nvidia_gpu.bat`), or offer to start it in its own window, which survives this session:
  `powershell -c "Start-Process -FilePath '<portable folder>\run_nvidia_gpu.bat' -WorkingDirectory '<portable folder>'"`.
  Wait with `system-stats` until it answers (it takes 10-60 s).
- **New install**: `comfy --skip-prompt --workspace=<install> launch --background -- --port 8188`;
  `comfy stop` stops it.

If the server isn't on `127.0.0.1:8188`, export `COMFY_LOCAL_URL=http://host:port` (comfy-cli
and `comfy_graph.py` both read it), or pass `--host`/`--port`.

## New install (into the project)

Only when the user chose it. Downloads ComfyUI, PyTorch (~3 GB) and ComfyUI-Manager; models
come separately.

```bash
comfy --skip-prompt --workspace=tools/comfy-ui/ComfyUI install --nvidia --fast-deps
```

- `--workspace` is the ComfyUI folder itself. **Always pass it**: without it comfy-cli installs
  into `~/Documents/comfy`.
- GPU: `--nvidia` (check `nvidia-smi`; `--cuda-version 12.8` etc. if needed), `--amd`,
  `--m-series` or `--cpu`. `--version latest` = latest stable release (default: nightly master).
- Git-ignore the install (`tools/comfy-ui/ComfyUI/`); ask before editing `.gitignore`.
- Don't use `comfy set-default`: skills read the path from `AGENTS.md` and pass
  `--workspace`, so one machine can serve several projects.
- Models the workflows need: `comfy --skip-prompt --workspace=<install> model download --url <url> --relative-path models/<folder>`
  (`HF_API_TOKEN` / `CIVITAI_API_TOKEN` env vars for gated files). **Ask before every
  download**: they are often several GB. Custom nodes: `comfy --workspace=<install> node install <registry-id>`
  (lowercase registry id, e.g. `comfyui-impact-pack`).

## Working with graphs

ComfyUI has two graph formats:
- **UI workflow** (`nodes` + `links`): what the canvas saves and reloads. Keep this one as the
  reloadable record (drag it onto the canvas).
- **API graph** (`{"<id>": {"class_type", "inputs"}}`): what the server executes. Edit and run
  this one. Node ids inside subgraphs look like `52:31`.

### The current setup = latest history

The server can't see the unsaved browser canvas. Rule for the user: **after changing anything
in ComfyUI, queue the workflow once**; that run is the setup the skills read.

```bash
uv run --no-project --python 3.12 python -I <skill>/scripts/comfy_graph.py latest <work dir>
```

Writes `<work dir>/api.json` (executable) and `ui.json` (canvas, if the run came from the
browser) and prints every node with its plain inputs. Empty history → ask the user to queue
once. Use a work dir in the scratchpad.

### Edit

```bash
comfy_graph.py set     api.json 52:31.value="a bowstring release" 52:36.value=1.5
comfy_graph.py seed    api.json                 # new random seed/noise_seed on every sampler
comfy_graph.py seed    api.json --node 52:3     # only this node
comfy_graph.py preview api.json 52:28 --id 900  # PreviewAny: returns a node's text output
```

Find nodes by `class_type` and role (the `nodes` summary), not by remembered ids.
Before running a graph you built yourself, `comfy --skip-prompt --json workflow validate --workflow api.json`
checks node types, inputs and **enum values, which include the model file names**, so a
missing model is reported before the run.

### Run

```bash
comfy --skip-prompt --json run --workflow api.json --wait --timeout 600 < /dev/null
```

`data`: `status` (`completed`), `prompt_id`, `outputs` (view URLs), `outputs_by_node`
(`{"<node id>": [urls]}`), `elapsed_seconds`. Text from `PreviewAny` nodes: `comfy --json jobs status <prompt_id>`
→ `data.text_outputs["<node id>"]`. `--timeout` is the longest *silence* allowed, not a
total limit. UI-format files are accepted too (converted client-side), but the API graph
from history is the reliable input.

Without `--wait` it returns the `prompt_id` at once; `comfy --json jobs wait <id> --timeout 1800`
blocks later (`jobs ls`, `jobs cancel <id>`).

### Inputs and outputs

```bash
comfy --skip-prompt --json upload <file> ...  < /dev/null          # into ComfyUI's input/; name for LoadImage etc.
comfy --skip-prompt --json download <prompt_id> -o <dir> < /dev/null
```

`download` writes `<dir>/<short id>_000.<ext>` ... and lists them in `data.files[]`
(`path`, `node_id`, `size`). Download into a scratch dir, then move each file to the name the
calling skill gives it. `--url-only` returns the URLs without downloading.

### Models and the machine

```bash
comfy --skip-prompt --workspace=<install> --json model list --relative-path models/loras
comfy --skip-prompt --json model search -t "<words>" --type lora   # filename match on the running server
comfy --skip-prompt --json system-stats               # VRAM, versions
comfy --skip-prompt --json free                        # unload models / free VRAM (never interrupts a run)
```

## When something fails

Go by `error.code`; the envelope's `hint` is written for comfy-cli in general, so check it
against the install rules above before following it (on an existing install it may say
`comfy launch` or `comfy node install`, which are not allowed there).

| `error.code` | What it means | Fix |
|---|---|---|
| `server_not_running` | Nothing answers on the server address | "The server" above: the user's own start for an existing install, `comfy launch --background` only for a new one. Check `COMFY_LOCAL_URL` if ComfyUI runs on another port |
| `prompt_rejected` | The server checked the graph and refused nodes; per node in `details.node_errors` | See the two rows below |
| ↳ unknown `class_type` | A custom node pack is missing or failed to load | `comfy --json nodes search <name>`: `data.count` 0 or `data.close_match: true` = not installed. Existing install: tell the user which pack is needed. New install: `comfy node install <registry-id>` (ask first) |
| ↳ value not in list (`ckpt_name`, `lora_name`, `vae_name`, `unet_name`...) | The model file isn't where the loader looks | `comfy --json nodes show <LoaderClass>`: `inputs[].choices` lists the files the server sees. Use the exact name from there, or tell the user what is missing. Never change permissions in `models/` |
| `workflow_not_api_format` / `conversion_error` | A UI-format file could not be converted | Use the API graph from `comfy_graph.py latest`, or have the user use File → Export (API) |
| `workflow_invalid_json` | Not valid JSON | Look at its first bytes: often an HTML error page saved as `.json` |
| `ws_timeout` / `ws_disconnected` | comfy-cli lost the connection mid-run; the server keeps the job | `comfy --json jobs status <id>`, or reattach: `comfy --json-stream jobs watch <id>` |
| timeout during `run` | The server was silent longer than `--timeout` (silence, not total time) | Check `jobs status <id>`; re-run with a larger `--timeout`, or submit without `--wait` and `jobs wait <id>` |
| `internal_error` | A comfy-cli bug (`details.exception`, `details.traceback`) | Re-read files it may have written, try another route once, don't loop. A `UnicodeEncodeError` here = `PYTHONUTF8=1` is missing |

**A job seems stuck:**

```bash
comfy --json jobs ls                      # still tracked? queue position?
comfy --json jobs status <prompt_id>      # what the server thinks
comfy --json-stream jobs watch <prompt_id>  # live events, one JSON line each
comfy --json jobs cancel <prompt_id>      # stop it (ask the user first)
```

| Symptom | Likely cause | Do |
|---|---|---|
| `pending`, `queue_position > 0` | Jobs ahead of it (maybe the user's own from the canvas) | Wait, or ask before cancelling theirs |
| `running`, no progress events | A long sampler step or model load, or a hung custom node | Wait one step's worth; then ask whether to cancel |
| `error` with no `error_message` | ComfyUI crashed mid-run | Read the server log (below) |

**Still unclear:** `comfy --json which` (which install was picked and why), `comfy --json env`,
`comfy --json system-stats` (VRAM: an out-of-memory error → `comfy free`, smaller size or
batch), and the server log: for an existing install `<install>/user/comfyui.log` (also shown
in the user's ComfyUI console window), for a comfy-cli-launched one `comfy logs --tail 200`.

## Showing results

Open a finished file in the user's VS Code window: `code -r "<path>"` (images show, audio
plays).

## Constraints

- Generations use the user's GPU: confirm before batches.
- comfy-cli can't see or drive the browser canvas; it runs graphs on the server.
- More commands: `comfy --help`, `comfy <command> --help`, `comfy --json discover` (the
  whole command tree and error codes).
