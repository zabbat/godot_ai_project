// SOURCE: "Screen Damage Flash (Square Gradient Hit Effect)" by hltt
// https://godotshaders.com/shader/screen-damage-flash-square-gradient-hit-effect/
// LICENSE: MIT. Author tested on Godot 4.5.
// TYPE: canvas_item, full-screen ColorRect overlay. Complexity: medium-low.
// TECHNIQUES: square distance from the centre (max(abs(x), abs(y))), smoothstep feathering,
//   pow() for edge falloff, single "intensity" uniform animated by a tween.
// USAGE (from the page):
//   var tween = create_tween()
//   tween.tween_property(material, "shader_parameter/intensity", 1.0, 0.1)
//   tween.tween_property(material, "shader_parameter/intensity", 0.0, 0.2)
// Code below is verbatim.

shader_type canvas_item;

uniform vec4  flash_color : source_color = vec4(1.0, 0.0, 0.0, 1.0);
uniform float intensity   : hint_range(0.0, 1.0) = 0.0;
uniform float edge_power  : hint_range(0.1, 4.0) = 2.5;
uniform float inner_ratio : hint_range(0.0, 1.0) = 0.75;
uniform float feather     : hint_range(0.01, 1.0) = 0.4;

void fragment() {

    vec2 uv = UV * 2.0 - 1.0;


    float dist = max(abs(uv.x), abs(uv.y));


    float a = smoothstep(inner_ratio, inner_ratio + feather, dist);
    a = pow(a, edge_power);
    a *= intensity;

    COLOR = vec4(flash_color.rgb, a * flash_color.a);
}
