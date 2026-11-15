// SOURCE: adapted from "Stylized fire (3D)" by GDQuest, itself based on MinionsArt's stylized fire
// https://godotshaders.com/shader/stylized-fire-3d/
// LICENSE: MIT. ADAPTED (not the original code): Godot 3 built-ins ported to 4, one camera-facing
//   quad instead of a particle mesh, procedural teardrop instead of a mask texture, colour
//   gradient instead of vertex colour. Made for the tower project's torches
//   (godot/tower-v-1/common/effects/fire/flame.gdshader), Godot 4.7.2 Mobile, 2026-11-02.
// TYPE: spatial, on a QuadMesh (e.g. 0.4 x 0.7 m) with center_offset = (0, size.y / 2, 0), so
//   the quad's bottom edge sits at the node's origin and the flame grows up from it. Assign a
//   seamless NoiseTexture2D (FastNoiseLite, frequency ~0.02, 2 octaves, 128 px) to noise_texture.
//   Set render_priority = 1 on the material if it must draw over other transparent effects.
// TECHNIQUES: billboard that keeps the node's scale (the code a StandardMaterial3D generates with
//   "billboard keep scale"), billboard pushed towards the camera so the flame covers the mesh it
//   burns on, teardrop shape from UV (round base via sqrt, tapered tip via pow), two layers of
//   upward-scrolling noise for sway and erosion (licking tongues, more at the tip), three-colour
//   gradient driven by the eroded value, per-instance noise offset from NODE_POSITION_WORLD.
// NOTES: unshaded, blend_mix, no depth write; 2 texture reads per pixel, low cost (one small
//   quad). Uses TIME, so the flame keeps moving while the game is paused; drive your own time
//   uniform if it must freeze. With a steep camera a full billboard still looks right (the flame
//   rises "up the screen" like the upright units do).
// COMPANION PARTICLES (built-in materials, no custom shader), as used in the project's fire.tscn:
//   cinders: GPUParticles3D, 10 particles, lifetime 1.1, sphere emitter r 0.08, direction up,
//     spread 25, velocity 1-2.2, damping 0.6-1.2, turbulence (strength 1.5, influence 0.08-0.15),
//     color_ramp yellow > orange > transparent red; draw pass QuadMesh 0.06 with an unshaded,
//     additive, vertex-colour, particle-billboard StandardMaterial3D and a round soft texture
//     (radial GradientTexture2D, white > transparent). Without the texture they look like pixels.
//   smoke: GPUParticles3D, 6 particles, lifetime 2.2, starting 0.6 above the flame, velocity
//     0.5-0.9, random angle and angular velocity, scale_curve 0.4 > 1, color_ramp dark grey
//     alpha 0 > 0.45 > 0; same round texture, blend_mix. Light-grey smoke read as white blobs on
//     a dark night scene; 30 % dark smoke was invisible.
//   Leave local_coords off so cinders and smoke trail behind a moving torch.
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;

/** Seamless noise that scrolls up through the flame. */
uniform sampler2D noise_texture : repeat_enable, filter_linear;
group_uniforms colors;
/** Hot centre, body and outer edge of the flame. */
uniform vec4 core_color : source_color = vec4(1.0, 0.93, 0.6, 1.0);
uniform vec4 body_color : source_color = vec4(1.0, 0.55, 0.12, 1.0);
uniform vec4 edge_color : source_color = vec4(0.8, 0.14, 0.04, 1.0);
group_uniforms shape;
/** How fast the noise rises (flame cycles per second). */
uniform float rise_speed : hint_range(0.0, 4.0) = 1.3;
/** How far the flame sways sideways, mostly at the top. */
uniform float sway : hint_range(0.0, 0.5) = 0.18;
/** How much the noise eats into the flame; higher = more ragged tongues. */
uniform float erosion : hint_range(0.0, 1.5) = 0.6;
/** Width of the soft outline. */
uniform float edge_softness : hint_range(0.01, 0.3) = 0.06;
/** Metres the flame is drawn towards the camera, so it covers what it burns on instead of
being cut by it. */
uniform float toward_camera : hint_range(0.0, 0.5) = 0.35;

void vertex() {
	mat4 billboard = mat4(
			normalize(INV_VIEW_MATRIX[0]) * length(MODEL_MATRIX[0]),
			normalize(INV_VIEW_MATRIX[1]) * length(MODEL_MATRIX[1]),
			normalize(INV_VIEW_MATRIX[2]) * length(MODEL_MATRIX[2]),
			MODEL_MATRIX[3]);
	billboard[3].xyz += normalize(CAMERA_POSITION_WORLD - MODEL_MATRIX[3].xyz) * toward_camera;
	MODELVIEW_MATRIX = VIEW_MATRIX * billboard;
}

void fragment() {
	float h = 1.0 - UV.y;  // 0 at the base, 1 at the tip
	// Each flame gets its own part of the noise, so several flames don't burn in step.
	vec2 seed = NODE_POSITION_WORLD.xz * 0.731;
	float n1 = texture(noise_texture, UV * vec2(1.0, 0.8) + vec2(0.0, TIME * rise_speed) + seed).r;
	float n2 = texture(noise_texture, UV * vec2(1.7, 1.3) + vec2(0.37, TIME * rise_speed * 1.6) + seed).r;
	float n = n1 * 0.6 + n2 * 0.4;

	// Teardrop: round at the base, tapering to a tip; it sways with the noise near the top.
	float x = UV.x - 0.5 + (n - 0.5) * sway * h * 2.0;
	float width = 0.47 * sqrt(clamp(h / 0.22, 0.0, 1.0)) * pow(1.0 - h, 0.9);
	float shape = (width - abs(x)) / max(width, 0.001);

	// Noise eats the flame from the edges and more towards the tip: licking tongues.
	float flame = shape - (1.0 - n) * erosion * (0.35 + h);

	vec3 color = mix(edge_color.rgb, body_color.rgb, smoothstep(0.0, 0.3, flame));
	color = mix(color, core_color.rgb, smoothstep(0.35, 0.7, flame));
	ALBEDO = color;
	ALPHA = smoothstep(0.0, edge_softness, flame);
}
