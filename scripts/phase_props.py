"""Phase 4/5: structural lenses/hinges/pads and physically layered clothing."""
from pathlib import Path
import sys,math
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import *
from character_studio import render_views,reset_pose
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-hair-v0.2.blend'));reset_pose()

# Fit the inherited nail shells onto the actual finger surface, with a clear
# 0.9 mm nail thickness. The original sample has nearly coplanar nail tips.
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();bm.verts.index_update()
components=[];seen=set()
for seed in bm.verts:
    if seed.index in seen:continue
    todo=[seed];island=[];seen.add(seed.index)
    while todo:
        v=todo.pop();island.append(v.index)
        for e in v.link_edges:
            j=e.other_vert(v).index
            if j not in seen:seen.add(j);todo.append(bm.verts[j])
    if len(island)==18:components.append(island)
nail_ids={i for island in components for i in island}
world=[body.matrix_world@v.co for v in body.data.vertices]
skin_bvh=BVHTree.FromPolygons(world,[tuple(p.vertices) for p in body.data.polygons if not any(i in nail_ids for i in p.vertices)])
inverse=body.matrix_world.inverted()
for i in nail_ids:
    hit=skin_bvh.find_nearest(world[i])
    if hit[0] is not None:
        original_normal=(body.matrix_world.to_3x3()@body.data.vertices[i].normal).normalized()
        alignment=original_normal.dot(hit[1])
        # Keep a solid nail plate: the inner cap and outer dome must not collapse
        # to the very same projected surface.
        thickness=.00055+.00075*max(0,min(1,(alignment+.15)/.65))
        body.data.vertices[i].co=inverse@(hit[0]+hit[1]*thickness)
bm.free()
# Preserve the inherited open skin normals. Correct orientation only on closed
# tiny nail islands after conforming them, using their signed volume.
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();bm.verts.index_update();seen=set()
for seed in bm.verts:
    if seed.index in seen:continue
    todo=[seed];island=[];seen.add(seed.index)
    while todo:
        v=todo.pop();island.append(v)
        for e in v.link_edges:
            other=e.other_vert(v)
            if other.index not in seen:seen.add(other.index);todo.append(other)
    fs={f for v in island for f in v.link_faces};edges={e for v in island for e in v.link_edges}
    if all(len(e.link_faces)==2 for e in edges):
        volume=sum(f.verts[0].co.dot(f.verts[j].co.cross(f.verts[j+1].co))/6 for f in fs for j in range(1,len(f.verts)-1))
        if volume<0:
            for f in fs:f.normal_flip()
bm.to_mesh(body.data);bm.free()

def remove(name):
    ob=bpy.data.objects.get(name)
    if ob:bpy.data.objects.remove(ob,do_unlink=True)

navy=toon('Production / Structured knit','242D42','141F32',.0003)
coatmat=toon('Production / Lab coat cotton','F1F2F5','C3CDDE',.00035)
lining=toon('Production / Coat lining','D7DFEB','B1BDD2',.0002)
cyan=toon('Production / Cyan piping','52BFDD','338EA8',.00015)
stitch=toon('Production / Topstitch','ABB8CB','ABB8CB',0)
metal=toon('Production / Brushed fittings','73859B','414F65',.0001)
frame_mat=bpy.data.materials['Researcher / Charcoal glasses']

# Use the existing frame, but fit it to the actual nose/temples.
glasses=bpy.data.objects['Researcher_Glasses']
def fit_y(y):return y+.013*max(0,min(1,(-y+.005)/.10))
for key in glasses.data.shape_keys.key_blocks:
    for p in key.data:p.co.y=fit_y(p.co.y)
for p in glasses.data.polygons:p.use_smooth=True
bevel=glasses.modifiers.new('Frame edge bevel','BEVEL');bevel.width=.00025;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.7

def glass_material(name,alpha,roughness,ior):
    m=bpy.data.materials.new(name);m.diffuse_color=(.85,.95,1,alpha);m.surface_render_method='BLENDED'
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(.85,.95,1,1);bs.inputs['Roughness'].default_value=roughness;bs.inputs['IOR'].default_value=ior
    bs.inputs['Transmission Weight'].default_value=.9;bs.inputs['Alpha'].default_value=alpha
    bs.inputs['Coat Weight'].default_value=.25;bs.inputs['Coat Roughness'].default_value=.06
    m.roughness=roughness
    return m
lensmat=glass_material('Production / Optical lenses',.025,.07,1.46)
padmat=toon('Production / Silicone nose pads','B6C2CE','8A9BAE',0)
parts=[]
for side in [-1,1]:
    cx=side*.040;cz=1.451;segments=64;rings=9;vertices=[];faces=[]
    # A shallow curved optical surface with a real edge thickness.
    for layer in range(2):
        vertices.append((cx,fit_y(-.112)-.0012+layer*.00055,cz))
        for j in range(1,rings+1):
            t=j/rings
            for i in range(segments):
                a=2*math.pi*i/segments
                x=cx+.0305*t*math.copysign(abs(math.cos(a))**.46,math.cos(a));z=cz+.0165*t*math.copysign(abs(math.sin(a))**.58,math.sin(a))
                y=fit_y(-.112+.016*(abs(x)/.085)**2)-.0012*(1-t*t)+layer*.00055
                vertices.append((x,y,z))
    layer_count=1+segments*rings
    for layer in range(2):
        o=layer*layer_count
        for i in range(segments):faces.append((o,o+1+(i+1)%segments,o+1+i) if layer==0 else (o,o+1+i,o+1+(i+1)%segments))
        for j in range(rings-1):
            for i in range(segments):
                a=o+1+j*segments+i;b=o+1+j*segments+(i+1)%segments
                faces.append((a,a+segments,b+segments,b) if layer==0 else (a,b,b+segments,a+segments))
    for i in range(segments):
        a=1+(rings-1)*segments+i;b=1+(rings-1)*segments+(i+1)%segments
        faces.append((a,b,b+layer_count,a+layer_count))
    ob=mesh('Optical_Lens_'+str(side),vertices,faces,lensmat);recalc(ob);parts.append(ob)
    parts.append(ellipsoid('Glasses_Hinge_'+str(side),(side*.074,fit_y(-.099),1.463),(.0024,.0021,.0032),metal,segments=20,rings=12))
    parts.append(ellipsoid('Glasses_Pad_'+str(side),(side*.0095,-.0865,1.444),(.0023,.0016,.0042),padmat,segments=20,rings=12))
    parts.append(tube('Glasses_PadArm_'+str(side),[(side*.009,-.100,1.457),(side*.010,-.093,1.451),(side*.0095,-.0875,1.445)],metal,.0007))
    parts.append(tube('Glasses_HingePin_'+str(side),[(side*.074,fit_y(-.099),1.459),(side*.074,fit_y(-.099),1.467)],metal,.0006))
# Keep the existing glasses morph binding: added parts share the same two keys.
for ob in parts:
    ob.shape_key_add(name='Basis');key=ob.shape_key_add(name='GlassesSlide')
    for p in key.data:p.co.z-=.012;p.co.y-=.003
    bpy.ops.object.select_all(action='DESELECT');glasses.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=glasses
    with bpy.context.temp_override(object=glasses,active_object=glasses,selected_objects=[glasses,ob],selected_editable_objects=[glasses,ob]):bpy.ops.object.join()
glasses['construction']='Original frame fitted to face; optical lens shells, beveled hinges, pins, silicone pads and pad arms; GlassesSlide retained'

# Rebuild only the original knit surfaces as continuous tailored geometry.
for name in ['Researcher_Knit','Researcher_Turtleneck','Researcher_CoatOpening','Researcher_LapelShadow_-1','Researcher_LapelShadow_1']:remove(name)
profile=[(.935,.108,.074,-.004),(1.00,.110,.076,-.004),(1.06,.118,.083,-.007),(1.12,.127,.092,-.011),(1.18,.136,.093,-.008),(1.23,.138,.090,-.002),(1.26,.123,.079,.002),(1.285,.090,.066,.004),(1.301,.055,.048,.006)]
verts=[];faces=[];n=64
for row,(z,rx,ry,cy) in enumerate(profile):
    for i in range(n):
        a=2*math.pi*i/n
        fold=.0015*math.exp(-((z-1.15)/.06)**2)*max(0,-math.sin(a))*math.sin(a*3+z*32)
        verts.append(((rx+fold)*math.cos(a),cy+(ry+fold)*math.sin(a),z))
for row in range(len(profile)-1):
    for i in range(n):
        a=row*n+i;b=row*n+(i+1)%n;faces.append((a,b,b+n,a+n))
knit=mesh('Researcher_Knit',verts,faces,navy,CHEST);solidify(knit,.0011)
sub=knit.modifiers.new('Knit form smoothing','SUBSURF');sub.levels=1;sub.render_levels=1
# Folded double collar with a physical lip rather than an open cylinder.
verts=[];faces=[];rings=[(1.301,.055,.048),(1.335,.049,.044),(1.338,.047,.042),(1.333,.045,.040),(1.301,.052,.045)]
for row,(z,rx,ry) in enumerate(rings):
    for i in range(n):
        a=2*math.pi*i/n;verts.append((rx*math.cos(a),(.006 if row==0 else .009)+ry*math.sin(a),z))
for row in range(len(rings)-1):
    for i in range(n):
        a=row*n+i;b=row*n+(i+1)%n;faces.append((a,b,b+n,a+n))
collar=mesh('Researcher_Turtleneck',verts,faces,navy,CHEST);recalc(collar)
bpy.ops.object.select_all(action='DESELECT');knit.select_set(True);collar.select_set(True);bpy.context.view_layer.objects.active=knit
with bpy.context.temp_override(object=knit,active_object=knit,selected_objects=[knit,collar],selected_editable_objects=[knit,collar]):bpy.ops.object.join()
bm=bmesh.new();bm.from_mesh(knit.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(knit.data);bm.free()

coat=bpy.data.objects['Researcher_Coat'];coat.data.materials[0]=coatmat
# Authored tension folds in the coat sides and waist; no uniform noise.
for v in coat.data.vertices:
    p=v.co;a=math.atan2(p.y,p.x)
    flare=max(0,min(1,(1.015-p.z)/.185))
    p.x*=1+.39*flare;p.y*=1+.36*flare
    waist=.002*math.exp(-((p.z-1.035)/.055)**2)*math.sin(2*a+.5)
    side=.0025*math.exp(-((p.z-1.18)/.045)**2)*abs(math.cos(a))**5
    p.y+=(waist+side)*math.sin(a)
sub=coat.modifiers.new('Tailored coat surface','SUBSURF');sub.levels=1;sub.render_levels=1
solidify(coat,.0018,.0004)
coat.data.materials.append(lining)
for mod in coat.modifiers:
    if mod.type=='SOLIDIFY':mod.material_offset=1;mod.material_offset_rim=1

for side in ['L','R']:
    sleeve=bpy.data.objects['Researcher_CoatSleeve_'+side];sleeve.data.materials[0]=coatmat
    arm=bpy.data.objects['Armature'];upper=arm.data.bones['J_Bip_'+side+'_UpperArm'];lower=arm.data.bones['J_Bip_'+side+'_LowerArm'];start=upper.head_local;end=lower.tail_local;axis=(end-start).normalized();length=(end-start).length
    for v in sleeve.data.vertices:
        rel=v.co-start;t=rel.dot(axis)/length;radial=rel-axis*rel.dot(axis)
        if radial.length<1e-6:continue
        a=math.atan2(radial.z,radial.y)
        # Two folds concentrated at the elbow, with a quieter forearm.
        amp=.0020*math.exp(-((t-.51)/.075)**2)*math.sin((t-.51)*70)*( .35+.65*max(0,math.cos(a-.8)))
        amp+=.0012*math.exp(-((t-.16)/.06)**2)*math.sin(t*48)*max(0,-math.sin(a))
        ease=.005*math.exp(-((t*length-(elbow-start).dot(axis))/.060)**2)
        v.co+=radial.normalized()*(amp+ease)
    # Transfer nearby original arm weights instead of an arbitrary linear cut.
    from mathutils.kdtree import KDTree
    source=[]
    for v in body.data.vertices:
        groups={body.vertex_groups[g.group].name:g.weight for g in v.groups}
        if sum(groups.get('J_Bip_'+side+'_'+part,0) for part in ['UpperArm','LowerArm','Hand'])>.25:source.append(v)
    kd=KDTree(len(source))
    for i,v in enumerate(source):kd.insert(body.matrix_world@v.co,i)
    kd.balance();sleeve.vertex_groups.clear();mapping={}
    for v in sleeve.data.vertices:
        weights={};neighbours=kd.find_n(v.co,6)
        for co,i,d in neighbours:
            factor=1/max(.001,d)**4
            for g in source[i].groups:
                name=body.vertex_groups[g.group].name
                if arm.data.bones.get(name) and arm.data.bones[name].use_deform:weights[name]=weights.get(name,0)+factor*g.weight
        largest=sorted(weights.items(),key=lambda x:-x[1])[:4];total=sum(w for name,w in largest)
        for name,w in largest:
            group=mapping.get(name)
            if group is None:group=sleeve.vertex_groups.new(name=name);mapping[name]=group
            group.add([v.index],w/total,'REPLACE')
    for mod in sleeve.modifiers:
        if mod.type=='ARMATURE':mod.use_deform_preserve_volume=True
    solidify(sleeve,.0016,.00035)
    # Cuff stitching follows the rest-pose wrist cross-section.
    p=start.lerp(end,.947);w=axis.cross(Vector((0,1,0))).normalized();radius=.038
    points=[tuple(p+radius*(Vector((0,1,0))*math.cos(a)+w*math.sin(a))) for a in np.linspace(0,2*math.pi,65)[:-1]]
    tube('Coat_CuffSeam_'+side,points,stitch,.00045,lower.name,True,2)

rows=np.array([(1.278,.119,.075,.002),(1.265,.143,.086,.002),(1.245,.151,.096,0),(1.205,.147,.100,-.006),(1.13,.137,.105,-.006),(1.04,.126,.085,0),(.94,.1564,.0997,0),(.83,.2016,.1210,0)])[::-1]
def cloth_y(x,z):
    rx=np.interp(z,rows[:,0],rows[:,1]);ry=np.interp(z,rows[:,0],rows[:,2]);cy=np.interp(z,rows[:,0],rows[:,3])
    if z>1.278:
        q=min(1,(z-1.278)/.03);rx=rx*(1-q)+.055*q;ry=ry*(1-q)+.053*q
    return float(cy-ry*math.sqrt(max(.02,1-(x/rx)**2)))
def lapel_y(x,z):return cloth_y(x,z)-.001-.003*math.exp(-((abs(x)-.071)/.026)**2)*math.exp(-((z-1.23)/.055)**2)
def piping(points,y_fn,depth):
    out=[]
    for (x1,z1),(x2,z2) in zip(points,points[1:]):
        for t in np.linspace(0,1,18,endpoint=False):
            x=x1+(x2-x1)*t;z=z1+(z2-z1)*t;out.append((x,y_fn(x,z)-depth,z))
    x,z=points[-1];out.append((x,y_fn(x,z)-depth,z));return out

for sign in [-1,1]:
    lapel=bpy.data.objects['Researcher_Lapel_'+str(sign)]
    bm=bmesh.new();bm.from_mesh(lapel.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True);bm.to_mesh(lapel.data);bm.free()
    for v in lapel.data.vertices:v.co.y=lapel_y(v.co.x,v.co.z)
    lapel.data.materials[0]=coatmat
    # Make both collars front-facing and hold the notched outer contour.
    bm=bmesh.new();bm.from_mesh(lapel.data);bm.normal_update()
    if sum(f.normal.y for f in bm.faces)>0:
        for f in bm.faces:f.normal_flip()
    bm.to_mesh(lapel.data);bm.free();solidify(lapel,.0024,.00055)
    for p in lapel.data.polygons:p.use_smooth=True
    for name in ['Researcher_LapelSeam_'+str(sign),'Researcher_CoatTrim_'+str(sign)]:remove(name)
    pts=[(sign*.048,1.305),(sign*.101,1.260),(sign*.085,1.221)]
    tube('Researcher_LapelSeam_'+str(sign),piping(pts,lapel_y,.0022),cyan,.00095,CHEST)
    pts=[]
    for z in np.linspace(1.12,.842,64):
        rx=np.interp(z,rows[:,0],rows[:,1]);ry=np.interp(z,rows[:,0],rows[:,2]);cy=np.interp(z,rows[:,0],rows[:,3])
        pts.append((sign*rx*math.sin(.55),cy-ry*math.cos(.55)-.0022,z))
    tube('Researcher_CoatTrim_'+str(sign),pts,cyan,.0011,CHEST)

# A sewn-on pocket with a bowed front and genuinely open upper edge.
for name in ['Researcher_Pocket','Researcher_PocketTrim','Researcher_Pen','Researcher_PenClip']:remove(name)
coat_eval=coat.evaluated_get(bpy.context.evaluated_depsgraph_get());coat_mesh=coat_eval.to_mesh()
coat_bvh=BVHTree.FromPolygons([coat.matrix_world@v.co for v in coat_mesh.vertices],[tuple(p.vertices) for p in coat_mesh.polygons]);coat_eval.to_mesh_clear()
def on_coat(x,z):
    hit=coat_bvh.ray_cast(Vector((x,-.5,z)),Vector((0,1,0)))
    if hit[0] is None:return Vector((x,cloth_y(x,z),z)),Vector((0,-1,0))
    return hit[0],hit[1]
verts=[];faces=[];normals=[];nx=10;nz=12
for j in range(nz):
    t=j/(nz-1);z=1.097+.047*t
    for i in range(nx):
        u=i/(nx-1);x=.094+.036*u
        bow=.0016+.0065*math.sin(math.pi*u)*( .4+.6*t)
        p,normal=on_coat(x,z);verts.append(tuple(p+normal*bow));normals.append(normal)
for j in range(nz-1):
    for i in range(nx-1):
        a=j*nx+i;faces.append((a,a+nx,a+nx+1,a+1))
pocket=mesh('Researcher_Pocket',verts,faces,coatmat,CHEST);solidify(pocket,.0012,.0003)
top=[tuple(Vector(verts[(nz-1)*nx+i])+normals[(nz-1)*nx+i]*.0014) for i in range(nx)]
tube('Researcher_PocketTrim',top,cyan,.00065,CHEST)
edge_ids=[j*nx+1 for j in reversed(range(1,nz-1))]+[nx+i for i in range(2,nx-1)]+[j*nx+nx-2 for j in range(2,nz-1)]
edge=[tuple(Vector(verts[i])+normals[i]*.0009) for i in edge_ids]
tube('Pocket_Topstitch',edge,stitch,.00035,CHEST)
px=.117;p1,n1=on_coat(px,1.113);p2,n2=on_coat(px,1.181);p1+=n1*.0034;p2+=n2*.0034
def pen_point(z):return p1.lerp(p2,(z-1.113)/.068)
tube('Researcher_Pen',[pen_point(1.113),pen_point(1.181)],cyan,.0017,CHEST,res=4)
tube('Researcher_PenCap',[pen_point(1.172),pen_point(1.182)],metal,.00195,CHEST,res=4)
tube('Researcher_PenClip',[pen_point(1.181)+n2*.0015,pen_point(1.179)+n2*.0023,pen_point(1.151)+n2*.0023,pen_point(1.150)+n2*.0015],metal,.00055,CHEST,res=3)

# Toon separation is intentional, with opaque skin/cloth and clear optical layers.
for m in bpy.data.objects['Face'].data.materials:
    if 'Face_00_SKIN' in m.name:
        t=m.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon
        t.shading_toony_factor=.9;t.shading_shift_factor=-.14;t.gi_equalization_factor=.65
        t.shade_color_factor=rgb('DBAD99')
        m.roughness=.9
# Continuous torso falloff lets the jacket bend with the existing hips/spine.
bone_profile=[(.94,'J_Bip_C_Hips'),(1.045,'J_Bip_C_Spine'),(1.13,'J_Bip_C_Chest'),(1.22,CHEST)]
for name in ['Researcher_Knit','Researcher_Coat','Researcher_CoatTrim_-1','Researcher_CoatTrim_1']:
    ob=bpy.data.objects[name];ob.vertex_groups.clear()
    groups={bone:ob.vertex_groups.new(name=bone) for z,bone in bone_profile}
    for v in ob.data.vertices:
        z=v.co.z
        if z<=bone_profile[0][0]:groups[bone_profile[0][1]].add([v.index],1,'REPLACE');continue
        if z>=bone_profile[-1][0]:groups[bone_profile[-1][1]].add([v.index],1,'REPLACE');continue
        for (z1,b1),(z2,b2) in zip(bone_profile,bone_profile[1:]):
            if z1<=z<=z2:
                t=(z-z1)/(z2-z1);groups[b1].add([v.index],1-t,'REPLACE');groups[b2].add([v.index],t,'REPLACE');break
new_uv([o for o in bpy.data.objects if o.type=='MESH' and o.name not in ['Face','Body'] and not o.get('detail_tier',0)])
save_phase('tailored')
save_phase('master')
render_views(ROOT/'previews/v0.2/after')
