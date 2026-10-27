"""Approximate portrait camera, locked for baseline and reconstruction.
This does not claim a perspective solution for a stylized drawing.
"""
from pathlib import Path
import sys,json,math,bpy,numpy as np
from mathutils import Vector,Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
args=sys.argv[sys.argv.index('--')+1:];enable_vrm();out=ROOT/'previews/v0.3/hero-comparison';out.mkdir(exist_ok=True)
model=ROOT/args[0];land=json.loads((ROOT/'previews/v0.3'/args[1]/'landmarks.json').read_text())['world_landmarks_m']
eye=(Vector(land['pupil_left'])+Vector(land['pupil_right']))/2;chin=Vector(land['chin'])
direction=Vector((math.sin(math.radians(15)),-math.cos(math.radians(15)),0));q=(-direction).to_track_quat('-Z','Y')@Quaternion((0,0,1),math.radians(-9.5))
right=q@Vector((1,0,0));up=q@Vector((0,1,0));scale=(eye-chin).dot(up)/(615-393)
target=eye-right*(6*scale)+up*(48*scale);position=target+direction*2
manifest={'reference_crop':[180,10,820,680],'reference_eye_midpoint':[506,393],'reference_chin':[520,615],'yaw_degrees':15,'camera_roll_degrees':-9.5,'ortho_scale':670*scale,'position':list(position),'rotation':list(q),'limitation':'Approximate portrait pose, not an exact 45-degree orthographic reference. Both baseline and reconstruction use the same camera and lights.'}
(out/'camera.json').write_text(json.dumps(manifest,indent=2))
for tag,path in [('before',ROOT/'models/researcher-a-reference-audit-v0.3.blend'),('after',model)]:
    bpy.ops.wm.open_mainfile(filepath=str(path));reset_pose();camera=setup();scene=bpy.context.scene
    bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
    camera.data.type='ORTHO';camera.data.ortho_scale=manifest['ortho_scale'];camera.location=position;camera.rotation_mode='QUATERNION';camera.rotation_quaternion=q
    scene.render.resolution_x=640;scene.render.resolution_y=670;scene.render.filepath=str(out/(tag+'.png'));bpy.ops.render.render(write_still=True)
