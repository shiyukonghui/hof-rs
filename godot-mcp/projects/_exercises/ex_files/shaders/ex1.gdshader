shader_type canvas_item;
uniform float speed = 1.0;
uniform vec4 tint : source_color = vec4(1.0, 0.5, 0.5, 1.0);
void fragment() { COLOR = tint * 0.5; }
