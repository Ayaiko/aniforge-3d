import bpy,sys,json,math
import numpy as np
from pathlib import Path
sys.path.insert(0,'/Users/graind/.codex/skills/anime-face-sculpting/scripts')
from constrained_relax import relax_region
ROOT=Path('/Users/graind/Documents/ChatGPT/vTuber');OUT=ROOT/'artifacts/anime-face-learning';MODELS=ROOT/'models/anime-face-learning'
s=bpy.context.scene;head=bpy.data.objects['Anime013_Head'];meshes=[o for o in s.objects if o.type=='MESH'];original={o.name:np.array([v.co[:] for v in o.data.vertices]) for o in meshes}
counts={o.name:[len(o.data.vertices),len(o.data.polygons)] for o in meshes}
# Exact camera matrices are held constant across every candidate.
cameras={v:{'matrix':[list(r) for r in bpy.data.objects['REF_'+v].matrix_world],'ortho_scale':bpy.data.objects['REF_'+v].data.ortho_scale} for v in ['front','side','quarter']}
def restore():
 for o in meshes:
  for v,co in zip(o.data.vertices,original[o.name]):v.co=co
  o.data.update()
def clay(stage):
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
 for view in ['front','side','quarter']:
  s.camera=bpy.data.objects['REF_'+view];s.render.filepath=str(OUT/'validation'/f'{stage}-{view}.png');bpy.ops.render.render(write_still=True)
def eye_labels(stage):
 shade=s.display.shading;shade.light='FLAT';shade.color_type='OBJECT'
 for o in meshes:o.color=(1,0,0,1) if o.name=='Anime013_Eye_L' else ((0,1,0,1) if o.name=='Anime013_Eye_R' else (0,0,0,1))
 s.camera=bpy.data.objects['REF_front'];s.render.filepath=str(OUT/'validation'/f'{stage}-eyes.png');bpy.ops.render.render(write_still=True)
 shade.light='MATCAP';shade.color_type='MATERIAL'
def relax():
 co=original[head.name];x=np.abs(co[:,0]);z=co[:,2];y=co[:,1]
 weights=np.exp(-((x-.039)/.027)**4-((z-1.425)/.055)**4)
 weights[(y>-.035)|(x<.014)|((z<1.405)&(x<.030))|(z<1.365)|(z>1.485)]=0
 # All original eye/mouth rims and mesh singularities remain fixed in helper.
 return relax_region(head,weights,steps=10,strength=.38,max_move=.002,axis_mask=(0,1,0))
def eyes():
 reports=[]
 for name in ['Anime013_Eye_L','Anime013_Eye_R']:
  o=bpy.data.objects[name];co=original[name].copy();center=(co[:,[0,2]].min(axis=0)+co[:,[0,2]].max(axis=0))/2
  ids=set(v for p in o.data.polygons if p.material_index in [1,2] for v in p.vertices)
  # Smooth radial remap enlarges the iris while avoiding a discontinuity at a material seam.
  dx=co[:,0]-center[0];dz=co[:,2]-center[1];r=np.sqrt(dx*dx+dz*dz)
  factor=1+.15*np.exp(-(r/.011)**4)
  co[:,0]=center[0]+dx*factor;co[:,2]=center[1]+dz*factor
  # Only the forward-facing cap moves behind the rim; back of globe stays in place.
  front=np.clip((-.073-co[:,1])/.0075,0,1)
  co[:,1]+=.0007*front**2
  for v,p in zip(o.data.vertices,co):v.co=p
  o.data.update();reports.append({'name':name,'iris_radial_scale_max':float(factor.max()),'maximum_depth_recession_m':float((co[:,1]-original[name][:,1]).max()),'max_total_movement_m':float(np.linalg.norm(co-original[name],axis=1).max())})
 return reports
results={}
clay('before');eye_labels('before')
for stage in ['relax-only','eyes-only','combined']:
 restore();report={}
 if stage in ['relax-only','combined']:report['relax']=relax()
 if stage in ['eyes-only','combined']:report['eyes']=eyes()
 assert counts=={o.name:[len(o.data.vertices),len(o.data.polygons)] for o in meshes}
 for view,v in cameras.items():
  cam=bpy.data.objects['REF_'+view];assert v['matrix']==[list(r) for r in cam.matrix_world];assert v['ortho_scale']==cam.data.ortho_scale
 clay(stage);eye_labels(stage)
 s.camera=bpy.data.objects['REF_quarter'];s['anime_face_learning_status']='Experimental candidate; compare with source; not production approval'
 bpy.ops.wm.save_as_mainfile(filepath=str(MODELS/f'trial-{stage}.blend'),copy=True)
 report['counts_unchanged']=True
 report['head_front_projection_max_drift_m']=float(np.abs(np.array([v.co[:] for v in head.data.vertices])[:,[0,2]]-original[head.name][:,[0,2]]).max())
 results[stage]=report
(OUT/'trial-changes.json').write_text(json.dumps({'cameras':cameras,'counts':counts,'trials':results},indent=2))
print('TRIALS_COMPLETE',json.dumps(results),flush=True)
