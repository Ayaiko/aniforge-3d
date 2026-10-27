from pathlib import Path
import sys,math
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import save_phase
from character_studio import reset_pose
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-master-v0.2.blend'));reset_pose()
arm=bpy.data.objects['Armature']
for side in ['L','R']:
    ob=bpy.data.objects['Researcher_CoatSleeve_'+side]
    if ob.get('final_elbow_ease'):continue
    start=arm.data.bones['J_Bip_'+side+'_UpperArm'].head_local;elbow=arm.data.bones['J_Bip_'+side+'_LowerArm'].head_local;end=arm.data.bones['J_Bip_'+side+'_LowerArm'].tail_local
    axis=(end-start).normalized();joint=(elbow-start).dot(axis)
    for v in ob.data.vertices:
        delta=v.co-start;along=delta.dot(axis);radial=delta-axis*along
        if radial.length:v.co+=radial.normalized()*(.005*math.exp(-((along-joint)/.060)**2))
    ob['final_elbow_ease']=.005
save_phase('master')
