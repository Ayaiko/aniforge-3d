import bpy,bmesh,json,sys,math
from pathlib import Path
import numpy as np
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/orbital-refinement-01';V=O/'validation';M=R/'models/orbital-refinement-01';s=bpy.context.scene;head=bpy.data.objects['Anime013_Head'];orig=np.array([v.co[:] for v in head.data.vertices])
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
(O/'ear-root-lowered-contract.json').write_text(json.dumps({'input':bpy.data.filepath,'intent':'Remove small pyramidal skin protrusions above the integrated ear roots.','free_indices':[655,656,689,690,740,741,747,748],'max_full_movement_m':.013,'protected':['ear shell','eye openings and eye meshes','nose/mouth/chin','all other head vertices','reference cameras','topology'],'acceptance':'Reduced visible root spike without a new depression, shading seam, crossings or changed reference silhouette. Whole-head likeness remains separate.'},indent=2))
results={}
for pct in ["lowered"]:
 stage=f'ear-root-{pct}';data=json.load(open(O/(stage+'-coordinates.json')));co=np.array(data['vertices']);free=set(data['indices']);assert all(np.allclose(co[i],orig[i],atol=1e-8,rtol=0) for i in range(len(co)) if i not in free)
 for i in range(len(co)):
  if i not in free:co[i]=orig[i]
 for v,c in zip(head.data.vertices,co):v.co=c
 head.data.update();a=bx_audit.audit(head);q=qa_check.run(objects=[head.name],profile='render');assert a['non_manifold_edges']==0 and a['self_intersections']==0 and q['pass']
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 for view in ['front','side','quarter']:
  s.camera=bpy.data.objects['REF_'+view];s.render.filepath=str(V/f'{stage}-{view}.png');assert bpy.ops.render.render(write_still=True)=={'FINISHED'}
 s.camera=bpy.data.objects['REF_quarter'];s['orbital_refinement_status']='EXPERIMENTAL ear root fairing on orbital candidate; visual decision pending. Whole likeness and animation FAIL.';assert bpy.ops.wm.save_as_mainfile(filepath=str(M/(stage+'.blend')),copy=True)=={'FINISHED'}
 results[stage]={'head_audit':a,'qa':q,'max_move_from_orbital_m':float(np.linalg.norm(co-orig,axis=1).max())}
(O/'ear-root-lowered-results.json').write_text(json.dumps(results,indent=2));print('RESULT',json.dumps({k:v['max_move_from_orbital_m'] for k,v in results.items()}))
