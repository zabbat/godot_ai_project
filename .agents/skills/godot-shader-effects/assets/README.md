# Shader examples

Full, working shaders found online, kept as reference implementations and starting points (frameworks) for new effects. Each file starts with a header comment with the following, followed by the original code:

- the source URL, author and license
- the shader type and how to set it up
- the techniques it uses
- known issues and mobile cost

All compiled and rendered without errors in **Godot 4.7.2, Mobile renderer** (2026-11-01).

These files live outside the Godot project, so Godot does not import them. To use one, copy it into the project (where it goes: the "Shaders and materials" section of the `godot-development` skill), keep the credit header, then adapt and simplify it.

Sorted from simpler to more complex:

| File | Type | Effect | Main techniques | License | Mobile cost |
|---|---|---|---|---|---|
| [screen_damage_flash.gdshader](screen_damage_flash.gdshader) | canvas_item | Red vignette flash on the screen edges when hit | square distance from centre, smoothstep feather, pow falloff, tweened `intensity` | MIT | low |
| [rain_and_snow_parallax.gdshader](rain_and_snow_parallax.gdshader) | canvas_item | Falling rain/snow streaks over the screen, near and far layers | procedural columns via `mod`, sin-hash per column, `fract` wrap, slant, trail vs. hard drop | MIT | low |
| [vertical_dissolve.gdshader](vertical_dissolve.gdshader) | spatial | Mesh dissolves bottom-to-top with a glowing wavy edge | local-space height mask, summed sine waves, scrolling noise texture, `discard`, emissive border | CC0 | low-medium |
| [stylized_fire_billboard.gdshader](stylized_fire_billboard.gdshader) | spatial | Flickering stylized flame on a camera-facing quad (torches, campfires); header has the companion cinder and smoke particle recipe | billboard keeping scale, offset towards the camera, procedural teardrop from UV, two layers of rising noise for sway and erosion, 3-colour gradient, per-instance noise seed from `NODE_POSITION_WORLD` | MIT (adapted) | low |
| [dissolve_perlin_3d.gdshader](dissolve_perlin_3d.gdshader) | spatial | PBR material that dissolves with organic noise and glowing edges | procedural 3D Perlin noise in local space, step threshold + edge band, alpha scissor, `group_uniforms`, normal/AO/roughness/parallax maps | MIT | medium-high (procedural noise per pixel) |
| [rain_drop_ripples_2d.gdshader](rain_drop_ripples_2d.gdshader) | canvas_item | Raindrop ripples on the ground, distorting what is below | hashed grid cells, expanding sine rings, numeric derivative to a pseudo-normal, screen texture distortion, world-anchored UVs | CC0 | high (25-iteration loop + 2 screen reads) |
| [toon_water_3d.gdshader](toon_water_3d.gdshader) | spatial | Wind Waker style toon water with waves and foam at intersections | vertex waves, procedural circle pattern, **depth texture linearised for Godot 4.3+ reverse-Z**, depth-based opacity and foam, screen texture background, value noise | CC0 | high |

Project example (not copied here, lives in the game): `godot/tower-v-1/levels/night_battle/dark_mist.gdshader`. It is a world-space gradient mist sheet with two drifting noise-texture layers. The cost is low (one quad, two texture reads).

## Which to start from

- **Screen overlays** (hit flash, vignette, rain on the camera): `screen_damage_flash`, `rain_and_snow_parallax`.
- **Showing/hiding a mesh** (spawn, death, teleport): `vertical_dissolve` (cheap, directional) or `dissolve_perlin_3d` (organic, heavier).
- **Weather on the ground** (rain ripples, puddles): the ripple maths in `rain_drop_ripples_2d`, ported to a 3D ground shader. Use world `xz` and perturb `NORMAL_MAP` instead of reading the screen, and use `MAX_RADIUS = 1` for phones.
- **Fire** (torches, braziers, campfires, burning debris): `stylized_fire_billboard` for the flame, with the cinder and smoke particle recipe in its header. Adapted rather than original code; the original GDQuest version (a mask texture on particle meshes, Godot 3 built-ins) is linked in the header.
- **Water, or anything reacting to where it meets other geometry** (foam, soft edges, force fields): the depth part of `toon_water_3d`.

## Adding a new example

1. Save the full code as `<effect>.gdshader` with the header comment (source, author, license, type, techniques, notes). Keep the code as-is; note any fix in the header.
2. Compile-test it in the project's Godot version and renderer (load it in a `ShaderMaterial` on a mesh or `ColorRect`, render a few frames, check the output for shader errors).
3. Add a row to the table above.
