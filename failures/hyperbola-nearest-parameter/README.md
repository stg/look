# Hyperbola edge conversion does not terminate

Expected: `EdgeCurve::parse_curve3d` returns a curve or an error.
Observed: both reduced inputs exceed a two-second external deadline, before
tessellation or GPU work.

| Fixture | Edge | Hyperbola | Entities |
| --- | ---: | ---: | ---: |
| [case-a.stepdata](case-a.stepdata) | #21027 | #21030 | 10 |
| [case-b.stepdata](case-b.stepdata) | #21705 | #21708 | 10 |

## Solver findings

The hot stack is `ShellHolder::to_compressed_shell_with_losses` →
`EdgeCurve::parse_curve3d` → hyperbola nearest-parameter search → quartic solve.
Both hyperbolas have semi-axes `4.221322574161E-006`.

For edge #21027, placement conversion produces unit-hyperbola coordinates:

```text
start = (378344.16604005481349304, 378344.16603863245109096, 0)
end   = (379028.12966573756420985, 379028.12966431496897712, 0)
```

`UnitHyperbola::search_parameter` returns approximately `13.536706733082546`
and `13.538512882622197` immediately. Quartic solves with coefficients derived
from either point exceed two seconds. In `matext4cgmath` 0.1.0,
`solver::solve_cubic` and `solver::pre_solve_quartic` both use unbounded Newton
`while` loops without stagnation checks; the quartic solver calls the cubic
solver. Which loop stalls has not been isolated. Small rounding changes affect
whether the solve terminates.

The caller
[`UnitHyperbola::search_nearest_parameter`](../../vendor/truck/truck-geometry/src/specifieds/hyperbola.rs)
also ignores the iteration limit and ranks roots with `self.subs(root)`,
then returns `asinh(root)`. That parameter mismatch is a separate correctness issue.

## Reproduce

```console
python failures/check.py
```

Or run only these two cases with an existing probe:

```console
python failures/hyperbola-nearest-parameter/run.py --exe PATH_TO_EDGE_PROBE --expect-timeout
```

`repro.rs` resolves only the selected edge and calls `parse_curve3d`.
The wrapper kills and reaps each timed-out child. The `.stepdata` fixtures are
data sections for this probe, not complete models for the Look CLI.
