from pathlib import Path
import sys, math
import bpy
from mathutils import Vector, Quaternion
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vrm_env import ROOT, enable_vrm
enable_vrm()
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
source=args[0] if args else 'models/base-import.blend'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/source))
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1280
scene.render.resolution_y=1280
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
scene.view_settings.view_transform='Standard'
scene.world=bpy.data.worlds.new('Preview World')
scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(0.8,0.82,0.85,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=0.7
for name,location,energy,size in [('Key',(-2,-3,4),400,4),('Fill',(3,-1,2),150,3)]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.shape='DISK'; data.size=size
    ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob); ob.location=location
    ob.rotation_euler=(Vector((0,0,1.35))-ob.location).to_track_quat('-Z','Y').to_euler()
arm=next(ob for ob in bpy.data.objects if ob.type=='ARMATURE')
expression=args[4] if len(args)>4 else ''
if expression:
    values={'blink':{'Fcl_EYE_Close':1},'talk':{'Fcl_MTH_A':.75},'smile':{'Fcl_MTH_Joy':.7,'Fcl_BRW_Fun':.4}}[expression]
    for key in bpy.data.objects['Face'].data.shape_keys.key_blocks:
        for suffix,value in values.items():
            if key.name.endswith(suffix):key.value=value
for side,angle in [('L',1.22),('R',-1.22)]:
    bone=arm.pose.bones.get('J_Bip_'+side+'_UpperArm')
    if bone:
        r=bone.bone.matrix_local.to_quaternion()
        bone.rotation_mode='QUATERNION'
        bone.rotation_quaternion=r.inverted() @ Quaternion((0,1,0),angle) @ r
headshot=len(args)>3 and args[3]=='head'
angle=math.radians(float(args[2])) if len(args)>2 else 0
target=Vector((0,0,1.445 if headshot else 1.35))
camera_data=bpy.data.cameras.new('Preview Camera');camera_data.type='ORTHO';camera_data.ortho_scale=0.43 if headshot else 0.68
camera=bpy.data.objects.new('Preview Camera',camera_data);scene.collection.objects.link(camera)
camera.location=(2.5*math.sin(angle),-2.5*math.cos(angle),target.z+.06)
camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera=camera
scene.render.filepath=str(ROOT/(args[1] if len(args)>1 else 'previews/base-front.png'))
bpy.ops.render.render(write_still=True)
