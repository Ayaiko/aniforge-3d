"""Phases 1/3: edit the existing head, preserve all expression shapes and bones."""
from pathlib import Path
import sys,math,json
import bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import *
from character_studio import render_views,reset_pose
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/backups/researcher-a-pre-v0.2.blend'))
reset_pose();face=bpy.data.objects['Face'];inverse=face.matrix_world.inverted()
keys_before=[k.name for k in face.data.shape_keys.key_blocks]
bones_before={b.name:tuple(v for row in b.matrix_local for v in row) for b in bpy.data.objects['Armature'].data.bones}

# Remove only the flat triangular nose graphic; the underlying original face stays.
bpy.ops.object.select_all(action='DESELECT');face.select_set(True);bpy.context.view_layer.objects.active=face
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for p in face.data.polygons:p.select='Drawn face accents' in face.data.materials[p.material_index].name
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.delete(type='ONLY_FACE');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.delete_loose();bpy.ops.object.mode_set(mode='OBJECT')

def gauss(x,c,r):return math.exp(-((x-c)/r)**2)
skin_index=next(i for i,m in enumerate(face.data.materials) if 'Face_00_SKIN' in m.name)
skin_vertices={i for p in face.data.polygons if p.material_index==skin_index for i in p.vertices}
for key in face.data.shape_keys.key_blocks:
    for i in skin_vertices:
        co=face.matrix_world@key.data[i].co;x,y,z=co
        front=max(0,min(1,(-y-.025)/.03))
        cheek=.0032*gauss(abs(x),.056,.025)*gauss(z,1.413,.031)
        bridge=.0034*gauss(x,0,.009)*gauss(z,1.433,.022)
        tip=.0021*gauss(x,0,.012)*gauss(z,1.411,.011)
        lip=.0013*gauss(x,0,.018)*(gauss(z,1.387,.002)+.8*gauss(z,1.3825,.0025))
        socket=-.0015*gauss(abs(x),.043,.024)*gauss(z,1.448,.019)
        co.y-=(cheek+bridge+tip+lip+socket)*front
        co.x+=math.copysign(.0018*gauss(abs(x),.043,.028)*gauss(z,1.372,.014),x)
        co.z-=.0013*gauss(x,0,.025)*gauss(z,1.356,.010)
        key.data[i].co=inverse@co

# The new spherical eye needs the existing closed lids to cover its depth too.
lid_vertices=skin_vertices|{i for p in face.data.polygons if any(s in face.data.materials[p.material_index].name for s in ['FaceEyeline','FaceEyelash']) for i in p.vertices}
basis=face.data.shape_keys.key_blocks[0]
for key in list(face.data.shape_keys.key_blocks)[1:]:
    if not any(key.name.endswith(s) for s in ['Fcl_EYE_Close','Fcl_EYE_Close_L','Fcl_EYE_Close_R','Fcl_EYE_Joy','Fcl_EYE_Joy_L','Fcl_EYE_Joy_R']):continue
    for i in lid_vertices:
        co=face.matrix_world@key.data[i].co
        if .018<abs(co.x)<.073 and 1.43<co.z<1.464:
            movement=(key.data[i].co-basis.data[i].co).length
            co.y-=.005*max(0,min(1,(movement-.0005)/.005))
            key.data[i].co=inverse@co

# Trace the existing eyelid and mouth boundary loops, rather than replacing a head.
from collections import Counter,defaultdict
counts=Counter()
for p in face.data.polygons:
    if p.material_index==skin_index:
        for edge in p.edge_keys:counts[tuple(sorted(edge))]+=1
graph=defaultdict(list)
for (a,b),n in counts.items():
    if n==1:graph[a].append(b);graph[b].append(a)
loops=[];visited=set()
for seed in graph:
    if seed in visited:continue
    sequence=[seed];previous=None;current=seed
    for _ in range(1000):
        visited.add(current);candidates=[i for i in graph[current] if i!=previous]
        if not candidates:break
        nxt=candidates[0]
        if nxt==seed:break
        sequence.append(nxt);previous,current=current,nxt
    pts=[face.matrix_world@face.data.vertices[i].co for i in sequence]
    center=sum(pts,Vector())/len(pts)
    if len(sequence)<40 and (1.43<center.z<1.46 or 1.38<center.z<1.39):loops.append(sequence)

skin=face.data.materials[skin_index]
crease=toon('Production / Lid crease','D29E8D','C69082',0)
lipmat=toon('Production / Lip vermilion','C48E80','AA786F',0)

def attach_rim(sequence,is_mouth):
    pts=[face.matrix_world@face.data.vertices[i].co for i in sequence];n=len(pts);center=sum(pts,Vector())/n
    normals=[]
    for j,p in enumerate(pts):
        tangent=pts[(j+1)%n]-pts[(j-1)%n];normal=Vector((-tangent.z,0,tangent.x)).normalized()
        if normal.dot(p-center)<0:normal=-normal
        normals.append(normal)
    profile=[(.0007,-.0002),(0,-.0012),(-.0006,.0008),(-.0005,.0020)] if not is_mouth else [(.0005,0),(0,-.0009),(-.0002,.0007)]
    vertices=[];polygons=[]
    for distance,depth in profile:
        for p,normal in zip(pts,normals):vertices.append(tuple(p+normal*distance+Vector((0,depth,0))))
    for row in range(len(profile)-1):
        for j in range(n):polygons.append((row*n+j,row*n+(j+1)%n,(row+1)*n+(j+1)%n,(row+1)*n+j))
    ob=mesh('Attached_Lip' if is_mouth else 'Attached_Lid',vertices,polygons,lipmat if is_mouth else skin,bone=None)
    ob.data.materials.append(crease)
    if not is_mouth:
        for p in ob.data.polygons:
            if p.index//n==2:p.material_index=1
    uv=ob.data.uv_layers.new(name=face.data.uv_layers.active.name)
    for l in ob.data.loops:
        co=ob.data.vertices[l.vertex_index].co;uv.data[l.index].uv=((co.x+.11)/.22,(co.z-1.34)/.27)
    # Copy actual deform weights from the corresponding original loop vertex.
    for g in face.vertex_groups:ob.vertex_groups.new(name=g.name)
    for row in range(len(profile)):
        for j,i in enumerate(sequence):
            for g in face.data.vertices[i].groups:ob.vertex_groups[g.group].add([row*n+j],g.weight,'REPLACE')
    ob.shape_key_add(name='Basis')
    for key in list(face.data.shape_keys.key_blocks)[1:]:
        target=ob.shape_key_add(name=key.name)
        for row,(distance,depth) in enumerate(profile):
            for j,i in enumerate(sequence):target.data[row*n+j].co=face.matrix_world@key.data[i].co+normals[j]*distance+Vector((0,depth,0))
    recalc(ob);join_to_face(ob)

for loop in loops:
    center=sum((face.matrix_world@face.data.vertices[i].co for i in loop),Vector())/len(loop)
    attach_rim(loop,center.z<1.40)

# More density only on curved facial skin. Texture shells keep their edge shape.
crease_attr=face.data.attributes.get('crease_edge') or face.data.attributes.new('crease_edge','FLOAT','EDGE')
non_skin={i for p in face.data.polygons if p.material_index!=skin_index for i in p.vertices}
for e in face.data.edges:
    if any(i in non_skin for i in e.vertices):crease_attr.data[e.index].value=1
sub=face.modifiers.new('Facial surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1
sub.show_only_control_edges=True

# Original eye look bones/iris and all original morph names remain in service.
white=toon('Production / Eyeball sclera','EEF2F2','CCD6E0',0)
for side,x in [('L',.040),('R',-.0405)]:
    ob=ellipsoid('EyeGlobe_'+side,(x,-.0565,1.447),(.023,.0205,.016),white,'J_Adj_'+side+'_FaceEye' if bpy.data.objects['Armature'].data.bones.get('J_Adj_'+side+'_FaceEye') else 'J_Bip_C_Head')
    bm=bmesh.new();bm.from_mesh(ob.data)
    aperture=[f for f in bm.faces if f.calc_center_median().y<-.057 and ((f.calc_center_median().x-x)/.0195)**2+((f.calc_center_median().z-1.447)/.0135)**2<1]
    bmesh.ops.delete(bm,geom=aperture,context='FACES');bm.to_mesh(ob.data);bm.free()
    ob['anatomy']='Spherical scleral volume with a real anterior aperture behind the retained animated iris'
    new_uv([ob])

# Concave iris/pupil profile; deterministic 1024px painted color without random noise.
iris_material=next(m for m in face.data.materials if 'EyeIris' in m.name)
iris_indices={i for p in face.data.polygons if 'EyeIris' in face.data.materials[p.material_index].name for i in p.vertices}
for key in face.data.shape_keys.key_blocks:
    for i in iris_indices:
        co=face.matrix_world@key.data[i].co;cx=.040 if co.x>0 else -.0405
        r=math.sqrt(((co.x-cx)/.019)**2+((co.z-1.447)/.013)**2)
        co.y+=.00065*max(0,1-r*r);key.data[i].co=inverse@co
size=1024;yy,xx=np.mgrid[0:size,0:size];u=((xx/(size-1))%.5-.25)/.153;v=(yy/(size-1)-.505)/.322;r=np.sqrt(u*u+v*v)
color=np.zeros((size,size,4),dtype=np.float32);color[:,:,3]=1
upper=np.clip((v+.05)*1.0,0,1);base=np.array([.32,.66,.70]);top=np.array([.17,.38,.46])
color[:,:,:3]=base[None,None,:]*(1-upper[:,:,None])+top[None,None,:]*upper[:,:,None]
color[r<.36,:3]=[.065,.13,.18];color[r>.91,:3]=[.12,.22,.29]
# One restrained drawn glint, with the physical corneal layer added later.
color[((u+.32)/.14)**2+((v-.35)/.14)**2<1,:3]=[.9,.98,1]
image=bpy.data.images.new('Researcher iris detail 1024',width=size,height=size,alpha=True);image.pixels.foreach_set(color.ravel());image.pack()
g=iris_material.vrm_addon_extension.mtoon1;g.pbr_metallic_roughness.base_color_texture.index.source=image;g.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source=image
assert [k.name for k in face.data.shape_keys.key_blocks]==keys_before,'Morph names changed'
assert bones_before=={b.name:tuple(v for row in b.matrix_local for v in row) for b in bpy.data.objects['Armature'].data.bones},'Rig changed'
face['production_changes']='Cheek/jaw/bridge/lip sculpt; attached 3D eyelid/lip rims; creased selective subdivision'
save_phase('face')
render_views(ROOT/'previews/v0.2/phase1-face',['face','side','quarter'])
