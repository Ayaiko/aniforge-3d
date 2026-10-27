"""Save a useful native Blender workspace; changes display state, not geometry."""
from pathlib import Path
import sys,math
import bpy
from mathutils import Euler,Quaternion,Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
enable_vrm()
for version in ['master','realtime']:
    path=ROOT/f'models/researcher-a-{version}-v0.2.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
    arm=bpy.data.objects['Armature']
    for side,angle in [('L',1.22),('R',-1.22)]:
        pb=arm.pose.bones['J_Bip_'+side+'_UpperArm'];r=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=r.inverted()@Quaternion((0,1,0),angle)@r
    bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=bpy.data.objects['Face']
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                s=area.spaces.active;s.shading.type='MATERIAL';s.overlay.show_overlays=False;s.clip_start=.01
                if s.region_3d:
                    s.region_3d.view_location=Vector((0,0,1.36));s.region_3d.view_rotation=Euler((math.pi/2,0,0)).to_quaternion();s.region_3d.view_distance=.65;s.region_3d.view_perspective='ORTHO'
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    print('Native workspace prepared',version,flush=True)
