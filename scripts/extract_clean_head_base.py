"""Read CC0 Blender asset with autoexec disabled; export raw coordinates only."""
import bpy,json
from pathlib import Path
out=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/reconstruction-v2-mcp')
objects=[]
for name in ['GEO-head_stylized','GEO-head_stylized.eye.L','GEO-head_stylized.eye.R']:
    ob=bpy.data.objects[name]
    objects.append({'name':name,'vertices':[list(v.co) for v in ob.data.vertices],
                    'faces':[list(p.vertices) for p in ob.data.polygons],
                    'matrix':[list(r) for r in ob.matrix_world],
                    'groups':{g.name:[v.index for v in ob.data.vertices if any(w.group==g.index for w in v.groups)] for g in ob.vertex_groups}})
    print(name,'bounds',[(min(v.co[i] for v in ob.data.vertices),max(v.co[i] for v in ob.data.vertices)) for i in range(3)],'matrix',ob.matrix_world)
(out/'cc0-stylized-head-payload.json').write_text(json.dumps(objects))
