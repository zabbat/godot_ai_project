// SOURCE: "Rain and Snow with Parallax Effect" by Brian Smith (steampunkdemon.itch.io)
// https://godotshaders.com/?p=5326
// LICENSE: MIT. Written for Godot 4.
// TYPE: canvas_item on a ColorRect/TextureRect covering the screen. Complexity: medium.
// TECHNIQUES: procedural streaks with no textures: the screen is cut into vertical columns
//   (mod on UV.x, tilted by "slant"), each column gets a pseudo-random value rn from a
//   sin-hash, rn drives speed, length, width and transparency so near/far drops differ
//   (parallax). fract() wraps the drops vertically. Two output variants: blurred trail
//   (rain, smoothstep) and hard drop (snow, step).
// NOTES: 2D screen overlay only; does not live in the 3D scene (no torchlight, no ground hits).
//   Uses TIME, so it keeps falling while paused; the comments show how to use a time uniform.
// Code below is verbatim.

// Rain and Snow shader by Brian Smith (steampunkdemon.itch.io)
// MIT licence

shader_type canvas_item;

uniform float rain_amount = 200.0;
uniform float near_rain_length : hint_range(0.01, 1.0) = 0.2;
uniform float far_rain_length : hint_range(0.01, 1.0) = 0.1;
uniform float near_rain_width : hint_range(0.1, 1.0) = 1.0;
uniform float far_rain_width : hint_range(0.1, 1.0) = 0.5;
uniform float near_rain_transparency : hint_range(0.1, 1.0) = 1.0;
uniform float far_rain_transparency : hint_range(0.1, 1.0) = 0.5;
// Replace the below reference to source_color with hint_color if you are using a version of Godot before 4.
uniform vec4 rain_color : source_color = vec4(0.8, 0.8, 0.8, 1.0);
uniform float base_rain_speed : hint_range(0.1, 1.0) = 0.5;
uniform float additional_rain_speed : hint_range(0.1, 1.0) = 0.5;
uniform float slant : hint_range(-1.0, 1.0) = 0.2;

void fragment() {
// To control the rainfall from your program comment out the below line and add a new uniform above as:
// uniform float time = 10000.0;
// Then update the time uniform from your _physics_process function by adding delta. You can then pause the rainfall by not changing the time uniform.
	float time = 10000.0 + TIME;

// Uncomment the following line if you are applying the shader to a TextureRect and using a version of Godot before 4.
//	COLOR = texture(TEXTURE,UV);

	vec2 uv = vec2(0.0);
	float remainder = mod(UV.x - UV.y * slant, 1.0 / rain_amount);
	uv.x = (UV.x - UV.y * slant) - remainder;
	float rn = fract(sin(uv.x * rain_amount));
	uv.y = fract((UV.y + rn));

// Blurred trail. Works well for rain:
//	COLOR = mix(COLOR, rain_color, smoothstep(1.0 - (far_rain_length + (near_rain_length - far_rain_length) * rn), 1.0, fract(uv.y - time * (base_rain_speed + additional_rain_speed * rn))) * (far_rain_transparency + (near_rain_transparency - far_rain_transparency) * rn) * step(remainder * rain_amount, far_rain_width + (near_rain_width - far_rain_width) * rn));

// No trail. Works well for snow:
	COLOR = mix(COLOR, rain_color, step(1.0 - (far_rain_length + (near_rain_length - far_rain_length) * rn), fract(uv.y - time * (base_rain_speed + additional_rain_speed * rn))) * (far_rain_transparency + (near_rain_transparency - far_rain_transparency) * rn) * step(remainder * rain_amount, far_rain_width + (near_rain_width - far_rain_width) * rn));
}
