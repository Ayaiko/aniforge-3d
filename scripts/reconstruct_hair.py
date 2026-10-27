"""Authored controlled ribbon surfaces; primary forms, no strand/noise detail.
Sections are independently editable quad strips with a real thin back surface.
"""
from pathlib import Path
import sys,math,json
import bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import mesh,recalc,toon
from reconstruction_review import render_iteration
from character_studio import reset_pose,setup
iteration4='--refine' in sys.argv
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/('models/researcher-a-reconstruction-03-primary-v0.3.blend' if iteration4 else 'models/researcher-a-reconstruction-01-face-v0.3.blend')));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
old_names=[o.name for o in bpy.data.objects if o.type=='MESH' and ('Hair_' in o.name or o.get('detail_tier',-1)>0 or o.get('reconstruction_tier'))]
old_count=sum(len(bpy.data.objects[n].data.vertices) for n in old_names)
for name in old_names:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
cap=bpy.data.objects['Researcher_BobCap']
if iteration4:
    original_name=cap.data.name
    with bpy.data.libraries.load(str(ROOT/'models/researcher-a-reconstruction-01-face-v0.3.blend'),link=False) as (src,dst):dst.meshes=[original_name]
    cap.data=dst.meshes[0]
for v in cap.data.vertices:
    x,y,z=v.co
    # Recess the old coverage shell at the nape; new curved tips define the hem.
    if z<1.406:v.co.z+=(.014 if iteration4 else .026)*max(0,(1.406-z)/.075)
    if z>1.54:v.co.z+=(.004*math.exp(-((x-.022)/.033)**2)-.009*(x/.13)**2)*min(1,(z-1.54)/.05)
    if iteration4:
        v.co.x*=.965
        if z>1.56:
            target=1.608-4.8*(v.co.x-.020)**2-4.3*(y-.015)**2
            blend=max(0,min(1,(z-1.56)/.040));v.co.z=(1-blend)*v.co.z+blend*target
base=toon('Reconstruction / Hair main','252C40','172035',.00018)
shadow=toon('Reconstruction / Hair lower layers','222A3E','172034',.00014)
cap.data.materials.clear();cap.data.materials.append(shadow)
records=[]

def interpolate(points,t):
    n=len(points);q=t*(n-1);i=min(n-2,int(q));u=q-i
    p0=points[max(0,i-1)];p1=points[i];p2=points[i+1];p3=points[min(n-1,i+2)]
    return .5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)

def surface(name,points,widths,depth=.0024,material=base,twist=0):
    points=[Vector(p) for p in points];rows=57;cols=13;vertices=[];faces=[]
    if iteration4:
        points[0].z=1.597
        if name in ['Hair_SweptInner','Hair_SweptMiddle','Hair_SweptOuter']:
            for p in points:p.y+=.035*max(0,min(1,(1.48-p.z)/.075))
        if name in ['Hair_RightBob','Hair_BehindEar','Hair_RearMass_00']:
            for p in points:p.y+=.022*math.exp(-((p.z-1.443)/.049)**2)
        if name=='Hair_EarTuck':points[-1].z+=.018
        if name=='Hair_FringeMain':points[-1].z+=.005
        if name=='Hair_FringeAccent':points[-1].z+=.009;points[-1].x-=.003
    # Broad curved front/back sections, not elliptical primitive cross-sections.
    for back in [False,True]:
        for row in range(rows):
            t=row/(rows-1);p=interpolate(points,t)
            tangent=(interpolate(points,min(1,t+.001))-interpolate(points,max(0,t-.001))).normalized()
            normal=Vector((p.x, p.y-.015,(p.z-1.485)*.62))
            normal-=tangent*normal.dot(tangent)
            if normal.length<1e-5:normal=Vector((0,-1,0))
            normal.normalize();across=tangent.cross(normal).normalized();normal=across.cross(tangent).normalized()
            angle=twist*math.sin(math.pi*t);a=across*math.cos(angle)+normal*math.sin(angle);n=normal*math.cos(angle)-across*math.sin(angle)
            if iteration4:
                anchors=[0,.22,.50,.88,1];k=min(3,int(np.searchsorted(anchors,t,side='right')-1));u=(t-anchors[k])/(anchors[k+1]-anchors[k]);u=u*u*(3-2*u)
                width=widths[k]*(1-u)+widths[k+1]*u
            else:width=float(np.interp(t,np.linspace(0,1,len(widths)),widths))
            width=max(width,.00018)
            for col in range(cols):
                u=2*col/(cols-1)-1
                # Controlled crease-free camber and a thin real thickness.
                crown=depth*(1-u*u)*math.sin(math.pi*t)**.4
                offset=crown-(.0011 if back else 0)
                pos=p+a*(u*width)+n*offset
                if iteration4:pos.x*=.965
                vertices.append(tuple(pos))
    layer=rows*cols
    for back in [False,True]:
        start=layer*int(back)
        for row in range(rows-1):
            for col in range(cols-1):
                a=start+row*cols+col;f=(a,a+1,a+cols+1,a+cols)
                faces.append(tuple(reversed(f)) if back else f)
    for row in range(rows-1):
        a=row*cols;b=(row+1)*cols;faces.append((a,b,b+layer,a+layer))
        a=row*cols+cols-1;b=(row+1)*cols+cols-1;faces.append((a,a+layer,b+layer,b))
    for row in [0,rows-1]:
        for col in range(cols-1):
            a=row*cols+col;faces.append((a,a+layer,a+1+layer,a+1) if row==0 else (a,a+1,a+1+layer,a+layer))
    ob=mesh(name,vertices,faces,material);recalc(ob)
    uv=ob.data.uv_layers.new(name='Authored hair surface')
    for p in ob.data.polygons:
        for li in p.loop_indices:
            i=ob.data.loops[li].vertex_index;back=i>=layer;i%=layer
            uv.data[li].uv=(.02+.44*(i%cols)/(cols-1)+.50*back,.02+.96*(i//cols)/(rows-1))
    ob['method']='Controlled quad surface with authored centerline, width, camber and twist'
    ob['control_points']=[list(p) for p in points];ob['half_widths']=widths;ob['rows']=rows;ob['cols']=cols;ob['reconstruction_tier']='Primary form'
    records.append({'name':name,'vertices':len(vertices),'faces':len(faces),'control_points':[list(p) for p in points],'widths':widths})
    return ob

surface('Hair_SweptOuter',[(.014,-.007,1.599),(-.078,-.030,1.574),(-.126,-.041,1.477),(-.130,-.053,1.391),(-.105,-.057,1.340)],[.004,.020,.019,.015,.0002],.0028,twist=-.12)
surface('Hair_SweptMiddle',[(.022,-.025,1.604),(-.042,-.074,1.578),(-.101,-.097,1.491),(-.109,-.089,1.402),(-.087,-.067,1.344)],[.003,.021,.020,.014,.0002],.0032,twist=.1)
surface('Hair_SweptInner',[(.027,-.038,1.600),(-.005,-.092,1.571),(-.066,-.112,1.505),(-.091,-.110,1.421),(-.077,-.086,1.355)],[.003,.019,.018,.010,.0002],.0025,twist=-.12)
surface('Hair_FringeMain',[(.027,-.042,1.600),(.001,-.100,1.565),(-.017,-.120,1.524),(-.035,-.119,1.477),(-.057,-.108,1.447)],[.002,.014,.015,.011,.0002],.0027,twist=.08)
surface('Hair_FringeAccent',[(.030,-.048,1.592),(.012,-.105,1.551),(-.006,-.125,1.512),(-.020,-.124,1.473),(-.039,-.111,1.447)],[.001,.008,.008,.005,.0002],.0018,twist=-.1)
surface('Hair_RightPart',[(.030,-.031,1.600),(.060,-.080,1.574),(.077,-.085,1.528),(.083,-.063,1.487),(.093,-.041,1.464)],[.002,.018,.016,.010,.0002],.0026,twist=.1)
surface('Hair_EarTuck',[(.029,-.006,1.600),(.087,-.023,1.573),(.109,-.028,1.522),(.104,-.022,1.480),(.101,-.005,1.456)],[.003,.016,.014,.007,.0002],.0022,twist=-.12)
surface('Hair_RightBob',[(.027,.024,1.597),(.090,.044,1.565),(.129,.036,1.476),(.127,.030,1.391),(.104,.014,1.343)],[.003,.018,.018,.016,.0002],.0026,twist=.18)
surface('Hair_BehindEar',[(.093,.010,1.493),(.119,.016,1.458),(.119,.028,1.406),(.100,.018,1.366),(.078,-.001,1.342)],[.006,.013,.012,.008,.0002],.002,shadow,twist=-.22)
# Deliberately different primary rear masses, fanning from the off-centre part.
for i,a in enumerate([.26,.58,.94,1.30,1.66,2.02,2.40,2.78,3.02]):
    drift=[.12,.20,.17,.08,-.10,-.18,-.15,-.09,.10][i]
    end_z=[1.346,1.342,1.337,1.340,1.334,1.338,1.344,1.339,1.347][i]
    def polar(rad_x,rad_y,angle,z):return (rad_x*math.cos(angle),.014+rad_y*math.sin(angle),z)
    pts=[(.025+.008*math.cos(a),.015+.010*math.sin(a),1.599),polar(.092,.091,a+.06,1.566),polar(.128,.125,a+drift,1.476),polar(.119,.111,a+drift*.65,1.389),polar(.088,.079,a-.04,end_z)]
    width=[.015,.019,.023,.024,.023,.024,.021,.018,.012][i]
    surface('Hair_RearMass_%02d'%i,pts,[.003,width*.82,width,width*.73,.0002],.0026,base if i%3 else shadow,twist=drift)
cap['reconstruction']='Hidden coverage shell recessed at hem; visible hair replaced by controlled surfaces'
if iteration4:
    # Subdivide locally before cutting; project the boundary onto a smooth oval.
    bm=bmesh.new();bm.from_mesh(cap.data)
    edges=[e for e in bm.edges if any(v.co.x>.065 and abs(v.co.y-.025)<.05 and abs(v.co.z-1.444)<.055 for v in e.verts)]
    bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True)
    fs=[f for f in bm.faces if f.calc_center_median().x>.065 and ((f.calc_center_median().y-.025)/.028)**2+((f.calc_center_median().z-1.444)/.032)**2<1]
    bmesh.ops.delete(bm,geom=fs,context='FACES')
    for v in bm.verts:
        if v.co.x>.065 and any(e.is_boundary for e in v.link_edges):
            yy=(v.co.y-.025)/.028;zz=(v.co.z-1.444)/.032;r=math.sqrt(yy*yy+zz*zz)
            if .6<r<1.5:v.co.y=.025+yy/r*.028;v.co.z=1.444+zz/r*.032
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(cap.data);bm.free();recalc(cap)
directory=render_iteration('04-hair-refinement' if iteration4 else '02-hair')
(directory/'changes.json').write_text(json.dumps({'method':'Controlled Surface Modeling; no primitive/subdivision workflow','removed_meshes':old_names,'removed_vertices':old_count,'new_primary_surfaces':records,'tertiary_details_added':0,'artistic_status':'Pending actual visual inspection'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('models/researcher-a-reconstruction-04-hair-v0.3.blend' if iteration4 else 'models/researcher-a-reconstruction-02-hair-v0.3.blend')))
print('HAIR PRIMARY SAVED',len(records),sum(r['vertices'] for r in records),flush=True)
