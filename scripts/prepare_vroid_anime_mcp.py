import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';p=json.loads((out/'vroid-anime-payload.json').read_text());calls=[]
setup="""import bpy
scene=bpy.data.scenes.new('Anime_Primary_Reference_V2')
bpy.context.window.scene=scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
shade=scene.display.shading
shade.light='MATCAP'
shade.studio_light='clay_studio.exr'
shade.color_type='SINGLE'
shade.show_cavity=False
shade.show_shadows=False
for ob in bpy.data.scenes['Geometry_Failure_Analysis_V2'].objects:
    if ob.type=='CAMERA':scene.collection.objects.link(ob)
print('ANIME_PRIMARY_SCENE_CREATED')
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='vroid-primary-scene'))
for pi,name in [(7,'HeadSkin'),(8,'Ears'),(1,'EyeWhite'),(5,'Iris'),(0,'MouthInterior')]:
    primitive=p['primitives'][pi];ids=primitive['indices'];used=sorted(set(ids));remap={v:i for i,v in enumerate(used)}
    coords=[[-(p['positions'][v][0]-.00025545),p['positions'][v][2],p['positions'][v][1]] for v in used]
    coords=[[round(v,7) for v in co] for co in coords];faces=[[remap[v] for v in ids[i:i+3]] for i in range(0,len(ids),3)];on='V2_Anime_'+name
    code=f"import bpy,bmesh\ncoords={coords!r}\nfaces={faces!r}\nme=bpy.data.meshes.new({on+'_Mesh'!r})\nme.from_pydata(coords,[],faces)\nme.update()\nob=bpy.data.objects.new({on!r},me)\nbpy.context.scene.collection.objects.link(ob)\nfor poly in me.polygons:poly.use_smooth=True\nob['source']='VRoid CC0 Base_Female, original shape, no body/hair imported'\nob['source_primitive']={pi}\nprint('ANIME_HEAD_PART_LINKED',ob.name,len(me.vertices),len(me.polygons))"
    calls.append(dict(tool='execute_blender_code',arguments={'code':code},label='vroid-primary-'+name))
for view in ['front','side','quarter']:
    code=f"import bpy\nscene=bpy.context.scene\nscene.camera=bpy.data.objects['REF_{view}']\nscene.render.filepath='/tmp/vtuber-anime-010-{view}.png'\nbpy.ops.render.render(write_still=True)"
    calls.extend([dict(tool='execute_blender_code',arguments={'code':code},label='render-anime-010-'+view),dict(tool='look',arguments={'image':'Render Result','max_size':900},label='anime-010-'+view)])
calls.append(dict(tool='execute_blender_code',arguments={'code':"import bpy\nbpy.ops.wm.save_as_mainfile(filepath='/tmp/vtuber-anime-head-010-source-aligned.blend',copy=True)"},label='anime-010-preserve'))
(out/'vroid-anime-request.json').write_text(json.dumps(calls));print(len(calls),'real MCP actions')
