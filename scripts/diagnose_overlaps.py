"""Locate the exact faces reported by the unmodified QA check."""
import bpy,bmesh,json,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/(args[0] if args else 'models/researcher-a.blend')))
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'))
from qa_check import _point_in_tri
records=[]
for name in (args[1:] or ['Body','Face']):
    ob=bpy.data.objects[name];bm=bmesh.new();bm.from_object(ob,bpy.context.evaluated_depsgraph_get());bm.transform(ob.matrix_world)
    layer=bm.faces.layers.int.new('source_face')
    for i,f in enumerate(bm.faces):f[layer]=i
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update();bm.faces.ensure_lookup_table()
    verts=[v.co.copy() for v in bm.verts];tris=[tuple(v.index for v in f.verts) for f in bm.faces]
    normals=[f.normal.copy() for f in bm.faces];bvh=BVHTree.FromPolygons(verts,tris,epsilon=0)
    pairs=set()
    for ti,t in enumerate(tris):
        a,b,c=[verts[i] for i in t];n=normals[ti];cen=(a+b+c)/3
        for p in [cen,cen.lerp(a,.6),cen.lerp(b,.6),cen.lerp(c,.6)]:
            for _,_,tj,_ in bvh.find_nearest_range(p,.0002):
                if ti==tj or set(t)&set(tris[tj]):continue
                n2=normals[tj]
                if abs(n.dot(n2))<.999:continue
                a2,b2,c2=[verts[i] for i in tris[tj]]
                q=p-n2*n2.dot(p-a2)
                if _point_in_tri(q,a2,b2,c2,n2):pairs.add((min(ti,tj),max(ti,tj)))
    for i,j in pairs:
        f1,f2=bm.faces[i],bm.faces[j]
        record={'object':name,'kind':'same' if normals[i].dot(normals[j])>0 else 'back','polygons':[f1[layer],f2[layer]],'materials':[ob.data.materials[f.material_index].name for f in [f1,f2]],'centers':[list(f.calc_center_median()) for f in [f1,f2]],'vertices':[[list(v.co) for v in f.verts] for f in [f1,f2]],'normal_dot':normals[i].dot(normals[j])}
        records.append(record)
    bm.free()
(ROOT/'previews/overlap-locations.json').write_text(json.dumps(records,indent=2))
for r in records:print(r['object'],r['kind'],r['polygons'],r['materials'],r['centers'])
