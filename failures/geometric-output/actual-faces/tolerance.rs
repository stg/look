use std::{fs, str::FromStr};
use truck_meshalgo::prelude::*;
use truck_stepio::r#in::{ruststep::ast::DataSection, Table};
fn main() {
    let path = std::env::args().nth(1).expect("expected STEP input");
    let text = fs::read_to_string(path).expect("read");
    let start = text.find("DATA;").expect("DATA");
    let end = start + text[start..].find("ENDSEC;").expect("ENDSEC") + 7;
    let data = DataSection::from_str(&text[start..end]).expect("parse");
    let table = Table::from_data_section(&data);
    let mut bounds = BoundingBox::<Point3>::new();
    for (id, shell) in &table.shell {
        let (shell, _) = table
            .to_compressed_shell_with_losses(*id, shell)
            .expect("shell conversion");
        for p in shell.vertices {
            bounds.push(p)
        }
        for edge in &shell.edges {
            let (a, b) = edge.curve.range_tuple();
            for i in 0..=4 {
                bounds.push(edge.curve.subs(a + (b - a) * i as f64 / 4.));
            }
        }
    }
    let diameter = bounds.diameter();
    let tolerance = if diameter.is_finite() && diameter > 0. {
        (diameter * 0.001).max(1e-6)
    } else {
        1e-3
    };
    println!("model diameter {diameter:.9}, chord tolerance {tolerance:.9}");
}
