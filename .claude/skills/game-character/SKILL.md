---
name: game-character
description: Keep a game's characters (heroes, mobs, bosses, the player, NPCs) in one fixed structure - a short character bible for people (by default Appearance, Voice and Background; a type can drop or add sections) in docs/characters/<type>/<name>/, and a resource sheet in prototype/characters/<type>/<name>.md listing every resource the character needs in the game (3D model, face portrait, half portrait, voice reference, greeting line, death sound...) with its status, master, take and Godot file. Each character type has an AGENTS.md saying which bible sections and which resources its characters have (mobs may have no voice lines). Interviews the user ("what does he look like?", "what 2D graphics does a character need?"), generates the missing resources through the tool skills, and marks resources outdated when the design changes. Optional: only for games that have characters. Use when the user says "set up characters", "create a new character X", "add a hero / mob / enemy / boss / NPC", "update X's appearance / voice / background", "generate X" or "generate all assets for X", "what is missing for X", "add a resource to all mobs", or renames or removes a character.
---

# Game characters

A game whose design has characters keeps each of them in one fixed shape, so the AI can ask the right questions, find every file of a character, and generate what is missing. **Optional**: a game without characters (a puzzle game) never sets this up, and nothing here applies until the folders exist.

The repo conventions around it (docs vs prototype, `assets/`, tools, asset map, export) are the `godot-ai-architecture` skill. This skill only adds the character structure on top. The tool skills make the files: `comfy-ui-images` (portraits, cut-outs), `comfy-ui-sound-effects` (creature sounds, deaths), `generate-voice-lines` (voice reference and spoken lines; it runs Kokoro and `chatterbox-text-to-speech`), `blender-3d-modeling` and `glb-3d-model-and-animations` (models). Building the character in Godot is `godot-development`.

| File | What |
|---|---|
| [references/interview.md](references/interview.md) | The questions to ask, per bible section and per resource. **Read before creating or updating a character.** |
| [references/resources.md](references/resources.md) | The default resource set: what each resource is, what it depends on, which tool makes it, default paths, tips. **Read before generating.** |
| [assets/](assets/) | Templates for the folders and files below (`{{TYPE}}`, `{{NAME}}`, `{{DISPLAY_NAME}}`, `{{DATE}}` placeholders). |

## Structure

```
docs/characters/                         for people: who the characters are
  AGENTS.md                              index: the types, every character, one line each
  <type>/                                heroes/, mobs/, bosses/, player/ ... (snake_case, plural)
    AGENTS.md                            the type: which bible sections it uses + its characters
    <name>/                              snake_case, the same name everywhere (zombie, orc_warrior)
      <name>.md                          the character bible
      <name>_ref_<desc>.png              optional design references (concept, outfit, pose)
                                         (the voice reference clip is a resource: assets/, see "Voice reference")
prototype/characters/                    for building: what each character needs in the game
  AGENTS.md                              index + the status values
  <type>/
    AGENTS.md                            the type's resource set: every resource its characters have,
                                         with spec, tool, master path and Godot path patterns
    <name>.md                            the resource sheet: one row per resource, with status
```

- **Bible = design** (`docs/`, no engine details): a short, simple doc. Default sections: **Appearance** (age, sex, species, build, hair colour, clothing...; ends with one line of prompt keywords), **Voice** (how it talks: pitch, energy, mood, favourite words; its greeting; its voice reference) and **Background** (personality and where it comes from: "moody", "a knight from a royal family"). A type can drop a section or add one (Story role, Behaviour). **Sheet = build** (`prototype/`): which files exist, where, and how they get into Godot. The split follows the architecture skill's docs/prototype rule.
- **Types decide what a character has.** The type's two `AGENTS.md` files are the contract: `docs/characters/<type>/AGENTS.md` lists the bible sections (a silent mob has no Voice), `prototype/characters/<type>/AGENTS.md` the resource set (a mob has no greeting line). A new character copies its type's lists. A game with only one kind of character still has one type folder.
- **Masters stay in `assets/`, organized by type of file** (portraits with portraits, sounds with sounds), named after the character. The sheet ties them together; never make `assets/characters/`.
- **Exact game data** (HP, damage, skills) stays in `prototype/game_data.md`; the sheet links to the character's section there. Systems shared by all heroes or mobs stay in their design docs (`docs/game_design/heroes.md`); the bible is about one individual or kind.
- The same `<name>` is used for the docs folder, the sheet, the master files and the Godot folder.

### The resource sheet

```markdown
# Zombie - resources

Type: [mobs](AGENTS.md) · Bible: [zombie.md](../../../docs/characters/mobs/zombie/zombie.md) ·
Game data: [game_data.md#zombie](../../game_data.md#zombie) · Godot: `entities/mobs/zombie/`

| Resource | Status | Master (`assets/`) | Take | In Godot | Notes |
|---|---|---|---|---|---|
| Face portrait | in game | `2d/portraits/zombie/zombie_portrait.png` | `006-asset-1-zombie-portrait.png` | `entities/mobs/zombie/zombie_portrait.png` | |
| Half portrait | missing | | | | |
| 3D model | in game | `3d/third_party/kaykit/Skeleton_Minion.glb` | (vendor) | `entities/mobs/zombie/zombie_visual.tscn` | vendor model |
| Death sound | outdated | `audio/sfx/characters/zombie_death/` | `012-sound-2-zombie-death.wav` | ... | appearance changed 2026-11-04 |
```

**Status** values (the sheet's whole state; keep them exact so they can be counted):

| Status | Means |
|---|---|
| `missing` | needed, nothing made yet |
| `takes` | takes exist in a tool's `output/`, none chosen yet (name them in Notes) |
| `chosen` | master copied to `assets/` with its record, not in the game yet |
| `in game` | mapped in the asset map, exported, and used by the Godot files |
| `outdated` | exists, but the bible part it depends on changed after it was made (say what in Notes) |
| `not needed` | this character skips a resource its type has (say why in Notes) |

The sheet can have rows its type does not have (a boss with an extra laugh); the type's list is the minimum, not a maximum.

## Set up characters

When the user says "set up characters", or asks to create a character and `docs/characters/` does not exist. Also run from the architecture skill's new-project steps when the user says the game has characters.

1. Read the root `AGENTS.md`, `docs/game_design/` (game idea, any heroes/enemies docs), `docs/style/` and `assets/AGENTS.md`.
2. **Ask for the types** (suggest them from the design: "heroes, mobs, bosses, the player character?").
3. **For each type, agree its bible sections and resource set** (interview.md "Types"): show the defaults from [references/resources.md](references/resources.md) and ask what to drop or add ("Does a mob speak? Does it need a half portrait? Does the player need in-game 2D graphics?"). Agree the master and Godot path patterns, following what `assets/AGENTS.md` and `prototype/godot_structure.md` already use.
4. Create the folders and `AGENTS.md` files from [assets/](assets/) and fill the placeholders.
5. Register it:
   - root `AGENTS.md`: mention the characters in the `docs/` and `prototype/` rows of the layout table, and add "Project paths" rows `Character bibles | docs/characters/` and `Character resource sheets | prototype/characters/`;
   - a line for `characters/` in `docs/AGENTS.md` and `prototype/AGENTS.md`;
   - `assets/AGENTS.md`: if its layout has no place for a resource the set needs (spoken lines: `audio/voice/<name>/`), add it.
6. If the game already has characters (in design docs, `game_data.md`, Godot), offer to bring them in: one bible and one sheet each, with rows filled from what exists (`in game` for what Godot already uses). Move the per-character text out of the old docs and leave a link; the old doc keeps what is shared by all.

## Create a new character

"Create a new character X", "add a mob X".

1. Find the type (ask if unclear; offer to make a new type if none fits, with the "Types" questions).
2. Create `docs/characters/<type>/<name>/<name>.md` from the bible template with **only the type's sections**, and `prototype/characters/<type>/<name>.md` from the sheet template with **one `missing` row per resource of the type**.
3. **Interview** ([references/interview.md](references/interview.md)): go section by section, a few questions at a time, each with concrete suggestions drawn from the game design and the style docs. Write each answer into the bible as soon as it is given. The user may say "you decide": then write a proposal, mark it `(proposed)` and say so; may say "later": leave the section's placeholder and mark it **(open)**. Do not invent silently.
4. Ask which resources this character skips (`not needed`) or adds.
5. Add the character to both type `AGENTS.md` lists and, if the game data needs it, say that `prototype/game_data.md` needs its values (ask for them or leave them open).
6. Ask: "Generate its resources now?" If yes, go to "Generate".

## Update a character

"Update X's appearance", "X's voice should be deeper", "change X's background".

1. Read the bible and the sheet. Change only the sections asked for; keep the user's other text. If the change is vague, ask the interview questions for that section first.
2. If the look changed, rewrite the Appearance prompt keywords to match, and show them.
3. **Find the resources that depend on the changed section** (each resource's "Depends on" in the type's resource set; [references/resources.md](references/resources.md) has the defaults). Set their status to `outdated` with the date and reason in Notes (`2026-11-04: armour changed to rusted plate`). Resources still `missing` stay `missing`.
4. Tell the user which resources are outdated and **ask which to regenerate now** (one multi-select question); the rest stay `outdated` until later. Never regenerate without asking: every take costs time.
5. If the change touches game data or behavior (a mob becomes faster), that is `prototype/game_data.md` and the Godot build, not this skill: say so.

## Generate

"Generate X", "generate all assets for X", "make the missing portraits", or after create/update.

1. Read the bible, the sheet, the type's resource set, the style docs, and [references/resources.md](references/resources.md).
2. **List the plan before starting**: every row that is `missing` or `outdated` (or only those asked for), with the tool and a one-line prompt summary for each. Ask the user to confirm or trim it. Check the tools that are needed are ready (ComfyUI server running, Kokoro and Chatterbox installed for voices: the tool skills say how).
3. **Order** so later resources can build on earlier ones: face portrait (fixes the look) → half portrait (same face and outfit, the face portrait as reference) → 2D in-game graphics → 3D model (portraits as reference) → voice reference → spoken lines (with the voice reference) → sounds.
4. **For each resource, use its tool skill** (resources.md names it), with prompts built from the bible (the Appearance prompt keywords and the style doc's keywords) and the spec from the type's resource set. Takes go to the tool's `output/` as that skill names them. Set the row to `takes` and name the takes in Notes.
5. **The user chooses.** Show the takes; never choose a master yourself unless asked to. Then follow the architecture skill: copy the chosen take to the master path with its record, add or update the asset map entry, export. Set the row to `chosen` (and fill Master and Take), or `in game` once Godot uses it (fill In Godot). If the file is new to Godot (no field links it yet), say so: linking it is Godot work.
6. Replacing an outdated resource: the new take replaces the master **at the same path** (Godot targets stay stable); its record names the new take, and the old take goes in the record's `Rejected:` line.
7. Report the sheet's status at the end (what is in game, chosen, still missing).

## Other commands

| Request | Do |
|---|---|
| "What is missing for X?" / "status of the characters" | Read the sheets and list each character's rows that are not `in game` / `not needed`, grouped by status. |
| "All mobs need a hurt sound" (change a type) | Add the resource to the type's resource set (spec, tool, paths, depends on), then add a `missing` row to every sheet of that type. Removing one: ask first, then mark the rows `not needed`. |
| "Rename X to Y" | Rename the docs folder, its files, the sheet and the index lines. Masters, asset-map targets and Godot files are renamed only if the user agrees (it is a Godot change too: `godot-development`, then export and check sync). Take files are never renamed. |
| "Remove X" | Ask first. Remove the bible and sheet and the index lines; say which masters, asset map entries and Godot files belonged to it and ask whether to remove those too. |
| "Change X's type" | Move both files, then compare the two types' lists: add `missing` rows for the new type's resources, ask about rows the new type does not have. |

## Voice reference

A character that speaks gets one **voice reference**: a calm 6-8 s clean clip that Chatterbox clones for every line, so all its lines sound like one person. **Making it and every spoken line is the `generate-voice-lines` skill**: it designs the voice with Kokoro from the bible's "Voice" section (or uses a recording the user owns or a licensed clip), and generates lines by kind (greeting, spell call, battle cry...). Hand voice resources to that skill; give it the bible and the sheet.

The clip is a resource, not documentation: its master lives in **`assets/audio/voice/<name>/<name>_voice_reference.wav`** with a `.md` record (the Kokoro recipe, or the source and rights), committed, never in `docs/`. It has no asset map entry (it is not in the game). Chatterbox uses a git-ignored copy at `<cbx>/voices/<name>.wav`, registered in `<cbx>/AGENTS.md`. The bible's Voice section links the master and names the voice blend in one line. A recording of a real person is committed only if the user has the rights and says so; otherwise it stays only in `<cbx>/voices/` and the record says where it came from.

## Rules

- **Only when the folders exist.** No `docs/characters/` → no character rules; offer "set up characters" only when the user talks about characters.
- **The type's lists are the contract**: never add a section or resource to one character silently when the type should have it; ask whether it is for the type or this character only.
- **Ask, don't invent**: unknown parts are asked for, proposed `(proposed)` or left **(open)**.
- **The bible changes first**, then the resources: a resource is made from the bible, so an appearance change goes into the bible before any image is generated.
- **Keep the sheet current in the same step** as any change to the character's files (a new take, a chosen master, an export, a Godot link).
- Update the `AGENTS.md` indexes (both type lists, `docs/characters/AGENTS.md`, `prototype/characters/AGENTS.md`) whenever a character or type is added, renamed or removed.
- Templates and this skill are shared between projects: ask the user before changing them. The project's character files can be changed freely.

## Outside a game repo

In a project with no `prototype/` (a music video), only the bible part applies: `docs/characters/<name>/<name>.md` (or the project's own place, asked once), used to keep a character consistent across images and clips.
