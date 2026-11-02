// SOURCE: "Rain Drop (floor effect)" by SEED (Kode Game Studio)
// https://godotshaders.com/shader/rain-drop-floor-effect/
// LICENSE: CC0 on the page (the header also says CC0 / MIT). Godot 4.x.
// TYPE: canvas_item on a ColorRect over the ground; a helper script on the page
//   (RainDropEffect.gd) sets world_top_left / rect_size_world from the Camera2D. Complexity: medium-high.
// TECHNIQUES: procedural raindrop ripples (port of a Shadertoy ripple effect): a grid of cells,
//   each with a hashed position and time offset (hash12/hash22), expanding rings from sin()
//   with smoothstep envelopes, a numeric derivative turned into a pseudo-normal, and that
//   normal used to distort the screen texture (hint_screen_texture). World-anchored UVs so the
//   ripples do not slide with the camera.
// NOTES: 2D only, but the ripple maths ports to a 3D ground shader (use world_pos.xz instead of
//   pixel_world_pos and perturb NORMAL_MAP instead of reading the screen). The nested loop runs
//   (2*MAX_RADIUS+1)^2 = 25 iterations per pixel plus two screen reads: expensive on phones;
//   lower MAX_RADIUS to 1 (9 iterations) for mobile.
// Code below is verbatim.

// Rain Drop Ground Effect Shader
// Author: Seed (Kode Game Studio)
// Engine: Godot 4.x
// License: CC0 / MIT - Free to use and modify

shader_type canvas_item;
render_mode unshaded, blend_mix;

// We capture what's already rendered to the screen
// so the rain effect blends with the ground texture
uniform sampler2D SCREEN_TEXTURE : hint_screen_texture, filter_linear_mipmap;

// World-space top-left position of the rect (set from script)
uniform vec2 world_top_left;
// World-space size of the rect (set from script)
uniform vec2 rect_size_world;

// Custom parameters
uniform float pattern_scale : hint_range(4.0, 64.0) = 16.0; // Rain drop density
uniform float offset_amount : hint_range(0.0, 0.2) = 0.05;  // Distortion amount
uniform float effect_mix    : hint_range(0.0, 1.0) = 0.55;  // Effect strength

// Constants for droplet simulation
const int   MAX_RADIUS  = 2;
const bool  DOUBLE_HASH = false;
const float HASHSCALE1  = 0.1031;
const vec3  HASHSCALE3  = vec3(0.1031, 0.1030, 0.0973);

// Random helpers for procedural animation
float hash12(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * HASHSCALE1);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}
vec2 hash22(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * HASHSCALE3);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.xx + p3.yz) * p3.zy);
}

void fragment(){
    // Convert UV to stable world coordinates (no camera-follow)
    vec2 pixel_world_pos = world_top_left + UV * rect_size_world;
    vec2 stable_uv = pixel_world_pos / pattern_scale;

    vec2 p0 = floor(stable_uv);
    vec2 circles = vec2(0.0);

    // Generate animated circular ripples
    for (int j = -MAX_RADIUS; j <= MAX_RADIUS; ++j){
        for (int i = -MAX_RADIUS; i <= MAX_RADIUS; ++i){
            vec2 pi  = p0 + vec2(float(i), float(j));
            vec2 hsh = DOUBLE_HASH ? hash22(pi) : pi;
            vec2 p   = pi + hash22(hsh);

            float t  = fract(0.3 * TIME + hash12(hsh));
            vec2  v  = p - stable_uv;
            float d  = length(v) - (float(MAX_RADIUS) + 1.0) * t;

            float h  = 1e-3;
            float d1 = d - h;
            float d2 = d + h;

            float p1 = sin(31.0 * d1) * smoothstep(-0.6, -0.3, d1) * smoothstep(0.0, -0.3, d1);
            float p2 = sin(31.0 * d2) * smoothstep(-0.6, -0.3, d2) * smoothstep(0.0, -0.3, d2);

            circles += 0.5 * normalize(v) * ((p2 - p1) / (2.0 * h) * pow(1.0 - t, 2.0));
        }
    }

    // Average the results
    circles /= float((MAX_RADIUS * 2 + 1) * (MAX_RADIUS * 2 + 1));

    // Build a pseudo-normal vector for distortion
    float len2 = clamp(dot(circles, circles), 0.0, 1.0);
    vec3 n = vec3(circles, sqrt(1.0 - len2));

    // Distortion offset
    vec2 shift = offset_amount * n.xy;

    // Sample screen before and after distortion
    vec3 base_color = texture(SCREEN_TEXTURE, SCREEN_UV).rgb;
    vec3 displaced  = texture(SCREEN_TEXTURE, SCREEN_UV - shift).rgb;

    // Blend the original and distorted image
    vec3 final_color  = mix(base_color, displaced, effect_mix);

    COLOR = vec4(final_color, 1.0);
}
