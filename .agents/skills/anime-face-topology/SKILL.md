---
name: anime-face-topology
description: Build or repair anime facial edge flow, eyelid and mouth openings, and cheek-to-jaw continuity in Blender when matching a character reference or diagnosing pinched facial shading.
---

# Anime face topology

Establish whether the task is a new facial cage or repair of an existing checkpoint. Preserve the chosen character, current version and reference cameras; a tutorial example does not authorize replacing the head.

Read [source-notes.md](references/source-notes.md) for reviewed tutorial passages and their evidence limits. This workflow combines those observations with a separately tested Blender 5.2.2 procedure.

## Diagnose before editing

Read the selected file/scene, Blender version, mesh counts, shape keys, modifiers, materials and transforms. Work on a copy. Identify boundary components by location: intentional eye/mouth openings are different from non-manifold edges with three or more incident faces. Inspect base and evaluated surfaces separately. Record duplicate vertices/faces, zero-area faces, winding, warped quads and non-adjacent triangle crossings.

Inspect several adjacency rings beyond each aperture. Existing concentric rims may terminate abruptly into fans; adding more rim loops does not repair their connection to cheek and jaw. Distinguish graph-distance neighborhoods from continuous quad loops. Global triangle/quad or warpage counts locate questions, not a production verdict.

Look at the facial cage in front, profile and 45 degrees, then near 20 degrees for the cheek transition and from high/low angles for depth. Black wedges can come from folded faces or custom normals; raising subdivision is not a repair. Check normals on a mesh copy first. Do not weld intentional UV/feature seams using an arbitrary global distance.

When comparing repair against a new cage, read [production-audit.md](references/production-audit.md) for structural lessons from Blender Studio Rain/Snow and the limits of a topology-only experiment. Preserve the target character's reference proportions; production examples do not supply replacement facial ratios.

## Build or repair

For a new cage, make a centered symmetric half surface and control the eye opening and facial profile before adding skull depth. Use Mirror merging/clipping with a tolerance related to model scale; inspect the seam before applying it. Keep the origin or Mirror object on the intended symmetry plane; an offset half mesh must not automatically use origin-to-geometry. The sclera can be an integrated surface behind the rim or a separate eye according to the asset. Place quad loops around the eyelid aperture and lip opening with enough spacing for closure. Route poles away from the moving lid/lip margin and away from a visible cheek highlight.

For repair, retain a usable loop layout. Protect eye corners, lip corners and the profile; regularize the surface between them. Rebuild only a demonstrably damaged patch when existing loops cannot support the intended opening. Subdivision can reveal the quality of a coherent cage but must not hide defects. Check shape-key correspondence before any topology change; a rigged mesh needs a migration plan.

## Acceptance

Render the same front/profile/45-degree cameras before and after, in clay and wireframe. Retain only edits that improve the named defect without moving locked landmarks outside the project's tolerance or adding crossings/non-manifold edges. Report pre-existing defects that remain. Technical validity and character likeness are separate verdicts; neither follows from script success.
