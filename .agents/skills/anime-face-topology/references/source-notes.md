# Evidence and adaptation

Review completed 2026-10-27 by chronological storyboards across the entire timeline plus the available caption stream. This is not continuous playback or every-frame inspection. The project coverage ledger is `artifacts/anime-face-full-review/coverage-manifest.json`; exact frames, hashes and per-sheet captions are retained there. ASR can misrecognize words. Project-specific Python procedures are adaptations, not code supplied by the creator.

Source: [Natsumori Katsu, plane-based face modeling](https://www.youtube.com/watch?v=uUqQw6VpFP8). Reviewed 24 sheets / 718 frames, maximum 10-second gap, and the complete creator English caption stream.

00:46–10:39: mirrored half-cage, eye/mouth openings and profile, then internal surfaces and skull/neck. Sclera grows from the opening in this example; a separate sphere is not mandatory. 14:09 onward: shading and cage cleanup. Around 24:01: extruded iris piece with depth. Around 25:23: cheekbone at 45 degrees and soft cheek fullness near 20 degrees, plus high/low inspection. Later: UV/paint and coordinated lid/lash blinking from 47:19.

Transfer: symmetry origin is a known plane, not automatically geometry center. Subdivision is useful on a coherent cage; it cannot fix folded faces. Global welds and applying modifiers before painting are stage choices requiring seam/rig checks. Changed Basis coordinates must propagate appropriately to other keys.

Compatibility exercised in Blender 5.2.2 LTS: bmesh, mesh data, Mirror properties and fixed-camera renders. Complete eyelid construction, UV painting and blink deformation have not been reproduced by this project.
