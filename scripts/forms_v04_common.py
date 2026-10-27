from pathlib import Path
import math,json,shutil,hashlib
import bpy,bmesh,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import mesh,recalc,toon
import reconstruction_review
OUT=ROOT/'previews/v0.4';OUT.mkdir(exist_ok=True)
CAL=json.loads((ROOT/'previews/v0.3/reference-calibration.json').read_text());S=CAL['meters_per_reference_pixel'];EYE=CAL['eye_z']
def initialize(path):
    enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/path));reset_pose();setup()
    bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
def finish(stage,filename,changes):
    reconstruction_review.OUT=OUT;directory=reconstruction_review.render_iteration(stage)
    (directory/'changes.json').write_text(json.dumps(changes,indent=2))
    export_contours(directory)
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models'/filename));return directory
def spline(points,t):
    points=[Vector(p) for p in points];q=t*(len(points)-1);i=min(len(points)-2,int(q));u=q-i
    a,b,c,d=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
    return .5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
def world_front(u,v,y):return Vector(((u-200)*S,y,EYE-(v-222)*S))
def boundary_surface(name,left,right,ys,material,bulge=.003,rows=49,cols=11,back_projection=False):
    """Independent contour boundaries define the surface, not a centreline tube."""
    vertices=[];polys=[];layer=rows*cols
    for back in [0,1]:
        for row in range(rows):
            t=row/(rows-1);l=spline(left,t);r=spline(right,t);y=float(np.interp(t,np.linspace(0,1,len(ys)),ys))
            if (r-l).length<.7:r.x+=.35;l.x-=.35
            for col in range(cols):
                u=col/(cols-1);p=l.lerp(r,u);depth=y-bulge*math.sin(math.pi*u)**.8+back*.0012
                co=world_front(p.x,p.y,depth)
                if back_projection:co.x=-co.x;co.y=-depth
                vertices.append(tuple(co))
    for back in [0,1]:
        start=back*layer
        for j in range(rows-1):
            for i in range(cols-1):
                a=start+j*cols+i;f=(a,a+1,a+cols+1,a+cols);polys.append(tuple(reversed(f)) if back else f)
    for j in range(rows-1):
        a=j*cols;b=a+cols;polys.extend([(a,b,b+layer,a+layer),(a+cols-1,a+cols-1+layer,b+cols-1+layer,b+cols-1)])
    for j in [0,rows-1]:
        for i in range(cols-1):
            a=j*cols+i;polys.append((a,a+layer,a+1+layer,a+1) if j==0 else (a,a+1,a+1+layer,a+layer))
    ob=mesh(name,vertices,polys,material);recalc(ob);uv=ob.data.uv_layers.new(name='Surface regions')
    for p in ob.data.polygons:
        rr={(i%layer)//cols for i in p.vertices};cc={(i%layer)%cols for i in p.vertices};end=len(rr)==1;wall=len(cc)==1 and not end
        for li in p.loop_indices:
            i=ob.data.loops[li].vertex_index;back=i>=layer;j=(i%layer)//cols;k=(i%layer)%cols
            if end:value=(.52+.44*k/(cols-1),(.003 if j==0 else .982)+.009*back)
            elif wall:value=((.475 if k==0 else .985)+.010*back,.02+.96*j/(rows-1))
            else:value=(.02+.44*k/(cols-1)+.5*back,.02+.96*j/(rows-1))
            uv.data[li].uv=value
    ob['construction']='Independent reference contour boundaries; controlled surface section and depth'
    ob['surface_rows']=rows;ob['surface_cols']=cols;ob['reference_left']=[list(p) for p in left];ob['reference_right']=[list(p) for p in right];ob['form_part']='back_hair' if back_projection else 'front_hair'
    return ob
def export_contours(directory):
    results={};scene=bpy.context.scene
    for view in ['front','quarter','side','back']:
        cam=bpy.data.objects['REF_'+view];traces={}
        for ob in bpy.data.objects:
            if ob.type!='MESH' or ob.hide_render:continue
            if ob.get('surface_rows'):
                rows,cols=ob['surface_rows'],ob['surface_cols'];paths=[]
                for col in [0,cols-1]:
                    coords=[]
                    for row in range(rows):
                        co=ob.matrix_world@ob.data.vertices[row*cols+col].co;q=world_to_camera_view(scene,cam,co);coords.append([q.x*400,(1-q.y)*450])
                    paths.append(coords)
                traces[ob.name]={'boundaries':paths,'reference_left':list(ob.get('reference_left',[])),'reference_right':list(ob.get('reference_right',[])),'part':ob.get('form_part')}
        results[view]=traces
    (directory/'internal-contours.json').write_text(json.dumps(results,indent=2))
