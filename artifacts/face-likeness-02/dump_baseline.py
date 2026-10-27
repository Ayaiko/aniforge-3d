import bpy,json,bmesh
from pathlib import Path
O=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/face-likeness-02');s=bpy.context.scene;report={'scene':s.name,'blender':bpy.app.version_string,'meshes':{},'cameras':{}}
for o in s.objects:
 if o.type=='MESH':
  bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();loops=[];edges={e for e in bm.edges if e.is_boundary}
  while edges:
   e=edges.pop();chain=[e.verts[0],e.verts[1]]
   for _ in range(1000):
    es=[e for e in chain[-1].link_edges if e in edges]
    if not es:break
    e=es[0];edges.remove(e);n=e.other_vert(chain[-1])
    if n==chain[0]:break
    chain.append(n)
   loops.append([v.index for v in chain])
  report['meshes'][o.name]={'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'face_materials':[p.material_index for p in o.data.polygons],'materials':[{'name':m.name,'diffuse':list(m.diffuse_color)} for m in o.data.materials],'boundary_loops':loops,'shape_keys':bool(o.data.shape_keys),'matrix':[list(r) for r in o.matrix_world]};bm.free()
 if o.type=='CAMERA':report['cameras'][o.name]={'matrix':[list(r) for r in o.matrix_world],'ortho_scale':o.data.ortho_scale}
(O/'baseline.json').write_text(json.dumps(report,indent=2));print('BASELINE_DUMPED',list(report['meshes']))
