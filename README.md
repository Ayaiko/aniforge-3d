# AniForge 3D

Blender, MCP and Codex scripts for reference-driven anime character reconstruction, mesh inspection, retopology experiments and visual validation.

**Status: research prototype.** The current character has not passed likeness or facial-deformation gates. A successful script run or mesh QA result does not mean the model is production-ready. The latest repair/rebuild comparison is summarized in [docs/STATUS.md](docs/STATUS.md).

## Source layout

- `scripts/` — character construction, reference alignment, geometry checks, rendering and export experiments.
- `.agents/skills/` — project skills and Blender helpers, including the tutorial-learning and anime face/eye workflows.
- `artifacts/*/*.py` — authored experiment and audit code retained under its original phase path. Rejected modeling experiments are included as historical code, not recommended presets.
- `artifacts/*/live-mcp/run_request.py` — saved-request MCP clients. These can mutate the open Blender session; inspect each request before executing it.
- `docs/` — current limitations and source-snapshot scope.
- `licenses/` — notices for bundled third-party skill code. The repository's original [MIT license](LICENSE) is preserved.

## Running the code

The scripts were developed with **Blender 5.2.2 LTS** on Apple Silicon macOS. Blender jobs use Blender's Python and `bpy`; analysis helpers additionally use packages such as NumPy, SciPy, Pillow and OpenCV. Live MCP clients use the Python `mcp` SDK and the configured `mcp-for-blender` executable.

Read the script before running it and use a saved copy of the intended `.blend` input. A typical background invocation is:

```sh
blender --background --factory-startup --disable-autoexec \
  /path/to/copied-input.blend --python-exit-code 1 \
  --python /path/to/aniforge-3d/scripts/your_selected_script.py
```

This is an example invocation pattern, not a universal entrypoint. Scripts have different required scene names, checkpoints and local inputs. Many historical experiment scripts retain machine-local absolute paths and must be configured for another checkout. This first upload preserves their source rather than claiming a portable one-command pipeline.

For live MCP, keep the connection on `127.0.0.1`, enable `BLENDER_MCP_SAFE_MODE=1`, and use an absolute `uvx` path when the desktop PATH differs. Do not execute downloaded asset scripts merely to inspect topology.

## What is included

This upload contains code, skills and their source notices. Model checkpoints, reference artwork, rendered images, downloaded tutorial videos/captions, third-party character assets, local environments, credentials and generated data are excluded. Scripts that depend on those inputs need the local workspace data; cloning this repository alone does not reproduce the experiments.

`package.json` and its lockfile preserve optional JavaScript dependency metadata from the workspace. A browser viewer entrypoint is not included in this snapshot; no complete viewer build is claimed.

See [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md) for bundled skill attribution and upstream sources.
