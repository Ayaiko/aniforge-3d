from pathlib import Path
import sys, json
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vrm_env import ROOT, enable_vrm
bpy.ops.wm.read_factory_settings(use_empty=True)
enable_vrm()
bpy.ops.import_scene.vrm(filepath=str(ROOT / 'assets/base/Sendagaya_Shibu.vrm'))
report = {'objects': [], 'materials': []}
for ob in bpy.data.objects:
    row = {'name': ob.name, 'type': ob.type, 'location': list(ob.location), 'dimensions': list(ob.dimensions)}
    if ob.type == 'MESH':
        row.update(vertices=len(ob.data.vertices), polygons=len(ob.data.polygons), materials=[m.name if m else None for m in ob.data.materials], keys=[k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [])
    if ob.type == 'ARMATURE':
        row['bones'] = {b.name: list(b.head_local) for b in ob.data.bones if any(x in b.name.lower() for x in ['head','neck','eye','chest','hips'])}
    report['objects'].append(row)
for material in bpy.data.materials:
    report['materials'].append({'name': material.name, 'diffuse': list(material.diffuse_color), 'mtoon': material.vrm_addon_extension.mtoon1.enabled})
(ROOT / 'previews/base-inventory.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'models/base-import.blend'))
print(json.dumps(report, indent=2))
