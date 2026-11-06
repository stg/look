// SPDX-License-Identifier: MIT OR Apache-2.0
@group(0) @binding(3) var surface_normals: NORMAL_TYPE;

fn normal_sample(pixel: vec2<i32>, sample_index: i32) -> vec4<f32> {
    return textureLoad(surface_normals,safe_pixel(pixel),sample_index);
}
fn edge_difference(pixel: vec2<i32>, offset: vec2<i32>) -> f32 {
    let z=depth_at(pixel);
    let p=position_at(pixel,z);
    let q=position_at(pixel+offset,depth_at(pixel+offset));
    let scale=max(distance(position_at(pixel+vec2(1,0),z),p)*length(vec2<f32>(offset)),1e-7);
    var difference = 0.0;
    var covered = 0.0;
    for (var i=0; i<SAMPLE_COUNT; i++) {
        let a = normal_sample(pixel,i);
        let b = normal_sample(pixel+offset,i);
        if (a.w > 0.5) {
            covered += 1.0;
            if (b.w < 0.5) { difference += 1.0; }
            else {
                // 0 at 30 degrees and below, 1 at 60 degrees and above.
                let crease=1.0-smoothstep(0.5,0.8660254,clamp(dot(a.xyz,b.xyz),-1.0,1.0));
                // A real occluding contour can separate parallel planes. Test
                // distance from the plane, not raw depth or a part identifier.
                let separation=abs(dot(a.xyz,q-p))/scale;
                difference += max(crease,smoothstep(1.5,3.0,separation));
            }
        }
    }
    return difference / max(covered,1.0);
}
fn edge_coverage(pixel: vec2<i32>) -> vec2<f32> {
    var covered = 0.0;
    for (var i=0; i<SAMPLE_COUNT; i++) { covered += normal_sample(pixel,i).w; }
    covered /= f32(SAMPLE_COUNT);
    if (covered <= 0.0 || params.effect.z <= 0.0) { return vec2(0.0,covered); }
    let directions = array<vec2<i32>,8>(
        vec2(1,0),vec2(-1,0),vec2(0,1),vec2(0,-1),
        vec2(1,1),vec2(-1,1),vec2(1,-1),vec2(-1,-1));
    let radius = params.effect.w;
    var edge = 0.0;
    for (var step=1; step<=i32(ceil(radius+0.5)); step++) {
        for (var d=0u; d<8u; d++) {
            let offset = directions[d]*step;
            // Integrate a one-pixel footprint rather than rounding the width.
            let coverage = clamp(radius+1.0-length(vec2<f32>(offset)),0.0,1.0);
            if (coverage > 0.0) {
                edge = max(edge,edge_difference(pixel,offset)*coverage);
            }
        }
    }
    return vec2(edge,covered);
}
