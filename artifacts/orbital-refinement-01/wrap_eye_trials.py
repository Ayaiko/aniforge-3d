import bpy,json,sys,math
import numpy as np
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/orbital-refinement-01';V=O/'validation';M=R/'models/orbital-refinement-01';s=bpy.context.scene;h=bpy.data.objects['Anime013_Head']
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
base=np.array([v.co[:] for v in h.data.vertices]);eye_original={n:np.array([v.co[:] for v in bpy.data.objects[n].data.vertices]) for n in ['Anime013_Eye_L','Anime013_Eye_R']}
def apply(obj,co):
 for v,c in zip(obj.data.vertices,co):v.co=c
 obj.data.update()
def render(stage):
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
 for v in ['front','side','quarter']:
  s.camera=bpy.data.objects['REF_'+v];s.render.filepath=str(V/f'{stage}-{v}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
 s.view_settings.view_transform='Standard';s.view_settings.look='None';s.display.shading.light='FLAT';s.display.shading.color_type='OBJECT'
 for o in [x for x in s.objects if x.type=='MESH']:o.color=(1,0,0,1) if o.name=='Anime013_Eye_L' else ((0,1,0,1) if o.name=='Anime013_Eye_R' else (0,0,0,1))
 s.camera=bpy.data.objects['REF_front'];s.render.filepath=str(V/f'{stage}-labels.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.display.shading.light='MATCAP';s.display.shading.color_type='MATERIAL';s.camera=bpy.data.objects['REF_quarter']
results={}
for pct in [35,70]:
 stage=f'fair-{pct}-wrap';co=np.array(json.load(open(O/f'fair-{pct}-coordinates.json'))['vertices']);apply(h,co);eyes=[]
 for n,orig in eye_original.items():
  o=bpy.data.objects[n];c=orig.copy();center=(c[:,0].max()+c[:,0].min())/2;sign=1 if center>0 else -1;t=np.clip((sign*(c[:,0]-center)-.013)/.012,0,1);w=t*t*(3-2*t);dy=.0085*w*w;c[:,1]+=dy;apply(o,c)
  # Central iris/pupil and gaze geometry are protected in this pass.
  iris_ids={i for p in o.data.polygons if p.material_index in [1,2] for i in p.vertices};assert np.array_equal(c[list(iris_ids)],orig[list(iris_ids)])
  q=qa_check.run(objects=[n],profile='render');a=bx_audit.audit(o);assert q['pass'] and a['self_intersections']==0
  eyes.append({'name':n,'max_move_m':float(dy.max()),'changed_vertices':int((dy>0).sum()),'iris_pupil_unchanged':True,'qa':q,'audit':a})
 a=bx_audit.audit(h);q=qa_check.run(objects=[h.name],profile='render');assert q['pass'] and a['self_intersections']==0 and a['non_manifold_edges']==0
 render(stage);s['orbital_refinement_status']='EXPERIMENTAL orbital depth fairing + outer sclera curvature; visual gate pending. Full likeness and animation FAIL.';assert bpy.ops.wm.save_as_mainfile(filepath=str(M/(stage+'.blend')),copy=True)=={'FINISHED'}
 results[stage]={'head_audit':a,'head_qa':q,'eyes':eyes}
(O/'wrap-trial-results.json').write_text(json.dumps(results,indent=2));print('RESULT',json.dumps({k:{'head_qa':v['head_qa']['pass'],'eye_qa':[x['qa']['pass'] for x in v['eyes']]} for k,v in results.items()}))
