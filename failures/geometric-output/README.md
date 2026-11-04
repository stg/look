# Reported geometric output cases

Eleven reported cached thumbnails were examined. These are separate from the
hyperbola nontermination reports. The original models, cached images, source
paths, and diagnostic logs remain in the locally ignored `failures/private/`
directory and are not part of this shareable corpus. All source hashes were
verified before analysis. Prefixes below identify the user-provided cache keys.
Each row now links an actual reduced reproduction. The checklist in
[`../REPRODUCERS.md`](../REPRODUCERS.md) records its expected invariant,
command and verified result. Reproduction does not mean a geometry fix has landed.

| Case / key prefix | Verified reduced reproducer and finding | Status |
| --- | --- | --- |
| 01 `1b5da4958391` | [Actual edge](actual-edges/case-01.stepdata) and [two-face loss reproduction](actual-faces/case-01.stepdata): closed rational spline produces NaN endpoint residuals; 6 of 52 faces were lost. The endpoint check evaluates outside its valid interior knot span. | Two-face import and lost-face diagnostic verified. |
| 02 `1e212cb5856f` | [Actual edge](actual-edges/case-02.stepdata) and [two-face loss reproduction](actual-faces/case-02.stepdata): closed rational spline produces NaN outside its valid interior knot span; 6 conversion failures and one additional meshing loss among 27 faces. | Two-face conversion loss verified; the [separate meshing loss](actual-faces/case-02-parity.stepdata) reproduces `ContradictoryDualParity` in a second two-face fixture. |
| 03 `1ed619a3e4ca` | [Actual bounded face](actual-faces/case-03.stepdata): the two original circular boundaries differ in axial position by only 0.254 source units, yet Look renders a tall cone. | Verified: compiled mesh axial bounds reach 20.1829 instead of the source bound 2.9271. |
| 04 `2a37b8bdb6e5` | [Actual B-spline edge](actual-edges/case-04.stepdata) and [two-face loss reproduction](actual-faces/case-04.stepdata): endpoint residual 0.0001257; 14 of 77 faces lost. | The [two-face streak fixture](actual-faces/case-04-streak.stepdata) also reproduces the fan; numerical per-knot-span search finds a minimum endpoint distance of 0.00012566 mm, exceeding the stated 0.000005 mm uncertainty. |
| 05 `2af42211d657` | [Actual B-spline edge](actual-edges/case-05.stepdata) and [two-face loss reproduction](actual-faces/case-05.stepdata): endpoint residual 0.01536; 2 of 38 faces lost. | A numerical per-knot-span search finds the endpoint within 3.7e-11 mm of the source curve (declared uncertainty 1e-7 mm), while Look compares the untrimmed spline end at parameter 1.0 (0.01536 mm away); the actual vertex is at parameter 0.98034. A separate [two-face streak fixture](actual-faces/case-05-streak.stepdata) reproduces the visible fan. |
| 06 `2ad4d391cea6` | [Actual circle edge](actual-edges/case-06.stepdata) and [two-face loss reproduction](actual-faces/case-06.stepdata): endpoint residual 0.00005012; source declares 0.001 inch closure uncertainty. Four of 572 faces lost. | The same edge also removes a [large planar face](actual-faces/case-06-plane.stepdata). A [vertex-projected control](actual-faces/case-06-control.stepdata) restores the smaller face; reduced face restoration and its localized full-thumbnail change are verified; any additional reported symptom is unconfirmed. |
| 07 `2b9801cc8acd` | [Actual hyperbola edge](actual-edges/case-07.stepdata) and [two-face loss reproduction](actual-faces/case-07.stepdata): endpoint residual 0.0008598; 9 of 130 faces lost. | Two-face loss verified; numerical nearest-point search gives approximately 0.00060485 mm against 0.00002 mm declared uncertainty. A [vertex-projected control](actual-faces/case-07-control.stepdata) restores the face; reduced face restoration and its localized full-thumbnail change are verified; any additional reported symptom is unconfirmed. |
| 08 `2dd8b827c073` | [Two actual faces](actual-faces/case-08.stepdata), a cylinder and torus, reproduce the visible fan; each rendered alone lacks the same fan. | Reduced visual reproduction verified; CPU mesh contains triangles far from either analytic surface. The tolerance violation is verified; the detailed mesher mechanism is deferred. |
| 09 `2e2afd7c6836` | [Two actual faces](actual-faces/case-09.stepdata), a cylinder and torus, reproduce the visible fan; each rendered alone lacks the same fan. | Reduced visual reproduction verified; CPU mesh contains triangles far from either analytic surface. The tolerance violation is verified; the detailed mesher mechanism is deferred. |
| 10 `2e6b9baf2882` | [Two actual faces](actual-faces/case-10.stepdata), a cylinder and torus, reproduce the visible fan; each rendered alone lacks the same fan. | Reduced visual reproduction verified; CPU mesh contains triangles far from either analytic surface. The tolerance violation is verified; the detailed mesher mechanism is deferred. |
| 11 `2e9f34c218e9` | [Two actual STL facets](actual-faces/case-11.stldata) share an edge in the same direction with nearly opposite normals. A [winding-consistent control](actual-faces/case-11-consistent.stldata) reveals the culled facet. In the original, 207 of 674 shared edges have matching rather than opposing directions. | Reduced visual reproduction verified; input winding is inconsistent. |

For cases 01 and 02, the `front()`/`back()` endpoint check uses the first and last full knot values, whereas the degree-13 rational spline is defined over its narrower interior support. The numerical check verifies that the support endpoints match the declared closed-edge vertex. For case 05, the source endpoint lies in the interior of the bounded spline, but conversion checks the untrimmed full spline.

The full-model diagnostic controls for cases 06 and 07 project only the same
vertices used in the reduced controls. Their loss counts decrease from 4 to 3
and from 9 to 8 respectively, with no new lost face IDs, but the resulting
thumbnail changes are localized: case 06 changes 113 pixels in the contact
area (x=243-267, y=265-286), and case 07 changes 163 pixels near the
body/lead notch (x=300-321, y=302-328), on 512 x 512 images. These changes
confirm the visual effect of the reduced losses; they do not establish whether
the user intended an additional symptom. The byte-identical original capture,
projected full-source control, rendered control and result logs remain in the
ignored local `failures/private/cases/case-06/` and `case-07/` directories.
The separate case 06 plane fixture verifies the large face #7209 is also lost.

The six edge fixtures contain the actual affected edge and its dependency
closure; names and full models are absent. Directly runnable probes are below.
The face fixtures contain only one or two source faces and their geometry. The two STL triangles are an exact subset; the comparison file swaps
one triangle's winding and normal. The case 06 and 07 controls change only the
implicated endpoint positions to their nearest locations on the declared
curve; they demonstrate the loss boundary and are not changes to Look. Cases 03 through 05 and 08 through 11 visual results were
verified with the copied StepThumbs 0.3.2 Look renderer; a self-contained reduced-render wrapper is provided below.


## Private end-to-end thumbnail reproduction

All eleven user-reported images have also been reproduced end-to-end with the
archived originals, using StepThumbs 0.3.2 and its statically linked Look
renderer on the original Windows machine. The generated PNG for every case was
byte-identical to its reported cached PNG; all eleven generated profile hashes
matched the common original cache profile. The image equality verifies the
reported output was reproduced, not that the output is geometrically correct.

The private archives and captures are not included in a public clone. With
`failures/private/cases/manifest.json` and its per-case `source.gz` and
`cached.png` files present, run from the Look checkout:

```powershell
python failures/geometric-output/render-private.py --exe PATH_TO_COPY_OF_StepThumbs.exe
```

Use the relevant StepThumbs build containing this Look renderer, not F3D. Pass
`--case case-08` (repeatable) to select cases. IDs `case-01` through `case-11`
correspond to the table rows in order. The manifest verifies the SHA-256 of each
original and cached PNG. A neutral fixed config mirrors the recorded settings;
the harness compares its resulting profile and PNG hashes to the private
manifest. Its output and detailed results are kept in ignored per-case folders.
On another GPU or renderer build, PNG bytes may vary even if the image looks
similar, in which case inspect both images and the profile rather than treating
a hash mismatch alone as proof of a different geometry issue.

The uncompressed model and isolated settings/cache live only in a temporary
directory beneath `%LOCALAPPDATA%/StepThumbnail/private-probes`, then are
deleted. A Windows kill-on-close job contains the renderer and its worker; the
external deadline is 10 seconds at most. No real user settings, registration,
original files or system thumbnail cache are changed. Pillow is optional for
the pixel-difference statistic; SHA-256 checks require only Python 3.

## Run the reduced reproductions

From the Look root, build `truck-stepio` and compile the shared standalone
probe against that exact release rlib. The following assumes an x64 MSVC build
with static CRT, as used for the verified results:

```powershell
$messages = cargo build --release --locked -p truck-stepio --message-format=json | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'truck-stepio build failed' }
$rlib = @($messages | Where-Object { $_.reason -eq 'compiler-artifact' -and $_.target.name -eq 'truck_stepio' } | ForEach-Object { $_.filenames } | Where-Object { $_ -like '*.rlib' })[-1]
if (-not $rlib) { throw 'truck_stepio rlib not found' }
$probe = Join-Path $env:TEMP 'look-edge-probe.exe'
rustc --edition 2021 -O -C lto=thin -C codegen-units=1 -C target-feature=+crt-static,+avx,+fma -L "dependency=$(Split-Path $rlib)" --extern "truck_stepio=$rlib" failures/hyperbola-nearest-parameter/repro.rs -o $probe
if ($LASTEXITCODE -ne 0) { throw 'probe compilation failed' }
python failures/geometric-output/actual-edges/run.py --exe $probe
python failures/geometric-output/actual-edges/check-splines.py  # requires numpy and scipy
python failures/geometric-output/actual-edges/check-closed.py   # requires numpy and scipy
python failures/geometric-output/actual-edges/check-analytic.py # requires numpy and scipy
```


The edge probe does not invoke the renderer. The six two-face loss fixtures,
the independent case 02 parity loss, and the one- and two-face visual fixtures
can be exercised with the native Look CLI:

```powershell
python failures/geometric-output/actual-faces/losses.py --look-exe PATH_TO_LOOK.exe
python failures/geometric-output/actual-faces/render.py --look-exe PATH_TO_LOOK.exe
```

Both wrappers also accept `--exe PATH_TO_StepThumbs.exe` for the StepThumbs
worker used in the initial cache comparison. `losses.py` checks the original face ID and loss type in the importer output,
with a five-second hard timeout per process. `render.py` renders the reduced
faces and both STL controls under an external ten-second process-tree deadline;
it verifies the STL winding relationship and puts PNGs under ignored
`failures/private/reduced-results/`. Pass `--case 09` or `--case 11-consistent`
to select a fixture, and `--no-edges` to compare without edge enhancement.
For cases 04, 05 and 08 through 10, `triangles-check.py` measures each
triangle centroid's distance to both infinite source surfaces in the original
local coordinate frame. It also checks that every mesh vertex agrees with one
of those surfaces within 0.0001 source units. `tolerance.rs` independently
repeats the Look importer calculation: the diagonal of converted shell vertices
and five samples per edge, multiplied by the default 0.001 linear deflection.
The maximum centroid deviations, diameters and tolerances measured were:

| Case | Model diameter | Chord tolerance | Maximum centroid deviation | Ratio |
| --- | ---: | ---: | ---: | ---: |
| 04 | 6.715087 | 0.006715 | 0.746880 | 111x |
| 05 | 14.915397 | 0.014915 | 2.436118 | 163x |
| 08 | 19.339076 | 0.019339 | 2.374273 | 123x |
| 09 | 6.732280 | 0.006732 | 0.364907 | 54x |
| 10 | 3.721559 | 0.003722 | 1.081192 | 291x |

The numerical wrapper requires each maximum to exceed ten times the measured
tolerance. Legitimate chordal approximation therefore does not explain these
large triangles. The exact mesher failure mechanism is left for subsequent corrective work.
Build both probes against matching rlibs from the same build:

```powershell
python failures/geometric-output/actual-faces/build-bounds.py --triangles --rlib PATH_TO_LOOK_RLIB --stepio-rlib PATH_TO_TRUCK_STEPIO_RLIB --meshalgo-rlib PATH_TO_TRUCK_MESHALGO_RLIB --native-lib-dir PATH_TO_WINDOWS_NATIVE_LIBS --static-crt
```

Alternatively pass both already compiled executables to
`triangles-check.py --exe PATH_TO_TRIANGLES_PROBE.exe --tolerance-exe PATH_TO_TOLERANCE_PROBE.exe`.
These fixtures contain only actual implicated faces or triangles and their
dependencies; they are not complete source models.

For case 03, the source's bounded circular edges are at axial positions
2.672928114281 and 2.927071885719. `bounds.rs` calls the same Look scene
compiler and reports compiled mesh bounds after the Z-up transform. A compiled
probe produced Y bounds `[2.6729276, 20.182932]`; the expected maximum is
approximately 2.9271. Build the Look library with the same settings, select the `liblook-*.rlib`
produced by that build, and run:

```powershell
python failures/geometric-output/actual-faces/build-bounds.py --rlib PATH_TO_LOOK_RLIB --native-lib-dir PATH_TO_WINDOWS_NATIVE_LIBS --static-crt
```

The native library directory should contain `windows.0.52.0.lib`; match the
CRT flag to the rlib. This compiles `bounds.rs` to a temporary executable and
runs the bounded check. Alternatively,
`python failures/geometric-output/actual-faces/bounds-check.py --exe PATH_TO_BOUNDS_PROBE.exe`
uses an existing probe. The check temporarily copies the fixture under the
excluded private-probes folder and uses an external timeout.

Match the toolchain and CRT/CPU flags to the rlib. The two separate hanging
edge cases and their own watchdog are described in
[`../hyperbola-nearest-parameter/README.md`](../hyperbola-nearest-parameter/README.md).

Each call has an external two-second timeout; the wrapper kills and reaps the
child if it expires. It checks the currently observed endpoint-rejection
messages. The test is deliberately diagnostic: a future fix may require
updating the expected result. No original models, F3D, or GPU are used.
