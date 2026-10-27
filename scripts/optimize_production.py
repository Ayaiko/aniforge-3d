"""Export copy only: resample hair, bake compatible shapes, preserve the master."""
from pathlib import Path
import sys,json,math,hashlib
import bpy,bmesh,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from production_common import *
from character_studio import reset_pose
enable_vrm();master=ROOT/'models/researcher-a-master-v0.2.blend';master_hash=hashlib.sha256(master.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(master));reset_pose()
for ob in list(bpy.data.objects):
    if ob.name.startswith('Guide_'):bpy.data.objects.remove(ob,do_unlink=True)
for ob in bpy.data.objects:
    if ob.type=='MESH':
        for mod in ob.modifiers:
            if mod.type=='ARMATURE':mod.use_deform_preserve_volume=False
# The master uses volume-preserving skinning. VRM uses linear skinning, so add
# a small elbow ease allowance to keep the sleeve outside the inherited arm.
arm=bpy.data.objects['Armature']
for side in ['L','R']:
    ob=bpy.data.objects['Researcher_CoatSleeve_'+side]
    start=arm.data.bones['J_Bip_'+side+'_UpperArm'].head_local;elbow=arm.data.bones['J_Bip_'+side+'_LowerArm'].head_local;end=arm.data.bones['J_Bip_'+side+'_LowerArm'].tail_local
    axis=(end-start).normalized();joint=(elbow-start).dot(axis)
    for v in ob.data.vertices:
        delta=v.co-start;along=delta.dot(axis);radial=delta-axis*along
        if radial.length:v.co+=radial.normalized()*(.008*math.exp(-((along-joint)/.044)**2))
# Cull only the occluded outer-elbow skin patch in the clothed realtime copy.
# The inner strip stays connected; the complete body remains in the master.
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);hidden=[]
for side in ['L','R']:
    start=arm.data.bones['J_Bip_'+side+'_UpperArm'].head_local;elbow=arm.data.bones['J_Bip_'+side+'_LowerArm'].head_local;end=arm.data.bones['J_Bip_'+side+'_LowerArm'].tail_local
    axis=(end-start).normalized();joint=(elbow-start).dot(axis)
    for f in bm.faces:
        p=body.matrix_world@f.calc_center_median();delta=p-start;along=delta.dot(axis);radial=delta-axis*along
        if abs(along-joint)<.08 and radial.length<.06 and radial.y>-.010:hidden.append(f)
bmesh.ops.delete(bm,geom=list(set(hidden)),context='FACES');bm.to_mesh(body.data);bm.free()

# VRM 0 has no matcap multiplier; disconnect a disabled inherited matcap rather
# than exporting its texture and accidentally restoring the old glossy rim.
for material in bpy.data.materials:
    g=material.vrm_addon_extension.mtoon1
    if g.enabled:
        m=g.extensions.vrmc_materials_mtoon
        if max(m.matcap_factor)<1e-6:m.matcap_texture.index.source=None
# Hair samples carry the original authored silhouette/flow, at a lower density.
for ob in list(bpy.data.objects):
    tier=ob.get('detail_tier',0)
    if ob.type!='MESH' or not tier:continue
    rows=int(ob['rows']);cols=int(ob['cols']);nr=34 if tier==1 else 26 if tier==2 else 20;nc=10 if tier==1 else 8
    a=np.array([v.co[:] for v in ob.data.vertices]).reshape(rows,cols,3)
    ri=np.round(np.linspace(0,rows-1,nr)).astype(int)
    vertices=[];faces=[]
    for r in ri:
        for k in range(nc):
            t=k*cols/nc;i=int(t);fraction=t-i
            p=a[r,i%cols]*(1-fraction)+a[r,(i+1)%cols]*fraction
            if ob.name=='Hair_Secondary_LeftSweep':p[1]-=.0035*math.sin(math.pi*(len(vertices)//nc)/max(1,nr-1))
            vertices.append(tuple(p))
    for j in range(nr-1):
        for k in range(nc):
            aa=j*nc+k;bb=j*nc+(k+1)%nc;faces.append((aa,bb,bb+nc,aa+nc))
    faces.extend([tuple(reversed(range(nc))),tuple((nr-1)*nc+k for k in range(nc))])
    data=bpy.data.meshes.new(ob.name+'_Realtime');data.from_pydata(vertices,[],faces);data.update()
    for m in ob.data.materials:data.materials.append(m)
    ob.data=data;ob.vertex_groups.clear();g=ob.vertex_groups.new(name=HEAD);g.add(list(range(len(vertices))),1,'REPLACE')
    uv=data.uv_layers.new(name='Hair flow')
    for p in data.polygons:
        wrap=any(i%nc==0 for i in p.vertices) and any(i%nc==nc-1 for i in p.vertices)
        for li in p.loop_indices:
            idx=data.loops[li].vertex_index;u=idx%nc/nc
            if wrap and u==0:u=1
            uv.data[li].uv=(u,idx//nc/(nr-1))
            if len(p.vertices)==nc:
                angle=2*math.pi*(idx%nc)/nc;uv.data[li].uv=(.75+.1*math.cos(angle),.86+.07*math.sin(angle))
    recalc(ob)
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(data);bm.free()
    for p in data.polygons:p.use_smooth=True

# Toon-compatible transparent optical layers for realtime VRM.
for name in ['Production / Optical lenses','Production / Corneal optical coat']:
    old=bpy.data.materials.get(name)
    if not old:continue
    replacement=toon(name+' realtime','EAF5FF','EAF5FF',0);g=replacement.vrm_addon_extension.mtoon1;g.alpha_mode='BLEND';g.pbr_metallic_roughness.base_color_factor=(*rgb('EAF5FF'),.015)
    replacement.surface_render_method='BLENDED'
    for ob in bpy.data.objects:
        if ob.type=='MESH':
            for slot in ob.material_slots:
                if slot.material==old:slot.material=replacement

for name in ['Researcher_Glasses','Researcher_Knit','Researcher_Coat']:
    ob=bpy.data.objects[name]
    for mod in list(ob.modifiers):
        if mod.type=='BEVEL' or (name in ['Researcher_Knit','Researcher_Coat'] and mod.type=='SUBSURF'):ob.modifiers.remove(mod)
cap=bpy.data.objects['Researcher_BobCap'];mod=cap.modifiers.new('Covered scalp simplification','DECIMATE');mod.ratio=.65

def bake_shapes(ob):
    # Evaluate identical topology once per expression. No voxel remesh or key loss.
    names=[k.name for k in ob.data.shape_keys.key_blocks]
    original=[k for k in ob.data.shape_keys.key_blocks]
    for m in list(ob.modifiers):
        if m.type=='NODES' and m.name.startswith('MToon Outline'):ob.modifiers.remove(m)
    dg=bpy.context.evaluated_depsgraph_get();coords=[];basis_mesh=None;signature=None
    for index,k in enumerate(original):
        for other in original:other.value=0
        if index:k.value=1
        bpy.context.view_layer.update();evaluated=ob.evaluated_get(dg);me=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=dg)
        sig=(len(me.vertices),tuple(tuple(p.vertices) for p in me.polygons))
        if signature is None:signature=sig
        elif sig!=signature:raise RuntimeError('Modifier changed topology across morphs: '+ob.name)
        a=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',a);coords.append(a)
        if index==0:basis_mesh=me.copy()
        evaluated.to_mesh_clear()
    for k in original:k.value=0
    ob.shape_key_clear();ob.data=basis_mesh
    if ob.data.shape_keys:ob.shape_key_clear()
    for name,a in zip(names,coords):ob.shape_key_add(name=name).data.foreach_set('co',a)
    for m in list(ob.modifiers):
        if m.type!='ARMATURE':ob.modifiers.remove(m)
    print('Baked morph geometry',ob.name,len(names),'shapes',len(basis_mesh.vertices),'verts',flush=True)

for ob in list(bpy.data.objects):
    if ob.type!='MESH':continue
    if ob.data.shape_keys:bake_shapes(ob)
    else:
        for mod_name in [m.name for m in ob.modifiers if m.type not in ['ARMATURE','NODES']]:apply(ob,ob.modifiers[mod_name])
new_uv([bpy.data.objects[name] for name in ['Researcher_Coat','Researcher_Knit','Researcher_CoatSleeve_L','Researcher_CoatSleeve_R','Researcher_Lapel_-1','Researcher_Lapel_1','Researcher_Pocket']])
meta=bpy.data.objects['Armature'].data.vrm_addon_extension.vrm0.meta;meta.title='Researcher A — Realtime 0.2';meta.version='0.2.0'
save_phase('realtime')
result=bpy.ops.export_scene.vrm(filepath=str(ROOT/'models/researcher-a-realtime-v0.2.vrm'),armature_object_name='Armature')
if result!={'FINISHED'}:raise RuntimeError('VRM export did not finish')
assert hashlib.sha256(master.read_bytes()).hexdigest()==master_hash,'Master was overwritten during optimization'
print('Master unchanged; realtime VRM exported',flush=True)
