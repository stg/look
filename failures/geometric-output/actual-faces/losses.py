"""Check the documented source-face losses and endpoint-projected controls."""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from support import record, run, temporary

CASES = [
    ("01", 811, 2, "EdgeCurveConversionFailed"),
    ("02", 320, 2, "EdgeCurveConversionFailed"),
    ("02-parity", 119, 2, "ContradictoryDualParity"),
    ("04", 17, 2, "EdgeCurveConversionFailed"),
    ("05", 560, 2, "EdgeCurveConversionFailed"),
    ("06", 14018, 2, "EdgeCurveConversionFailed"),
    ("06-plane", 7209, 2, "EdgeCurveConversionFailed"),
    ("06-clarified", 7209, 1, "EdgeCurveConversionFailed"),
    ("07", 559, 2, "EdgeCurveConversionFailed"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--look-exe", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    if not 0 < args.timeout <= 10:
        parser.error("timeout must be in (0, 10]")
    executable = args.look_exe.resolve(strict=True)
    failed = False
    cases = CASES + [("06-control", None, 2, None), ("07-control", None, 2, None)]
    for name, face, count, reason in cases:
        fixture = HERE / ("case-" + name + ".stepdata")
        if name == "06-clarified":
            text = fixture.read_text(encoding="ascii")
            assert "CONVERSION_BASED_UNIT('INCH'" in text
            assert "GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT" in text
            assert re.search(r"UNCERTAINTY_MEASURE_WITH_UNIT\s*\(\s*LENGTH_MEASURE\s*\(\s*1\.E-3\s*\)", text)
        with temporary("look-face-loss-") as directory:
            source = Path(directory) / "case.step"
            shutil.copyfile(fixture, source)
            code, log, timed_out = run([executable, "inspect", source, "--up-axis", "z", "--json"], args.timeout)
        record("loss-" + name, log)
        records = []
        for line in log.splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        if face is None:
            ok = code == 0 and "warning:" not in log and "EdgeCurveConversionFailed" not in log
            finding = "both control faces survive"
        else:
            field = "terminal_reason" if reason == "ContradictoryDualParity" else "refusal_tag"
            matched = any(isinstance(r, dict) and r.get("source_face_id") == face and r.get(field) == reason
                          for r in records)
            if reason == "EdgeCurveConversionFailed":
                matched &= any(isinstance(r, dict) and r.get("source_face_id") == face
                               and r.get("declared_shell_faces") == count
                               and r.get("surviving_shell_faces") == count - 1 for r in records)
            ok = matched and (code != 0 if count == 1 else code == 0 and "warning: 1 of 2 STEP faces" in log)
            finding = f"face #{face}: {reason}; {count - 1}/{count} faces survive"
        ok = ok and not timed_out
        print("case-" + name, finding if ok else "UNEXPECTED (see log)", flush=True)
        failed |= not ok
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
