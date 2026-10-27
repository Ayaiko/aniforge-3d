import bpy,bmesh,json,sys,math
from pathlib import Path
import numpy as np
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/orbital-refinement-01';V=O/'validation';M=R/'models/orbital-refinement-01';s=bpy.context.scene;head=bpy.data.objects['Anime013_Head'];orig=np.array([v.co[:] for v in head.data.vertices]);mesh_faces=[list(p.vertices) for p in head.data.polygons]
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
cams={n:{'matrix':[list(r) for r in bpy.data.objects[n].matrix_world],'scale':bpy.data.objects[n].data.ortho_scale} for n in ['REF_front','REF_side','REF_quarter']}
contract={'input':bpy.data.filepath,'intent':'Fair the depth transition in the existing orbital skin without moving lid apertures or adding geometry.','technique':'Authored screened thin-plate solve in XZ parameterization; not Blender brush strokes.','protected':['all X/Z','24+24 lid boundary coordinates','mouth/nose/chin','eye meshes','original cameras','connectivity'],'checks':{'eye_iou_min':.85,'eye_outside_max':.05,'no_new_crossings':True,'no_nonmanifold':True,'same_boundary_loops':[32,24,24],'visual_improvement_required':True},'trials':['35%','70%','100% of solved displacement'],'maximum_full_displacement_m':.007492,'whole_likeness_cannot_follow_from_local_metric':True};(O/'trial-contract.json').write_text(json.dumps(contract,indent=2))
def apply(co):
 for v,c in zip(head.data.vertices,co):v.co=c
 head.data.update()
def render(stage):
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
 # Use the original artistic display for all clay comparisons.
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
 for name in ['front','side','quarter']:
  s.camera=bpy.data.objects['REF_'+name];s.render.filepath=str(V/f'{stage}-{name}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 s.display.shading.light='FLAT';s.display.shading.color_type='OBJECT'
 for o in [x for x in s.objects if x.type=='MESH']:o.color=(1,0,0,1) if o.name=='Anime013_Eye_L' else ((0,1,0,1) if o.name=='Anime013_Eye_R' else (0,0,0,1))
 s.camera=bpy.data.objects['REF_front'];s.render.filepath=str(V/f'{stage}-labels.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
 # Restore display state before saving the editable trial.
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.display.shading.light='MATCAP';s.display.shading.color_type='MATERIAL';s.camera=bpy.data.objects['REF_quarter']
def bend(ids):
 bm=bmesh.new();bm.from_mesh(head.data);bm.verts.ensure_lookup_table();bm.normal_update();angles=[]
 for e in bm.edges:
  if len(e.link_faces)==2 and any(v.index in ids for v in e.verts):angles.append(math.degrees(e.calc_face_angle()))
 bm.free();return {'max_dihedral_deg':float(np.max(angles)),'p95_dihedral_deg':float(np.percentile(angles,95)),'mean_dihedral_deg':float(np.mean(angles))}
ids=set(json.load(open(O/'fair-100-coordinates.json'))['free_indices']);results={}
for stage in ['before','fair-35','fair-70','fair-100']:
 co=orig if stage=='before' else np.array(json.load(open(O/(stage+'-coordinates.json')))['vertices']);apply(co);assert np.array_equal(co[:,[0,2]],orig[:,[0,2]])
 assert mesh_faces==[list(p.vertices) for p in head.data.polygons]
 for name,c in cams.items():assert c['matrix']==[list(r) for r in bpy.data.objects[name].matrix_world] and c['scale']==bpy.data.objects[name].data.ortho_scale
 audit=bx_audit.audit(head);qa=qa_check.run(objects=[head.name],profile='render');results[stage]={'max_move_m':float(np.abs(co-orig).max()),'bend':bend(ids),'audit':audit,'qa':qa};assert audit['self_intersections']==0 and audit['non_manifold_edges']==0 and qa['pass']
 render(stage)
 if stage!='before':
  s['orbital_refinement_status']='EXPERIMENTAL: local eye mask and clay visual review pending; whole likeness/animation FAIL.';assert bpy.ops.wm.save_as_mainfile(filepath=str(M/(stage+'.blend')),copy=True)=={'FINISHED'}
(O/'trial-results.json').write_text(json.dumps(results,indent=2));print('RESULT',json.dumps({k:{'max_move_m':v['max_move_m'],'bend':v['bend'],'head_qa_pass':v['qa']['pass']} for k,v in results.items()}))
