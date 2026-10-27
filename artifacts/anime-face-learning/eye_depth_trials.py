import bpy,json
import numpy as np
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-learning';s=bpy.context.scene
obs=[bpy.data.objects[n] for n in ['Anime013_Eye_L','Anime013_Eye_R']];base={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in obs};meshes=[o for o in s.objects if o.type=='MESH'];results={}
for mm in [2,4,6]:
 stage=f'eye-depth-{mm}mm'
 for o in obs:
  co=base[o.name].copy();cx=(co[:,0].min()+co[:,0].max())/2;cz=(co[:,2].min()+co[:,2].max())/2
  dx=co[:,0]-cx;dz=co[:,2]-cz;r=np.sqrt(dx*dx+dz*dz);f=1+.12*np.exp(-(r/.011)**4)
  co[:,0]=cx+dx*f;co[:,2]=cz+dz*f;co[:,1]+=mm/1000
  for v,p in zip(o.data.vertices,co):v.co=p
  o.data.update()
 s.render.engine='BLENDER_WORKBENCH';shade=s.display.shading;shade.light='MATCAP';shade.studio_light='clay_studio.exr';shade.color_type='MATERIAL';s.render.image_settings.file_format='PNG'
 for view in ['front','side','quarter']:
  s.camera=bpy.data.objects['REF_'+view];s.render.filepath=str(O/'validation'/f'{stage}-{view}.png');bpy.ops.render.render(write_still=True)
 shade.light='FLAT';shade.color_type='OBJECT'
 for o in meshes:o.color=(1,0,0,1) if o.name=='Anime013_Eye_L' else ((0,1,0,1) if o.name=='Anime013_Eye_R' else (0,0,0,1))
 s.camera=bpy.data.objects['REF_front'];s.render.filepath=str(O/'validation'/f'{stage}-eyes.png');bpy.ops.render.render(write_still=True)
 shade.light='MATCAP';shade.color_type='MATERIAL';s.camera=bpy.data.objects['REF_quarter']
 s['anime_face_learning_status']='Eye-depth experiment only; likeness not certified'
 bpy.ops.wm.save_as_mainfile(filepath=str(R/'models/anime-face-learning'/f'trial-{stage}.blend'),copy=True)
 results[stage]={'depth_translation_m':mm/1000,'iris_radial_scale_max':1.12,'head_geometry_unchanged':True}
(O/'eye-depth-trial-changes.json').write_text(json.dumps(results,indent=2));print('EYE_DEPTH_TRIALS_COMPLETE')
