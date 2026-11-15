---
name: godot-shader-effects
description: How to create visual effects with shaders in Godot 4 (spatial, canvas_item and particle shaders) - first searching online for an existing shader to use as a framework, then adapting it, with techniques from simple to advanced (tint/flash, scrolling UVs, noise dissolve, world-space masks, vertex waves, depth and screen-texture effects, particle shaders), best practices, mobile performance, Godot 3 to 4 porting, common gotchas, and how to verify the result with screenshots. Use when creating or changing a shader, a ShaderMaterial, a visual effect (weather, mist, glow, dissolve, water, flashes, outlines), or when an effect cannot be done with StandardMaterial3D, ParticleProcessMaterial or the Environment alone.
---

# Godot shader effects

How to build visual effects with shaders in a Godot 4 project (written for the **Mobile renderer** and phone targets; the project's engine version, renderer and folder paths are in its root `AGENTS.md` and `prototype/godot_structure.md`). GDScript for game logic, Godot shading language (`.gdshader`) for shaders.

## Workflow

1. **Search online first.** Before writing a shader from scratch, look for an existing one that does the same or a similar effect and can serve as a framework (see below). Most effects (dissolve, water, outline, rain, fog, hit flash, toon shading) already exist in some form.
2. **Check whether a shader is needed at all.** `StandardMaterial3D` (emission, transparency, billboards, proximity/distance fade, UV scrolling via `uv1_offset` tweens), `ParticleProcessMaterial`, `Environment` (fog, glow, adjustments) and lights cover a lot. A built-in feature is cheaper to maintain than a custom shader.
3. **Start from a framework**, not a blank file: an online example, or a built-in material converted to a shader (right-click the material in the inspector, then **Convert to ShaderMaterial**; works for `StandardMaterial3D` and `ParticleProcessMaterial`). The converted code is long but shows exactly how Godot does it.
4. **Adapt and simplify** to the project: remove unused uniforms and features, expose tuning values as uniforms with hints, follow the style guide below.
5. **Verify with a screenshot** after each change (see "Verifying"), and check readability and frame rate (phone).
6. **Document** the effect in the relevant doc in `docs/` (what it does, file, tuning uniforms, what was tried and dropped).

### Searching for an existing shader

**Check the local examples first**: [assets/README.md](assets/README.md) lists full, compile-tested shaders found online (screen flash, screen rain/snow, vertical dissolve, Perlin dissolve, raindrop ripples, toon water with depth foam), each with source, license, techniques and mobile cost. If one is close to the effect, start from it. If you adapt a new online shader that is a good reference, add it there (steps at the end of that README).

Then look online, in order:

- **godotshaders.com**: the main community library. Search by effect name ("rain", "dissolve", "water", "outline"). Each page shows the code, the shader type, the license and the Godot version; **read the comments**, they often contain Godot 4 ports and fixes for newer versions.
- **Godot docs** (docs.godotengine.org, "Shaders" section): official tutorials (first 2D/3D shader, screen-reading shaders, advanced post-processing, converting GLSL).
- **Godot Asset Library** / store.godotengine.org: packaged effects (weather, juice/hit-flash packs).
- **GitHub** ("godot 4 <effect> shader") and **Shadertoy** (GLSL; needs porting, see "Porting").

Evaluate a candidate before using it:

| Check | Why |
|---|---|
| Godot version | Godot 3 shaders do not compile in 4 (renamed hints and built-ins). Shaders that read depth written before **4.3** may be wrong (reverse-Z change). |
| Renderer | Must work on **Mobile**. Anything that needs `hint_normal_roughness_texture`, SDFGI, volumetric fog etc. is Forward+ only. |
| Cost | Screen/depth texture reads, many texture samples, heavy procedural noise, full-screen passes and lots of transparent overdraw are expensive on phones. |
| License | Prefer CC0 or MIT. Note the source and license in a comment at the top of the adapted shader. Page images/assets are usually not covered by the code license. |
| Comments | Look for bug reports ("broken in 4.4", "only grey"), fixes, unused uniforms. |

Credit the source at the top of the file:

```glsl
// Based on "3D burn dissolve" by hancan (godotshaders.com, MIT), adapted for Godot 4.7 Mobile.
```

## Shader basics (quick reference)

- File: `.gdshader`, first line `shader_type spatial;` (3D), `canvas_item;` (2D/UI), `particles;` (GPU particle behaviour), `sky;` or `fog;`.
- `render_mode ...;` on the next line changes how Godot draws it.
- Processor functions: `vertex()` (per vertex, move geometry), `fragment()` (per pixel, set colour/material outputs), `light()` (per light per pixel; **does not run with vertex shading**, which the docs say is forced by default on mobile; check `rendering/shading/overrides/force_vertex_shading`).
- Pass data from `vertex()` to `fragment()` with `varying`.
- Godot strips code for outputs you never write, so unused features cost nothing.
- Assign with a `ShaderMaterial` (on a mesh's `material`, `material_override`, or a particle draw pass mesh).

Most useful **spatial render modes** for effects:

| Render mode | Use |
|---|---|
| `unshaded` | Ignore lighting (glows, mist, UI-like effects). Cheapest. |
| `blend_mix` / `blend_add` | Normal alpha blending / additive (fire, glow, sparks). |
| `depth_draw_never` | Transparent overlays that must not hide what is behind them. |
| `depth_test_disabled` | Draw over everything. |
| `cull_disabled` | Visible from both sides (flat sheets, cards, dissolving meshes). |
| `fog_disabled`, `shadows_disabled` | Keep fog off the effect / the effect does not receive shadows. |
| `world_vertex_coords` | `VERTEX`/`NORMAL` in world space (world-anchored effects). |

Most useful **built-ins**: `TIME`, `VERTEX`, `NORMAL`, `UV`, `COLOR`, `MODEL_MATRIX`, `INV_VIEW_MATRIX`, `VIEW`, `SCREEN_UV`, `FRAGCOORD`, `NODE_POSITION_WORLD`, `CAMERA_POSITION_WORLD`, `INSTANCE_CUSTOM` (particle data); outputs `ALBEDO`, `ALPHA`, `EMISSION` (can exceed 1.0 for glow), `ROUGHNESS`, `NORMAL_MAP`, `ALPHA_SCISSOR_THRESHOLD`. Writing `ALPHA` moves the material into the (more expensive, sorted) transparent pipeline.

## Techniques, from simple to advanced

Short snippets below. For complete, working versions of most of these techniques, see the shaders in [assets/](assets/README.md).

### 1. Tint / hit flash (canvas_item or spatial)

One uniform blended over the base colour, animated from GDScript with a tween.

```glsl
shader_type canvas_item;

uniform vec4 flash_color : source_color = vec4(1.0);
uniform float flash_amount : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec4 tex = texture(TEXTURE, UV);
	COLOR = vec4(mix(tex.rgb, flash_color.rgb, flash_amount), tex.a);
}
```

```gdscript
var tween := create_tween()
material.set_shader_parameter("flash_amount", 1.0)
tween.tween_method(func(v: float) -> void: material.set_shader_parameter("flash_amount", v), 1.0, 0.0, 0.15)
```

For many 3D units sharing one material, use an `instance uniform` (per-object value without duplicating the material; set with `set_instance_shader_parameter()` on the `GeometryInstance3D`).

### 2. Scrolling and animated UVs

Offset texture coordinates by `TIME` for flowing water, lava, clouds, energy fields. Sample the same texture twice at different scales and directions and combine them to hide repetition.

```glsl
vec2 uv1 = UV * 2.0 + vec2(0.05, 0.02) * TIME;
vec2 uv2 = UV * 3.4 - vec2(0.03, 0.04) * TIME;
float n = (texture(noise_tex, uv1).r + texture(noise_tex, uv2).r) * 0.5;
```

### 3. Noise threshold: dissolve with a burning edge

Compare a noise value with a threshold uniform; `smoothstep` gives a soft edge, and an emission band just above the threshold gives the glow.

```glsl
shader_type spatial;
render_mode cull_disabled;

uniform sampler2D dissolve_noise;
uniform float dissolve_amount : hint_range(0.0, 1.0) = 0.0;
uniform float burn_size : hint_range(0.0, 0.3) = 0.05;
uniform vec4 burn_color : source_color = vec4(1.0, 0.5, 0.1, 1.0);

void fragment() {
	float n = texture(dissolve_noise, UV).r;
	ALBEDO = vec3(0.6);
	EMISSION = burn_color.rgb * 3.0 * (1.0 - smoothstep(dissolve_amount, dissolve_amount + burn_size, n));
	ALPHA = step(dissolve_amount, n);
	ALPHA_SCISSOR_THRESHOLD = 0.5;
}
```

`ALPHA_SCISSOR_THRESHOLD` keeps it a cutout (no blending, no sorting problems). Procedural 3D noise on `VERTEX` instead of a texture avoids UV seams but costs more per pixel.

### 4. World-space masks and gradients (reference: dark mist)

Compute the world position in `vertex()` and fade or mask by world coordinates. Effects stay anchored to the level regardless of the mesh's UVs.

Example: a dark mist sheet, a flat transparent plane above the battlefield that fades from clear to almost black along world z, broken up by two layers of drifting noise. If the project has one, `prototype/godot_structure.md` lists where it is (e.g. a `dark_mist.gdshader` in the level's folder).

```glsl
varying vec3 world_pos;

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	float depth = smoothstep(clear_z, dark_z, world_pos.z);
	ALBEDO = mist_color.rgb;
	ALPHA = depth * max_alpha;
}
```

### 5. Vertex displacement (waves, wind, wobble)

Move `VERTEX` in `vertex()`; the mesh needs enough subdivisions. Displacement does not update normals: set `NORMAL` yourself or use a scrolling `NORMAL_MAP` so lighting is not flat.

```glsl
uniform float wave_height = 0.2;
uniform float wave_frequency = 1.5;
uniform float wave_speed = 2.0;

void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX.y += (sin(wp.x * wave_frequency + TIME * wave_speed)
			+ cos(wp.z * wave_frequency + TIME * wave_speed)) * 0.5 * wave_height;
}
```

Use world position (not local `VERTEX`) so neighbouring meshes line up. Use `COLOR` (vertex colour) or `UV.y` as a mask so, for example, only the top of grass sways.

### 6. Depth texture effects (soft edges, foam, intersection glow)

Read the scene depth behind a transparent surface to find where it meets other geometry. **Godot 4.3+ uses reverse-Z** (near = 1.0, far = 0.0): many older shaders get comparisons backwards. Use this linearization (Forward+ and Mobile):

```glsl
uniform sampler2D depth_texture : hint_depth_texture, filter_nearest;

void fragment() {
	float raw = texture(depth_texture, SCREEN_UV).x;
	vec4 view = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, raw, 1.0);
	view.xyz /= view.w;
	float scene_depth = -view.z;          // distance to what is behind
	float surface_depth = -VERTEX.z;      // VERTEX is in view space in fragment()
	float gap = scene_depth - surface_depth;
	float edge = 1.0 - smoothstep(0.0, 0.5, gap);  // 1 at the intersection
	ALBEDO = mix(vec3(0.1, 0.3, 0.6), vec3(1.0), edge);
	ALPHA = 0.8;
}
```

The depth texture only contains **opaque** objects. Reading it has a cost on phones; use it only when the effect needs it.

### 7. Screen texture effects (refraction, heat haze, distortion)

```glsl
uniform sampler2D screen_texture : hint_screen_texture, filter_linear_mipmap;

void fragment() {
	vec2 offset = (texture(noise_tex, UV + TIME * 0.05).rg - 0.5) * 0.02;
	ALBEDO = textureLod(screen_texture, SCREEN_UV + offset, 0.0).rgb;
}
```

In 3D the screen is captured after the opaque pass: transparent objects are not in it, and the material itself becomes transparent. A mipmap filter plus a higher LOD gives a cheap blur. Full-screen and screen-reading effects are among the most expensive things on mobile.

### 8. Particle shaders

`shader_type particles;` controls particle **behaviour** (`start()` once per particle, `process()` every frame; `TRANSFORM`, `VELOCITY`, `CUSTOM`, `LIFETIME`, `INDEX`, `RANDOM_SEED`, `ACTIVE`). The look comes from the draw-pass mesh's own material, which can read `INSTANCE_CUSTOM`. GPU particles only. Usually start from a `ParticleProcessMaterial` and only convert it to a shader when you need behaviour it cannot do. For weather (rain, snow), prefer a simple emitter whose lifetime ends at the flat ground over particle collision, and keep counts modest on phones.

## Best practices

- **Uniforms are the interface.** Every tuning value is a uniform with a sensible default and a hint:
  - `source_color` on every colour (and colour texture). Without it colours look washed out.
  - `hint_range(min, max[, step])` on numbers.
  - `hint_default_white` / `hint_default_black` / `hint_normal` on optional textures.
  - `filter_*` / `repeat_enable` on samplers.
  - Group them with `group_uniforms name;`, and document them with `/** ... */` comments, which show in the inspector.
- **Set parameters from GDScript** with `material.set_shader_parameter("name", value)`. Wrong types fail silently, so match the uniform's type exactly.
- **Per-object variation without new materials**: `instance uniform` (max ~16 per shader, no textures). **Project-wide values** (wind direction, storm intensity, lightning flash): `global uniform`, defined in Project Settings > Shader Globals first, set with `RenderingServer.global_shader_parameter_set()` (cheap to set, expensive to read back).
- **Share, don't copy**: one `.gdshader` used by many `ShaderMaterial`s. Put shared helper functions (noise, hashing, remapping) in a `.gdshaderinc` file and `#include` it. Where shader, material and effect files go, and how materials are shared, is defined in the **"Shaders and materials" section of the `godot-development` skill**. Follow it.
- **`const` over uniform** for values that never change. Use `#if` / `#define` to compile out optional features rather than runtime `if` on a uniform when the branch is heavy.
- **Noise**: a `NoiseTexture2D` (FastNoiseLite, `seamless = true`) is usually cheaper on phones than procedural noise in the shader. Keep it large and soft for atmospheric effects.
- **Style** (Godot shader style guide):
  - Order: `shader_type`, `render_mode`, file comment, uniforms, constants, varyings, functions, `vertex()`, `fragment()`, `light()`.
  - Formatting: tabs, `snake_case`, `CONSTANT_CASE`, always write `0.5` not `.5`, braces on the same line, lines under 100 characters.
  - Add a short comment at the top saying what the effect is and how it is used.

## Mobile performance

- **Transparency is the main cost.** Transparent surfaces are sorted, drawn back to front and overdraw each other. Keep them few and small on screen. Prefer `ALPHA_SCISSOR_THRESHOLD` (cutout) over blending when hard edges are fine.
- **`unshaded`** when the effect does not need lighting. Avoid `discard` (it disables the depth prepass for that surface).
- **Few texture samples**, simple maths, no loops over many iterations. Avoid screen/depth texture reads and full-screen passes unless they are the point of the effect.
- Precision qualifiers (`mediump`/`lowp`) can speed up fragment code but behave inconsistently across mobile drivers; leave them out unless profiling says otherwise.
- Uniform buffers are smaller on mobile (~16 KB); put big data in a texture.
- Add one effect at a time and check the frame rate on a real phone with a full wave on screen.

## Gotchas

- **`TIME` keeps running when the game is paused** (it follows `Engine.time_scale`). If an effect must freeze on pause, drive your own `time` uniform from `_process()`.
- **Transparent sorting vs. labels**: health bars and `Label3D`s here use `no_depth_test`. A large transparent sheet can still draw over them depending on sort order. Give overlays like the mist `render_priority = -1` so they draw first.
- **Colour banding** in dark, smooth gradients: enable `rendering/anti_aliasing/quality/use_debanding` (check `project.godot`; it may already be on).
- **Fine noise detail looks blocky/grainy** when magnified or contrast-boosted; use low frequency and 1 octave for mist, smoke and clouds.
- **Built-in depth fog is measured from the camera**, so with a steep top-down camera it draws rings on the ground and barely changes along the field. A world-space shader mask (technique 4) gives direct control.
- **No implicit casts** (`float(2)`, not `2`); **local variables are not zero-initialized**; compare floats with a tolerance; out-of-bounds array access or infinite loops can break rendering or hang the editor.
- Functions must be declared above where they are used.
- Global uniforms must exist in Project Settings before the shader is saved, or it fails to compile.

## Porting

**Godot 3 to 4** (common renames found in older examples):

| Godot 3 | Godot 4 |
|---|---|
| `hint_color`, `hint_albedo` | `source_color` |
| `hint_white`, `hint_black` | `hint_default_white`, `hint_default_black` |
| `SCREEN_TEXTURE`, `DEPTH_TEXTURE` built-ins | `uniform sampler2D x : hint_screen_texture;` / `hint_depth_texture` |
| `WORLD_MATRIX` | `MODEL_MATRIX` |
| `CAMERA_MATRIX`, `INV_CAMERA_MATRIX` | `INV_VIEW_MATRIX`, `VIEW_MATRIX` |
| `depth_draw_alpha_prepass` | `depth_prepass_alpha` |
| depth comparisons (pre-4.3) | reverse-Z: near = 1.0, use the linearization in technique 6 |

**Shadertoy / GLSL to Godot**: put the `mainImage` body into `fragment()` of a `canvas_item` shader; `fragColor` becomes `COLOR`, `fragCoord` becomes `FRAGCOORD.xy` (or use `UV`, whose y is flipped), `iTime` becomes `TIME`, `iResolution.xy` becomes `1.0 / SCREEN_PIXEL_SIZE`, `iChannel0` becomes `TEXTURE` or a `sampler2D` uniform; `iMouse`, `iFrame`, `iTimeDelta` need your own uniforms. Shadertoy shaders are often full-screen and heavy: check the cost before using one on mobile.

## Verifying

Render a screenshot from the real scene instead of guessing. Put a small `SceneTree` script in the session scratchpad (not in the project) and run it with the project's Godot (`config/features` in `project.godot` gives the version; the executable's path and the project folder are in `prototype/godot_structure.md`):

```gdscript
extends SceneTree
# Usage: godot --path <project> -s shot.gd -- <scene.tscn> <out.png> [wait_seconds]

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var scene = load(args[0]).instantiate()
	root.add_child(scene)
	await create_timer(float(args[2]) if args.size() > 2 else 5.0).timeout
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(args[1])
	quit()
```

```sh
"$GODOT" --path <godot project folder> -s "$SCRATCH/shot.gd" -- res://<path to scene>.tscn "$SCRATCH/out.png" 10
```

Do not use `--headless` (nothing is rendered). Grep the output for `error`/`warn` (shader compile errors appear there). Take shots at more than one moment for animated effects, view them, and compare before/after. A still image cannot show motion: tell the user when flicker or drift still needs checking in the running game.

## Checklist

1. Checked the local examples in `assets/`, then searched online for an existing shader (godotshaders.com, docs, asset library, GitHub); checked version, renderer, license, cost and comments.
2. A built-in material/feature would not do the job.
3. Adapted the framework: credited the source, removed unused parts, uniforms with hints and defaults.
4. Works on the Mobile renderer; transparency and texture reads kept low.
5. Paused-game behaviour, transparent sorting with labels/health bars, and readability checked.
6. Screenshot-verified, then documented in `docs/`.
