"""Project-local VRM add-on registration for reproducible Blender jobs."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]

def enable_vrm():
    addon = ROOT / 'tools/vrm-addon/VRM_Addon_for_Blender-release'
    name = 'io_scene_vrm'
    link = ROOT / 'tools' / name
    if not link.exists():
        link.symlink_to(addon, target_is_directory=True)
    sys.path.insert(0, str(ROOT / 'tools'))
    import addon_utils
    addon_utils.enable(name, default_set=True, persistent=True)
    return sys.modules[name]
