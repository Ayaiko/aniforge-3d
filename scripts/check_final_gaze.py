from pathlib import Path
import sys,bpy
from mathutils import Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup,render_views
enable_vrm()
for tag,path in [('before','models/researcher-a-reference-audit-v0.3.blend'),('after','models/researcher-a-reconstruction-master-v0.3.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/path));reset_pose();render_views(ROOT/f'previews/v0.3/full-body/{tag}',['full'])
reset_pose();setup();scene=bpy.context.scene;scene.render.resolution_x=800;scene.render.resolution_y=900
arm=bpy.data.objects['Armature']
def rotate(name,axis,angle):
    pb=arm.pose.bones[name];q=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q.inverted()@Quaternion(axis,angle)@q
rotate('J_Bip_C_Head',(0,0,1),.35)
for side in ['L','R']:
    rotate('J_Adj_'+side+'_FaceEye',(0,0,1),-.18)
for view in ['front','quarter']:
    scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(ROOT/f'previews/v0.3/validation-master/head-eye-look-{view}.png');bpy.ops.render.render(write_still=True)
print('ADDITIONAL GAZE/FULL BODY CHECK WITHOUT SAVING SOURCE',flush=True)
