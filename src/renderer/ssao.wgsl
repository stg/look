// SPDX-License-Identifier: MIT OR Apache-2.0
struct Params {
    inverse_view_projection: mat4x4<f32>,
    camera: vec4<f32>,
    viewport: vec4<f32>,
    effect: vec4<f32>,
    background: vec4<f32>,
};
@group(0) @binding(0) var colour: texture_2d<f32>;
@group(0) @binding(1) var depth: DEPTH_TYPE;
@group(0) @binding(2) var<uniform> params: Params;

@vertex fn vertex_main(@builtin(vertex_index) index: u32) -> @builtin(position) vec4<f32> {
    let p = array<vec2<f32>, 3>(vec2(-1.0,-1.0), vec2(3.0,-1.0), vec2(-1.0,3.0));
    return vec4(p[index], 0.0, 1.0);
}
fn safe_pixel(p: vec2<i32>) -> vec2<i32> {
    return clamp(p, vec2<i32>(params.viewport.xy), vec2<i32>(params.viewport.xy + params.viewport.zw) - vec2(1));
}
fn depth_at(p: vec2<i32>) -> f32 {
    var result = 1.0;
    for (var sample_index = 0; sample_index < SAMPLE_COUNT; sample_index++) {
        result = min(result, textureLoad(depth, safe_pixel(p), sample_index));
    }
    return result;
}
fn position_at(p: vec2<i32>, z: f32) -> vec3<f32> {
    let uv = (vec2<f32>(p) + vec2(0.5) - params.viewport.xy) / params.viewport.zw;
    let point = params.inverse_view_projection * vec4(uv.x*2.0-1.0, 1.0-uv.y*2.0, z, 1.0);
    return point.xyz / point.w;
}
fn normal_at(pixel: vec2<i32>, p: vec3<f32>) -> vec3<f32> {
    let l = position_at(pixel+vec2(-1,0), depth_at(pixel+vec2(-1,0)));
    let r = position_at(pixel+vec2(1,0), depth_at(pixel+vec2(1,0)));
    let u = position_at(pixel+vec2(0,-1), depth_at(pixel+vec2(0,-1)));
    let d = position_at(pixel+vec2(0,1), depth_at(pixel+vec2(0,1)));
    let dx = select(p-l, r-p, distance(r,p) < distance(l,p));
    let dy = select(p-u, d-p, distance(d,p) < distance(u,p));
    let cross_normal = cross(dx, dy);
    if (dot(cross_normal,cross_normal) < 1e-20) { return vec3(0.0); }
    var normal = normalize(cross_normal);
    if (dot(normal, params.camera.xyz-p) < 0.0) { normal = -normal; }
    return normal;
}
EDGE_SHADER
fn occlusion_factor(pixel: vec2<i32>, z: f32) -> f32 {
    if (params.effect.x <= 0.0) { return 1.0; }
    let p = position_at(pixel, z);
    let normal = normal_at(pixel,p);
    let radius = params.effect.y;
    let world_radius = max(distance(position_at(pixel+vec2<i32>(i32(radius),0),z),p),1e-6);
    let angle_offset = fract(sin(dot(vec2<f32>(pixel),vec2(12.9898,78.233)))*43758.5453)*6.2831853;
    var occlusion = 0.0;
    for (var i = 0u; i < select(0u,32u,params.effect.x > 0.0); i++) {
        let fraction = (f32(i)+0.5)/32.0;
        let angle = f32(i)*2.3999632 + angle_offset;
        let offset = vec2<i32>(round(vec2(cos(angle),sin(angle))*sqrt(fraction)*radius));
        let sample_pixel = safe_pixel(pixel+offset);
        let sample_depth = depth_at(sample_pixel);
        if (sample_depth < 0.999999) {
            let delta = position_at(sample_pixel,sample_depth)-p;
            let distance_to_sample = length(delta);
            if (distance_to_sample > 1e-7) {
                let horizon = max(dot(normal,delta/distance_to_sample)-0.08,0.0);
                let falloff = 1.0-smoothstep(0.0,world_radius*1.5,distance_to_sample);
                occlusion += horizon*falloff;
            }
        }
    }
    return clamp(1.0-params.effect.x*occlusion/32.0*4.0,0.15,1.0);
}
@fragment fn fragment_main(@builtin(position) screen: vec4<f32>) -> @location(0) vec4<f32> {
    let pixel = vec2<i32>(screen.xy);
    let original = textureLoad(colour, pixel, 0);
    let z = depth_at(pixel);
    if (z >= 0.999999 || original.a <= 0.001) { return original; }
    let factor = occlusion_factor(pixel,z);
    let edge = edge_coverage(pixel);
    // Keep antialiased background coverage unchanged, including opaque white.
    let shaded = original.rgb*factor;
    let surface = max(shaded-params.background.rgb*(1.0-edge.y),vec3(0.0));
    return vec4(shaded-surface*edge.x*params.effect.z,original.a);
}
