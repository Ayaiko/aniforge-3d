"""Install-independent, bounded trial of the reviewed skill protocols on existing geometry."""
from pathlib import Path
import json,math,hashlib,shutil
import numpy as np
from PIL import Image,ImageDraw
root=Path(__file__).resolve().parents[1];out=root/'artifacts/skills-workflow-upgrade';analysis=out/'source_analysis';analysis.mkdir(exist_ok=True)
proof=json.loads((root/'artifacts/reconstruction-v2-mcp/anime-013-final-geometry-proof-parsed.json').read_text());head=next(o for o in proof['objects'] if o['name']=='Anime013_Head');vs=head['vertices']
S=.0007797915761063738;EYE=1.446197748184204
nose=min((p for p in vs if abs(p[0])<.01 and 1.405<p[2]<1.44),key=lambda p:p[1]);chin=min((p for p in vs if abs(p[0])<.008 and p[1]<-.045 and p[2]>1.33),key=lambda p:p[2]);mouth=min((p for p in vs if abs(p[0])<.003 and 1.385<p[2]<1.390),key=lambda p:p[1])
points=np.array([[(146-200)*S,-.0805,EYE+(222-224)*S],[(249-200)*S,-.0805,EYE+(222-220)*S],nose,mouth,chin])
hero_pixels=np.array([[423,405],[589,384],[491,479],[520,529],[526,616]],float);crop=np.array([212,80]);targets=(hero_pixels-crop)*2/3
best=None
for degrees in np.arange(0,55.01,.25):
    yaw=math.radians(degrees);qx=points[:,0]*math.cos(yaw)+points[:,1]*math.sin(yaw);qz=-points[:,2];A=[];b=[]
    for x,z,target in zip(qx,qz,targets):A.extend([[x,-z,1,0],[z,x,0,1]]);b.extend(target)
    A=np.array(A);b=np.array(b);weights=np.repeat(np.sqrt([3,3,1,1,3]),2);coef=np.linalg.lstsq(A*weights[:,None],b*weights,rcond=None)[0];pred=(A@coef).reshape(-1,2);err=np.mean(np.sum((pred-targets)**2,axis=1));a,c,tx,ty=coef
    if best is None or err<best['mse']:best={'mse':float(err),'yaw_degrees':float(degrees),'roll_radians':float(math.atan2(c,a)),'scale_pixels_per_m':float(math.hypot(a,c)),'translation':[float(tx),float(ty)],'predicted':pred.tolist()}
theta=math.radians(best['yaw_degrees']);roll=best['roll_radians'];scale=best['scale_pixels_per_m'];R=np.array([[math.cos(roll),-math.sin(roll)],[math.sin(roll),math.cos(roll)]]);target2=R.T@((np.array([200,225])-best['translation'])/scale)
right0=np.array([math.cos(theta),math.sin(theta),0]);up0=np.array([0,0,1]);back=np.array([math.sin(theta),-math.cos(theta),0]);target=right0*target2[0]+up0*(-target2[1]);location=target+back*3;right=math.cos(roll)*right0+math.sin(roll)*up0;up=-math.sin(roll)*right0+math.cos(roll)*up0;matrix=np.eye(4);matrix[:3,:3]=np.column_stack([right,up,back]);matrix[:3,3]=location
best.update({'matrix':matrix.tolist(),'ortho_scale':450/scale,'landmark_rms_px':math.sqrt(best['mse']),'reference_crop':[212,80,812,755],'note':'Approximate orthographic proxy of the supplied hero pose. No image warp. 45-degree REF_quarter remains separate; no exact 45-degree plate exists.'});(analysis/'hero-camera-registration.json').write_text(json.dumps(best,indent=2))
hero=Image.open(root/'assets/concepts/researcher-a-refined-v3.png').crop((212,80,812,755)).resize((400,450),Image.Resampling.LANCZOS);hero.save(analysis/'hero-reference.png')
eye_curves=[[[120,216],[134,211],[155,212],[168,223]],[[120,216],[133,232],[152,233],[168,223]],[[225,222],[236,212],[257,208],[274,212]],[[225,222],[239,234],[263,229],[274,212]]]
def curve(points):
    result=[]
    for t in np.linspace(0,1,81):
        w=np.array([(1-t)**3,3*t*(1-t)**2,3*t*t*(1-t),t**3]);result.append(tuple(w@np.array(points)))
    return result
mask=Image.new('RGBA',(400,450),(0,0,0,0));draw=ImageDraw.Draw(mask)
for k in [0,2]:draw.polygon(curve(eye_curves[k])+list(reversed(curve(eye_curves[k+1]))),fill=(255,255,255,255))
mask.save(analysis/'front-eye-reference-mask.png')
sources=[]
for role,path in [('front','assets/references/alignment-v0.3/front.png'),('side','assets/references/alignment-v0.3/side.png'),('back','assets/references/alignment-v0.3/back.png'),('hero','assets/concepts/researcher-a-refined-v3.png')]:
    p=root/path;sources.append({'role':role,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(Image.open(p).size)})
manifest={'schema':'vtuber.reference_manifest.v1','source_files':sources,'primary_view':'front','active_scene':'Anime_Reference_013','expected_primary_parts':{'count':4,'labels':['Anime013_Head','Anime013_Eye_L','Anime013_Eye_R','Anime013_MouthCavity']},'structural_parts':['head','left eye','right eye','mouth cavity'],'excluded_parts':['hair','clothes','glasses','reference empties','cameras','objects from other scenes'],'coordinate_contract':{'metres_per_pixel':S,'eye_z':EYE,'front_u':'200+x/S','side_u':'200+y/S','v':'222-(z-eye_z)/S','side_reference_is_mirrored':True},'validation_thresholds':{'visible_eye_mask_iou_min':.85,'eye_surface_outside_reference_ratio_max':.05,'landmark_drift_px_max':4,'self_crossings_max':0,'warped_quads_max':0,'part_count_exact':True},'overrides':{'no_new_character_or_base_mesh':True,'no_added_polygons':True,'no_hair_or_high_frequency_sculpting':True,'preserve_original_files':True,'generic_human_ratios_forbidden':True,'full_hair_mask_vs_bald_head_iou_forbidden':True,'metrics_alone_cannot_pass_artistic_gate':True},'uncertainties':['Hair-covered skull contour is inferred.','No exact orthographic 45-degree reference; hero proxy camera is approximate.','Reference eye polygons are hand traced and have roughly 1-2 px uncertainty.']}
(out/'reference_manifest.json').write_text(json.dumps(manifest,indent=2));(analysis/'facial-features.json').write_text(json.dumps({'front_eye_beziers':eye_curves,'front_nose':[200,257],'front_mouth':[200,297],'front_chin':[200,345],'side_nose':[53,257],'side_chin':[100,344],'hero_landmarks_crop':targets.tolist()},indent=2))
# Packed reference images: temp paths avoid a native Documents file-open stall.
for view in ['front','side','back']:shutil.copy2(root/f'assets/references/alignment-v0.3/{view}.png',f'/tmp/vtuber-workflow-reference-{view}.png')
calls=[]
setup="import bpy,json,math\nfrom mathutils import Matrix\nassert bpy.context.scene.name=='Anime_Reference_013'\nscene=bpy.context.scene\ncam=bpy.data.objects.get('REF_hero_workflow')\nif cam is None:\n    data=bpy.data.cameras.new('REF_hero_workflow_Data')\n    cam=bpy.data.objects.new('REF_hero_workflow',data)\n    scene.collection.objects.link(cam)\ncam.data.type='ORTHO'\ncam.data.ortho_scale="+repr(best['ortho_scale'])+"\ncam.matrix_world=Matrix("+repr(best['matrix'])+")\nprint('HERO_CAMERA_REGISTERED_WITHOUT_WARPING_REFERENCE')"
calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='skills-register-hero-camera'))
setup="""import bpy,math
scene=bpy.context.scene
col=bpy.data.collections.get('REF_Workflow_Images')
if col is None:
    col=bpy.data.collections.new('REF_Workflow_Images')
    scene.collection.children.link(col)
col['exclude_from_export']=True
"""
for view,loc,rot in [('front',(0,.25,EYE-3*S),(math.pi/2,0,0)),('side',(-.25,0,EYE-3*S),(math.pi/2,0,math.pi/2)),('back',(0,-.25,EYE-3*S),(math.pi/2,0,math.pi))]:
    setup+=f"\nimg=bpy.data.images.load('/tmp/vtuber-workflow-reference-{view}.png',check_existing=True)\nimg.pack()\nob=bpy.data.objects.get('REF_Image_{view}')\nif ob is None:\n    ob=bpy.data.objects.new('REF_Image_{view}',None)\n    col.objects.link(ob)\nob.empty_display_type='IMAGE'\nob.data=img\nob.empty_display_size={450*S!r}\nob.location={loc!r}\nob.rotation_euler={rot!r}\nob.color=(1,1,1,.25)\nob.hide_render=True\nob['metres_per_pixel']={S!r}\nob['role']='Reference only; cameras and overlays are the measurement authority'\n"
setup+="print('REFERENCE_IMAGES_PACKED_AND_EXPORT_EXCLUDED')"
calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='skills-reference-images-packed'))
def render(stage,view,camera,labels=False):
    if labels:
        code="""import bpy
scene=bpy.context.scene
shade=scene.display.shading
shade.light='FLAT'
shade.color_type='OBJECT'
for ob in scene.objects:
    if ob.type=='MESH':
        ob.color=(1,0,0,1) if ob.name=='Anime013_Eye_L' else ((0,1,0,1) if ob.name=='Anime013_Eye_R' else (0,0,0,1))
"""
    else:code="import bpy\nscene=bpy.context.scene\nscene.display.shading.light='MATCAP'\nscene.display.shading.studio_light='clay_studio.exr'\nscene.display.shading.color_type='MATERIAL'\n"
    code+=f"scene.camera=bpy.data.objects[{camera!r}]\nscene.render.filepath='/tmp/vtuber-skills-{stage}-{view}.png'\nbpy.ops.render.render(write_still=True)\nprint('RENDERED_{stage}_{view}')"
    calls.extend([dict(tool='execute_blender_code',arguments={'code':code},label=f'skills-render-{stage}-{view}'),dict(tool='look',arguments={'image':'Render Result','max_size':900},label=f'skills-{stage}-{view}')])
for view,cam in [('front','REF_front'),('side','REF_side'),('quarter','REF_quarter'),('hero','REF_hero_workflow')]:render('before',view,cam)
render('before','eye-label','REF_front',True)
edit="""import bpy,json
scene=bpy.context.scene
before={o.name:[len(o.data.vertices),len(o.data.polygons)] for o in scene.objects if o.type=='MESH'}
for name in ['Anime013_Eye_L','Anime013_Eye_R']:
    ob=bpy.data.objects[name]
    lo=min(v.co.y for v in ob.data.vertices)
    hi=max(v.co.y for v in ob.data.vertices)
    center=(lo+hi)/2
    for v in ob.data.vertices:v.co.y=-.073+(v.co.y-center)*(.0075/((hi-lo)/2))
    ob.data.update()
    ob['workflow_primary_fix']='Existing eye depth compressed; no topology or polygon change'
head=bpy.data.objects['Anime013_Head']
for mod in head.modifiers:
    if mod.type=='SUBSURF':
        mod.show_viewport=False
        mod.show_render=False
head['surface_preview_gate']='Rejected: evaluated eye-root warps and neck self-crossings; subdivision disabled'
after={o.name:[len(o.data.vertices),len(o.data.polygons)] for o in scene.objects if o.type=='MESH'}
assert before==after
print(json.dumps({'before':before,'after':after,'topology_unchanged':True,'new_character_created':False}))
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':edit},label='skills-bounded-primary-correction'))
for view,cam in [('front','REF_front'),('side','REF_side'),('quarter','REF_quarter'),('hero','REF_hero_workflow')]:render('after',view,cam)
render('after','eye-label','REF_front',True)
save="""import bpy,json
scene=bpy.context.scene
scene.display.shading.light='MATCAP'
scene.display.shading.color_type='MATERIAL'
scene.camera=bpy.data.objects['REF_quarter']
scene['workflow_status']='Primary forms checkpoint only; artistic gate pending, no hair/detail/export'
bpy.ops.wm.save_as_mainfile(filepath='/tmp/vtuber-workflow-primary-01.blend',copy=True)
print('CHECKPOINT_PRIMARY_01_SAVED_SEPARATELY')
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':save},label='skills-primary-checkpoint'))
audit=(root/'artifacts/reconstruction-v2-mcp/audit-frozen-head.py').read_text().replace("assert scene.name=='Geometry_Failure_Analysis_V2'","assert scene.name=='Anime_Reference_013'").replace('Frozen V2 head-002; read-only geometry analysis through live MCP','Skills workflow primary checkpoint: existing mesh, no topology growth')
calls.append(dict(tool='execute_blender_code',arguments={'code':audit},label='skills-primary-audit'))
(out/'workflow-trial-mcp-request.json').write_text(json.dumps(calls));print('Manifest, masks, hero registration and',len(calls),'bounded MCP steps ready; hero fit rms',best['landmark_rms_px'])
