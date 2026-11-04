use look::{
    config::{MaterialMode, UpAxis},
    scene::compile_scene_for_render,
    timing::Timings,
};
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let r: f64 = args[2].parse().unwrap();
    let big: f64 = args[3].parse().unwrap();
    let small: f64 = args[4].parse().unwrap();
    let y0: f64 = args[5].parse().unwrap();
    let cx: f64 = args.get(6).map(|s| s.parse().unwrap()).unwrap_or(0.);
    let cy: f64 = args.get(7).map(|s| s.parse().unwrap()).unwrap_or(0.);
    let scene = compile_scene_for_render(
        std::path::Path::new(&args[1]),
        UpAxis::Z,
        MaterialMode::Source,
        &mut Timings::default(),
    )
    .expect("scene import");
    let mut max = (0.0, [0.; 3], [[0.; 3]; 3]);
    let mut n = 0;
    let mut bad = 0;
    let mut vertex_near = 0;
    let mut vertex_count = 0;
    let mut vertex_max: f64 = 0.;
    for g in &scene.geometries {
        for t in g.indices.chunks_exact(3) {
            let mut p = [0.; 3];
            let mut vertices = [[0.; 3]; 3];
            for (index, &i) in t.iter().enumerate() {
                let v = g.vertices[i as usize].position;
                vertices[index] = [v[0] as f64, v[1] as f64, v[2] as f64];
                let vr = (v[0] as f64 - cx).hypot(v[1] as f64 - cy);
                let vd = (vr - r)
                    .abs()
                    .min(((vr - big).hypot(v[2] as f64 - y0) - small).abs());
                vertex_count += 1;
                if vd < 1e-4 {
                    vertex_near += 1
                }
                vertex_max = vertex_max.max(vd);
                for j in 0..3 {
                    p[j] += v[j] as f64 / 3.0;
                }
            }
            let rho = (p[0] - cx).hypot(p[1] - cy);
            let cyl = (rho - r).abs();
            let tor = ((rho - big).hypot(p[2] - y0) - small).abs();
            let d = cyl.min(tor);
            n += 1;
            if d > 0.05 {
                bad += 1
            }
            if d > max.0 {
                max = (d, p, vertices);
            }
        }
    }
    println!("triangles {n}, centroids > 0.05 source units from either surface {bad}, maximum {:.6}, centroid {:?}",max.0,max.1);
    println!("vertices near source surfaces {vertex_near}/{vertex_count}, maximum vertex surface distance {vertex_max:.6}");
    println!("worst triangle vertices {:?}", max.2);
}
