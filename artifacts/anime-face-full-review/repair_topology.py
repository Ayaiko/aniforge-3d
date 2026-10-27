import bpy,bmesh,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-full-review';V=O/'validation';s=bpy.context.scene
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
head=bpy.data.objects['Anime013_Head'];assert not head.data.shape_keys
meshes=[o for o in s.objects if o.type=='MESH'];initial={o.name:{'verts':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'matrix':[list(r) for r in o.matrix_world]} for o in meshes}
original_cameras={o.name:{'matrix':[list(r) for r in o.matrix_world],'scale':o.data.ortho_scale} for o in s.objects if o.type=='CAMERA'}
before=bx_audit.audit(head);(O/'before-head-audit.json').write_text(json.dumps(before,indent=2))
# Declared gate: remove only opposing duplicate cap triangles, preserve every retained
# coordinate and all original eye/mouth boundaries, no new face or increased density.
(O/'trial-contract.json').write_text(json.dumps({'input':bpy.data.filepath,'hypothesis':'Two opposed duplicate triangular flaps cause the two overconnected neck-cap edges. Remove both faces of each zero-thickness flap.','technical_gate':{'overconnected_edges':0,'same_boundary_loops':[32,24,24],'retained_vertex_movement_m':0,'new_faces':0,'no_new_crossings':True},'artistic_gate':'Required views must not regress. This repair alone does not prove improved facial likeness.','whole_head_likeness':'FAIL; remains a separate required gate'},indent=2))
# Snapshot the source mesh in memory for exact before renders.
source_mesh=head.data.copy();source_mesh.name='TutorialReview_SourceSnapshot'
bm=bmesh.new();bm.from_mesh(head.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();groups={}
for f in bm.faces:groups.setdefault(tuple(sorted(v.index for v in f.verts)),[]).append(f)
flaps=[fs for fs in groups.values() if len(fs)>1];assert len(flaps)==2
removed=[]
for fs in flaps:
 assert len(fs)==2 and all(len(f.verts)==3 for f in fs)
 assert fs[0].normal.dot(fs[1].normal)<-.999
 assert all(abs(v.co.z-1.325)<1e-6 for f in fs for v in f.verts)
 removed.append({'faces':[f.index for f in fs],'verts':[v.index for v in fs[0].verts],'areas':[f.calc_area() for f in fs]})
bmesh.ops.delete(bm,geom=[f for fs in flaps for f in fs],context='FACES')
bm.normal_update();bm.to_mesh(head.data);bm.free();head.data.update();after=bx_audit.audit(head)
assert after['non_manifold_edges']==0 and after['boundary_loops']==before['boundary_loops']
assert after['faces']==before['faces']-4 and after['verts']==before['verts']-2
assert after['self_intersections']==0 and after['flipped_faces']==0
retained={tuple(v.co) for v in head.data.vertices};assert retained.issubset({tuple(v) for v in initial[head.name]['verts']})
for o in meshes:
 if o!=head:assert initial[o.name]['verts']==[list(v.co) for v in o.data.vertices] and initial[o.name]['faces']==[list(p.vertices) for p in o.data.polygons]
 assert initial[o.name]['matrix']==[list(r) for r in o.matrix_world]
for name,d in original_cameras.items():assert d['matrix']==[list(r) for r in bpy.data.objects[name].matrix_world] and d['scale']==bpy.data.objects[name].data.ortho_scale
(O/'after-head-audit.json').write_text(json.dumps(after,indent=2))
qa=qa_check.run(objects=[head.name],profile='render');(O/'head-asset-qa.json').write_text(json.dumps(qa,indent=2))
raw=bx_audit.deliverable([head],profile='render');(O/'head-delivery-qa.json').write_text(json.dumps(raw,indent=2))
assert qa['pass'] and raw['pass'],(qa,raw)
s['anime_face_learning_status']='Topology repair only: 4 opposed duplicate neck-cap triangles and 2 loose flap-tip vertices removed. Whole facial likeness and animation topology remain FAIL. Original checkpoints unchanged.'
output=R/'models/anime-face-full-review/tutorial-reviewed-topology-repair.blend'
# Snapshot is analysis-only and must not persist in the candidate.
source_mesh.use_fake_user=False
assert bpy.ops.wm.save_as_mainfile(filepath=str(output),copy=True)=={'FINISHED'}
repaired_mesh=head.data
# Supplemental cameras are only in this headless analysis process, not the saved model.
ref=bpy.data.objects['REF_front'];target=Vector((0,0,ref.location.z))
extra={}
for label,az,el in [('twenty',20,0),('high',20,20),('low',20,-20)]:
 d=bpy.data.cameras.new('TutorialReview_'+label);c=bpy.data.objects.new('TutorialReview_'+label,d);s.collection.objects.link(c);a=math.radians(az);e=math.radians(el);c.location=target+Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ref.data.ortho_scale;extra[label]=c
s.render.engine='BLENDER_WORKBENCH';s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';shade=s.display.shading;shade.light='MATCAP';shade.studio_light='clay_studio.exr';shade.color_type='MATERIAL'
views={v:bpy.data.objects['REF_'+v] for v in ['front','side','quarter']};views.update(extra)
for stage,mesh in [('before',source_mesh),('after',repaired_mesh)]:
 head.data=mesh
 for name,cam in views.items():
  s.camera=cam;s.render.filepath=str(V/f'{stage}-{name}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
head.data=repaired_mesh
# Actual edge geometry overlay, not a triangulated render proxy.
head.show_wire=True;head.show_all_edges=True
# A separate head-only flat mask pass uses Standard, independently of clay display.
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
shade.light='FLAT';shade.color_type='OBJECT'
for o in meshes:o.color=(1,0,0,1) if o.name=='Anime013_Eye_L' else ((0,1,0,1) if o.name=='Anime013_Eye_R' else (0,0,0,1))
s.camera=views['front'];s.render.filepath=str(V/'after-eye-labels-standard.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
report={'removed_opposed_duplicate_flaps':removed,'vertices_removed':2,'faces_removed':4,'retained_vertices_moved':0,'other_meshes_unchanged':True,'original_cameras_unchanged':True,'before':{k:before[k] for k in ['verts','faces','tris_equivalent','non_manifold_edges','boundary_loops']},'after':{k:after[k] for k in ['verts','faces','tris_equivalent','non_manifold_edges','boundary_loops']},'output':str(output),'head_qa_pass':qa['pass'],'head_delivery_qa_pass':raw['pass'],'whole_head_likeness':'FAIL','animation_ready':'FAIL'}
(O/'topology-repair-result.json').write_text(json.dumps(report,indent=2));print('RESULT',json.dumps(report))
