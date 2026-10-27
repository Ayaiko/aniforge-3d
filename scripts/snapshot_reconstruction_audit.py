from pathlib import Path
import sys,json,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose
from production_common import stats
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-master-v0.2.blend'));reset_pose()
report={'source':str(ROOT/'models/researcher-a-master-v0.2.blend'),'evaluated_statistics':stats(),'meshes':{},'materials':{},'rigs':{}}
for ob in bpy.data.objects:
    if ob.type=='MESH' and not ob.hide_render:
        report['meshes'][ob.name]={'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'base_triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),'uv_maps':[u.name for u in ob.data.uv_layers],'materials':[m.name for m in ob.data.materials],'modifiers':[{'name':m.name,'type':m.type,'levels':getattr(m,'levels',None),'render_levels':getattr(m,'render_levels',None)} for m in ob.modifiers],'shape_keys':[k.name for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'weight_max_influences':max((len(v.groups) for v in ob.data.vertices),default=0),'unweighted_vertices':sum(not v.groups for v in ob.data.vertices),'object_custom_properties':{k:str(ob[k])[:800] for k in ob.keys()}}
    if ob.type=='ARMATURE':report['rigs'][ob.name]={'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in ob.data.bones}}
for mat in bpy.data.materials:
    if not mat.users:continue
    images={n.image.name:n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image} if mat.node_tree else {}
    report['materials'][mat.name]={'mtoon':mat.vrm_addon_extension.mtoon1.enabled,'nodes':[n.type for n in mat.node_tree.nodes] if mat.node_tree else [],'images':[{'name':n,'size':list(i.size),'packed':bool(i.packed_file)} for n,i in images.items()]}
(ROOT/'previews/v0.3/audit-baseline-detailed.json').write_text(json.dumps(report,indent=2));print('BASELINE AUDIT',len(report['meshes']),flush=True)
