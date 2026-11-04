#!/usr/bin/env python3
"""Run each standalone geometry probe in a separately timed child process."""
import argparse
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
CASES = [("case-a.stepdata", "21027"), ("case-b.stepdata", "21705")]


def run_child(command, timeout):
    flags = 0x08000000 if os.name == "nt" else 0
    child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace",
                             creationflags=flags)
    try:
        try:
            out, err = child.communicate(timeout=timeout)
            return child.returncode, out, err, False
        except subprocess.TimeoutExpired:
            child.kill()
            out, err = child.communicate()
            return child.returncode, out, err, True
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--rlib", type=Path, help="truck_stepio rlib from the current Look release build")
    choices.add_argument("--exe", type=Path, help="use an already compiled copy of repro.rs")
    parser.add_argument("--timeout", type=float, default=2.0,
                        help="hard timeout per case in seconds (maximum 10; default 2)")
    parser.add_argument("--static-crt", action="store_true",
                        help="match an rlib built for MSVC with +crt-static")
    args = parser.parse_args()
    if not 0 < args.timeout <= 10:
        parser.error("--timeout must be greater than zero and at most 10 seconds")
    with tempfile.TemporaryDirectory(prefix="look-hyperbola-repro-") as temp:
        if args.exe:
            executable = args.exe.resolve(strict=True)
        else:
            rlib = args.rlib.resolve(strict=True)
            executable = Path(temp) / ("edge-probe.exe" if os.name == "nt" else "edge-probe")
            command = ["rustc", "--edition=2021", "-O", "-C", "lto=thin", "-C", "codegen-units=1"]
            features = []
            if args.static_crt:
                features.append("+crt-static")
            if platform.machine().lower() in ("amd64", "x86_64"):
                features.extend(["+avx", "+fma"])
            if features:
                command.extend(["-C", "target-feature=" + ",".join(features)])
            command += ["-L", "dependency=" + str(rlib.parent), "--extern",
                        "truck_stepio=" + str(rlib), str(HERE / "repro.rs"), "-o", str(executable)]
            print("Compiling only the standalone probe against", rlib, flush=True)
            code, out, err, timed_out = run_child(command, 180)
            if out:
                print(out, end="")
            if err:
                print(err, end="", file=sys.stderr)
            if timed_out or code:
                print("Probe compilation failed or timed out", file=sys.stderr)
                return 2
        failures = 0
        for filename, edge in CASES:
            print(f"\n{filename} (edge #{edge}):", flush=True)
            code, out, err, timed_out = run_child([str(executable), str(HERE / filename), edge], args.timeout)
            if out:
                print(out, end="")
            if err:
                print(err, end="", file=sys.stderr)
            if timed_out:
                failures += 1
                print(f"FAIL: exceeded {args.timeout:g} seconds; child was killed and reaped")
            elif code:
                failures += 1
                print(f"FAIL: child exited with code {code}")
        return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
