from pathlib import Path
import sys,math,json
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import recalc
from controlled_hair_surface import build
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-07-roots-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
records=[]
for index,ob in enumerate(sorted([o for o in bpy.data.objects if o.get('reconstruction_tier')],key=lambda o:o.name)):
    rows,cols=ob['rows'],ob['cols'];a=np.array([v.co[:] for v in ob.data.vertices]).reshape(2,rows,cols,3)
    if ob.name!='Hair_BehindEar':
        root=Vector(a[:,0].mean(axis=(0,1)));angle=(index/18)*math.pi*2
        target=Vector((.023+.007*math.cos(angle),.009+.007*math.sin(angle),1.600+.0015*math.sin(angle)))
        delta=target-root
        for row in range(rows):
            t=row/(rows-1);a[:,row]+=np.array(delta)*max(0,1-t/.26)**2
            if ob.name=='Hair_RearMass_03':a[:,row,:,1]+=.0025*math.exp(-((t-.10)/.12)**2)
            if ob.name=='Hair_RearMass_07':a[:,row,:,0]-=.0025*math.exp(-((t-.08)/.10)**2)
        for v,p in zip(ob.data.vertices,a.reshape(-1,3)):v.co=p
        recalc(ob);records.append(ob.name)
material=bpy.data.objects['Hair_RightPart'].data.materials[0]
build('Hair_ForeheadTransition',[(.026,-.045,1.588),(.029,-.095,1.554),(.031,-.108,1.532),(.048,-.105,1.502),(.075,-.067,1.476)],[.003,.015,.016,.010,.0002],material,depth=.0028)
directory=render_iteration('08-primary-resolution')
(directory/'changes.json').write_text(json.dumps({'geometry_changes':['17 crown roots fitted to a shared part under coverage shell to remove floating spikes','A new authored forehead transition surface lowers the visible hairline','Rear root layers separated by 2.5 mm near measured contact zones'],'root_surfaces_edited':records,'new_primary_surfaces':['Hair_ForeheadTransition'],'tertiary_details_added':0,'artistic_status':'Pending inspection'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-08-primary-v0.3.blend'))
