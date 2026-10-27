"""Add light-reactive corneal caps, transferred to the existing eye morphs."""
from pathlib import Path
import sys,math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import *
from character_studio import reset_pose,render_views
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-tailored-v0.2.blend'));reset_pose()
for side,cx in [('L',.040),('R',-.0405)]:
    globe=bpy.data.objects['EyeGlobe_'+side]
    for v in globe.data.vertices:v.co.x=cx+(v.co.x-cx)*(.0205/.023)
face=bpy.data.objects['Face'];face.data.calc_loop_triangles()
triangles=[tuple(t.vertices) for t in face.data.loop_triangles if 'EyeIris' in face.data.materials[face.data.polygons[t.polygon_index].material_index].name]
world=[face.matrix_world@v.co for v in face.data.vertices];surface=BVHTree.FromPolygons(world,triangles,all_triangles=True)
material=bpy.data.materials.new('Production / Corneal optical coat');material.surface_render_method='BLENDED';material.diffuse_color=(1,1,1,.055)
bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value=(1,1,1,1);bs.inputs['Roughness'].default_value=.045;bs.inputs['IOR'].default_value=1.376;bs.inputs['Alpha'].default_value=.055;bs.inputs['Transmission Weight'].default_value=.9;bs.inputs['Coat Weight'].default_value=.6;bs.inputs['Coat Roughness'].default_value=.035
for side,cx in [('L',.040),('R',-.0405)]:
    points=[(cx,1.4465,0)]
    segments=40;rings=8;polygons=[]
    for j in range(1,rings+1):
        r=j/rings
        for i in range(segments):
            a=2*math.pi*i/segments;points.append((cx+.0148*r*math.cos(a),1.4465+.0076*r*math.sin(a),r))
    vertices=[];attachments=[]
    for x,z,r in points:
        nearest,normal,index,distance=surface.ray_cast(Vector((x,-.3,z)),Vector((0,1,0)))
        if nearest is None:raise RuntimeError('Corneal sample missed the original iris')
        # Leave a tiny clear dome over the animated iris, not an opaque eye shell.
        if normal.y>0:normal=-normal
        p=nearest+Vector((0,-(.00085+.0010*(1-r*r)),0));vertices.append(tuple(p));attachments.append((nearest.copy(),triangles[index],p-nearest))
    for i in range(segments):polygons.append((0,1+(i+1)%segments,1+i))
    for j in range(rings-1):
        for i in range(segments):
            a=1+j*segments+i;b=1+j*segments+(i+1)%segments;polygons.append((a,b,b+segments,a+segments))
    ob=mesh('Attached_Cornea_'+side,vertices,polygons,material,bone=None);recalc(ob)
    if ob.data.polygons[0].normal.y>0:
        bm=bmesh.new();bm.from_mesh(ob.data)
        for f in bm.faces:f.normal_flip()
        bm.to_mesh(ob.data);bm.free()
    for g in face.vertex_groups:ob.vertex_groups.new(name=g.name)
    for i,(p,tri,offset) in enumerate(attachments):
        bary=barycentric_transform(p,*[world[k] for k in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        weights={}
        for k,w in zip(tri,bary):
            for g in face.data.vertices[k].groups:weights[g.group]=weights.get(g.group,0)+g.weight*max(0,w)
        total=sum(weights.values())
        for group,w in weights.items():
            if w>1e-7:ob.vertex_groups[group].add([i],w/total,'REPLACE')
    uv=ob.data.uv_layers.new(name=face.data.uv_layers.active.name)
    for loop in ob.data.loops:
        p=ob.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((p.x-cx)/.04+.5,(p.z-1.447)/.03+.5)
    cr=ob.data.attributes.new('crease_edge','FLOAT','EDGE')
    for v in cr.data:v.value=1
    ob.shape_key_add(name='Basis')
    for key in list(face.data.shape_keys.key_blocks)[1:]:
        target=ob.shape_key_add(name=key.name)
        for i,(p,tri,offset) in enumerate(attachments):target.data[i].co=barycentric_transform(p,*[world[k] for k in tri],*[face.matrix_world@key.data[k].co for k in tri])+offset
    join_to_face(ob)
face['eye_optics']='1024px iris, concave pupil profile, full sclera volume, light-reactive corneal caps with transferred original blink/look deformation'
save_phase('master')
render_views(ROOT/'previews/v0.2/after',['face','quarter'])
