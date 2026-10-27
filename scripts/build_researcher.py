"""Build the project character from a CC0 rigged base; preserve face topology."""
from pathlib import Path
import sys, math, json
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from mathutils.geometry import barycentric_transform,tessellate_polygon
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT, enable_vrm
bpy.ops.wm.read_factory_settings(use_empty=True)
enable_vrm()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/base-import.blend'))
print('BUILD: imported',flush=True)
arm=bpy.data.objects['Armature']
face=bpy.data.objects['Face']
body=bpy.data.objects['Body']
HEAD='J_Bip_C_Head'; CHEST='J_Bip_C_UpperChest'

def rgb(value):
    values=[int(value[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values)

def bitmap_rgb(value):
    # Packed PNG pixels are encoded sRGB; material factors above are linear.
    return tuple(int(value[i:i+2],16)/255 for i in (0,2,4))

def toon(name,color,shade=None,outline=.00055):
    material=bpy.data.materials.new(name)
    gltf=material.vrm_addon_extension.mtoon1
    gltf.enabled=True
    gltf.pbr_metallic_roughness.base_color_factor=(*rgb(color),1)
    m=gltf.extensions.vrmc_materials_mtoon
    m.shade_color_factor=rgb(shade or color)
    m.shading_toony_factor=1
    m.shading_shift_factor=.1
    m.gi_equalization_factor=1
    m.parametric_rim_color_factor=(0,0,0)
    m.outline_width_mode='worldCoordinates' if outline else 'none'
    m.outline_width_factor=outline
    m.outline_color_factor=rgb('171D2C')
    material.diffuse_color=(*rgb(color),1)
    return material

navy=toon('Researcher / Navy knit','202839','171F31')
white=toon('Researcher / Lab coat','F2F3F6','C9CFDE')
cyan=toon('Researcher / Cyan seams','4EC3E6','309AB9',.00025)
frame=toon('Researcher / Charcoal glasses','303744','202738',.00015)
hairmat=toon('Researcher / Navy bob','252C40','192033',.00065)
hairlight=toon('Researcher / Hair light','3F4B68','29374D',.0002)
hairgraphic=toon('Researcher / Painted hair bands','252C40','192033',.00065)
image=bpy.data.images.new('Researcher painted hair band',width=256,height=256,alpha=True)
pixels=[]
for iy in range(256):
    for ix in range(256):
        u=ix/255;v=iy/255
        band=.31+.05*math.sin(math.pi*u/.5)
        c=bitmap_rgb('3F4B68') if .07<u<.43 and band<v<band+.026 else bitmap_rgb('252C40')
        pixels.extend((*c,1))
image.pixels=pixels;image.pack()
hg=hairgraphic.vrm_addon_extension.mtoon1
hg.pbr_metallic_roughness.base_color_factor=(1,1,1,1)
hg.pbr_metallic_roughness.base_color_texture.index.source=image
hg.extensions.vrmc_materials_mtoon.shade_color_factor=(.6,.65,.75)
hg.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source=image
metal=toon('Researcher / Pen clip','8A97A9','5B6778',.0002)
skinshadow=toon('Researcher / Drawn face accents','D1A18D','D1A18D',0)
lipline=toon('Researcher / Mouth line','875E60','875E60',0)
coatshadow=toon('Researcher / Coat shadow','D2D8E5','D2D8E5',0)
knitshadow=toon('Researcher / Knit shadow','151E2F','151E2F',0)

def bind(ob,bone=HEAD):
    vg=ob.vertex_groups.new(name=bone)
    vg.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    mod=ob.modifiers.new('Researcher rig','ARMATURE');mod.object=arm
    ob.parent=arm
    return ob

def mesh(name,verts,faces,mat,bone=HEAD,smooth=True):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    for p in data.polygons:p.use_smooth=smooth
    bind(ob,bone)
    return ob

def tube(name,points,mat,radius=.0012,bone=HEAD,cyclic=False):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=12
    data.bevel_depth=radius;data.bevel_resolution=2
    spl=data.splines.new('POLY');spl.points.add(len(points)-1)
    for p,co in zip(spl.points,points):p.co=(*co,1)
    spl.use_cyclic_u=cyclic
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.data.materials.append(mat)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    bpy.ops.object.convert(target='MESH');ob.select_set(False)
    return bind(ob,bone)

def ellipsoid_ring(z,rx,ry,cy,n=48):
    return [(rx*math.cos(2*math.pi*i/n),cy+ry*math.sin(2*math.pi*i/n),z) for i in range(n)]

def shell(name,rings,mat,bone=CHEST,n=48):
    verts=[]
    for z,rx,ry,cy in rings:verts.extend(ellipsoid_ring(z,rx,ry,cy,n))
    faces=[]
    for row in range(len(rings)-1):
        for i in range(n):faces.append((row*n+i,row*n+(i+1)%n,(row+1)*n+(i+1)%n,(row+1)*n+i))
    return mesh(name,verts,faces,mat,bone)

# Preserve all expression deltas while making the eye area slightly less round.
for key in face.data.shape_keys.key_blocks:
    for p in key.data:
        co=face.matrix_world @ p.co
        x,y,z=co
        eye=math.exp(-((abs(x)-.041)/.043)**4)*math.exp(-((z-1.447)/.034)**4)
        front=max(0,min(1,(-y-.025)/.035))
        co.x*=.96
        co.z=1.447+(z-1.447)*(1-.24*eye*front)
        if z<1.435:co.z-=.004*max(0,min(1,(1.435-z)/.10))
        p.co=face.matrix_world.inverted() @ co

# Eyeliner is a textured surface on top of skin: give it a stable depth separation.
line_vertices={i for p in face.data.polygons if any(s in face.data.materials[p.material_index].name for s in ['FaceEyeline','FaceEyelash','FaceBrow']) for i in p.vertices}
offset=face.matrix_world.inverted().to_3x3() @ Vector((0,-.0015,0))
for key in face.data.shape_keys.key_blocks:
    for i in line_vertices:key.data[i].co+=offset

# Skin and lines use flat drawn colors, rather than glossy material rims.
for material in list(bpy.data.materials):
    gltf=material.vrm_addon_extension.mtoon1
    if not gltf.enabled:continue
    m=gltf.extensions.vrmc_materials_mtoon
    m.parametric_rim_color_factor=(0,0,0)
    m.matcap_factor=(0,0,0)
    m.shading_toony_factor=1
    m.gi_equalization_factor=1
    if 'Face_00_SKIN' in material.name:
        gltf.pbr_metallic_roughness.base_color_texture.index.source=None
        gltf.pbr_metallic_roughness.base_color_factor=(*rgb('F6D4BF'),1)
        m.shade_multiply_texture.index.source=None
        m.shade_color_factor=rgb('E6B5A2')
        m.outline_color_factor=rgb('523B42');m.outline_width_factor=.00035
    if any(s in material.name for s in ['FaceBrow','FaceEyeline','FaceEyelash']):
        gltf.pbr_metallic_roughness.base_color_factor=(*rgb('252C40'),1)
        m.shade_color_factor=rgb('252C40')
    if 'EyeIris' in material.name:
        # A new procedural flat iris texture, rather than tinting an amber bitmap.
        image=bpy.data.images.get('Researcher teal iris') or bpy.data.images.new('Researcher teal iris',width=256,height=256,alpha=True)
        pixels=[]
        for py in range(256):
            for px in range(256):
                u=((px/255)% .5-.25)/.153;v=(py/255-.505)/.322;r=(u*u+v*v)**.5
                if r<.38:c=bitmap_rgb('142331')
                elif r>.92:c=bitmap_rgb('213548')
                else:
                    q=max(0,min(1,(1-v)/2))
                    c=bitmap_rgb('377E91') if v>.0 else bitmap_rgb('5CAFB7')
                if ((u+.34)/.18)**2+((v-.38)/.18)**2<1:c=(.88,.97,1)
                if ((u-.31)/.09)**2+((v+.4)/.11)**2<1:c=(.45,.78,.84)
                pixels.extend((*c,1))
        image.pixels=pixels;image.pack()
        gltf.pbr_metallic_roughness.base_color_texture.index.source=image
        gltf.pbr_metallic_roughness.base_color_factor=(1,1,1,1)
        m.shade_multiply_texture.index.source=image
        m.shade_color_factor=(1,1,1)
    if 'EyeHighlight' in material.name:
        # The new iris contains its own coherent highlights.
        image=bpy.data.images.get('Researcher transparent') or bpy.data.images.new('Researcher transparent',width=4,height=4,alpha=True)
        image.pixels=[0.0]*64;image.pack()
        gltf.pbr_metallic_roughness.base_color_texture.index.source=image
        m.shade_multiply_texture.index.source=image
        gltf.alpha_mode='BLEND'

print('BUILD: materials',flush=True)
# Drop unused extra-eye/highlight overlays. Keep every expression key intact.
bpy.ops.object.select_all(action='DESELECT');face.select_set(True)
bpy.context.view_layer.objects.active=face
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
for p in face.data.polygons:
    p.select=any(s in face.data.materials[p.material_index].name for s in ['EyeExtra','EyeHighlight'])
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.delete(type='ONLY_FACE');bpy.ops.object.mode_set(mode='OBJECT')
# Weld only seams that stay coincident in ALL 42 expression shapes.
kd=KDTree(len(face.data.vertices))
for v in face.data.vertices:kd.insert(v.co,v.index)
kd.balance();safe=set()
for v in face.data.vertices:
    others=[i for co,i,d in kd.find_range(v.co,1e-7) if i>v.index]
    for other in others:
        if all((k.data[v.index].co-k.data[other].co).length<1e-7 for k in face.data.shape_keys.key_blocks):safe.update([v.index,other])
for v in face.data.vertices:v.select=v.index in safe
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.remove_doubles(threshold=1e-7)
bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.delete_loose();bpy.ops.object.mode_set(mode='OBJECT')
face.select_set(False)
# Remove the sample hairstyle and neck bow; the underlying skin and rig remain.
if bpy.data.objects.get('Hair001'):
    bpy.data.objects.remove(bpy.data.objects['Hair001'],do_unlink=True)
bm=bmesh.new();bm.from_mesh(body.data)
remove=[p for p in bm.faces if any(s in body.data.materials[p.material_index].name for s in ['AccessoryNeck','Tops_','HairBack'])]
remove+= [p for p in bm.faces if 'Body_00_SKIN' in body.data.materials[p.material_index].name and .90<(body.matrix_world@p.calc_center_median()).z<1.326 and abs((body.matrix_world@p.calc_center_median()).x)<.17 and p not in remove]
bmesh.ops.delete(bm,geom=remove,context='FACES')
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
# The sample's nail shells were almost coplanar with fingertips. Keep the nails,
# but move each whole shell outward by 0.8 mm, rather than deleting hand faces.
bm.verts.ensure_lookup_table();bm.verts.index_update();bm.normal_update()
seen=set();nails=0
for seed in bm.verts:
    if seed.index in seen:continue
    component=[];todo=[seed];seen.add(seed.index)
    while todo:
        v=todo.pop();component.append(v)
        for e in v.link_edges:
            other=e.other_vert(v)
            if other.index not in seen:seen.add(other.index);todo.append(other)
    if len(component)!=18:continue
    normal=sum((v.normal for v in component),Vector()).normalized()
    for v in component:v.co+=normal*.0008
    nails+=1
print('Separated nail shells:',nails,flush=True)
bm.to_mesh(body.data);bm.free()
for i,material in enumerate(body.data.materials):
    if 'Tops_' in material.name:body.data.materials[i]=white
    elif 'HairBack' in material.name:body.data.materials[i]=hairmat

# Open coat body over a continuous navy knit torso; no texture-only fake opening.
knit=shell('Researcher_Knit',[(.94,.105,.065,-.002),(1.03,.111,.072,-.006),(1.12,.121,.084,-.011),(1.20,.137,.081,-.006),(1.26,.109,.066,.0)],navy)
collar=shell('Researcher_Turtleneck',[(1.225,.080,.100,-.005),(1.25,.071,.089,-.005),(1.28,.061,.069,0),(1.339,.055,.056,.006)],navy)
# Purpose-built open coat panels, with a real opening instead of overlapping sample clothes.
coat_rings=[(1.278,.119,.075,.002),(1.265,.143,.086,.002),(1.245,.151,.096,0),(1.205,.147,.100,-.006),(1.13,.137,.105,-.006),(1.04,.126,.085,0),(.94,.135,.087,0),(.83,.145,.089,0)]
verts=[];faces=[];n=52
for z,rx,ry,cy in coat_rings:
    opening=.52 if z>1.14 else .55
    for i in range(n):
        a=-math.pi/2+opening+(2*math.pi-2*opening)*i/(n-1)
        verts.append((rx*math.cos(a),cy+ry*math.sin(a),z))
for row in range(len(coat_rings)-1):
    for i in range(n-1):
        a=row*n+i;faces.append((a,a+n,a+n+1,a+1))
coat=mesh('Researcher_Coat',verts,faces,white,CHEST)
for side in ['L','R']:
    upper=arm.data.bones['J_Bip_'+side+'_UpperArm'];lower=arm.data.bones['J_Bip_'+side+'_LowerArm']
    start=upper.head_local;elbow=lower.head_local;end=lower.tail_local
    axis=(end-start).normalized();v=Vector((0,1,0));w=axis.cross(v).normalized()
    vertices=[];faces=[];samples=[(-.055,.008),(-.035,.025),(0,.042),(.06,.050),(.12,.051),(.23,.051),(.38,.049),(.50,.045),(.62,.044),(.72,.042),(.85,.039),(.97,.036)]
    for t,r in samples:
        p=start.lerp(end,t)
        for i in range(24):
            a=2*math.pi*i/24;vertices.append(tuple(p+r*(v*math.cos(a)+w*math.sin(a))))
    for j in range(len(samples)-1):
        for i in range(24):faces.append((j*24+i,j*24+(i+1)%24,(j+1)*24+(i+1)%24,(j+1)*24+i))
    sleeve=mesh('Researcher_CoatSleeve_'+side,vertices,faces,white,upper.name)
    lower_group=sleeve.vertex_groups.new(name=lower.name)
    elbow_t=(elbow-start).length/(end-start).length
    for j,(t,r) in enumerate(samples):
        weight=max(0,min(1,(t-elbow_t+.08)/.16))
        ids=list(range(j*24,(j+1)*24))
        sleeve.vertex_groups[upper.name].add(ids,1-weight,'REPLACE')
        if weight:lower_group.add(ids,weight,'REPLACE')
    sub=sleeve.modifiers.new('Rounded sleeve','SUBSURF');sub.levels=1
    with bpy.context.temp_override(object=sleeve,active_object=sleeve):bpy.ops.object.modifier_apply(modifier=sub.name)
print('BUILD: sleeves',flush=True)
# Keep a navy inset panel in front of the existing white top.
frontverts=[(-.048,-.075,1.265),(.048,-.075,1.265),(.061,-.113,1.23),(.080,-.100,1.12),(.068,-.081,.94),(-.068,-.081,.94),(-.080,-.100,1.12),(-.061,-.113,1.23)]
mesh('Researcher_CoatOpening',frontverts,[tuple(reversed(range(8)))],navy,smooth=False)
for side in [-1,1]:
    # Clearly structured white lapels, separated from the navy knit.
    verts=[(side*.046,-.088,1.306),(side*.105,-.101,1.259),(side*.087,-.124,1.220),(side*.113,-.116,1.190),(side*.071,-.124,1.122),(side*.052,-.121,1.245)]
    if side<0:verts.reverse()
    mesh('Researcher_Lapel_'+str(side),verts,[tuple(range(6))],white,smooth=False)
    mesh('Researcher_LapelShadow_'+str(side),[(side*.052,-.123,1.243),(side*.112,-.118,1.189),(side*.072,-.126,1.120)],[(0,1,2)],coatshadow,smooth=False)
    tube('Researcher_LapelSeam_'+str(side),[(side*.048,-.0895,1.305),(side*.101,-.104,1.260),(side*.085,-.126,1.221)],cyan,.0013,CHEST)
    tube('Researcher_CoatTrim_'+str(side),[(side*.072,-.125,1.120),(side*.073,-.111,1.040),(side*.064,-.093,.945)],cyan,.0015,CHEST)

# The pocket and pen are separate editable forms with a visible purpose.
mesh('Researcher_Pocket',[(.085,-.099,1.155),(.129,-.086,1.155),(.124,-.079,1.102),(.083,-.099,1.102)],[(0,1,2,3)],white,smooth=False)
tube('Researcher_PocketTrim',[(.085,-.1005,1.153),(.128,-.0875,1.153)],cyan,.0011,CHEST)
tube('Researcher_Pen',[(.106,-.098,1.129),(.107,-.097,1.187)],cyan,.0033,CHEST)
tube('Researcher_PenClip',[(.107,-.101,1.184),(.110,-.101,1.182),(.110,-.101,1.158),(.108,-.100,1.156)],metal,.0009,CHEST)

# Ring openings stay outside the cheeks. This prevents a cap cutting across eyes.
profiles=[(1.603,.018,.018,0),(1.598,.046,.039,0),(1.586,.077,.064,.0),(1.568,.101,.086,.15),(1.545,.114,.101,.60),(1.515,.121,.105,1.02),(1.48,.124,.103,1.15),(1.44,.124,.100,1.20),(1.39,.120,.094,1.26),(1.35,.102,.082,1.30)]
verts=[];faces=[];n=96
for z,rx,ry,opening in profiles:
    for i in range(n):
        a=-math.pi/2+opening+(2*math.pi-2*opening)*i/(n-1)
        verts.append((rx*math.cos(a),.010+ry*math.sin(a),z))
for row in range(len(profiles)-1):
    for i in range(n-1):
        a=row*n+i;faces.append((a,a+n,a+n+1,a+1))
faces.append(tuple(reversed(range(n))))
cap=mesh('Researcher_BobCap',verts,faces,hairmat)
bm=bmesh.new();bm.from_mesh(cap.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cap.data);bm.free()
sub=cap.modifiers.new('Smooth bob foundation','SUBSURF');sub.levels=1
with bpy.context.temp_override(object=cap,active_object=cap):bpy.ops.object.modifier_apply(modifier=sub.name)

print('BUILD: cap',flush=True)
def hair_lock(name,points,width,highlight=False):
    # A swept closed oval, not a flat sheet. Its width follows the curve tangent.
    verts=[];faces=[];rows=42;cols=16
    points=[Vector(p) for p in points]
    for p in points:p.z+=.009*max(0,min(1,(p.z-1.53)/.05))
    def bezier(t):
        return (1-t)**3*points[0]+3*(1-t)**2*t*points[1]+3*(1-t)*t*t*points[2]+t**3*points[3]
    for row in range(rows):
        t=row/(rows-1)
        center=bezier(t)
        tangent=bezier(min(1,t+.001))-bezier(max(0,t-.001))
        across=Vector((-tangent.z,0,tangent.x)).normalized()
        w=width*(.22+.78*math.sin(math.pi*(.07+.93*t))**.65)
        w=max(.0005,w)
        for col in range(cols):
            a=2*math.pi*col/cols
            p=center+across*(w*math.cos(a))+Vector((0,-max(.0004,.0045*math.sin(math.pi*(.07+.93*t)))*math.sin(a),0))
            verts.append(tuple(p))
    for row in range(rows-1):
        for col in range(cols):
            a=row*cols+col;b=row*cols+(col+1)%cols
            faces.append((a,b,b+cols,a+cols))
    faces.extend([tuple(reversed(range(cols))),tuple((rows-1)*cols+i for i in range(cols))])
    ob=mesh(name,verts,faces,hairgraphic if highlight else hairmat)
    uv=ob.data.uv_layers.new(name='Hair length')
    for p in ob.data.polygons:
        wrap=any(i%cols==cols-1 for i in p.vertices) and any(i%cols==0 for i in p.vertices)
        for li in p.loop_indices:
            idx=ob.data.loops[li].vertex_index
            u=idx%cols/cols
            if wrap and u==0:u=1
            uv.data[li].uv=(u,idx//cols/(rows-1))
        if len(p.vertices)==cols:
            for li in p.loop_indices:
                idx=ob.data.loops[li].vertex_index;a=2*math.pi*(idx%cols)/cols
                uv.data[li].uv=(.75+.10*math.cos(a),.9+.07*math.sin(a))
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    return ob

# Broad, curved masses follow the asymmetric part and leave the pupils readable.
hair_lock('Researcher_LeftOuter',[(.005,-.025,1.588),(-.064,-.052,1.581),(-.130,-.038,1.462),(-.108,-.025,1.350)],.021,True)
hair_lock('Researcher_LeftMid',[(.025,-.033,1.586),(-.050,-.078,1.575),(-.120,-.086,1.466),(-.096,-.066,1.348)],.024,True)
hair_lock('Researcher_FringeMain',[(.033,-.044,1.583),(-.020,-.103,1.566),(-.063,-.111,1.504),(-.080,-.102,1.474)],.022,True)
hair_lock('Researcher_FringeFine',[(.039,-.051,1.578),(.008,-.113,1.553),(-.034,-.116,1.505),(-.053,-.110,1.476)],.010,True)
hair_lock('Researcher_RightFringe',[(.036,-.037,1.585),(.070,-.080,1.581),(.093,-.093,1.523),(.084,-.091,1.474)],.019,True)
hair_lock('Researcher_TuckedSide',[(.041,-.021,1.588),(.116,-.028,1.579),(.119,-.038,1.501),(.102,-.036,1.453)],.022,True)
hair_lock('Researcher_RightBob',[(.077,.005,1.563),(.133,.0,1.520),(.123,-.011,1.401),(.107,-.009,1.352)],.020)
hair_lock('Researcher_LeftTip', [(-.099,.008,1.503),(-.132,-.011,1.438),(-.118,-.033,1.373),(-.085,-.051,1.345)],.017)

# Rounded rectangular glasses, in a curved face plane, are rigidly weighted to the head.
parts=[]
for side in [-1,1]:
    pts=[];cx=side*.040;cz=1.451;rx=.033;rz=.019
    for i in range(64):
        a=2*math.pi*i/64
        x=cx+rx*math.copysign(abs(math.cos(a))**.46,math.cos(a))
        z=cz+rz*math.copysign(abs(math.sin(a))**.58,math.sin(a))
        y=-.112+.016*(abs(x)/.085)**2
        pts.append((x,y,z))
    parts.append(tube('Researcher_GlassesRim',pts,frame,.00135,cyclic=True))
    parts.append(tube('Researcher_GlassesTemple',[(side*.073,-.100,1.463),(side*.099,-.045,1.461),(side*.102,.010,1.449),(side*.100,.019,1.440)],frame,.0014))
parts.append(tube('Researcher_GlassesBridge',[(-.008,-.112,1.459),(-.005,-.117,1.463),(0,-.119,1.464),(.005,-.117,1.463),(.008,-.112,1.459)],frame,.0013))
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.object.join();glasses=bpy.context.object;glasses.name='Researcher_Glasses'
glasses.shape_key_add(name='Basis')
slide=glasses.shape_key_add(name='GlassesSlide')
for p in slide.data:p.co.z-=.012;p.co.y-=.003

# Explicit VRM expression bindings for independent eye, brow, mouth, and glasses control.
vrm=arm.data.vrm_addon_extension.vrm0
groups=vrm.blend_shape_master.blend_shape_groups
def expression(name,suffix,ob=face):
    key=next((k for k in ob.data.shape_keys.key_blocks if k.name.endswith(suffix)),None)
    if not key:return
    group=groups.add();group.name=name;group.preset_name='unknown';group.is_binary=False
    bind=group.binds.add();bind.mesh.mesh_object_name=ob.name;bind.index=key.name;bind.weight=1
for name,suffix in [('browDown','Fcl_BRW_Angry'),('browUp','Fcl_BRW_Surprised'),('mouthSmile','Fcl_MTH_Joy'),('mouthFrown','Fcl_MTH_Sorrow'),('eyeWide','Fcl_EYE_Surprised')]:expression(name,suffix)
expression('glassesSlide','GlassesSlide',glasses)

print('BUILD: expressions',flush=True)
# Drawn facial accents sit on the actual face and inherit every expression delta.
# Barycentric transfer keeps the mouth line attached while talking or smiling.
face.data.calc_loop_triangles()
skin_index=next(i for i,m in enumerate(face.data.materials) if 'Face_00_SKIN' in m.name)
triangles=[tuple(t.vertices) for t in face.data.loop_triangles if face.data.polygons[t.polygon_index].material_index==skin_index]
world=[face.matrix_world@v.co for v in face.data.vertices]
surface=BVHTree.FromPolygons(world,triangles,all_triangles=True)
print('BUILD: face surface',flush=True)
def face_accent(name,xzs,mat):
    vertices=[];attachments=[];polygons=[];points=[];point_ids={}
    # Tessellate and project a fine mesh; a single flat triangle can sink into a nose.
    def add_point(p):
        coord=(round(p.x,7),round(p.z,7))
        if coord not in point_ids:point_ids[coord]=len(points);points.append(coord)
        return point_ids[coord]
    polygon=[Vector((x,0,z)) for x,z in xzs]
    for tri in tessellate_polygon([polygon]):
        a,b,c=[polygon[i] for i in tri] if isinstance(tri[0],int) else tri
        n=8
        grid={}
        for i in range(n+1):
            for j in range(n+1-i):grid[i,j]=add_point(a+(b-a)*(i/n)+(c-a)*(j/n))
        for i in range(n):
            for j in range(n-i):
                polygons.append((grid[i,j],grid[i+1,j],grid[i,j+1]))
                if j<n-i-1:polygons.append((grid[i+1,j],grid[i+1,j+1],grid[i,j+1]))
    for x,z in points:
        point,normal,idx,distance=surface.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
        if point is None:raise RuntimeError('Face accent missed skin: '+name)
        tri=triangles[idx];attachments.append((point.copy(),tri))
        vertices.append(tuple(point+Vector((0,-.0012,0))))
    ob=mesh(name,vertices,polygons,mat,HEAD,False)
    uv=ob.data.uv_layers.new(name=face.data.uv_layers.active.name)
    for li in ob.data.loops:
        p=ob.data.vertices[li.vertex_index].co
        uv.data[li.index].uv=((p.x+.11)/.22,(p.z-1.34)/.26)
    if ob.data.polygons[0].normal.y>0:
        bm=bmesh.new();bm.from_mesh(ob.data)
        for p in bm.faces:p.normal_flip()
        bm.to_mesh(ob.data);bm.free()
    ob.shape_key_add(name='Basis')
    for source in list(face.data.shape_keys.key_blocks)[1:]:
        key=ob.shape_key_add(name=source.name)
        for p,(point,tri) in zip(key.data,attachments):
            target=[face.matrix_world@source.data[i].co for i in tri]
            p.co=barycentric_transform(point,*[world[i] for i in tri],*target)+Vector((0,-.0012,0))
    # Join matching keys into the face, so existing VRM bindings drive both.
    bpy.ops.object.select_all(action='DESELECT')
    face.select_set(True);ob.select_set(True)
    bpy.context.view_layer.objects.active=face
    with bpy.context.temp_override(object=face,active_object=face,selected_objects=[face,ob],selected_editable_objects=[face,ob]):
        if bpy.ops.object.join()!={'FINISHED'}:raise RuntimeError('Face accent join failed')
face_accent('Researcher_NoseAccent',[(.001,1.4165),(-.003,1.4078),(.002,1.4073)],skinshadow)

# Proper UV islands on new solid-color geometry, ready for subsequent painting.
bpy.ops.object.select_all(action='DESELECT')
plain=[o for o in bpy.data.objects if o.type=='MESH' and o not in [face,body] and not any(m==hairgraphic for m in o.data.materials)]
for ob in plain:ob.select_set(True)
bpy.context.view_layer.objects.active=plain[0]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02,area_weight=.5,correct_aspect=True,scale_to_bounds=True)
bpy.ops.object.mode_set(mode='OBJECT')
meta=vrm.meta
meta.title='Researcher A — Prototype 0.1'
meta.author='graind / project customization; CC0 base: pixiv'
meta.version='0.1.0'
meta.reference='https://vroid.pixiv.help/hc/en-us/articles/360012381793'
meta.license_name='CC0'
meta.commercial_ussage_name='Allow'

# Keep source asset fully editable and pack its referenced images.
bpy.ops.object.select_all(action='DESELECT')
arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a.blend'))
result=bpy.ops.export_scene.vrm(filepath=str(ROOT/'models/researcher-a.vrm'),armature_object_name=arm.name)
if result!={'FINISHED'}:raise RuntimeError(str(result))
report={'version':'0.1.0','objects':len(bpy.data.objects),'meshes':len([o for o in bpy.data.objects if o.type=='MESH']),'triangles':sum(len(p.vertices)-2 for ob in bpy.data.objects if ob.type=='MESH' for p in ob.data.polygons),'face_shape_keys':len(face.data.shape_keys.key_blocks),'glasses_control':'glassesSlide','export':str(ROOT/'models/researcher-a.vrm')}
(ROOT/'previews/researcher-build.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
