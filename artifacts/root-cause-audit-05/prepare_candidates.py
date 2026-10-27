import bpy,bmesh,json,sys,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));from mesh_audit import audit
from render_control import setup,render_set
R=P.parent.parent;source=R/'models/root-cause-audit-05/current-live-source.blend'
mode=sys.argv[sys.argv.index('--')+1];h=bpy.data.objects['Anime013_Head'];notes={}
if mode=='repair':
 old=[v.co.copy() for v in h.data.vertices]
 bm=bmesh.new();bm.from_mesh(h.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
 # Existing coordinates retained during this connectivity-only operation.
 tris=[f for f in bm.faces if len(f.verts)==3]
 result=bmesh.ops.join_triangles(bm,faces=tris,angle_face_threshold=math.radians(12),angle_shape_threshold=math.radians(45),cmp_seam=True,cmp_sharp=True,cmp_uvs=True,cmp_vcols=True,cmp_materials=True)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(h.data);bm.free();h.data.update()
 notes['topology_only']={'old_faces':1107,'new_faces':len(h.data.polygons),'new_quads_from_join':len(result['faces'])}
 notes['form_fit']={'mode':'conservative topology-only repair; depth-fit trial rejected for self-crossings. Vertex coordinates identical to captured current source.'}
elif mode=='clean':
 data=json.loads((P/'clean-cage-data.json').read_text());mesh=bpy.data.meshes.new('CleanAnimeHead_QuadCage');mesh.from_pydata(data['vertices'],[],data['faces']);mesh.update();h.data=mesh
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 # Fair only transitions at the existing cage resolution; this is an authored edit, not a production rig.
 bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
 protected=set(i for indices in data['groups'].values() for i in indices)
 for step in range(10):
  proposed={}
  for v in bm.verts:
   if v.index in protected or v.is_boundary:continue
   row=222-(v.co.z-1.446197748184204)/.0007797915761063738
   if row<245 or row>365:continue
   avg=sum((e.other_vert(v).co for e in v.link_edges),v.co*0)/len(v.link_edges)
   co=v.co.copy();co+=(avg-co)*.35;proposed[v.index]=co
  for i,co in proposed.items():bm.verts[i].co=co
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
 for name,indices in data['groups'].items():g=h.vertex_groups.new(name=name);g.add(indices,1,'REPLACE')
 # The new head contains its own attached mouth bag; original separate cavity remains saved but hidden in this prototype.
 bpy.data.objects['Anime013_MouthCavity'].hide_render=True
 notes['method']=data['method'];notes['provisional_regions']=['skull under hair','ear volumes','jaw-to-neck transition'];notes['eyes']='unchanged existing eyeball geometry; no new iris detail'
else:raise RuntimeError(mode)
(P/(mode+'-build-notes.json')).write_text(json.dumps(notes,indent=2));(P/(mode+'-mesh-audit.json')).write_text(json.dumps(audit(h),indent=2));(P/(mode+'-mesh-data.json')).write_text(json.dumps({'vertices':[list(v.co) for v in h.data.vertices],'faces':[list(f.vertices) for f in h.data.polygons]}))
setup();render_set(mode,levels=(0,1),wire=True)
print('CANDIDATE_DONE',mode,notes,flush=True)
