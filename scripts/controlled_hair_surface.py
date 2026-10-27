"""Editable authored ribbon with curved sections, thickness, and nonzero rim UVs."""
import math,numpy as np
from mathutils import Vector
from production_common import mesh,recalc
def spline(points,t):
    q=t*(len(points)-1);i=min(len(points)-2,int(q));u=q-i
    p0,p1,p2,p3=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
    return .5*(2*p1+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)
def build(name,points,widths,material,depth=.0024,rows=57,cols=13):
    points=[Vector(p) for p in points];vs=[];fs=[];layer=rows*cols
    for back in [0,1]:
        for row in range(rows):
            t=row/(rows-1);p=spline(points,t);tangent=(spline(points,min(1,t+.001))-spline(points,max(0,t-.001))).normalized()
            n=Vector((p.x,p.y-.015,(p.z-1.485)*.62));n-=tangent*n.dot(tangent);n.normalize();a=tangent.cross(n).normalized();n=a.cross(tangent).normalized()
            anchors=[0,.22,.5,.88,1];k=min(3,max(0,int(np.searchsorted(anchors,t,side='right')-1)));f=(t-anchors[k])/(anchors[k+1]-anchors[k]);f=f*f*(3-2*f)
            w=max(.00018,widths[k]*(1-f)+widths[k+1]*f)
            for col in range(cols):
                u=2*col/(cols-1)-1;vs.append(tuple(p+a*u*w+n*(depth*(1-u*u)*math.sin(math.pi*t)**.4-.0011*back)))
    for back in [0,1]:
        for row in range(rows-1):
            for col in range(cols-1):
                a=back*layer+row*cols+col;f=(a,a+1,a+cols+1,a+cols);fs.append(tuple(reversed(f)) if back else f)
    for row in range(rows-1):
        a=row*cols;b=(row+1)*cols;fs.append((a,b,b+layer,a+layer));a+=cols-1;b+=cols-1;fs.append((a,a+layer,b+layer,b))
    for row in [0,rows-1]:
        for col in range(cols-1):
            a=row*cols+col;fs.append((a,a+layer,a+1+layer,a+1) if row==0 else (a,a+1,a+1+layer,a+layer))
    ob=mesh(name,vs,fs,material);recalc(ob);uv=ob.data.uv_layers.new(name='Authored hair surface')
    for p in ob.data.polygons:
        rr={(v%layer)//cols for v in p.vertices};cc={(v%layer)%cols for v in p.vertices};end=len(rr)==1 and next(iter(rr)) in [0,rows-1];wall=len(cc)==1 and next(iter(cc)) in [0,cols-1] and not end
        for li in p.loop_indices:
            i=ob.data.loops[li].vertex_index;back=i>=layer;row=(i%layer)//cols;col=(i%layer)%cols
            uv.data[li].uv=(.52+.44*col/(cols-1),(.003 if row==0 else .982)+.009*back) if end else ((.475 if col==0 else .985)+.01*back,.02+.96*row/(rows-1)) if wall else (.02+.44*col/(cols-1)+.5*back,.02+.96*row/(rows-1))
    ob['control_points']=[list(p) for p in points];ob['half_widths']=widths;ob['rows']=rows;ob['cols']=cols;ob['reconstruction_tier']='Primary form';ob['method']='Authored controlled quad surface'
    return ob
