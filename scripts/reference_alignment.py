"""Reconstruction audit: calibrated orthographic views and actual source crops."""
from pathlib import Path
import sys,json,math,shutil,hashlib
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import stats
out=ROOT/'previews/v0.3';out.mkdir(parents=True,exist_ok=True)
source=ROOT/'models/researcher-a-master-v0.2.blend';backup=ROOT/'models/backups/researcher-a-before-reconstruction-v0.3.blend'
if not backup.exists():shutil.copy2(source,backup)
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(source));reset_pose()
face=bpy.data.objects['Face'];face_eval=face.evaluated_get(bpy.context.evaluated_depsgraph_get());me=face_eval.to_mesh()
world=np.array([face.matrix_world@v.co for v in me.vertices]);material_bounds={}
for i,m in enumerate(me.materials):
    ids={v for p in me.polygons if p.material_index==i for v in p.vertices}
    if not ids:continue
    a=world[list(ids)];material_bounds[m.name]={'min':a.min(axis=0).tolist(),'max':a.max(axis=0).tolist(),'center':((a.min(axis=0)+a.max(axis=0))/2).tolist()}
iris_indices={v for p in me.polygons if 'EyeIris' in me.materials[p.material_index].name for v in p.vertices}
iris=world[list(iris_indices)];eye_z=float((iris[:,2].min()+iris[:,2].max())/2)
skin_ids={v for p in me.polygons if 'Face_00_SKIN' in me.materials[p.material_index].name for v in p.vertices}
skin=world[list(skin_ids)];chin_candidates=skin[(abs(skin[:,0])<.018)&(skin[:,1]<-.03)&(skin[:,2]<1.40)]
chin_z=float(chin_candidates[:,2].min())
face_eval.to_mesh_clear()
reference={'front':{'crop':[116,50,516,500],'mirror':False,'axis_pixel':316,'eye_y':272,'chin_y':395,'hair_top_y':64,'landmarks':{'pupil_left':[262,274],'pupil_right':[365,270],'eye_left_outer':[236,271],'eye_left_inner':[284,273],'eye_right_inner':[341,269],'eye_right_outer':[389,266],'mouth_left':[298,348],'mouth_right':[335,346],'nose_tip':[314,326],'chin':[316,395],'cheek_left':[229,324],'cheek_right':[404,321],'hair_left':[139,260],'hair_right':[476,270]}},'side':{'crop':[575,50,975,500],'mirror':True,'axis_pixel':775,'eye_y':272,'chin_y':395,'hair_top_y':64,'landmarks':{'nose_tip':[921,307],'chin':[874,394],'lip_front':[902,347],'pupil':[862,269],'ear_center':[746,290],'hair_back':[605,250]}},'back':{'crop':[1044,50,1444,500],'mirror':False,'axis_pixel':1244,'eye_y':272,'chin_y':395,'hair_top_y':64,'landmarks':{'hair_left':[1058,260],'hair_right':[1435,260],'hair_top':[1245,65],'nape':[1244,418]}}}
scale=(eye_z-chin_z)/(395-272)
calibration={'source':str(source),'backup':str(backup),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'eye_z':eye_z,'chin_z':chin_z,'meters_per_reference_pixel':scale,'reference_image':'assets/references/researcher-a-turnaround-v3.png','views':reference,'annotation_uncertainty_pixels':3,'priority':'hero v3 likeness/style; turnaround front geometry; mirrored side profile; back hair flow','reference_conflicts':['Side artwork is mirrored for the comparison to keep its visible ear consistent with the character-left side camera.','Back hair width in the drawing is greater than front width; a single orthographic 3D silhouette cannot have both widths exactly. Front identity takes precedence.']}
(out/'reference-calibration.json').write_text(json.dumps(calibration,indent=2))
(out/'audit-existing.json').write_text(json.dumps({'geometry':stats(),'face_material_bounds':material_bounds,'eye_z':eye_z,'chin_z':chin_z},indent=2))

original=bpy.data.images.load(str(ROOT/'assets/references/researcher-a-turnaround-v3.png'),check_existing=True)
w,h=original.size;pixels=np.empty(w*h*4,dtype=np.float32);original.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4)
assets=ROOT/'assets/references/alignment-v0.3';assets.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene;setup();scene.render.resolution_x=800;scene.render.resolution_y=900
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
directory=out/'baseline';directory.mkdir(exist_ok=True)
for name,cfg in reference.items():
    x0,y0,x1,y1=cfg['crop'];a=pixels[h-y1:h-y0,x0:x1].copy()
    if cfg['mirror']:a=a[:,::-1].copy()
    image=bpy.data.images.new('Reference_'+name,width=x1-x0,height=y1-y0,alpha=True);image.pixels.foreach_set(a.ravel());image.filepath_raw=str(assets/(name+'.png'));image.file_format='PNG';image.save();image.pack()
    target=Vector((0,0,eye_z+(cfg['eye_y']-(y0+y1)/2)*scale))
    position={'front':(0,-2,target.z),'side':(2,0,target.z),'back':(0,2,target.z)}[name]
    data=bpy.data.cameras.new('REF_'+name);data.type='ORTHO';data.ortho_scale=(y1-y0)*scale
    camera=bpy.data.objects.new('REF_'+name,data);scene.collection.objects.link(camera);camera.location=position;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera['reference_view']=name
    data.show_background_images=True;item=data.background_images.new();item.image=image;item.alpha=.32;item.display_depth='BACK';item.frame_method='FIT'
    scene.camera=camera;scene.render.filepath=str(directory/(name+'.png'));bpy.ops.render.render(write_still=True)

def sheet(dest,columns):
    width=400;height=450;canvas=np.ones((height*3,width*len(columns),4),dtype=np.float32)
    for row,name in enumerate(['front','side','back']):
        for col,kind in enumerate(columns):
            path=assets/(name+'.png') if kind=='reference' else out/kind/(name+'.png')
            im=bpy.data.images.load(str(path),check_existing=False);im.scale(width,height);a=np.empty(width*height*4,dtype=np.float32);im.pixels.foreach_get(a);yy=(2-row)*height;canvas[yy:yy+height,col*width:(col+1)*width]=a.reshape(height,width,4);bpy.data.images.remove(im)
    im=bpy.data.images.new('Reference comparison',width=width*len(columns),height=height*3,alpha=True);im.pixels.foreach_set(canvas.ravel());im.filepath_raw=str(dest);im.file_format='PNG';im.save();bpy.data.images.remove(im)
sheet(out/'reference-vs-baseline.png',['reference','baseline'])
reset_pose();scene.camera=bpy.data.objects['REF_front'];bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reference-audit-v0.3.blend'))
print('CALIBRATION',eye_z,chin_z,scale,'saved source comparison and cameras',flush=True)
