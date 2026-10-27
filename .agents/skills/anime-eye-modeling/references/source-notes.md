# Evidence and adaptation

Review completed 2026-10-27 by chronological storyboards across the entire timeline plus the available caption stream. This is not continuous playback or every-frame inspection. The project coverage ledger is `artifacts/anime-face-full-review/coverage-manifest.json`; exact frames, hashes and per-sheet captions are retained there. ASR can misrecognize words. Project-specific Python procedures are adaptations, not code supplied by the creator.

Source: [Natsumori Katsu, five eye tips](https://www.youtube.com/watch?v=RAA4VOkqw-I). Reviewed 6 sheets / 173 frames, maximum 10-second gap, and all Japanese ASR segments.

04:00–06:04: upper-lid/corner slope and lash volume. 06:04–07:38: recess pupil/iris region and inspect gaze from several angles. This is distinct from translating the entire eyeball. 07:38: optional slight convergence. 08:25: sclera/iris balance changes expression; the video explicitly warns that excessive iris size can look wrong. 09:54–18:12: layered eye painting, restrained reflected light, optional highlight objects and lash/sclera tint. Later: source discussion and reflection.

Transfer: reference expression wins over generic attractiveness advice. Decorative patterns and convergence are optional. Paint layers need UV/image persistence, not just a saved blend.

Blender 5.2.2 project trial: material regions, fixed cameras and bounded whole-eye depth changes. This validates local occlusion only, not source pupil recession or character likeness. A display-color mask initially missed the green eye; corrected per-eye detection supersedes those initial results. Prefer linear IDs for future measurements.
