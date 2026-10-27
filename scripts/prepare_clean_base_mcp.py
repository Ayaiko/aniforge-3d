"""Import trusted raw CC0 quad cage into separate live MCP scene, no subdivision."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp'
source=json.loads((out/'cc0-stylized-head-payload.json').read_text())
head=source[0];origin=[head['matrix'][i][3] for i in range(3)]
calls=[]
setup="""import bpy
scene=bpy.data.scenes.new('Clean_Head_Base_V2')
bpy.context.window.scene=scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
shade=scene.display.shading
shade.light='MATCAP'
shade.studio_light='clay_studio.exr'
shade.color_type='SINGLE'
shade.show_cavity=False
shade.show_shadows=False
shade.background_type='VIEWPORT'
shade.background_color=(0.12,0.13,0.15)
for ob in bpy.data.scenes['Geometry_Failure_Analysis_V2'].objects:
    if ob.type in {'CAMERA','LIGHT'}:scene.collection.objects.link(ob)
print('CLEAN_CC0_BASE_SCENE_CREATED')
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='clean-base-create'))
for spec in source:
    name=spec['name'].replace('GEO-head_stylized','V2_Clean_Head');dn=name+'_Mesh'
    offsets=[spec['matrix'][i][3]-origin[i] for i in range(3)]
    coords=[]
    for co in spec['vertices']:
        x,y,z=[co[i]+offsets[i] for i in range(3)]
        coords.append([round(x*.9,7),round(y*.65-.007,7),round(1.446197748+(z-.1726)*.7,7)])
    calls.append(dict(tool='execute_blender_code',arguments={'code':f"import bpy\ndata=bpy.data.meshes.new({dn!r})\ndata.vertices.add({len(coords)})"},label=name+'-allocate'))
    for first in range(0,len(coords),1200):
        code=f"import bpy\ndata=bpy.data.meshes[{dn!r}]\ncoordinates={coords[first:first+1200]!r}\nfor i,co in enumerate(coordinates,{first}):data.vertices[i].co=co\nprint('CC0_POINTS',{first})"
        calls.append(dict(tool='execute_blender_code',arguments={'code':code},label=name+'-points-'+str(first)))
    for first in range(0,len(spec['faces']),1000):
        code=f"import bpy,bmesh\ndata=bpy.data.meshes[{dn!r}]\nbm=bmesh.new()\nbm.from_mesh(data)\nbm.verts.ensure_lookup_table()\nfaces={spec['faces'][first:first+1000]!r}\nfor face in faces:bm.faces.new([bm.verts[i] for i in face])\nbm.to_mesh(data)\nbm.free()"
        calls.append(dict(tool='execute_blender_code',arguments={'code':code},label=name+'-faces-'+str(first)))
    code=f"import bpy\ndata=bpy.data.meshes[{dn!r}]\ndata.update()\nob=bpy.data.objects.new({name!r},data)\nbpy.context.scene.collection.objects.link(ob)\nfor p in data.polygons:p.use_smooth=True\nob['source']='Blender Human Base Meshes v1.4.1, CC0, raw quad cage'\nprint('CC0_CAGE_LINKED',ob.name)"
    calls.append(dict(tool='execute_blender_code',arguments={'code':code},label=name+'-link'))
for view in ['front','side','quarter']:
    code=f"import bpy\nscene=bpy.context.scene\nscene.camera=bpy.data.objects['REF_{view}']\nscene.render.filepath='/tmp/vtuber-clean-base-initial-{view}.png'\nbpy.ops.render.render(write_still=True)"
    calls.append(dict(tool='execute_blender_code',arguments={'code':code},label='clean-initial-render-'+view))
    calls.append(dict(tool='look',arguments={'image':'Render Result','max_size':900},label='clean-initial-'+view))
calls.append(dict(tool='execute_blender_code',arguments={'code':"import bpy\nbpy.ops.wm.save_as_mainfile(filepath='/tmp/vtuber-clean-head-base-003.blend',copy=True)\nprint('CLEAN_BASE_SAVED_SEPARATELY')"},label='clean-base-save'))
assert all(len(c['arguments'].get('code','').encode())<180000 for c in calls)
(out/'clean-base-request.json').write_text(json.dumps(calls));print(len(calls),'MCP actions')
