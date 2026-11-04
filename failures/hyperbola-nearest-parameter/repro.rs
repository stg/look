//! Minimal standalone probe: the Python wrapper supplies a hard timeout.
use std::{env, fs, io::{self, Write}, str::FromStr};
use truck_stepio::r#in::{
    ruststep::{ast::DataSection, tables::EntityTable},
    EdgeCurveHolder, Table,
};

fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = env::args_os().skip(1);
    let fixture = args.next().ok_or("expected STEP data-section fixture")?;
    let edge_id: u64 = args.next().ok_or("expected edge entity ID")?
        .to_string_lossy().parse()?;
    if args.next().is_some() { return Err("unexpected argument".into()); }
    let text = fs::read_to_string(fixture)?;
    let section = DataSection::from_str(&text)?;
    let table = Table::from_data_section(&section);
    let edge = EntityTable::<EdgeCurveHolder>::get_owned(&table, edge_id)
        .map_err(|e| format!("could not resolve edge #{edge_id}: {e}"))?;
    println!("Resolved edge #{edge_id}; calling EdgeCurve::parse_curve3d");
    io::stdout().flush()?;
    edge.parse_curve3d().map_err(|e| format!("edge conversion failed: {e}"))?;
    println!("PASS: edge conversion returned");
    Ok(())
}
fn main() {
    if let Err(error) = run() { eprintln!("FAIL: {error}"); std::process::exit(1); }
}
