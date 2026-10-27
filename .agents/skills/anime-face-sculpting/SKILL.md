---
name: anime-face-sculpting
description: Refine primary and secondary anime facial forms in Blender against supplied front and profile references, using protected landmarks and controlled edits rather than generic human proportions or extra detail.
---

# Anime face sculpting

Use the supplied character as the proportion authority. Record eye corners, nose tip, neutral lip line, chin and cheek contour in the unchanged validation cameras. Hair-covered skull shape is inferred; do not score a bald head against a hair silhouette.

Read [source-notes.md](references/source-notes.md) for tutorial evidence and the tested-version boundary.

## Work in bounded passes

Save or copy the chosen checkpoint and record its hash. Inspect topology and modifiers before sculpting. Choose one defect: a cheek trough, oversized nose, lip projection, jaw mass or socket depth. State which front/profile measurements must remain fixed.

Adjust primary masses at the existing resolution. Restore collapsed local volume before smoothing instead of erasing the intended form. Check both views after each pass; preserve neutral expression. Refine secondary transitions only after mass and landmark positions hold. Supplement front/profile with 20-degree, 45-degree and high/low checks. Temporary vertex color or a clay/toon comparison can expose proportion problems, but keep the same display for before/after judgments. Mask lids, lip openings and nostrils when relaxing adjoining skin. General smoothing can shrink a chin, seal an opening or erase eyelid volume, so it is not a substitute for fitting the form.

For headless work prefer a deformation that directly expresses the intended mass change. The optional helper [constrained_relax.py](scripts/constrained_relax.py) takes caller-defined weights, fixes boundaries, caps total displacement, and can restrict motion to one axis. It preserves connectivity and refuses shape-key meshes. Use projected contour masks to protect side silhouettes too; preserving X/Z alone protects only the front projection. This helper approximates bounded relaxation; it is not a Blender brush stroke. Connectivity preservation does not imply that the visible form or occlusion is preserved.

Use real sculpt brushes only in an interactive session with a valid 3D View context. Blender 5.x brushes are assets; inspect the actual brush/operator API and do not replay old shortcut keys. Do not run headless Sculpt Mode filters. Remesh and dynamic topology change connectivity and can destroy UVs and shape keys; use a separate sculpt master only when that operation is within scope. Preserve an attribute-bearing source for transfer and inspect detail loss; voxel remesh does not produce deformation-ready facial loops.

## Keep or reject

Render before/after clay from fixed front, side and 45-degree cameras. Compare overlays, visible surface continuity and projected feature positions. Report maximum movement, vertex/face counts and geometry QA. If the proposed fix merely changes lighting, shifts a camera, hides a defect or worsens another required view, reject it. An eye/cheek improvement does not certify the whole head or authorize hair/detail work.
