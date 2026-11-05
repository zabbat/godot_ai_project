---
name: godot-ai-architecture
description: How a Godot 4 game repository built with an AI agent is organized - the five areas (docs for people, prototype as the build spec, assets as source masters, tools with one folder per tool and its output, the Godot project), the project paths table that skills read, keeping every game fact on the AI side so the Godot project can be rebuilt, the asset map and the export/sync scripts (tools/godot-sync), starting a new project from the bundled template, and migrating an existing project to the current layout. Use when starting, scaffolding or initializing a new Godot game repo, adding or removing a tool, deciding where a file or fact belongs, adding an image, model or sound to the game, changing game data, editing the asset map, running the export or the sync check, or bringing an older project up to date.
---

# Godot AI architecture

How a Godot game repository built together with an AI agent is organized, and how its parts reach the Godot project. What happens *inside* the Godot project (scenes, Resources, signals, shaders, audio playback, testing exports) is the `godot-development` skill.

This skill is generic: the project's own paths are in the repository's root `AGENTS.md` ("Project paths") and `prototype/godot_structure.md` (folders and key files inside the Godot project, engine version, Godot executable). Look paths up there; never hard-code them in a skill.

| Task | Where |
|---|---|
| Start a new project in an empty folder | [references/new_project.md](references/new_project.md) |
| Bring an existing project up to the current layout | [references/migrate.md](references/migrate.md) |
| Scripts, starter files and the repo template | [assets/](assets/README.md) |

## Repository layout

```
<repo>/
  AGENTS.md          map of the repo, project paths, rules (every folder has its own AGENTS.md index)
  docs/              the game, for people: what it is and why. Design only, no engine details.
    game_design/     systems, features, story (+ standard audio.md, menus.md)
    characters/      optional: one bible per character, by type (game-character skill)
    style/           standard 2d_style.md, 3d_style.md
    references/      what we aim for (style images, mood clips); never used in the game
  prototype/         the build spec: how each feature is built in Godot, exact game data,
                     decided rules, file conventions
    godot_structure.md  map of the Godot project's folders and key files
    characters/      optional: one resource sheet per character (game-character skill)
    asset_map/       which source asset becomes which Godot file, and how (TOML)
  assets/            source resources (images, models, sounds) + where each came from.
                     Only resources and records: no usage, no code.
  tools/             one folder per tool (see "Tools")
    godot-sync/      export_assets.py, check_sync.py (generic, copies of this skill's scripts)
    <tool>/          a tool's settings, scripts, working files, output/ (git-ignored)
  godot/<project>/   the Godot project: code, scenes, data, and files exported from assets/
  export/            built game exports (APK...), written by Godot (git-ignored)
  downloads/         the user's inbox for raw downloads (git-ignored; not needed to build)
  .claude/           skills and agents; generic
```

- **Five working areas**: `docs/`, `prototype/`, `assets/`, `tools/` and `godot/`. `export/` and `downloads/` are git-ignored outputs and inboxes; `.claude/` is shared between projects.
- **`docs/` is for people, `prototype/` is for building.** A designer can read `docs/` without knowing Godot; `prototype/` holds what is needed to generate the game in Godot (how, exact numbers, where files go). Keep engine details out of `docs/`.
- Information flows one way: `docs/` → `prototype/` → `godot/`, and `downloads/` or a tool's `output/` → `assets/` → (asset map) → `godot/`. Godot never reads from the other areas, and nothing raw (zips, downloads, takes) goes inside the Godot project.
- **The Godot project must be rebuildable** from the other areas alone. Delete `godot/`, hand an agent the docs, prototype and assets, and it should produce a similar game (not identical code, the same game). Git history is for exact restores.
- **Keep `prototype/godot_structure.md` current**: update it in the same step as creating, moving, renaming or removing a folder or key file in the Godot project, and when refactoring the structure.
- **Characters (optional)**: a game whose design has characters (heroes, mobs, bosses, the player) keeps each one as a bible in `docs/characters/<type>/<name>/` and a resource sheet in `prototype/characters/<type>/<name>.md`; the `game-character` skill sets this up and keeps it. If those folders exist, a change to a character's files updates its sheet in the same step; a game without characters has neither folder.

### Project paths

The root `AGENTS.md` has a "Project paths" table: one row per path a skill needs (Godot project, docs, asset map, each tool's folder or output). Skills read it instead of assuming a layout, so they work in any project.

- **A tool skill that finds no row for its folder asks the user once** (suggesting `tools/<tool>/`, or `tools/<tool>/output/<kind>/` for generated takes), then adds the row. It never guesses silently and never writes to the repo root.
- Paths inside the Godot project are not in this table; they are in `prototype/godot_structure.md`.

## Tools

Every tool the project uses (a generator like ComfyUI or Chatterbox, an editor like Blender, the project's own scripts) has **one folder in `tools/`**. Adding a tool is adding its folder and its row in "Project paths"; removing it is deleting both.

```
tools/
  AGENTS.md          index: one line per tool
  godot-sync/        generic scripts: export_assets.py, check_sync.py
  comfy-ui/
    output/images/<xxx>-asset-<desc>/          image takes (comfy-ui-images skill)
    output/sound-effects/<xxx>-sound-<desc>/   sound takes (comfy-ui-sound-effects skill)
  chatterbox/        settings/ (locked uv env), voices/, output/ (chatterbox-text-to-speech skill)
  kokoro/            settings/ (locked uv env), output/ (voice design + take check; generate-voice-lines skill)
  blender/           config/ (sandbox settings), models/ (.blend work files) (blender-3d-modeling skill)
```

Rules:
- **`output/` is for pure generation**: every take a generator makes, git-ignored, never edited. A chosen take is **copied** to `assets/` with its record; the take stays where it is.
- **Working files keep their own names** (`models/` for `.blend` files): they are reopened and changed, not one-off takes.
- **Where a script goes**: a script for one tool lives in that tool's folder; a generic script gets its own folder (`tools/godot-sync/`). Never put code in `assets/`.
- A tool's own settings (`config/`, `settings/`) are committed; its outputs and caches (`output/`, `.venv/`, voice clips) are git-ignored. Each tool folder has an `AGENTS.md`, and `tools/AGENTS.md` lists every tool.
- Take file names are stable: an asset's record names the take it came from (`Image: <file>`, `Audio: <file>`), and `check_sync.py` finds takes by file name, so never rename takes.

## Standard docs

Every project has these, created at the start with a placeholder line ("No style defined yet." / "Not designed yet.") and filled as decisions are made. Other docs are specific to the game.

| Doc | Covers |
|---|---|
| `docs/game_design/audio.md` | Music, sound effects, voices: what plays when, principles, open questions |
| `docs/game_design/menus.md` | Screens and menus, how they connect, HUD |
| `docs/style/2d_style.md` | 2D art style (characters, UI, icons), prompt keywords for generation |
| `docs/style/3d_style.md` | 3D art style (characters, props, buildings, environment) |
| `prototype/godot_structure.md` | Map of the Godot project |
| `prototype/game_data.md` | Exact game data |

Read the matching style doc before generating, choosing or making art. If the part you need says "No style defined yet", ask the user before inventing one, then write the decision into the doc.

## Where an outside file goes

| It is... | Goes to |
|---|---|
| A raw download as received (vendor zip, original file from a site) | `downloads/` (git-ignored) |
| A take a tool generated | that tool's `output/` (the tool's skill puts it there) |
| Something that shows what we want, not used in the game ("draw like this", "sound like this") | `docs/references/`, listed with what it is a reference for and where it came from |
| A resource the game uses (extracted from a zip, a chosen take) | `assets/`, with its source or license recorded |

## Keeping the docs complete

Nothing about the game may exist only in Godot. Every fact has a home outside it:

| Kind of fact | Lives in | Example |
|---|---|---|
| Design: what a feature is, why, open questions | `docs/` | "Mobs come in packs that share a lane" |
| How a feature is built in Godot, rules the build decided | `prototype/<feature>.md` | "Heroes on the ground sortie to hunt ranged mobs" |
| Exact game data: stats, attacks, skills, waves, structure HP, combat constants, layout positions | `prototype/` (a game data doc) | "Knight: HP 160, Cleave cooldown 5, area 2.5" |
| File conventions: where files go, naming, linking | `prototype/` | "portrait at `entities/heroes/<name>/<name>_portrait.png`" |
| Godot folders and key files | `prototype/godot_structure.md` | "`resources/encounters/`: nights and their waves" |
| What we aim for (style, mood) | `docs/references/` + the design doc that links it | a drawing-style image |
| Which asset is used where, converted how, with which import settings | `prototype/asset_map/` | `knight_portrait.png` → profile `portrait` |
| Where a resource came from (prompt, seed, license) | next to it in `assets/` | `knight_portrait.md` |

Rules:
- **Same step, both sides.** When you change a value or behavior in Godot (a `.tres`, a scene property, a constant, a rule in a script), update the prototype doc in the same change, and the other way around. Doc first is better: write the change, then build it.
- **Write behavior, not just numbers.** Targeting rules, triggers, priorities, spawn patterns and fall-backs in scripts are game facts too; describe them in words.
- **Say where each value lives in Godot** (file and field), so the two can be checked against each other.
- Before finishing a task, ask: *could someone rebuild this from the docs?* If not, write down what's missing.

## Source assets and the asset map

`assets/` holds the **chosen masters** at the best quality available, organized by type, then subject:

```
assets/
  2d/portraits/<unit>/        <unit>_portrait.png, .md (prompt, seed), _workflow.json
  3d/third_party/<pack>/      files taken out of the pack (original names), License.txt
  3d/third_party/sources.md   download page and license of every pack (zips stay in downloads/)
  audio/music/                tracks + sources.md (tool, prompt, link)
  audio/sfx/<category>/<event>/
```

- Work in progress stays in the tool's `output/`; a take is copied to `assets/` once it is picked. Never edit a master; a change is a new take.
- `assets/` says nothing about usage: no Godot paths, `.import` files or game data. Sound masters go to `assets/audio/`, whichever tool made them.

`prototype/asset_map/` maps sources to Godot files: one TOML file per area (`portraits.toml`, `models.toml`, `music.toml`, `sounds.toml`), `profiles.toml` with the conversion recipes, and `settings.toml` with the repo paths (`assets`, `godot_project`, the tools' `outputs`). An area is a file, not a folder, unless it needs files of its own.

Each piece of information has one home:

| Information | Where |
|---|---|
| Which source goes to which target | the area's `.toml` entries |
| How it is converted (size, format, ffmpeg args, import settings) | a profile in `profiles.toml` |
| Why the profile has those values, what the asset must look like | the prototype doc named in the profile's `spec` |

```toml
[[asset]]
source = "2d/portraits/knight/knight_portrait.png"     # relative to assets/
target = "entities/heroes/knight/knight_portrait.png"  # relative to the Godot project
profile = "portrait"                                   # recipe in profiles.toml
import = { loop = true }                               # optional: non-default import settings
import_notes = "prototype/models.md#animations"        # optional: settings too complex to list
```

- A `source` ending in `/` maps a whole folder (`exclude = ["*.psd"]` to skip files).
- Profiles have a `kind`: `copy`, `image` (Pillow: `format`, `size` with cover crop, never upscale, metadata dropped) or `ffmpeg` (`format`, `args`), plus optional `import` and `spec`. Typical ones: `copy`; `portrait` (square PNG at a size with ~2x headroom over its on-screen size); `sfx` (trim silence, normalize loudness, mono 16-bit WAV); `loop` (Ogg, untrimmed, loop on); `music`.
- Masters stay at full quality; the game size lives only in the profile, so changing it is one edit and one export.
- **Exported files are generated: never edit them in Godot.** Change the master or the entry and export again.
- **Targets are stable**, so Godot's `.import` and `.uid` files next to them stay valid across exports.
- **Non-default import settings** (loop, compression, animation library, loop modes) go in the profile or entry (`import`, as `[params]` keys of the `.import` file) or a linked doc; otherwise a rebuild loses them.
- **Export with `tools/godot-sync/export_assets.py`** (generic: reads `settings.toml`, writes only targets that changed, `--dry-run` to preview, area names to limit). Run it after changing a master, an entry or a profile, then let Godot reimport. Run `--dry-run` first and check that only the expected targets change.

## The godot-sync scripts

The generic scripts live in this skill's [assets/](assets/README.md) folder and are **copied** into each project's `tools/godot-sync/`; the skill's version is the canonical one.

| Script | Does |
|---|---|
| `export_assets.py` | Exports `assets/` into Godot following the asset map: `copy`, `image` (resize to a profile size, e.g. 720 masters → 480 portraits), `ffmpeg` (trim, normalize, convert audio), and writes import settings. |
| `check_sync.py` | Reports, one short line per problem: targets not exported (and whether the master or the Godot copy is newer, by file time), takes in the tools' output folders newer than the take a master was chosen from (its `.md` names the take; `Rejected: ...` silences reviewed ones), Godot media no entry produces, masters no entry uses, Godot folders missing from `godot_structure.md`, `AGENTS.md` indexes missing files or with broken links, Godot data and code changed after the game data / structure docs. |

When a recurring job would cost many reads (checking dozens of files against a doc, converting a batch), add it to a script instead of doing it by hand each time. Write it generic (paths from `settings.toml`) so it can join this skill's `assets/`. Changing the skill's scripts is a skill change: ask the user first.

## Checklist when adding something new

1. Is it described outside Godot? Write the design in `docs/` and the exact values and behavior in `prototype/` first (or in the same step). Nothing may exist only in Godot.
2. Is it an image, model or sound? Generate or collect it with its tool (takes in the tool's `output/`), copy the chosen master to `assets/` with its provenance, add an entry to `prototype/asset_map/`, and export it with `tools/godot-sync/export_assets.py`; never drop files straight into Godot.
3. Is it a new tool? Give it a folder in `tools/` with an `AGENTS.md`, add it to `tools/AGENTS.md` and a row to "Project paths", git-ignore its `output/`, and add the output folder to `outputs` in `settings.toml`.
4. Did you add, move or remove a folder or key file in the Godot project? Update `prototype/godot_structure.md`.
5. Does it belong to a character (and the project has `prototype/characters/`)? Update the character's resource sheet (`game-character` skill).
6. Update the `AGENTS.md` index of every folder where you added, renamed or removed a file.
7. Run `tools/godot-sync/check_sync.py` (or the `godot-resource-manager` agent) and fix what it reports.

How to build the thing inside Godot is the `godot-development` skill's checklist.
