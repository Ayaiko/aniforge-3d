# Current modeling status

Snapshot: 2026-10-27, Blender 5.2.2 LTS.

Detail work is paused for the user's Root Cause Audit. The audit used the current head and two copied-file experiments under the same Front / Side / 3/4 cameras, neutral clay, lights and display settings. Blender Studio Rain/Snow were studied for production topology structure only; their facial proportions and mesh connectivity were not transferred into the character.

| Result | Current head | A: conservative repair | B: new quad-cage prototype |
|---|---:|---:|---:|
| Vertices | 946 | 946 | 3,663 |
| Faces | 1,107 | 1,093 | 3,608 |
| Triangles | 400 | 372 | 0 |
| Vertices with valence >=6 | 87 | 77 | 0 |
| Sampled exposed-profile MAE, pixels | 6.36 | 6.36 | 11.18 |
| Likeness | FAIL | FAIL, unchanged | FAIL, worse |
| Whole-asset render-profile QA | — | PASS with warnings | FAIL, Head/Eye_L coplanar overlap |
| Production/deformation readiness | Not demonstrated | Not demonstrated | Not demonstrated |

A preserves every captured vertex coordinate. Its conservative joins reduce some triangulation but do not repair the primary facial forms. B has all quads and no detected non-adjacent overlap candidates within the head, but its cheek/jaw form is worse and it collides with the unchanged left eye. An all-quad cage is not automatically a successful production head.

The existing head already has concentric aperture neighborhoods. The issue is their transition into unevenly spaced, high-valence areas, together with incorrect primary masses. Increasing resolution or smoothing alone does not resolve that combination. Neighborhood counts are graph-distance groups, not proof of continuous edge loops.

The current head remains the safer reference foundation. B must not replace it. A carefully fitted manual rebuild has not been ruled out: this trial only rejects the analytic cage implementation tested here. Full eyelid closure, smile, jaw opening and corrective-shape validation remain untested.

The full local audit, renders and model files are deliberately outside this code-only upload. Audit scripts are in `artifacts/root-cause-audit-05/`. Some scripts reproduce failed attempts and should be used as evidence, not as an endorsed modeling pipeline.
