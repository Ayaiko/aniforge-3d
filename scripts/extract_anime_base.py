"""Read source geometry/keys only, never run asset scripts, preserve provenance."""
import bpy,json
from pathlib import Path
out=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/reconstruction-v2-mcp')
objects=[]
for ob in bpy.data.objects:
    if ob.type!='MESH' or not len(ob.data.polygons):continue
    vs=[list(ob.matrix_world@v.co) for v in ob.data.vertices]
    print('ANIME_BOUNDS',ob.name,[(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)])
    keys={}
    if ob.data.shape_keys:
        keys={k.name:[list(ob.matrix_world@v.co) for v in k.data] for k in ob.data.shape_keys.key_blocks}
    objects.append({'name':ob.name,'vertices':vs,'faces':[list(p.vertices) for p in ob.data.polygons],
                    'keys':keys,'materials':[m.name for m in ob.data.materials if m],
                    'material_ids':[p.material_index for p in ob.data.polygons],
                    'uv':[list(v.uv) for v in ob.data.uv_layers.active.data] if ob.data.uv_layers.active else []})
(out/'anime-barely-payload.json').write_text(json.dumps(objects))
