from pathlib import Path
import sys,math,json
import bpy
from mathutils import Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,render_views
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
version=args[0] if args else 'master'
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'models/researcher-a-{version}-v0.2.blend'))
face=bpy.data.objects['Face'];arm=bpy.data.objects['Armature']
def key(suffix,value):
    k=next(k for k in face.data.shape_keys.key_blocks if k.name.endswith(suffix));k.value=value
def rotation(name,axis,angle):
    pb=arm.pose.bones[name];r=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=r.inverted()@Quaternion(axis,angle)@r
def blink():key('Fcl_EYE_Close',1)
def talk_smile():
    key('Fcl_MTH_A',.60);key('Fcl_MTH_Joy',.35);key('Fcl_BRW_Fun',.25)
def wink():key('Fcl_EYE_Close_L',1);key('Fcl_MTH_Joy',.4)
def turn_look():
    rotation('J_Bip_C_Head',(0,0,1),.50)
    for side in ['L','R']:rotation('J_Adj_'+side+'_FaceEye',(0,0,1),-.18)
def arms_bend():
    for side,sign in [('L',1),('R',-1)]:
        rotation('J_Bip_'+side+'_UpperArm',(0,1,0),sign*.55)
        rotation('J_Bip_'+side+'_LowerArm',(0,0,1),-sign*2.10)
    rotation('J_Bip_C_Spine',(1,0,0),.15)
def arms_bend_140():
    arms_bend()
    for side,sign in [('L',1),('R',-1)]:rotation('J_Bip_'+side+'_LowerArm',(0,0,1),-sign*math.radians(140))
def glasses_slide():
    bpy.data.objects['Researcher_Glasses'].data.shape_keys.key_blocks['GlassesSlide'].value=1
for name,callback,views in [('blink',blink,['face']),('talk-smile',talk_smile,['face']),('wink',wink,['face']),('head-eye-look',turn_look,['face']),('elbow-120-torso',arms_bend,['quarter','full']),('elbow-140-torso',arms_bend_140,['quarter']),('glasses-slide',glasses_slide,['face'])]:
    if len(args)>1 and name!=args[1]:continue
    reset_pose();render_views(ROOT/f'previews/v0.2/poses-{version}'/name,views,pose_callback=callback)
reset_pose()
print('Rendered expression and deformation poses without saving source',version,flush=True)
