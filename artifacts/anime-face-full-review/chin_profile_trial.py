import bpy,bmesh,sys,json,math
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-full-review';V=O/'validation';s=bpy.context.scene;h=bpy.data.objects['Anime013_Head']
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
# Source-based transfer: fit the existing chin profile with a broad bounded move,
# rather than smoothing. User front/side reference, not tutorial head proportions.
contract={'input':bpy.data.filepath,'reference_side_chin_px':[100,344],'trace_uncertainty_px':2,'metres_per_pixel':0.0007797915761063738,'hypothesis':'Existing side chin is about 11 px behind the traced target. Move lower central chin forward up to 8 mm with smooth falloff.','protected':['all head X/Z coordinates','all vertices z>=1.385, including mouth, nose and eyes','all other mesh data','original camera transforms'],'acceptance':{'chin_side_error_px_max':2,'front_silhouette_change_px_max':0,'new_topology_defects_max':0,'visible_new_pinching':False},'classification':'Authored data-level mass deformation inspired by profile/multi-view practice; not a replay of sculpt strokes.'}
(O/'chin-trial-contract.json').write_text(json.dumps(contract,indent=2))
original=[v.co.copy() for v in h.data.vertices];before=bx_audit.audit(h);changes=[]
def ease(t):t=max(0,min(1,t));return t*t*(3-2*t)
for v,c in zip(h.data.vertices,original):
 w=(1-ease((abs(c.x)-.010)/.030))*(1-ease((c.z-1.360)/.025))*ease((-c.y-.035)/.025)
 if w>0:
  v.co.y-=.008*w;changes.append({'index':v.index,'weight':w,'move_m':.008*w})
h.data.update();after=bx_audit.audit(h)
assert before['verts']==after['verts'] and before['faces']==after['faces'] and after['self_intersections']==0 and after['non_manifold_edges']==0 and after['flipped_faces']==0
assert all(v.co.x==c.x and v.co.z==c.z for v,c in zip(h.data.vertices,original))
assert all(v.co==c for v,c in zip(h.data.vertices,original) if c.z>=1.385)
qa=qa_check.run(objects=[h.name],profile='render');assert qa['pass'];(O/'chin-trial-qa.json').write_text(json.dumps({'qa':qa,'audit':after},indent=2))
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
for view in ['front','side','quarter']:
 s.camera=bpy.data.objects['REF_'+view];s.render.filepath=str(V/f'chin-trial-{view}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
s['anime_face_learning_status']='EXPERIMENTAL chin profile trial: must inspect reference front/side/45 and reject if silhouette/shading regresses. Full likeness still FAIL.'
p=R/'models/anime-face-full-review/chin-profile-trial.blend';assert bpy.ops.wm.save_as_mainfile(filepath=str(p),copy=True)=={'FINISHED'}
(O/'chin-trial-changes.json').write_text(json.dumps({'changed_vertices':len(changes),'maximum_movement_m':max(c['move_m'] for c in changes),'changes':changes,'output':str(p)},indent=2));print('RESULT',len(changes),max(c['move_m'] for c in changes))
