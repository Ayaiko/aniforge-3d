"""Phase 0: non-destructive backup, complete inventory, fixed-camera before views."""
from pathlib import Path
import sys,json,hashlib,shutil
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import render_views
source=ROOT/'models/researcher-a.blend'
backup=ROOT/'models/backups/researcher-a-pre-v0.2.blend';backup.parent.mkdir(parents=True,exist_ok=True)
digest=hashlib.sha256(source.read_bytes()).hexdigest()
if backup.exists():
    if hashlib.sha256(backup.read_bytes()).hexdigest()!=digest:raise RuntimeError('Existing audit backup differs; refuse to overwrite it')
else:shutil.copy2(source,backup)
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(source))
out=ROOT/'previews/v0.2';out.mkdir(parents=True,exist_ok=True)
report={'source':str(source),'backup':str(backup),'source_sha256':digest,'blender':bpy.app.version_string,'meshes':{},'materials':{},'images':{},'rigs':{}}
dg=bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type=='ARMATURE':
        report['rigs'][ob.name]={'bone_count':len(ob.data.bones),'bones':{b.name:{'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'deform':b.use_deform} for b in ob.data.bones}}
    if ob.type!='MESH':continue
    me=ob.data;e=ob.evaluated_get(dg).to_mesh()
    stats={'vertices':len(me.vertices),'faces':len(me.polygons),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'evaluated_triangles':sum(len(p.vertices)-2 for p in e.polygons),'dimensions':list(ob.dimensions),'bounds':[list(ob.matrix_world@__import__('mathutils').Vector(c)) for c in ob.bound_box],'materials':[m.name for m in me.materials],'uv_maps':[u.name for u in me.uv_layers],'modifiers':[{'name':m.name,'type':m.type,'levels':getattr(m,'levels',None),'thickness':getattr(m,'thickness',None)} for m in ob.modifiers],'shape_keys':{},'vertex_groups':[g.name for g in ob.vertex_groups]}
    ob.evaluated_get(dg).to_mesh_clear()
    if me.shape_keys:
        base=np.array([p.co[:] for p in me.shape_keys.key_blocks[0].data])
        for key in me.shape_keys.key_blocks:
            co=np.array([p.co[:] for p in key.data]);d=np.linalg.norm(co-base,axis=1)
            stats['shape_keys'][key.name]={'vertices':len(co),'moved_vertices':int((d>1e-6).sum()),'max_delta_m':float(d.max()) if len(d) else 0,'sha256':hashlib.sha256(co.tobytes()).hexdigest()}
    report['meshes'][ob.name]=stats
for m in bpy.data.materials:
    used=sum(m==slot.material for ob in bpy.data.objects for slot in ob.material_slots)
    if not used:continue
    report['materials'][m.name]={'users_in_scene':used,'roughness':m.roughness,'metallic':m.metallic,'toon':m.vrm_addon_extension.mtoon1.enabled,'images':list({n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}) if m.node_tree else []}
for im in bpy.data.images:
    if im.type=='RENDER_RESULT':continue
    report['images'][im.name]={'size':list(im.size),'colorspace':im.colorspace_settings.name,'packed':bool(im.packed_file),'path':im.filepath}
report['limitations']=['Sparse faceted face skin; shallow eyelids and mouth','Hair clumps have uniform cross sections and blunt root caps; no secondary rear flow','Glasses lack pads, hinges and lenses','Coat and lapels are open single surfaces; pocket is a flat panel','Clothing chest is rigidly weighted; sleeve joint falloff needs stress poses']
(out/'audit-before.json').write_text(json.dumps(report,indent=2))
print('AUDIT meshes',len(report['meshes']),'tris',sum(m['triangles'] for m in report['meshes'].values()),'backup',backup,flush=True)
# Inventory boundary loops for physically attached eyelid/lip geometry.
face=bpy.data.objects['Face'];skin=next(i for i,m in enumerate(face.data.materials) if 'Face_00_SKIN' in m.name)
from collections import Counter,defaultdict
edges=Counter()
for p in face.data.polygons:
    if p.material_index==skin:
        for a,b in p.edge_keys:edges[tuple(sorted((a,b)))]+=1
graph=defaultdict(list)
for (a,b),count in edges.items():
    if count==1:graph[a].append(b);graph[b].append(a)
components=[];seen=set()
for seed in graph:
    if seed in seen:continue
    todo=[seed];component=[];seen.add(seed)
    while todo:
        i=todo.pop();component.append(i)
        for j in graph[i]:
            if j not in seen:seen.add(j);todo.append(j)
    coords=[face.matrix_world@face.data.vertices[i].co for i in component]
    components.append({'indices':component,'coordinates':[list(p) for p in coords],'bounds':[[min(p[j] for p in coords) for j in range(3)],[max(p[j] for p in coords) for j in range(3)]],'edges':[[a,b] for (a,b),count in edges.items() if count==1 and a in component and b in component]})
(out/'face-boundaries.json').write_text(json.dumps(components,indent=2))
render_views(out/'before')
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,'Source changed during audit'
