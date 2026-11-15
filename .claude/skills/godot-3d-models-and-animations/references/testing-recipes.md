# Testing recipes for models, clips and props

Short recipes that proved themselves. They add to section 7 of `SKILL.md`. Put scratch scripts in the
scratchpad or a temp folder, never in the repo, except the temporary scene below (delete it after).

## Headless checks (no window)

Fast, run them first: `godot --headless --path <project> -s <script.gd>`.

- Print what a file really contains: bones, clips with lengths and loop modes, bone count per
  skeleton, whether a downloaded file has a mesh (section 1 of `SKILL.md`).
- `scripts/measure_clip.gd`: length, root travel and foot speed of a clip on a model.
- Compare two skeletons: rest rotation per bone name, parents, and after posing both at the same
  time the direction of each bone to its child (retargeting check, `retargeting.md`).
- Time: **let the model sit in the tree for one frame** (`await process_frame`) before reading its pose;
  `seek(t, true)` updates the pose only after that. A script in `_init()` that does not await reads a
  rest pose and prints zeros.
- Typing: `var x := some_array[0]` fails (Variant) with warnings as errors; write the type
  (`var x: Node = ...`).

## Screenshots (window needed)

Run without `--headless`: `godot --path <project> --resolution 450x800 -s shot.gd`, then
`get_viewport().get_texture().get_image().save_png(path)` after a few frames.

- **A `-s` script does not register the project's autoloads in time** for scripts that use them
  (`Identifier not found`). To run the real game scenes, make a **temporary scene** inside the
  project (`_tmp_x.tscn` with a script as its root, `res://_tmp_x.tscn`), run it with
  `godot --path <project> res://_tmp_x.tscn`, and delete it with its `.uid` files afterwards.
- **A unit viewer** (a screen that shows one model, turning) is the cheapest place to judge a model,
  a clip and a prop: set a pose (`play(clip)`, `seek(t, true)`, `pause()`), stop the turntable, hide
  the UI, rotate the turntable to the view you want.
- **Contact sheets**: render several variants or times, `img.convert(Image.FORMAT_RGBA8)` each (a sheet
  of another format stays empty after `blit_rect`), `resize`, and `blit_rect` them into one image.
  Compare front, outer side and three-quarter views, and a close-up on the part you are tuning
  (focus the camera on it with `look_at`).
- Frame the part, not its parent bone: a prop in a hand is judged on the fist.
- **The real game camera** (a 3D battle seen from above) can be moved in a test: set its position near
  the unit and `look_at` it; reset nothing, the test ends.

## Logging a real run

Drive the real scene with a temporary scene and log the state, not pictures: the unit's
`current_animation` and speed when they change; positions over time (a flee: distance from the start,
the direction, the time); the resource playing in the sound pool (name, volume, distance to the
camera). Speed a battle up with `Engine.time_scale` only when timing does not matter, and wait on
`create_timer(t, true, false, true)` (ignoring the pause, following the time scale) so waits follow it.

Typical questions this answers: does the clip play and return to idle, is the right clip chosen for
each state, does a state cut another short as intended, does the unit stay inside its bounds, does
the sound play at all and how loud is it.
