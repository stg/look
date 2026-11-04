# Reduced failure cases

Reproduced with Look `daa3577`, Rust 1.96.1, release build, Windows x64.
The fixtures contain only the implicated geometry and its dependencies.

| Finding | Cases | Evidence |
| --- | --- | --- |
| Spline endpoint conversion rejects vertices on the source curve | 01, 02, 05 | [Endpoint checks and face losses](geometric-output/README.md#endpoint-conversion) |
| Edge rejected despite original closure uncertainty | 06 | [One-face reproduction with inch units](geometric-output/README.md#endpoint-conversion) |
| Bounded cone produces an oversized mesh | 03 | [Source and compiled bounds](geometric-output/README.md#cone-bounds) |
| Large triangle fans violate chord tolerance | 04, 05, 08, 09, 10 | [Measured surface deviation](geometric-output/README.md#triangle-fans) |
| Independent parity failure | 02-parity | [Lost face diagnostic](geometric-output/README.md#other-findings) |
| Source edge/winding issues; no importer bug established for these symptoms | 04 edge, 07, 11 | [Source checks and controls](geometric-output/README.md#other-findings) |
| Hyperbola conversion fails to terminate | A, B | [Minimal edges and solver findings](hyperbola-nearest-parameter/README.md) |

From the checkout root, with Rust/Cargo and Python 3:

```console
python failures/check.py
python failures/check.py --tools failures/out/tools.json --render
```

The first command builds matching probes and runs CPU checks. The second adds
GPU-rendered examples. Each probe has a 2–10 second deadline; exit 0 means the
documented observations were reproduced. Logs and images go to `failures/out/`.
For an MSVC build configured with `+crt-static`, add `--static-crt` when building
the probes. Add `--numerical` for the independent endpoint calculations
(NumPy/SciPy required).
