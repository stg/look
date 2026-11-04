use crate::{camera::PreparedCamera, config::RenderConfig};
use bytemuck::{Pod, Zeroable};
use wgpu::util::DeviceExt;

#[repr(C)]
#[derive(Clone, Copy, Pod, Zeroable)]
struct Params {
    inverse_view_projection: [[f32; 4]; 4],
    camera: [f32; 4],
    viewport: [f32; 4],
    effect: [f32; 4],
}
pub(super) struct Ssao {
    layout: wgpu::BindGroupLayout,
    pipeline: wgpu::RenderPipeline,
}
impl Ssao {
    pub(super) fn new(device: &wgpu::Device, samples: u32) -> Self {
        let layout = device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
            label: Some("StepThumbnail SSAO layout"),
            entries: &[
                wgpu::BindGroupLayoutEntry {
                    binding: 0,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Float { filterable: false },
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: false,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 1,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Texture {
                        sample_type: wgpu::TextureSampleType::Depth,
                        view_dimension: wgpu::TextureViewDimension::D2,
                        multisampled: samples > 1,
                    },
                    count: None,
                },
                wgpu::BindGroupLayoutEntry {
                    binding: 2,
                    visibility: wgpu::ShaderStages::FRAGMENT,
                    ty: wgpu::BindingType::Buffer {
                        ty: wgpu::BufferBindingType::Uniform,
                        has_dynamic_offset: false,
                        min_binding_size: None,
                    },
                    count: None,
                },
            ],
        });
        let source = include_str!("ssao.wgsl")
            .replace(
                "DEPTH_TYPE",
                if samples > 1 {
                    "texture_depth_multisampled_2d"
                } else {
                    "texture_depth_2d"
                },
            )
            .replace("SAMPLE_COUNT", &samples.to_string());
        let shader = device.create_shader_module(wgpu::ShaderModuleDescriptor {
            label: Some("StepThumbnail SSAO shader"),
            source: wgpu::ShaderSource::Wgsl(source.into()),
        });
        let pipeline_layout = device.create_pipeline_layout(&wgpu::PipelineLayoutDescriptor {
            label: Some("StepThumbnail SSAO pipeline layout"),
            bind_group_layouts: &[Some(&layout)],
            immediate_size: 0,
        });
        let pipeline = device.create_render_pipeline(&wgpu::RenderPipelineDescriptor {
            label: Some("StepThumbnail SSAO pipeline"),
            layout: Some(&pipeline_layout),
            vertex: wgpu::VertexState {
                module: &shader,
                entry_point: Some("vertex_main"),
                compilation_options: Default::default(),
                buffers: &[],
            },
            primitive: Default::default(),
            depth_stencil: None,
            multisample: Default::default(),
            fragment: Some(wgpu::FragmentState {
                module: &shader,
                entry_point: Some("fragment_main"),
                compilation_options: Default::default(),
                targets: &[Some(wgpu::ColorTargetState {
                    format: wgpu::TextureFormat::Rgba8UnormSrgb,
                    blend: None,
                    write_mask: wgpu::ColorWrites::ALL,
                })],
            }),
            multiview_mask: None,
            cache: None,
        });
        Self { layout, pipeline }
    }
    pub(super) fn apply(
        &self,
        device: &wgpu::Device,
        encoder: &mut wgpu::CommandEncoder,
        source: &wgpu::Texture,
        depth: &wgpu::TextureView,
        cameras: &[PreparedCamera],
        render: &RenderConfig,
        columns: u32,
    ) -> wgpu::Texture {
        let size = source.size();
        let target = device.create_texture(&wgpu::TextureDescriptor {
            label: Some("StepThumbnail SSAO output"),
            size,
            mip_level_count: 1,
            sample_count: 1,
            dimension: wgpu::TextureDimension::D2,
            format: wgpu::TextureFormat::Rgba8UnormSrgb,
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC,
            view_formats: &[],
        });
        let colour = source.create_view(&Default::default());
        let target_view = target.create_view(&Default::default());
        let background = crate::config::parse_hex_color(&render.background).unwrap_or([0.0; 4]);
        let uniforms = cameras
            .iter()
            .enumerate()
            .map(|(index, camera)| {
                let viewport = [
                    (index as u32 % columns * render.resolution[0]) as f32,
                    (index as u32 / columns * render.resolution[1]) as f32,
                    render.resolution[0] as f32,
                    render.resolution[1] as f32,
                ];
                let params = Params {
                    inverse_view_projection: camera.view_projection.inverse().to_cols_array_2d(),
                    camera: [
                        camera.position[0],
                        camera.position[1],
                        camera.position[2],
                        1.0,
                    ],
                    viewport,
                    effect: [
                        if render.ambient_occlusion {
                            render.ao_strength
                        } else {
                            0.0
                        },
                        render.ao_radius,
                        if render.edges {
                            render.edge_strength
                        } else {
                            0.0
                        },
                        render.edge_width,
                    ],
                };
                device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
                    label: Some("SSAO parameters"),
                    contents: bytemuck::bytes_of(&params),
                    usage: wgpu::BufferUsages::UNIFORM,
                })
            })
            .collect::<Vec<_>>();
        let groups = uniforms
            .iter()
            .map(|uniform| {
                device.create_bind_group(&wgpu::BindGroupDescriptor {
                    label: Some("SSAO inputs"),
                    layout: &self.layout,
                    entries: &[
                        wgpu::BindGroupEntry {
                            binding: 0,
                            resource: wgpu::BindingResource::TextureView(&colour),
                        },
                        wgpu::BindGroupEntry {
                            binding: 1,
                            resource: wgpu::BindingResource::TextureView(depth),
                        },
                        wgpu::BindGroupEntry {
                            binding: 2,
                            resource: uniform.as_entire_binding(),
                        },
                    ],
                })
            })
            .collect::<Vec<_>>();
        let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
            label: Some("StepThumbnail GPU ambient occlusion"),
            color_attachments: &[Some(wgpu::RenderPassColorAttachment {
                view: &target_view,
                depth_slice: None,
                resolve_target: None,
                ops: wgpu::Operations {
                    load: wgpu::LoadOp::Clear(wgpu::Color {
                        r: (background[0] * background[3]) as f64,
                        g: (background[1] * background[3]) as f64,
                        b: (background[2] * background[3]) as f64,
                        a: background[3] as f64,
                    }),
                    store: wgpu::StoreOp::Store,
                },
            })],
            depth_stencil_attachment: None,
            timestamp_writes: None,
            occlusion_query_set: None,
            multiview_mask: None,
        });
        pass.set_pipeline(&self.pipeline);
        for (i, group) in groups.iter().enumerate() {
            let x = i as u32 % columns * render.resolution[0];
            let y = i as u32 / columns * render.resolution[1];
            pass.set_viewport(
                x as f32,
                y as f32,
                render.resolution[0] as f32,
                render.resolution[1] as f32,
                0.0,
                1.0,
            );
            pass.set_scissor_rect(x, y, render.resolution[0], render.resolution[1]);
            pass.set_bind_group(0, group, &[]);
            pass.draw(0..3, 0..1);
        }
        drop(pass);
        target
    }
}
// SPDX-License-Identifier: MIT OR Apache-2.0
