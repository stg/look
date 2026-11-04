# Failure corpus verification checklist

These are reduced, neutral fixtures. Full original models, their filenames,
cached captures, and full-model diagnostic controls remain under the ignored
`private/` directory and are not included in the shareable corpus. No F3D is
used. The results below were verified on Windows with the local Look build.

From the Look checkout root, substitute paths for the built tools:

```powershell
# E: source-edge diagnostics, external two-second deadline.
python failures/geometric-output/actual-edges/run.py --exe PATH_TO_EDGE_PROBE.exe
# F: actual source-face loss and projected-control checks, five-second deadline.
python failures/geometric-output/actual-faces/losses.py --look-exe PATH_TO_LOOK.exe
# R: reduced visual cases, external ten-second deadline, no full originals.
python failures/geometric-output/actual-faces/render.py --look-exe PATH_TO_LOOK.exe
# T: surface deviation, source-coordinate agreement and actual model tolerance.
python failures/geometric-output/actual-faces/triangles-check.py --exe PATH_TO_TRIANGLES_PROBE.exe --tolerance-exe PATH_TO_TOLERANCE_PROBE.exe
# B: oversized bounded-cone mesh; external three-second deadline.
python failures/geometric-output/actual-faces/bounds-check.py --exe PATH_TO_BOUNDS_PROBE.exe
# C: the user-identified case 06 face, original unit and uncertainty context.
python failures/geometric-output/actual-faces/clarified.py --look-exe PATH_TO_LOOK.exe
# H: the two separate hyperbola hang reproducers. Exit 1 is expected on the
# current version because both children hit their deadlines and are reaped.
python failures/hyperbola-nearest-parameter/run.py --exe PATH_TO_EDGE_PROBE.exe
```

[Geometric reproduction instructions](geometric-output/README.md) describe
how to compile the standalone edge, bounds, triangle and tolerance probes
against matching rlibs. `R` supports `--case 09` or `--case 11-consistent` to
run individual fixtures; `F`, `E` and `T` run their small related sets.

| Case | Actual reduced input | Expected invariant | Current observed result and verified command |
| --- | --- | --- | --- |
| 01 | [edge](geometric-output/actual-edges/case-01.stepdata), [two faces](geometric-output/actual-faces/case-01.stepdata) | Finite closed-spline support endpoints coincide with the edge vertex; its face survives. | `E`, `F`: full-knot endpoint evaluation yields NaNs and the affected face is lost. Independent `check-closed.py` verifies support endpoints. |
| 02 | [edge](geometric-output/actual-edges/case-02.stepdata), [conversion loss](geometric-output/actual-faces/case-02.stepdata), [parity loss](geometric-output/actual-faces/case-02-parity.stepdata) | Closed edge is finite and both source faces survive. | `E`, `F`: NaN conversion refusal; the separate face independently fails `ContradictoryDualParity`. `check-closed.py` verifies the edge's interior support. |
| 03 | [one conical face](geometric-output/actual-faces/case-03.stepdata) | The bounded face stays between source axial coordinates 2.672928 and 2.927072. | `R`, `B`: tall cone renders; compiled transformed maximum reaches 20.182932. |
| 04 | [edge](geometric-output/actual-edges/case-04.stepdata), [loss pair](geometric-output/actual-faces/case-04.stepdata), [fan pair](geometric-output/actual-faces/case-04-streak.stepdata) | A surviving face and its tessellation respect their source geometry and chord tolerance. | `E`, `F`, `R`, `T`: face loss plus fan; mesh centroid deviation reaches 111× tolerance. Numerical spline search places the edge vertex outside stated source uncertainty, so do not assume that edge is valid. |
| 05 | [edge](geometric-output/actual-edges/case-05.stepdata), [loss pair](geometric-output/actual-faces/case-05.stepdata), [fan pair](geometric-output/actual-faces/case-05-streak.stepdata) | Endpoint on the source spline must reconcile; fan triangles respect source surfaces and tolerance. | `E`, `F`, `R`, `T`: face loss and fan (163× tolerance). `check-splines.py` locates the endpoint on the spline within uncertainty; converter instead checks the untrimmed end. |
| 06 | [user-identified bottom face](geometric-output/actual-faces/case-06-clarified.stepdata), [edge](geometric-output/actual-edges/case-06.stepdata), [projected control](geometric-output/actual-faces/case-06-control.stepdata) | The source face exists and its original inch/0.001-inch closure context remains attached; vertices within tolerance should reconcile. | `C`, `E`, `F`: source face #7209 is refused and dropped. The user-supplied face matches all 102 vertices, 104 connections and seven loops after conversion from inches to millimetres. |
| 07 | [edge](geometric-output/actual-edges/case-07.stepdata), [loss pair](geometric-output/actual-faces/case-07.stepdata), [projected control](geometric-output/actual-faces/case-07-control.stepdata) | A rejected edge and associated source face should be diagnosed; the control must survive. | `E`, `F`, `R`: one face is dropped and the projected control restores it. The source endpoint is numerically outside declared uncertainty. Full private control restores 163 pixels near the body/lead notch; whether another symptom was intended is unconfirmed. |
| 08 | [two faces](geometric-output/actual-faces/case-08.stepdata) | Triangles on the cylinder or torus respect the configured chord tolerance. | `R`, `T`: visible fan, maximum centroid deviation 123× tolerance. |
| 09 | [two faces](geometric-output/actual-faces/case-09.stepdata) | Triangles on the cylinder or torus respect the configured chord tolerance. | `R`, `T`: visible fan, maximum centroid deviation 54× tolerance. |
| 10 | [two faces](geometric-output/actual-faces/case-10.stepdata) | Triangles on the cylinder or torus respect the configured chord tolerance. | `R`, `T`: visible fan, maximum centroid deviation 291× tolerance. |
| 11 | [two source triangles](geometric-output/actual-faces/case-11.stldata), [winding control](geometric-output/actual-faces/case-11-consistent.stldata) | A consistently oriented two-triangle surface shares its common edge in opposite directions. | `R`: source facets share the edge in the same direction and one is culled; reversing the control facet restores it. The original input contains 207 such same-direction shared edges. |
| Hang A | [ten entities](hyperbola-nearest-parameter/case-a.stepdata) | Edge conversion terminates. | `H`: exceeds two seconds; child is killed and reaped. |
| Hang B | [ten entities](hyperbola-nearest-parameter/case-b.stepdata) | Edge conversion terminates. | `H`: exceeds two seconds; child is killed and reaped. |

The five fan ratios measure triangle-centroid distance to the nearer of both
infinite analytic source surfaces, not just trimmed patches. All emitted
vertices agree with a declared surface within 0.0001 source units; the mesh and
analytic measurements use the same source-local frame. See the geometric
README for model diameters, tolerances and limitations. The exact cause inside
the mesher remains for later investigation; no geometry fix is included here.
