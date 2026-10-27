"""Iteration 07: act on contour review and exact contact coordinates."""
from pathlib import Path
import sys,math,json
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import recalc
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-06-surface-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];mi=face.matrix_world.inverted()
def g(x,c,r):return math.exp(-((x-c)/r)**2)
for key in face.data.shape_keys.key_blocks:
    for v in key.data:
        p=face.matrix_world@v.co;x,y,z=p;ax=abs(x);front=max(0,min(1,(-y-.015)/.03))
        eye=g(ax,.04025,.025)*g(z,1.4462,.026)*front;mouth=g(x,0,.029)*g(z,1.385,.012)*front
        narrow=(.16*g(z,1.414,.043)+.025*g(z,1.48,.035))*(1-max(.92*eye,.9*mouth))
        ear=max(0,min(1,(y+.010)/.020))*g(ax,.095,.025)*g(z,1.445,.050)
        p.x*= (1-narrow*(1-ear))/(1-narrow*front)
        v.co=mi@p
changed=[]
for idx,ob in enumerate(sorted([o for o in bpy.data.objects if o.get('reconstruction_tier')],key=lambda o:o.name)):
    rows,cols=ob['rows'],ob['cols'];layer=rows*cols;a=np.array([v.co[:] for v in ob.data.vertices]).reshape(2,rows,cols,3);root_z=float(a[:,0,:,2].mean())
    for row in range(rows):
        t=row/(rows-1)
        if ob.name=='Hair_BehindEar':
            # This local lock was incorrectly raised to the global crown in 04.
            # Restore a local root above/behind the ear, not at the top of head.
            desired=1.494
            delta=(desired-root_z)*max(0,1-t/.28)**2
            a[:,row,:,2]+=delta
        else:
            root=max(0,1-t/.24)**2
            a[:,row,:,2]+=(.010+.0003*(idx%4))*root
            a[:,row,:,1]+=.010*root
        for back in [0,1]:
            for col in range(cols):
                p=a[back,row,col]
                frontal=max(0,min(1,(-p[1]-.040)/.055))
                if ob.name in ['Hair_FringeMain','Hair_FringeAccent','Hair_RightPart']:
                    p[2]-=.013*g(p[2],1.555,.035)*frontal
                if ob.name=='Hair_RightPart':p[0]-=.014*g(p[2],1.545,.037)*frontal
                if ob.name=='Hair_RearMass_00':p[0]+=.003*g(t,.14,.12)
                if ob.name=='Hair_RearMass_08':p[1]-=.002*g(t,.08,.08)
                if ob.name=='Hair_BehindEar':p[0]+=.003*g(p[2],1.537,.020)
    for v,p in zip(ob.data.vertices,a.reshape(-1,3)):v.co=p
    # Give the thin end walls real UV area. Their old front/back UV shared V.
    uv=ob.data.uv_layers.active.data
    for poly in ob.data.polygons:
        rr={((i%layer)//cols) for i in poly.vertices}
        if len(rr)==1 and next(iter(rr)) in [0,rows-1]:
            row=next(iter(rr));base=.003 if row==0 else .982
            for li in poly.loop_indices:
                i=ob.data.loops[li].vertex_index;uv[li].uv=(.52+.44*((i%layer)%cols)/(cols-1),base+.009*(i>=layer))
    recalc(ob);changed.append(ob.name)
body=bpy.data.objects['Body'];bi=body.matrix_world.inverted()
for v in body.data.vertices:
    p=body.matrix_world@v.co
    if p.z>1.55:p.z-=.014*max(0,min(1,(p.z-1.55)/.035));v.co=bi@p
directory=render_iteration('07-root-and-proportion')
(directory/'changes.json').write_text(json.dumps({'geometry_changes':['Front cheek planes narrowed further, with a separate ear protection mask','Frontal part lowered and pulled toward fringe to reduce forehead wedge','Hair roots raised onto crown with varied layering','Behind-ear local lock root restored from erroneous crown height','Hidden inherited scalp recessed at crown','Root contact layers separated using diagnosed contact locations'],'uv_changes':['All 18 controlled surfaces: 24 thin end-wall faces assigned nonzero UV area'],'meshes_directly_edited':changed,'tertiary_details_added':0,'artistic_status':'Pending image review'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-07-roots-v0.3.blend'))
print('ROOT CORRECTION SAVED',flush=True)
