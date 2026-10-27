"""Phase 2: preserve the bob silhouette, rebuild its flow at three detail levels."""
from pathlib import Path
import sys,math,json
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import *
from character_studio import render_views,reset_pose
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-face-v0.2.blend'));reset_pose()
cap=bpy.data.objects['Researcher_BobCap']
for v in cap.data.vertices:
    p=v.co;angle=math.atan2(p.y-.010,p.x)
    bottom=max(0,min(1,(1.41-p.z)/.06))
    p.z+=bottom*(.003*math.sin(7*angle+.4)+.002*math.sin(11*angle))
    # Cover the original rear scalp, which protruded through the old shell.
    p.y+=.012*math.exp(-((p.z-1.50)/.085)**2)*max(0,math.sin(angle))**3
cap_bvh=BVHTree.FromPolygons([v.co.copy() for v in cap.data.vertices],[tuple(p.vertices) for p in cap.data.polygons])

primary_names=['Researcher_LeftOuter','Researcher_LeftMid','Researcher_FringeMain','Researcher_FringeFine','Researcher_RightFringe','Researcher_TuckedSide','Researcher_RightBob','Researcher_LeftTip']
flows=[]
t=np.linspace(0,1,42);basis=np.stack([(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3],axis=1)
for name in primary_names:
    ob=bpy.data.objects[name];a=np.array([v.co[:] for v in ob.data.vertices]).reshape(42,16,3);center=a.mean(axis=1)
    controls=np.linalg.lstsq(basis,center,rcond=None)[0]
    controls[0,2]-=.006;controls[1,2]-=.001
    width=float(np.linalg.norm(a-center[:,None,:],axis=2).max())
    flows.append((name,controls.tolist(),width))
    bpy.data.objects.remove(ob,do_unlink=True)

base=toon('Production / Hair primary','252D43','182136',.00035)
mid=toon('Production / Hair secondary','2A334B','1B263C',.00025)
dark=toon('Production / Hair underlayer','20283B','172034',.00025)
cap.data.materials.clear();cap.data.materials.append(dark)
# A designed, broad painted band; no per-strand random glitter or noise.
h=1024;w=512;yy,xx=np.mgrid[0:h,0:w];u=xx/(w-1);v=yy/(h-1)
pixels=np.empty((h,w,4),dtype=np.float32);pixels[:]=[37/255,45/255,67/255,1]
band=.31+.025*np.cos((u-.25)*2*math.pi)
mask=(u>.09)&(u<.41)&(v>band)&(v<band+.023)
pixels[mask,:3]=[61/255,75/255,103/255]
image=bpy.data.images.new('Researcher hair flow 1024',width=w,height=h,alpha=True);image.pixels.foreach_set(pixels.ravel());image.pack()
g=base.vrm_addon_extension.mtoon1;g.pbr_metallic_roughness.base_color_factor=(1,1,1,1);g.pbr_metallic_roughness.base_color_texture.index.source=image
g.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source=image;g.extensions.vrmc_materials_mtoon.shade_color_factor=(.58,.64,.76)

guides=bpy.data.collections.new('Hair flow guides - editable');bpy.context.scene.collection.children.link(guides);guides.hide_render=True;guides.hide_viewport=True

def clump(name,controls,width,thickness,tier=1,twist=0,rows=None,cols=None):
    rows=rows or (64 if tier==1 else 44 if tier==2 else 30);cols=cols or (20 if tier==1 else 12 if tier==2 else 8)
    controls=[Vector(p) for p in controls]
    def curve(t):return (1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
    verts=[];faces=[]
    for j in range(rows):
        t=j/(rows-1);p=curve(t);tangent=(curve(min(1,t+.001))-curve(max(0,t-.001))).normalized()
        if tier==2 and 'Back_' in name:
            origin=Vector((0,.010,p.z));direction=p-origin;direction.z=0
            if direction.length:
                hit=cap_bvh.ray_cast(origin,direction.normalized())
                if hit[0]:p=hit[0]+direction.normalized()*(.0018*math.sin(math.pi*t))
        across=Vector((-tangent.z,0,tangent.x)).normalized()
        normal=tangent.cross(across).normalized()
        # Orient the broad front surface toward the local outer direction.
        if normal.y>0:normal=-normal
        theta=twist*math.sin(math.pi*t)
        side=across*math.cos(theta)+normal*math.sin(theta);depth=-across*math.sin(theta)+normal*math.cos(theta)
        taper=max(.015,math.sin(math.pi*t)**.58)*(1-.27*t)
        ww=max(.00022,width*taper);dd=max(.00015,thickness*taper*(.85+.15*math.cos(2*math.pi*t)))
        for k in range(cols):
            a=2*math.pi*k/cols
            verts.append(tuple(p+side*(ww*math.cos(a))+depth*(dd*math.sin(a))))
    for j in range(rows-1):
        for k in range(cols):
            a=j*cols+k;b=j*cols+(k+1)%cols;faces.append((a,b,b+cols,a+cols))
    faces.extend([tuple(reversed(range(cols))),tuple((rows-1)*cols+k for k in range(cols))])
    material=base if tier==1 else mid if tier==2 else dark
    ob=mesh(name,verts,faces,material);recalc(ob)
    uv=ob.data.uv_layers.new(name='Hair flow')
    for p in ob.data.polygons:
        wrap=any(i%cols==0 for i in p.vertices) and any(i%cols==cols-1 for i in p.vertices)
        for li in p.loop_indices:
            i=ob.data.loops[li].vertex_index;uu=i%cols/cols
            if wrap and uu==0:uu=1
            uv.data[li].uv=(uu,i//cols/(rows-1))
            if len(p.vertices)==cols:
                a=2*math.pi*(i%cols)/cols;uv.data[li].uv=(.75+.1*math.cos(a),.86+.07*math.sin(a))
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(ob.data);bm.free()
    ob['detail_tier']=tier;ob['flow_points']=[list(p) for p in controls];ob['width_m']=width;ob['thickness_m']=thickness;ob['twist_radians']=twist;ob['rows']=rows;ob['cols']=cols
    # Keep an actual cubic Bezier guide with the same endpoints and handles.
    data=bpy.data.curves.new('Guide_'+name,'CURVE');data.dimensions='3D';s=data.splines.new('BEZIER');s.bezier_points.add(1)
    a,b=s.bezier_points;a.co=controls[0];a.handle_right_type='FREE';a.handle_right=controls[1];a.handle_left=2*controls[0]-controls[1]
    b.co=controls[3];b.handle_left_type='FREE';b.handle_left=controls[2];b.handle_right=2*controls[3]-controls[2]
    guide=bpy.data.objects.new('Guide_'+name,data);guides.objects.link(guide);guide.hide_render=True
    return ob

for i,(name,controls,width) in enumerate(flows):clump(name,controls,width,.0048 if i<6 else .0058,1,twist=[-.14,.10,-.12,.16,.1,-.15,.16,-.08][i])

# Secondary locks break up the smooth rear shell and follow the same crown part.
for i,a in enumerate([.07,.35,.67,1.02,1.36,1.72,2.06,2.42,2.75,3.04]):
    shift=.004*math.sin(i*1.7);end_z=1.35+.008*math.sin(i*1.9)
    points=[(.025*math.cos(a),.010+.025*math.sin(a),1.584),(.106*math.cos(a+.10),.012+.095*math.sin(a+.10),1.564),(.128*math.cos(a-.04),.010+.112*math.sin(a-.04),1.42),(.105*math.cos(a)+shift,.010+.085*math.sin(a),end_z)]
    clump('Hair_Secondary_Back_%02d'%i,points,[.016,.012,.021,.014,.019,.010,.017,.023,.014,.009][i],.0035,2,twist=.13*math.sin(i))
clump('Hair_Secondary_LeftSweep',[(.01,-.043,1.579),(-.078,-.095,1.537),(-.129,-.082,1.409),(-.090,-.066,1.339)],.007,.0024,2,-.12)
clump('Hair_Secondary_EarTuck',[(.075,-.030,1.547),(.102,-.045,1.511),(.112,-.041,1.463),(.099,-.036,1.433)],.005,.002,2,.15)
# Sparse tertiary strands only at the silhouette, with roots inside existing masses.
for name,p in [
    ('Hair_Wisp_Left', [(-.104,-.036,1.454),(-.132,-.048,1.400),(-.128,-.056,1.356),(-.103,-.061,1.335)]),
    ('Hair_Wisp_Right',[(.111,.014,1.451),(.131,.017,1.410),(.123,-.005,1.361),(.112,-.016,1.342)]),
    ('Hair_Wisp_Nape',[(.012,.112,1.421),(.020,.115,1.379),(.008,.104,1.351),(.016,.092,1.337)]),
    ('Hair_Wisp_Forelock',[(.034,-.058,1.568),(.007,-.095,1.543),(-.022,-.115,1.510),(-.040,-.112,1.481)])]:
    clump(name,p,.0015,.0009,3,.2)

cap['detail_tier']=0;cap['purpose']='Scalp coverage under three levels of flowing mesh clumps'
save_phase('hair')
render_views(ROOT/'previews/v0.2/phase2-hair',['front','side','hair','quarter'])
