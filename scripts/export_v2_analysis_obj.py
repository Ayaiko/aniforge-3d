"""Read-only export of the frozen V2 trial for permitted native MCP import."""
from pathlib import Path
import bpy,json,hashlib
root=Path('/Users/graind/Documents/ChatGPT/vTuber');source=root/'models/reconstruction-v2/researcher-a-head-002.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
for ob in bpy.context.scene.objects:ob.select_set(ob.type=='MESH')
op=bpy.ops.wm.obj_export.get_rna_type();assert 'NEGATIVE_Z' in [i.identifier for i in op.properties['forward_axis'].enum_items]
destination=root/'artifacts/reconstruction-v2-mcp/head-002-analysis.obj'
bpy.ops.wm.obj_export(filepath=str(destination),export_selected_objects=True,export_uv=False,export_normals=True,export_materials=True,forward_axis='NEGATIVE_Z',up_axis='Y')
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(root/'artifacts/reconstruction-v2-mcp/analysis-source.json').write_text(json.dumps({'source':str(source),'sha256':digest,'obj':str(destination),'meshes':{o.name:{'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)} for o in bpy.context.scene.objects if o.type=='MESH'},'source_unchanged':True},indent=2))
print('READ ONLY OBJ',destination,flush=True)
