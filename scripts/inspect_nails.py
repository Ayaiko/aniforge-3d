from pathlib import Path
import sys,json
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/backups/researcher-a-pre-v0.2.blend'))
ob=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table();bm.verts.index_update();seen=set();islands=[]
for seed in bm.verts:
    if seed.index in seen:continue
    todo=[seed];component=[];seen.add(seed.index)
    while todo:
        v=todo.pop();component.append(v.index)
        for e in v.link_edges:
            j=e.other_vert(v).index
            if j not in seen:seen.add(j);todo.append(bm.verts[j])
    if len(component)==18:islands.append(component)
exclude={i for c in islands for i in c};coords=[ob.matrix_world@v.co for v in ob.data.vertices]
surface=BVHTree.FromPolygons(coords,[tuple(p.vertices) for p in ob.data.polygons if not any(i in exclude for i in p.vertices)])
records=[]
for component in islands:
    record=[]
    for i in component:
        p,n,index,d=surface.find_nearest(coords[i]);normal=(ob.matrix_world.to_3x3()@ob.data.vertices[i].normal).normalized()
        record.append({'index':i,'dot':normal.dot(n),'normal':list(normal),'co':list(coords[i])})
    print(component[0],[round(v['dot'],3) for v in record]);records.append(record)
(ROOT/'previews/v0.2/nail-source.json').write_text(json.dumps(records,indent=2))
