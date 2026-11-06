// SPDX-License-Identifier: MIT OR Apache-2.0
struct CameraLighting {
    view_projection: mat4x4<f32>,
    light_directions: array<vec4<f32>, 5>,
    light_colors: array<vec4<f32>, 5>,
    base_color: vec4<f32>,
    camera_position: vec4<f32>,
    ambient: vec4<f32>,
};
@group(0) @binding(0) var<uniform> globals: CameraLighting;
struct Input {
    @location(0) position: vec3<f32>,
    @location(2) model_0: vec4<f32>,
    @location(3) model_1: vec4<f32>,
    @location(4) model_2: vec4<f32>,
    @location(5) model_3: vec4<f32>,
};
struct Output {
    @builtin(position) @invariant clip_position: vec4<f32>,
    @location(0) world_position: vec3<f32>,
};
@vertex fn vertex_main(input: Input) -> Output {
    let model = mat4x4<f32>(input.model_0,input.model_1,input.model_2,input.model_3);
    let world = model * vec4(input.position,1.0);
    var output: Output;
    output.clip_position = globals.view_projection * world;
    output.world_position = world.xyz;
    return output;
}
@fragment fn fragment_main(input: Output) -> @location(0) vec4<f32> {
    // Face normals, independent of material seams, vertex smoothing and normal maps.
    let geometric = cross(dpdx(input.world_position),dpdy(input.world_position));
    let scale = max(max(abs(geometric.x),abs(geometric.y)),abs(geometric.z));
    if (scale <= 0.0) { return vec4(0.0); }
    let n = normalize(geometric/scale);
    return vec4(select(-n,n,dot(n,globals.camera_position.xyz-input.world_position)>0.0),1.0);
}
