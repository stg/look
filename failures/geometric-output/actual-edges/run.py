"""Reproduce the six reduced source-edge conversion refusals."""
import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from support import record, run

CASES = [(1, 815, "(NaN, NaN)"), (2, 333, "(NaN, NaN)"),
         (4, 21, "1.257e-4"), (5, 586, "1.536e-2"),
         (6, 7163, "5.012e-5"), (7, 573, "8.598e-4")]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=2)
    args = parser.parse_args()
    if not 0 < args.timeout <= 10:
        parser.error("timeout must be in (0, 10]")
    executable = args.exe.resolve(strict=True)
    failed = False
    for number, edge, expected in CASES:
        name = f"case-{number:02d}"
        code, log, timed_out = run([executable, HERE / (name + ".stepdata"), edge], args.timeout)
        record("edge-" + name, log)
        ok = code != 0 and not timed_out and expected in log
        print(name, "reproduced" if ok else "UNEXPECTED", log.strip(), flush=True)
        failed |= not ok
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
