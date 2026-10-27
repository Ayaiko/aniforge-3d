import bpy,json,sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]);out.parent.mkdir(exist_ok=True,parents=True)
a=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  a.append({'name':o.name,'v':len(o.data.vertices),'f':len(o.data.polygons),'min':[min(v.co[i] for v in o.data.vertices) for i in range(3)],'max':[max(v.co[i] for v in o.data.vertices) for i in range(3)],'shape_keys':list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],'uv_maps':len(o.data.uv_layers),'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in o.modifiers]})
out.write_text(json.dumps(a,indent=2));print('INVENTORY',[(x['name'],x['v'],x['f'],len(x['shape_keys'])) for x in a],flush=True)
