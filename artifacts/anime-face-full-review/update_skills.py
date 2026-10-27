from pathlib import Path
import shutil
S=Path('/Users/graind/.codex/skills');O=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/anime-face-full-review')
for n in ['anime-face-topology','anime-face-sculpting','anime-eye-modeling']:
 b=O/'prior-skills'/n;b.mkdir(parents=True,exist_ok=True)
 for f in ['SKILL.md','references/source-notes.md']:
  t=b/f;t.parent.mkdir(parents=True,exist_ok=True)
  if not t.exists():shutil.copy2(S/n/f,t)
p=S/'blender-tutorial-to-practice/SKILL.md'
p.write_text('''---
name: blender-tutorial-to-practice
description: Learn Blender techniques from supplied tutorials, document source coverage, adapt them to the installed Blender version, and verify a bounded exercise before codifying reusable modeling skills.
---

# Blender tutorial to practice

Use when the assignment is to learn from tutorial sources and apply that learning. Preserve the requested source order and completion boundary before modeling. This skill does not expand the character, asset, or publication scope.

## Establish what was reviewed

Read the actual source, not just its title, thumbnail or description. Keep a coverage ledger with source ID, duration, chapters, reviewed time ranges, available captions and the actual visual method. Separate downloaded, inspected and practiced statuses.

For a request to review the whole tutorial, inspect every chapter chronologically, including later corrections and caveats. Captions and storyboards can support full-timeline analysis but do not establish continuous playback or every-frame inspection. State the sampling interval and transcription uncertainty. If an operation or parameter is ambiguous, inspect that local sequence more closely rather than inventing it. Do not mark truncated or unseen tool output reviewed.

## Translate decisions, not shortcuts

For each useful technique distinguish:

- **Observed:** source and timestamp, geometry/visual decision, context and caveat.
- **Adapted:** how the target reference, topology, rig, units or installed API changes the method.
- **Authored:** a procedure or helper invented for the task.
- **Tested:** exact file/version, observable result, failures and what remains unverified.

A numerical relaxation is not evidence of a sculpt brush workflow. Moving an entire eyeball is not pupil recession. A voxel remesh is not deformation-ready facial retopology. Keep these operation boundaries explicit.

Use the installed Blender API for old tutorials. Preserve the target reference proportions and validation cameras. Choices made because a tutorial has no side reference do not override a supplied side plate. Do not convert a beginner shortcut, artist preference or project-specific tolerance into a universal rule.

## Practice one bounded transfer

Use the authorized checkpoint copy. Pin the input, active scene, protected landmarks and intended defect. Inspect base/evaluated topology before edits; distinguish intentional openings from overlapping faces and overconnected edges. Keep a useful existing cage. Shape keys and UV/rig correspondence need protection before connectivity changes.

Test one hypothesis with comparable front, profile and oblique views. Add high/low views when depth or eyelids are involved. Keep camera, display and lighting changes separate from geometry comparisons. Review primary forms before decorative shading. Retain a candidate only for the property its evidence supports; revert other attempts and preserve their failed verdicts.

## Validate the measurement before trusting the score

For geometric masks prefer object/material IDs or linear data passes. Display RGB changes under view transforms, lighting, antialiasing and compositing. Before comparing candidates, verify that each intended object is detected independently and inspect the mask overlay. A missing second eye cannot count as improved occlusion. State reference-trace uncertainty and sensitivity to the classifier.

Aperture overlap, manifoldness and displacement are local technical measures. They cannot certify character likeness or animation readiness. Review rendered appearance and topology separately, preserving FAIL for unresolved defects. File parsing, skill discovery and script execution prove only those operations.

## Codify after evidence

Update an existing skill where the capability already belongs. Keep reusable decisions in SKILL.md, source-specific observations in references, and project incidents in the retrospective. Report static validation, exercised behavior and independent review separately. Read [incident-review.md](references/incident-review.md) only when analyzing this workflow's failure pattern or deciding what an experiment proves.
''')
header='''Review completed 2026-10-27 by chronological storyboards across the entire timeline plus the available caption stream. This is not continuous playback or every-frame inspection. The project coverage ledger is `artifacts/anime-face-full-review/coverage-manifest.json`; exact frames, hashes and per-sheet captions are retained there. ASR can misrecognize words. Project-specific Python procedures are adaptations, not code supplied by the creator.\n\n'''
notes={
'anime-face-topology':'''Source: [Natsumori Katsu, plane-based face modeling](https://www.youtube.com/watch?v=uUqQw6VpFP8). Reviewed 24 sheets / 718 frames, maximum 10-second gap, and the complete creator English caption stream.

00:46–10:39: mirrored half-cage, eye/mouth openings and profile, then internal surfaces and skull/neck. Sclera grows from the opening in this example; a separate sphere is not mandatory. 14:09 onward: shading and cage cleanup. Around 24:01: extruded iris piece with depth. Around 25:23: cheekbone at 45 degrees and soft cheek fullness near 20 degrees, plus high/low inspection. Later: UV/paint and coordinated lid/lash blinking from 47:19.

Transfer: symmetry origin is a known plane, not automatically geometry center. Subdivision is useful on a coherent cage; it cannot fix folded faces. Global welds and applying modifiers before painting are stage choices requiring seam/rig checks. Changed Basis coordinates must propagate appropriately to other keys.

Compatibility exercised in Blender 5.2.2 LTS: bmesh, mesh data, Mirror properties and fixed-camera renders. Complete eyelid construction, UV painting and blink deformation have not been reproduced by this project.
''',
'anime-face-sculpting':'''Source: [Fusako / 3D self-study, anime head sculpt](https://www.youtube.com/watch?v=terg-xxS6R8). Reviewed 23 sheets / 686 frames, maximum 10-second gap, and all Japanese ASR segments; English captions were unavailable.

03:35: sphere and broad symmetric shaping; mask isolates neck. Local volume, creases, ear folds and repeated orbit checks follow. 22:50: provisional vertex color; flat/studio switching exposes proportions. 29:52: further form adjustment with protected eye regions. Around 40:07: toon material/outline. 43:52: explicit next-day critique of ears, neck and outer-eye volume. 46:15 onward: duplicate before voxel remesh, adjust resolution after ear-detail loss, transfer vertex color. This does not demonstrate animation-ready facial retopology.

The creator lacks a side drawing and invents that profile. Supplied project plates take precedence. Painted colors are provisional; remesh does not automatically preserve attributes. Custom numeric brush shortcuts are not Blender defaults.

Compatibility: Blender 5.2.2 data-level relaxation helper exercised separately; it preserves connectivity but its cheek trial worsened eye leakage and was rejected. It is authored, not the artist's sculpt strokes. Interactive brush workflow remains untested here.
''',
'anime-eye-modeling':'''Source: [Natsumori Katsu, five eye tips](https://www.youtube.com/watch?v=RAA4VOkqw-I). Reviewed 6 sheets / 173 frames, maximum 10-second gap, and all Japanese ASR segments.

04:00–06:04: upper-lid/corner slope and lash volume. 06:04–07:38: recess pupil/iris region and inspect gaze from several angles. This is distinct from translating the entire eyeball. 07:38: optional slight convergence. 08:25: sclera/iris balance changes expression; the video explicitly warns that excessive iris size can look wrong. 09:54–18:12: layered eye painting, restrained reflected light, optional highlight objects and lash/sclera tint. Later: source discussion and reflection.

Transfer: reference expression wins over generic attractiveness advice. Decorative patterns and convergence are optional. Paint layers need UV/image persistence, not just a saved blend.

Blender 5.2.2 project trial: material regions, fixed cameras and bounded whole-eye depth changes. This validates local occlusion only, not source pupil recession or character likeness. A display-color mask initially missed the green eye; corrected per-eye detection supersedes those initial results. Prefer linear IDs for future measurements.
'''}
for n,body in notes.items():(S/n/'references/source-notes.md').write_text('# Evidence and adaptation\n\n'+header+body)
p=S/'anime-face-topology/SKILL.md';t=p.read_text();t=t.replace('Look at the facial cage in front, profile and 45 degrees.','Look at the facial cage in front, profile and 45 degrees, then near 20 degrees for the cheek transition and from high/low angles for depth.');t=t.replace('Place quad loops around the eyelid aperture','Keep the origin or Mirror object on the intended symmetry plane; an offset half mesh must not automatically use origin-to-geometry. The sclera can be an integrated surface behind the rim or a separate eye according to the asset. Place quad loops around the eyelid aperture');t=t.replace('Check shape-key correspondence before any topology change;','Subdivision can reveal the quality of a coherent cage but must not hide defects. Check shape-key correspondence before any topology change;');p.write_text(t)
p=S/'anime-face-sculpting/SKILL.md';t=p.read_text().replace('Adjust primary masses at the existing resolution.','Adjust primary masses at the existing resolution. Restore collapsed local volume before smoothing instead of erasing the intended form.');t=t.replace('Refine secondary transitions only after mass and landmark positions hold.','Refine secondary transitions only after mass and landmark positions hold. Supplement front/profile with 20-degree, 45-degree and high/low checks. Temporary vertex color or a clay/toon comparison can expose proportion problems, but keep the same display for before/after judgments.');t=t.replace('use data-level deformation or the helper','prefer a deformation that directly expresses the intended mass change. The optional helper');t=t.replace('It takes caller-defined weights','takes caller-defined weights');t=t.replace('This helper approximates a bounded relaxation pass; it is not a Blender brush stroke.','This helper approximates bounded relaxation; it is not a Blender brush stroke. Its original cheek trial was rejected for increased sclera leakage, so do not treat that test as artistic validation.');t=t.replace('use a separate sculpt master only when that operation is within scope.','use a separate sculpt master only when that operation is within scope. Preserve an attribute-bearing source for transfer and inspect detail loss; voxel remesh does not produce deformation-ready facial loops.');p.write_text(t)
p=S/'anime-eye-modeling/SKILL.md';t=p.read_text().replace('4. Evaluate iris/pupil recession','4. Distinguish whole-eye positioning for socket occlusion from pupil/iris recession for gaze; they solve different problems. Evaluate iris/pupil recession');t=t.replace('Measure aperture overlap,','Prefer linear object/material IDs. Validate every eye mask independently and inspect the overlay before using metrics; display RGB thresholds can lose one eye under a view transform. Measure aperture overlap,');t=t.replace('A larger iris can reduce excessive sclera exposure, but','More sclera can be intentional for an energetic expression. A larger iris can reduce excessive sclera exposure, but');p.write_text(t)
print('Updated 4 skills; prior versions preserved')
