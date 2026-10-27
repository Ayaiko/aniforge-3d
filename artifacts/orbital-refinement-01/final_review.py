import bpy,bmesh,json,sys,hashlib,math
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/orbital-refinement-01';V=O/'validation';s=bpy.context.scene;head=bpy.data.objects['Anime013_Head'];base=json.load(open(O/'head-before.json'));names=['Anime013_Head','Anime013_Eye_L','Anime013_Eye_R','Anime013_MouthCavity']
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit,bx_review
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
co=np.array([v.co[:] for v in head.data.vertices]);original=np.array(base['vertices']);assert np.array_equal(co[:,[0,2]],original[:,[0,2]]);assert base['faces']==[list(p.vertices) for p in head.data.polygons]
for loop in base['boundary_loops']:assert np.array_equal(co[loop],original[loop])
free=set(json.load(open(O/'fair-70-coordinates.json'))['free_indices']);assert all(np.array_equal(co[i],original[i]) for i in range(len(co)) if i not in free)
for n,c in base['cameras'].items():assert c['matrix']==[list(r) for r in bpy.data.objects[n].matrix_world] and c['ortho_scale']==bpy.data.objects[n].data.ortho_scale
checks={};audits={};eyechanges=[]
for n in names:
 o=bpy.data.objects[n];checks[n]=qa_check.run(objects=[n],profile='render');audits[n]=bx_audit.audit(o);assert checks[n]['pass'] and audits[n]['self_intersections']==0 and audits[n]['non_manifold_edges']==0
 if n!=head.name:
  old=json.load(open(O/(n+'-before.json')));cur=np.array([v.co[:] for v in o.data.vertices]);oldco=np.array(old['vertices']);assert old['faces']==[list(p.vertices) for p in o.data.polygons]
  if n.endswith('MouthCavity'):assert np.array_equal(cur,oldco)
  else:
   assert np.array_equal(cur[:,[0,2]],oldco[:,[0,2]]);ids={i for p in o.data.polygons if p.material_index in [1,2] for i in p.vertices};assert np.array_equal(cur[list(ids)],oldco[list(ids)]);eyechanges.append({'name':n,'changed_vertices':int(np.any(cur!=oldco,axis=1).sum()),'max_move_m':float(np.abs(cur-oldco).max()),'iris_pupil_unchanged':True})
whole=bx_audit.deliverable([bpy.data.objects[n] for n in names],profile='render');(O/'retained-qa.json').write_text(json.dumps({'individual_checks':checks,'audits':audits,'whole_asset':whole},indent=2))
s['orbital_refinement_status']='LOCAL ORBITAL SURFACE PASS: fixed apertures, fair skin transitions, outer sclera curvature. WHOLE HEAD LIKENESS / DEFORMATION FAIL. Ear root/chin trials not incorporated. Original checkpoints preserved.'
s['workflow_status']='Orbital surface refinement checkpoint only; no hair/detail/UV/rig/final export approval'
s.camera=bpy.data.objects['REF_quarter'];s.render.filepath=str(V/'retained-quarter.png')
final=R/'models/orbital-refinement-01/orbital-refinement-retained.blend';assert bpy.ops.wm.save_as_mainfile(filepath=str(final),copy=True)=={'FINISHED'}
# Supplemental cameras stay analysis-only. Original validation cameras are unchanged.
ref=bpy.data.objects['REF_front'];target=Vector((0,0,ref.location.z));extra={}
for label,az,el in [('twenty',20,0),('high',20,20),('low',20,-20),('other-quarter',-45,0)]:
 d=bpy.data.cameras.new('OrbitalReview_'+label);c=bpy.data.objects.new('OrbitalReview_'+label,d);s.collection.objects.link(c);a=math.radians(az);e=math.radians(el);c.location=target+Vector((math.sin(a)*math.cos(e),-math.cos(a)*math.cos(e),math.sin(e)));c.rotation_euler=(target-c.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=ref.data.ortho_scale;extra[label]=c
original_eye={n:json.load(open(O/(n+'-before.json'))) for n in ['Anime013_Eye_L','Anime013_Eye_R']};final_meshes={n:bpy.data.objects[n].data for n in names};source_meshes={}
for n in ['Anime013_Head','Anime013_Eye_L','Anime013_Eye_R']:
 ob=bpy.data.objects[n];me=ob.data.copy();data=base if n==head.name else original_eye[n]
 for v,c in zip(me.vertices,data['vertices']):v.co=c
 me.update();source_meshes[n]=me
for stage in ['before','retained']:
 for n in source_meshes:bpy.data.objects[n].data=source_meshes[n] if stage=='before' else final_meshes[n]
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
 cams={v:bpy.data.objects['REF_'+v] for v in ['front','side','quarter']};cams.update(extra)
 for view,cam in cams.items():
  s.camera=cam;s.render.filepath=str(V/f'{stage}-{view}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
for n in source_meshes:bpy.data.objects[n].data=final_meshes[n]
wire=bx_review.review([bpy.data.objects[n] for n in names],str(V/'retained-wire'),views=('front','right','threequarter','low'),modes=('wire',),res=400)
report={'output':str(final),'stats':{n:{'verts':audits[n]['verts'],'faces':audits[n]['faces'],'tris':audits[n]['tris_equivalent'],'dimensions':audits[n]['dimensions']} for n in names},'head_changed_vertices':int(np.any(co!=original,axis=1).sum()),'head_max_move_m':float(np.abs(co-original).max()),'eye_changes':eyechanges,'aperture_coordinates_unchanged':True,'head_xz_unchanged':True,'other_head_regions_unchanged':True,'mouth_mesh_unchanged':True,'original_cameras_unchanged':True,'geometry_qa_individual_pass':True,'whole_asset_qa_pass':whole['pass'],'whole_asset_errors':whole['errors'],'full_likeness':'FAIL','animation_ready':'FAIL','ear_trials':'NOT INCORPORATED','wire':wire}
(O/'retained-result.json').write_text(json.dumps(report,indent=2,default=str));print('RESULT',json.dumps(report,default=str))
