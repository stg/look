use look::{
    config::{MaterialMode, UpAxis},
    scene::compile_scene_for_render,
    timing::Timings,
};
fn main() {
    let input = std::env::args_os().nth(1).expect("expected STEP input");
    let scene = compile_scene_for_render(
        std::path::Path::new(&input),
        UpAxis::Z,
        MaterialMode::Source,
        &mut Timings::default(),
    )
    .expect("scene import");
    println!(
        "bounds min {:?} max {:?}; geometry {}",
        scene.bounds.min,
        scene.bounds.max,
        scene.geometries.len()
    );
}
