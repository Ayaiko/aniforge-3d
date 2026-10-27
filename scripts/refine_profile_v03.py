"""Landmark-led local cage corrections, identical displacement on every key."""
from pathlib import Path
import sys,math,json,bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-10-cleanup-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];mi=face.matrix_world.inverted()
def displacement(p):
    x,y,z=p;front=max(0,min(1,(-y-.025)/.040))
    mouth=math.exp(-(x/.026)**4-((z-1.3855)/.014)**4)*front
    left=math.exp(-((x+.040)/.027)**4-((z-1.448)/.023)**4)*front
    return Vector((-.0018*left,-.009*mouth,.0023*mouth-.0024*left))
delta=[displacement(face.matrix_world@p.co) for p in face.data.shape_keys.key_blocks[0].data]
for key in face.data.shape_keys.key_blocks:
    for i,p in enumerate(key.data):p.co=mi@(face.matrix_world@p.co+delta[i])
ob=bpy.data.objects['EyeGlobe_R'];inverse=ob.matrix_world.inverted()
for p in ob.data.vertices:
    world=ob.matrix_world@p.co;p.co=inverse@(world+displacement(world))
# Same subtle asymmetry in the left frame; original slide target keeps its delta.
glasses=bpy.data.objects['Researcher_Glasses'];inverse=glasses.matrix_world.inverted()
for key in glasses.data.shape_keys.key_blocks:
    for p in key.data:
        world=glasses.matrix_world@p.co
        if world.x<-.012:world.z-=.0012*math.exp(-((world.x+.040)/.037)**4)
        p.co=inverse@world
directory=render_iteration('11-profile-landmarks')
(directory/'changes.json').write_text(json.dumps({'acceptance_before_phase':['Front geometric iris-center proxies within 3 pixels of annotated reference','Mouth center within 3 pixels in front; improve 14-pixel side setback','Keep original expression deltas by applying the same basis displacement to every key','No broken blink or mouth cavity'],'geometry_changes':['Perioral surface advanced by up to 9 mm and raised 2.3 mm','Viewer-left eye region moved outward 1.8 mm and down 2.4 mm to match reference asymmetry','Corresponding scleral volume and frame fitted to eye region'],'method':'Direct vertex editing with basis displacement propagated through all 42 keys','tertiary_details_added':0,'artistic_status':'Requires visual inspection; anchor alignment is not a whole-character likeness pass'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-11-profile-v0.3.blend'))
