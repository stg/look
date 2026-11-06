use look::{
    camera::prepare_camera,
    config::{
        CameraKind, LightingConfig, MaterialMode, NamedView, RenderConfig, UpAxis, ViewConfig,
    },
    renderer::{RenderedImage, Renderer, WgpuRenderer},
    scene::compile_scene,
    timing::Timings,
};

fn crease_darkening(before: &RenderedImage, after: &RenderedImage, x: i32) -> u64 {
    let mut total = 0;
    for y in 48..80 {
        for x in (x - 3)..=(x + 3) {
            let p = ((y * before.width as i32 + x) * 4) as usize;
            total += before.rgba[p].saturating_sub(after.rgba[p]) as u64;
        }
    }
    for (a, b) in before.rgba.chunks_exact(4).zip(after.rgba.chunks_exact(4)) {
        assert_eq!(a[3], b[3], "edges must preserve alpha");
        assert!((0..3).all(|i| b[i] <= a[i]), "edges must only darken");
    }
    total
}

#[test]
#[ignore = "requires a native GPU"]
fn crease_angles_fractional_widths_and_colour_seams() {
    let folder = tempfile::tempdir().unwrap();
    let lighting = LightingConfig {
        ambient: 1.0,
        intensity: 0.0,
        ..Default::default()
    };
    let base = RenderConfig {
        resolution: [128, 128],
        background: "#ffffff00".into(),
        base_color: "#b0b0b0".into(),
        material_mode: MaterialMode::Technical,
        antialias: true,
        edge_strength: 1.0,
        edge_width: 2.0,
        ..Default::default()
    };
    let mut renderer = WgpuRenderer::new().unwrap();
    let mut scores = Vec::new();
    for angle in [0.0_f32, 20.0, 30.0, 45.0, 60.0, 75.0] {
        let theta = angle.to_radians();
        let vertices = [
            [-1.0, -1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, 1.0, 0.0],
            [theta.cos(), -1.0, theta.sin()],
            [theta.cos(), 1.0, theta.sin()],
        ];
        let mut stl = String::from("solid fold\n");
        for triangle in [[0, 1, 2], [0, 2, 3], [1, 4, 5], [1, 5, 2]] {
            stl.push_str("facet normal 0 0 1\nouter loop\n");
            for i in triangle {
                let [x, y, z] = vertices[i];
                stl.push_str(&format!("vertex {x} {y} {z}\n"));
            }
            stl.push_str("endloop\nendfacet\n");
        }
        stl.push_str("endsolid fold\n");
        let model = folder.path().join(format!("fold-{angle}.stl"));
        std::fs::write(&model, stl).unwrap();
        let scene = compile_scene(&model, UpAxis::Y, &mut Timings::default()).unwrap();
        let camera = prepare_camera(
            &ViewConfig::named(NamedView::Front, CameraKind::Orthographic),
            &scene.bounds,
            base.resolution,
        );
        let hinge = camera.view_projection * glam::Vec4::new(0.0, 0.0, 0.0, 1.0);
        let x = ((hinge.x / hinge.w * 0.5 + 0.5) * 128.0).floor() as i32;
        let before = renderer
            .render_views(&scene, &[camera.clone()], &base, &lighting)
            .unwrap()
            .images
            .remove(0);
        let render = RenderConfig {
            edges: true,
            ..base.clone()
        };
        let after = renderer
            .render_views(&scene, &[camera.clone()], &render, &lighting)
            .unwrap()
            .images
            .remove(0);
        let score = crease_darkening(&before, &after, x);
        for point in [
            glam::Vec4::new(-0.5, 0.0, 0.0, 1.0),
            glam::Vec4::new(theta.cos() * 0.5, 0.0, theta.sin() * 0.5, 1.0),
        ] {
            let clip = camera.view_projection * point;
            let interior = ((clip.x / clip.w * 0.5 + 0.5) * 128.0).floor() as i32;
            assert_eq!(
                crease_darkening(&before, &after, interior),
                0,
                "flat face interiors must stay unlined"
            );
        }
        println!("crease {angle} degrees: {score}");
        scores.push(score);
        if angle == 60.0 {
            let mut last = 0;
            for width in [0.25, 0.5, 1.0, 1.5, 2.0] {
                let render = RenderConfig {
                    edge_width: width,
                    ..render.clone()
                };
                let after = renderer
                    .render_views(&scene, &[camera.clone()], &render, &lighting)
                    .unwrap()
                    .images
                    .remove(0);
                let score = crease_darkening(&before, &after, x);
                println!("width {width}: {score}");
                assert!(
                    score > last,
                    "fractional widths must change coverage continuously"
                );
                last = score;
            }
        }
        if angle == 0.0 {
            // Deliberately split the plane into independent coloured geometries.
            let mut seam = scene.clone();
            seam.source_hash = "coplanar-colour-seam".into();
            let mut left = seam.geometries[0].clone();
            let mut right = left.clone();
            left.indices.truncate(6);
            right.indices = right.indices[6..].to_vec();
            for (geometry, colour) in [
                (&mut left, [0.8, 0.1, 0.1, 1.0]),
                (&mut right, [0.1, 0.1, 0.8, 1.0]),
            ] {
                for vertex in geometry.source_attributes.as_mut().unwrap() {
                    vertex.color = colour;
                }
            }
            seam.geometries = vec![left, right];
            let mut instance = seam.instances[0].clone();
            instance.geometry = 1;
            seam.instances.push(instance);
            let render = RenderConfig {
                material_mode: MaterialMode::Source,
                ..base.clone()
            };
            let before = renderer
                .render_views(&seam, &[camera.clone()], &render, &lighting)
                .unwrap()
                .images
                .remove(0);
            let after = renderer
                .render_views(
                    &seam,
                    &[camera],
                    &RenderConfig {
                        edges: true,
                        ..render
                    },
                    &lighting,
                )
                .unwrap()
                .images
                .remove(0);
            assert_eq!(
                crease_darkening(&before, &after, x),
                0,
                "coplanar colour seams are not edges"
            );
        }
    }
    assert!(
        scores[0..3].iter().all(|&v| v == 0),
        "creases through 30 degrees must stay invisible"
    );
    assert!(
        scores[3] > 0 && scores[4] > scores[3],
        "45 degrees must fade toward 60 degrees"
    );
    assert!(
        scores[5] >= scores[4],
        "60 degrees must reach full strength"
    );
}
