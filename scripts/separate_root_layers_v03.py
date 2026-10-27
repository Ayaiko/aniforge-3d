from pathlib import Path
import sys,math,json,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import recalc
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-08-primary-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
for name,axis,amount,z,r in [('Hair_FringeAccent',1,-.004,1.598,.014),('Hair_SweptInner',1,-.002,1.598,.012),('Hair_SweptMiddle',1,.0015,1.598,.012),('Hair_RearMass_00',2,-.0035,1.594,.012),('Hair_RearMass_02',2,-.003,1.601,.010)]:
    ob=bpy.data.objects[name]
    for v in ob.data.vertices:v.co[axis]+=amount*math.exp(-((v.co.z-z)/r)**2)
    recalc(ob)
directory=render_iteration('09-root-clearance')
(directory/'changes.json').write_text(json.dumps({'geometry_changes':['Five overlapping crown layers separated locally by 1.5 to 4 mm using diagnosed contact coordinates'],'new_tertiary_details':0,'artistic_status':'Not approved: visual likeness still requires further sculpt/surface work'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-09-clearance-v0.3.blend'))
