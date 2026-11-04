# Geometric output

## Endpoint conversion

Expected: endpoints on a curve, within the source uncertainty, convert to a
bounded edge and the associated face survives.

| Case | Reduced edge / face | Observed result | Investigation |
| --- | --- | --- | --- |
| 01 | [edge #815](actual-edges/case-01.stepdata), [face #811](actual-faces/case-01.stepdata) | NaN endpoint residuals; face dropped. | Degree-13 rational spline. `front()`/`back()` evaluate the outer knots, outside the valid interior support. The true support endpoints coincide with the declared closed-edge vertex. |
| 02 | [edge #333](actual-edges/case-02.stepdata), [face #320](actual-faces/case-02.stepdata) | NaN endpoint residuals; face dropped. | Same full-knot versus interior-support error as 01. |
| 05 | [edge #586](actual-edges/case-05.stepdata), [face #560](actual-faces/case-05.stepdata) | Endpoint residual 0.01536 mm; face dropped. | The vertex lies at parameter 0.9803400964, within 3.7e-11 mm of the spline (uncertainty 1e-7 mm). Conversion instead checks the untrimmed endpoint at parameter 1.0. |
| 06 | [edge #7163](actual-edges/case-06.stepdata), [bottom face #7209](actual-faces/case-06-clarified.stepdata) | `EdgeCurveConversionFailed`; 0/1 faces survive. | Circle endpoint residual reaches 0.00005012 inch, below the original 0.001-inch closure uncertainty. The one-face fixture retains the original inch unit and uncertainty context. |

`check-closed.py`, `check-splines.py` and `check-analytic.py` independently
evaluate these curves. The latter two use bounded numerical minimization.
`losses.py` verifies the importer diagnostics, including the single-face case
06 (which exits nonzero because no triangles remain).

The rejection comes from
[`EdgeCurve::parse_curve3d` / `reconciles_edge_curve`](../../vendor/truck/truck-stepio/src/in/mod.rs#L3933).
It checks `curve.front()`/`back()` under `ToleranceCtx::unscaled_legacy()`;
the original closure uncertainty is not passed to this predicate.

## Cone bounds

[Case 03](actual-faces/case-03.stepdata) contains one bounded conical face.
Its circular boundaries have axial coordinates
`2.672928114281` and `2.927071885719`: a span of `0.254143771438` source units.

Expected compiled axial maximum: approximately `2.927072`.
`bounds.rs` observes transformed Y bounds `[2.6729276, 20.182932]` before GPU
rendering. The resulting image is an elongated cone. Mesher cause unresolved.

## Triangle fans

Each fixture contains a cylinder/torus face pair. Expected: triangle deviation
stays within the importer's chord tolerance. Observed:

| Case / fixture | Model diameter | Chord tolerance | Maximum centroid deviation | Ratio |
| --- | ---: | ---: | ---: | ---: |
| [04-streak](actual-faces/case-04-streak.stepdata) | 6.715087 | 0.006715 | 0.746880 | 111x |
| [05-streak](actual-faces/case-05-streak.stepdata) | 14.915397 | 0.014915 | 2.436118 | 163x |
| [08](actual-faces/case-08.stepdata) | 19.339076 | 0.019339 | 2.374273 | 123x |
| [09](actual-faces/case-09.stepdata) | 6.732280 | 0.006732 | 0.364907 | 54x |
| [10](actual-faces/case-10.stepdata) | 3.721559 | 0.003722 | 1.081192 | 291x |

Measurements use geometry-local coordinates and distance to the nearer of both
infinite analytic surfaces. Every emitted vertex lies within 0.0001 source
units of a declared surface; triangle interiors do not. `tolerance.rs` repeats
the importer's diameter calculation (converted vertices plus five samples per
edge) and its default 0.001 linear deflection. These are CPU mesh defects.
For 08–10, each face rendered alone lacks the paired fan. Mesher cause unresolved.

## Other findings

- **02-parity:** [two-face fixture](actual-faces/case-02-parity.stepdata)
  independently drops face #119 with `ContradictoryDualParity`. Cause unresolved.
- **04 edge:** [edge #21](actual-edges/case-04.stepdata) has a numerical minimum
  endpoint distance of 0.00012566 mm, above its 0.000005 mm source uncertainty.
  [Face #17](actual-faces/case-04.stepdata) is rejected. This source mismatch
  does not explain the separate fan fixture.
- **07:** [hyperbola edge #573](actual-edges/case-07.stepdata) has a numerical
  nearest distance of approximately 0.00060485 mm against 0.00002 mm source
  uncertainty. [Face #559](actual-faces/case-07.stepdata) is dropped. The
  [control](actual-faces/case-07-control.stepdata) projects the implicated
  vertex onto the curve and restores the face.
- **06 controls:** [two-face fixture](actual-faces/case-06.stepdata) drops face
  #14018; its [endpoint-projected control](actual-faces/case-06-control.stepdata)
  restores that face. This control is distinct from bottom face #7209; the
  latter is also lost in the [two-face plane fixture](actual-faces/case-06-plane.stepdata).
- **11:** [two original STL facets](actual-faces/case-11.stldata) traverse their
  common edge in the same direction and have nearly opposite normals; one is
  back-face culled. [Reversing one facet and its normal](actual-faces/case-11-consistent.stldata)
  restores visibility. The original has 207/674 shared edges with matching
  directions. Input winding is inconsistent; no Look defect established.
