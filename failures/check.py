"""Build and run the reduced failure corpus against this Look checkout."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from support import ROOT, output_dir, run


def build_tools(static_crt):
    command = ["cargo", "build", "--release", "--locked", "-p", "look",
               "--lib", "--bin", "look", "--message-format=json"]
    result = subprocess.run(command, cwd=ROOT.parent, stdout=subprocess.PIPE,
                            text=True, encoding="utf-8", check=True)
    libraries = {}
    native = set()
    look = None
    for line in result.stdout.splitlines():
        message = json.loads(line)
        if message.get("reason") == "build-script-executed":
            native.update(message.get("linked_paths", []))
        if message.get("reason") != "compiler-artifact":
            continue
        name = message["target"]["name"]
        if name == "look" and message.get("executable"):
            look = message["executable"]
        for filename in message.get("filenames", []):
            if filename.endswith(".rlib"):
                libraries[name] = filename
    if not look:
        raise RuntimeError("Cargo did not report a Look executable")
    destination = output_dir() / "bin"
    destination.mkdir(parents=True, exist_ok=True)
    base = ["rustc", "--edition=2021", "-O", "-C", "lto=thin", "-C", "codegen-units=1"]
    features = ["+crt-static"] if static_crt else []
    if platform.machine().lower() in ("amd64", "x86_64"):
        features += ["+avx", "+fma"]
    if features:
        base += ["-C", "target-feature=" + ",".join(features)]
    for directory in sorted({str(Path(path).parent) for path in libraries.values()}):
        base += ["-L", "dependency=" + directory]
    for directory in sorted(native):
        base += ["-L", directory]
    probes = {
        "edge": ("hyperbola-nearest-parameter/repro.rs", ["truck_stepio"]),
        "bounds": ("geometric-output/actual-faces/bounds.rs", ["look"]),
        "triangles": ("geometric-output/actual-faces/triangles.rs", ["look"]),
        "tolerance": ("geometric-output/actual-faces/tolerance.rs", ["truck_stepio", "truck_meshalgo"]),
    }
    tools = {"look": look}
    for name, (source, dependencies) in probes.items():
        executable = destination / (name + (".exe" if os.name == "nt" else ""))
        command = list(base)
        for dependency in dependencies:
            rlib = Path(libraries[dependency])
            command += ["-L", "dependency=" + str(rlib.parent),
                        "--extern", dependency + "=" + str(rlib)]
        command += [str(ROOT / source), "-o", str(executable)]
        code, log, timed_out = run(command, 180)
        if timed_out or code:
            raise RuntimeError(f"Could not compile {name}:\n{log}")
        tools[name] = str(executable.resolve())
    (output_dir() / "tools.json").write_text(json.dumps(tools, indent=2), encoding="utf-8")
    return tools


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", type=Path, help="reuse a previously built out/tools.json")
    parser.add_argument("--static-crt", action="store_true", help="match an MSVC build using +crt-static")
    parser.add_argument("--render", action="store_true", help="also produce GPU-rendered examples")
    parser.add_argument("--numerical", action="store_true", help="also run independent NumPy/SciPy endpoint checks")
    args = parser.parse_args()
    tools = json.loads(args.tools.read_text(encoding="utf-8")) if args.tools else build_tools(args.static_crt)
    checks = [
        ("edge conversion", "geometric-output/actual-edges/run.py", ["--exe", tools["edge"]]),
        ("face losses", "geometric-output/actual-faces/losses.py", ["--look-exe", tools["look"]]),
        ("cone bounds", "geometric-output/actual-faces/bounds-check.py", ["--exe", tools["bounds"]]),
        ("triangle deviation", "geometric-output/actual-faces/triangles-check.py",
         ["--exe", tools["triangles"], "--tolerance-exe", tools["tolerance"]]),
        ("hyperbola hangs", "hyperbola-nearest-parameter/run.py", ["--exe", tools["edge"], "--expect-timeout"]),
    ]
    if args.numerical:
        checks += [(name, "geometric-output/actual-edges/" + name + ".py", [])
                   for name in ("check-closed", "check-splines", "check-analytic")]
    if args.render:
        checks.append(("rendered examples", "geometric-output/actual-faces/render.py",
                       ["--look-exe", tools["look"]]))
    failed = False
    for name, script, arguments in checks:
        print("\n" + name, flush=True)
        result = subprocess.run([sys.executable, str(ROOT / script), *arguments], cwd=ROOT.parent)
        failed |= result.returncode != 0
    print("\n" + ("Observations changed; inspect logs." if failed else "All documented observations reproduced."))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
