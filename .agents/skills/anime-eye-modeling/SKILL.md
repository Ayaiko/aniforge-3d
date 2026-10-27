---
name: anime-eye-modeling
description: Model and correct anime eyelid apertures, sclera exposure, iris/pupil depth and gaze in Blender, preserving the expression and projected eye shape of supplied character references.
---

# Anime eye modeling

Treat lid aperture, lid rim/lashes, sclera, iris and pupil as different structures. A larger sphere or painted iris cannot repair the wrong aperture. Read [source-notes.md](references/source-notes.md) for the reviewed source and caveats.

## Measure and isolate

Use the selected checkpoint, not an arbitrary anime base. Record inner/outer corners, upper/lower curves, iris center/extent and exposed sclera separately for each eye. Identify the camera and whether the reference view is perspective, mirrored or asymmetric. Establish the expected neutral expression before considering gaze convergence.

Inspect eye components, material assignments and their depth against the skin. In profile and 45 degrees, check for a protruding white sphere, gaps at the rim, an iris floating above the sclera and a far eye visible through the face. Do not use the object's bounding box alone to infer the visible aperture.

## Edit in dependency order

1. Fit the aperture and upper-lid slope to the reference. Keep enough connected margin for future blinking; do not close the hole with an opaque patch.
2. Fit sclera curvature behind the lid. Small depth or curvature changes must be checked in profile and 45 degrees as well as front. Avoid whole-eye flattening that makes it a card.
3. Fit iris size/placement to the actual expression. More sclera can be intentional for an energetic expression. A larger iris can reduce excessive sclera exposure, but use reference measurements rather than a universal anime ratio.
4. Distinguish whole-eye positioning for socket occlusion from pupil/iris recession for gaze; they solve different problems. Evaluate iris/pupil recession and gaze using separate geometry where appropriate. Any convergence is a character/camera choice, not an automatic inward offset.
5. Add lash/rim emphasis only when requested and geometrically supported. Avoid texture or dark rims masking an incorrect socket.

## Validation

Render labeled eye mattes and clay from unchanged cameras. Prefer linear object/material IDs. Validate every eye mask independently and inspect the overlay before using metrics; display RGB thresholds can lose one eye under a view transform. Measure aperture overlap, iris position and eye-surface leakage outside the expected opening. Compare visible regions, not hidden spherical geometry. Inspect continuity and expression visually; a perfect aperture mask can coexist with an implausible eyeball. Preserve the rig/keys and check blink deformation when present. Report source-specific residuals and reject modifications that improve only one view.
