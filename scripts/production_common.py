from pathlib import Path
import math,json
import bpy,bmesh,numpy as np
from mathutils import Vector
from vrm_env import ROOT
HEAD='J_Bip_C_Head';CHEST='J_Bip_C_UpperChest'

def rgb(h):
    c=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in c)

def toon(name,color,shade=None,outline=.00035):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g=m.vrm_addon_extension.mtoon1;g.enabled=True
    g.pbr_metallic_roughness.base_color_factor=(*rgb(color),1)
    t=g.extensions.vrmc_materials_mtoon;t.shade_color_factor=rgb(shade or color)
    t.shading_toony_factor=.93;t.shading_shift_factor=-.05;t.gi_equalization_factor=.8
    t.parametric_rim_color_factor=(0,0,0);t.matcap_factor=(0,0,0)
    t.outline_width_mode='worldCoordinates' if outline else 'none';t.outline_width_factor=outline;t.outline_color_factor=rgb('1C2333')
    m.diffuse_color=(*rgb(color),1);m.roughness=.8;m.metallic=0
    return m

def bind(ob,bone=HEAD):
    arm=bpy.data.objects['Armature'];g=ob.vertex_groups.new(name=bone)
    g.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    mod=ob.modifiers.new('Character skin','ARMATURE');mod.object=arm;ob.parent=arm
    return ob

def mesh(name,vertices,polygons,material,bone=HEAD,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],polygons);data.update()
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);data.materials.append(material)
    for p in data.polygons:p.use_smooth=smooth
    if bone:bind(ob,bone)
    return ob

def apply(ob,modifier):
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):
        if bpy.ops.object.modifier_apply(modifier=modifier.name)!={'FINISHED'}:raise RuntimeError('Modifier failed: '+modifier.name)
    ob.select_set(False)

def recalc(ob):
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()

def tube(name,points,material,radius=.001,bone=HEAD,cyclic=False,res=3):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=16;data.bevel_depth=radius;data.bevel_resolution=res;data.use_fill_caps=True
    s=data.splines.new('POLY');s.points.add(len(points)-1)
    for p,c in zip(s.points,points):p.co=(*c,1)
    s.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    with bpy.context.temp_override(object=ob,active_object=ob,selected_objects=[ob],selected_editable_objects=[ob]):bpy.ops.object.convert(target='MESH')
    ob.select_set(False)
    if bone:bind(ob,bone)
    for p in ob.data.polygons:p.use_smooth=True
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return ob

def ellipsoid(name,center,radii,material,bone=HEAD,segments=48,rings=24):
    vertices=[(center[0],center[1],center[2]+radii[2])];polygons=[]
    for j in range(1,rings):
        phi=math.pi*j/rings
        for i in range(segments):
            a=2*math.pi*i/segments
            vertices.append((center[0]+radii[0]*math.sin(phi)*math.cos(a),center[1]+radii[1]*math.sin(phi)*math.sin(a),center[2]+radii[2]*math.cos(phi)))
    bottom=len(vertices);vertices.append((center[0],center[1],center[2]-radii[2]))
    for i in range(segments):polygons.append((0,1+i,1+(i+1)%segments))
    for j in range(rings-2):
        for i in range(segments):
            a=1+j*segments+i;b=1+j*segments+(i+1)%segments
            polygons.append((a,a+segments,b+segments,b))
    for i in range(segments):polygons.append((bottom,bottom-segments+(i+1)%segments,bottom-segments+i))
    ob=mesh(name,vertices,polygons,material,bone);recalc(ob)
    return ob

def solidify(ob,thickness,bevel=0):
    mod=ob.modifiers.new('Physical fabric thickness','SOLIDIFY');mod.thickness=thickness;mod.offset=0;mod.use_even_offset=True
    if bevel:
        m=ob.modifiers.new('Soft manufactured edge','BEVEL');m.width=bevel;m.segments=3;m.limit_method='ANGLE';m.angle_limit=.5
    return mod

def new_uv(objects):
    obs=[o for o in objects if o.type=='MESH']
    if not obs:return
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015,area_weight=.5,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def join_to_face(ob):
    face=bpy.data.objects['Face'];bpy.ops.object.select_all(action='DESELECT');face.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=face
    with bpy.context.temp_override(object=face,active_object=face,selected_objects=[face,ob],selected_editable_objects=[face,ob]):
        if bpy.ops.object.join()!={'FINISHED'}:raise RuntimeError('Face join failed')

def stats():
    dg=bpy.context.evaluated_depsgraph_get();out={}
    for o in bpy.data.objects:
        if o.type!='MESH' or o.hide_render:continue
        e=o.evaluated_get(dg);me=e.to_mesh()
        out[o.name]={'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'dimensions':list(o.dimensions),'materials':len(o.material_slots)}
        e.to_mesh_clear()
    return out

def save_phase(name):
    from character_studio import reset_pose
    reset_pose();path=ROOT/f'models/researcher-a-{name}-v0.2.blend'
    bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
    report=stats();out=ROOT/'previews/v0.2';out.mkdir(parents=True,exist_ok=True)
    (out/f'{name}-geometry.json').write_text(json.dumps(report,indent=2))
    print('SAVED',name,'tris',sum(x['triangles'] for x in report.values()),flush=True)
    return path
