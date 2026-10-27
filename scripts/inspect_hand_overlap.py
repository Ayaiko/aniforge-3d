import bpy,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'models/researcher-a.blend'))
ob=bpy.data.objects['Body']
for idx in [3648,4413,4134,4372,4799,5562,5286,5521]:
    p=ob.data.polygons[idx]
    print('POLYGON',idx)
    for i in p.vertices:
        v=ob.data.vertices[i]
        print(i,tuple(round(x,6) for x in ob.matrix_world@v.co),[(ob.vertex_groups[g.group].name,round(g.weight,3)) for g in v.groups if g.weight>.01])
