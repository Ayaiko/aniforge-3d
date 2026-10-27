import bpy,bmesh,json,sys
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/orbital-refinement-01';s=bpy.context.scene
sys.path.insert(0,str(R/'.agents/skills/blender-core/scripts'));import env_report
(O/'environment.json').write_text(json.dumps(env_report.run(),indent=2,default=str))
h=bpy.data.objects['Anime013_Head'];bm=bmesh.new();bm.from_mesh(h.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table();bm.normal_update()
loops=[];edges={e for e in bm.edges if e.is_boundary}
while edges:
 e=edges.pop();ordered=[e.verts[0],e.verts[1]]
 for _ in range(1000):
  es=[e for e in ordered[-1].link_edges if e in edges]
  if not es:break
  e=es[0];edges.remove(e);n=e.other_vert(ordered[-1])
  if n==ordered[0]:break
  ordered.append(n)
 loops.append([v.index for v in ordered])
d={'vertices':[list(v.co) for v in h.data.vertices],'faces':[list(p.vertices) for p in h.data.polygons],'edges':[[v.index for v in e.verts] for e in bm.edges],'normals':[list(v.normal) for v in bm.verts],'valence':[len(v.link_edges) for v in bm.verts],'boundary_loops':loops,'cameras':{o.name:{'matrix':[list(r) for r in o.matrix_world],'ortho_scale':o.data.ortho_scale} for o in s.objects if o.type=='CAMERA'}}
(O/'head-before.json').write_text(json.dumps(d,indent=2))
for o in [x for x in s.objects if x.type=='MESH' and x!=h]:
 (O/(o.name+'-before.json')).write_text(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'face_materials':[p.material_index for p in o.data.polygons]},indent=2))
print('RESULT',json.dumps({'scene':s.name,'blender':bpy.app.version_string,'boundaries':[[len(l),[list(bm.verts[i].co) for i in l[:3]]] for l in loops],'head':len(bm.verts),'custom_normals':h.data.has_custom_normals}));bm.free()
