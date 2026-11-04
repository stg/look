# Hyperbola edge conversion does not terminate

Two STEP connector models reach the same failure in `EdgeCurve::parse_curve3d`,
before tessellation or GPU work. Each `.stepdata` file contains only the ten
geometry entities needed to resolve the affected edge. These are STEP data
sections for the probe, not complete models for the `look` CLI. Neither full
model is included here.

| Original model | Fixture | Edge | Hyperbola |
| --- | --- | ---: | ---: |
| `case-a` | `case-a.stepdata` | `#21027` | `#21030` |
| `case-b` | `case-b.stepdata` | `#21705` | `#21708` |

**Expected:** each valid edge conversion returns promptly and its curve covers
the declared endpoints. **Observed:** both calls exceeded a two-second limit;
the wrapper killed and reaped each probe. It does not run Look's renderer,
launch F3D, or read or modify the original model files.

## Reproduce on Windows

From the Look repository root, use the same Rust toolchain and build settings as
the checkout. This builds only `truck-stepio` and its dependencies, not the
full workspace or test suite. Python 3 is needed for the external watchdog.

```powershell
$messages = cargo build --release --locked -p truck-stepio --message-format=json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'truck-stepio build failed' }
$rlib = @($messages | Where-Object { $_.reason -eq 'compiler-artifact' -and $_.target.name -eq 'truck_stepio' } | ForEach-Object { $_.filenames } | Where-Object { $_ -like '*.rlib' })[-1]
if (-not $rlib) { throw 'truck_stepio rlib not found in Cargo output' }
python failures/hyperbola-nearest-parameter/run.py --rlib $rlib
```

If that rlib was built for MSVC with `+crt-static`, append `--static-crt` to
the Python command. The wrapper compiles only `repro.rs` into a temporary
directory, then runs each case in its own child. Each child has an external
hard timeout of two seconds by default; `--timeout` can change it but cannot
exceed ten seconds. A timeout or conversion error makes the wrapper exit 1.
The child is killed and waited for on timeout or interruption. Do not run the
compiled probe directly without an external timeout.

An already compiled `repro.rs` can be supplied with `--exe PATH` instead of
`--rlib`; this skips compilation but retains the same external timeouts.

## Evidence

Native stack samples of the isolated importer showed the CPU-hot thread in
`truck_stepio::in::EdgeCurve::parse_curve3d`, called from
`ShellHolder::to_compressed_shell_with_losses`. The hot path repeatedly called
`_hypot`; no tessellation or GPU operation had begun.

Both edges reference a hyperbola with semi-axes
`4.221322574161E-006`. For `#21027`, Truck's placement conversion produces
these local coordinates:

```text
start: (378344.16604005481349304, 378344.16603863245109096, 0)
end:   (379028.12966573756420985, 379028.12966431496897712, 0)
```

The existing `UnitHyperbola::search_parameter` returns approximately
`13.536706733082546` and `13.538512882622197` immediately for these points.
By contrast, direct calls to `matext4cgmath::solver::solve_quartic` with the
exact derived coefficients for either point each exceeded two seconds. Its
Newton refinement uses a `while` loop without an iteration or progress bound.
This matches the sampled call path; tiny rounding differences in the inputs can
change whether the solver stalls.

As a localization control only, temporary copies of each full model in which
just the listed hyperbola was replaced by a circle imported in under 0.4 seconds.
That replacement changes geometry and is **not a fix or workaround**.

The same nearest-parameter implementation also ranks quartic roots using
`self.subs(root)` even though the returned hyperbola parameter is `asinh(root)`.
That candidate-ranking issue is separate from the unbounded refinement and
needs its own correctness coverage.

A future fix should validate any fast-path candidate in model space and ensure
the fallback terminates without silently accepting an unconverged or
geometrically invalid result. Kernel changes must follow this repository's
packet / worker / verification process.
