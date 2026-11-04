"""Render the reduced visual cases with the native Look CLI."""
import argparse
from pathlib import Path
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from support import output_dir, record, run, temporary

CASES = ["03", "04-streak", "05-streak", "06", "06-control", "07", "07-control",
         "08", "09", "10", "11", "11-consistent"]


def check_stl(path):
    raw = path.read_bytes()
    assert struct.unpack_from("<I", raw, 80)[0] == 2
    triangles = [struct.unpack_from("<12fH", raw, 84 + 50 * i) for i in range(2)]
    vertices = [[tuple(t[3 + j * 3:6 + j * 3]) for j in range(3)] for t in triangles]
    edges = [[(v[j], v[(j + 1) % 3]) for j in range(3)] for v in vertices]
    same = sum(a == c and b == d for a, b in edges[0] for c, d in edges[1])
    opposed = sum(a == d and b == c for a, b in edges[0] for c, d in edges[1])
    dot = sum(triangles[0][j] * triangles[1][j] for j in range(3))
    assert (opposed == 1 and same == 0 and dot > .99) if "consistent" in path.name else (
        same == 1 and opposed == 0 and dot < -.99)
    print(path.name, "same-directed edges", same, "opposed edges", opposed, "normal dot", round(dot, 6))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--look-exe", type=Path, required=True)
    parser.add_argument("--case", action="append", choices=CASES)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--no-edges", action="store_true")
    args = parser.parse_args()
    if not 0 < args.timeout <= 10:
        parser.error("timeout must be in (0, 10]")
    executable = args.look_exe.resolve(strict=True)
    failed = False
    for name in args.case or CASES:
        stl = name.startswith("11")
        fixture = HERE / ("case-" + name + (".stldata" if stl else ".stepdata"))
        if stl:
            check_stl(fixture)
        with temporary("look-render-") as directory:
            source = Path(directory) / ("case.stl" if stl else "case.step")
            shutil.copyfile(fixture, source)
            tag = "case-" + name + ("-no-edges" if args.no_edges else "")
            destination = output_dir() / (tag + ".png")
            destination.unlink(missing_ok=True)
            command = [executable, "render", source, "--view", "iso", "--camera", "orthographic",
                       "--resolution", "512x512", "--up-axis", "z", "--material-mode", "source",
                       "--ambient", "0.18", "--light-intensity", "1.2", "--background", "#ffffff00",
                       "--antialias", "--ambient-occlusion", "--output", destination]
            if not args.no_edges:
                command.append("--edges")
            code, log, timed_out = run(command, args.timeout)
            record(tag, log)
            ok = code == 0 and not timed_out and destination.is_file()
            print(tag, "rendered" if ok else "FAILED", flush=True)
            failed |= not ok
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
