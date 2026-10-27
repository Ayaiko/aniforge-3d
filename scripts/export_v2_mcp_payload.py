"""Read-only extraction of the new V2 trial for the safe live MCP session."""
from pathlib import Path
import bpy,json
root=Path('/Users/graind/Documents/ChatGPT/vTuber');out=root/'artifacts/reconstruction-v2-mcp'
bpy.ops.wm.open_mainfile(filepath=str(root/'models/reconstruction-v2/researcher-a-head-002.blend'))
objects=[]
for ob in bpy.context.scene.objects:
    entry={'name':ob.name,'type':ob.type,'matrix':[list(r) for r in ob.matrix_world]}
    if ob.type=='MESH':
        entry.update(vertices=[[round(c,7) for c in v.co] for v in ob.data.vertices],faces=[list(p.vertices) for p in ob.data.polygons],materials=[m.name for m in ob.data.materials],properties={'feature_loops':ob.get('feature_loops','')})
    elif ob.type=='CAMERA':entry.update(ortho_scale=ob.data.ortho_scale)
    elif ob.type=='LIGHT':entry.update(energy=ob.data.energy,size=ob.data.size)
    objects.append(entry)
materials={}
for m in bpy.data.materials:
    if m.users:
        node=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
        if node:materials[m.name]={'color':list(node.inputs['Base Color'].default_value),'roughness':node.inputs['Roughness'].default_value}
(out/'head-002-payload.json').write_text(json.dumps({'objects':objects,'materials':materials},separators=(',',':')))
print('READ ONLY PAYLOAD',len(objects),flush=True)
