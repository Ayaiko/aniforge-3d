import asyncio, base64, json, os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
OUT=Path(__file__).parent
SNAPSHOT="""import bpy, json
s=bpy.data.scenes['Scene']
def object_name(o):
    return o.name
print(json.dumps({'scene':s.name,'objects':[{'name':o.name,'type':o.type,'matrix':[list(r) for r in o.matrix_world],'mesh':{'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]} if o.type=='MESH' else None,'materials':[m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[(m.name,m.type) for m in o.modifiers]} for o in sorted(s.objects,key=object_name)],'camera':s.camera.name,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'frame':s.frame_current,'active_scene':bpy.context.window.scene.name,'active':bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,'selected':[o.name for o in bpy.context.selected_objects]}))
"""
CREATE="""import bpy, json
s=bpy.data.scenes.new('MCP_Integration_Test')
o=bpy.data.objects['Cube'].copy()
o.data=o.data.copy()
o.name='MCP_Test_Mesh'
o.data.name='MCP_Test_MeshData'
s.collection.objects.link(o)
o.data.vertices[0].co.x -= 0.2
o.data.update()
m=bpy.data.materials.new('MCP_Test_Material')
m.diffuse_color=(0.08,0.35,0.65,1)
o.data.materials.clear()
o.data.materials.append(m)
mod=o.modifiers.new('MCP_Test_Bevel','BEVEL')
mod.width=0.06
mod.segments=2
for name in ['Camera','Light']:
    source=bpy.data.objects[name]
    ob=source.copy()
    ob.data=source.data.copy()
    ob.name='MCP_Test_'+name
    s.collection.objects.link(ob)
    if ob.type=='CAMERA': s.camera=ob
s.world=bpy.data.worlds.new('MCP_Test_World')
s.world.color=(0.12,0.12,0.12)
s.render.engine='BLENDER_EEVEE'
s.render.resolution_x=384
s.render.resolution_y=384
s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
bpy.context.window.scene=s
bpy.context.view_layer.objects.active=o
o.select_set(True)
print(json.dumps({'test_scene':s.name,'mesh':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'modified_vertex':list(o.data.vertices[0].co),'material':m.name,'modifier':mod.type}))
"""
CLEANUP="""import bpy, json
bpy.context.window.scene=bpy.data.scenes['Scene']
s=bpy.data.scenes.get('MCP_Integration_Test')
if s:
    obs=list(s.objects)
    bpy.data.scenes.remove(s)
    for o in obs:
        if o.name.startswith('MCP_Test_'): bpy.data.objects.remove(o,do_unlink=True)
for group in [bpy.data.meshes,bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.worlds]:
    for d in list(group):
        if d.name.startswith('MCP_Test_') and d.users==0: group.remove(d)
print(json.dumps({'restored_scene':bpy.context.scene.name,'test_scene_remaining':bpy.data.scenes.get('MCP_Integration_Test') is not None}))
"""
async def main():
 env=dict(os.environ,BLENDER_MCP_SAFE_MODE='1',BLENDER_HOST='127.0.0.1',BLENDER_PORT='9876',DISABLE_TELEMETRY='true')
 async with stdio_client(StdioServerParameters(command='/opt/homebrew/bin/uvx',args=['mcp-for-blender'],env=env)) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize()
   async def call(name,args,label):
    res=await s.call_tool(name,args)
    parts=[]
    for n,c in enumerate(res.content):
     if c.type=='image':
      p=OUT/f'{label}-{n}.png'; p.write_bytes(base64.b64decode(c.data)); parts.append({'image':str(p)})
     elif c.type=='text': parts.append({'text':c.text})
    (OUT/f'{label}.json').write_text(json.dumps({'isError':res.isError,'content':parts},indent=2))
    print(label,json.dumps(parts),flush=True)
    if label != 'safe_mode_negative' and (res.isError or any('Code execution blocked' in p.get('text','') or p.get('text','').startswith(('Error','Rejected by safe mode')) for p in parts)): raise RuntimeError(label)
    return parts
   await call('disable_telemetry',{},'telemetry_disabled')
   await call('get_addon_status',{},'addon_status')
   before=await call('execute_blender_code',{'code':SNAPSHOT},'original_before')
   await call('look',{'mode':'viewport','max_size':800},'viewport_original')
   await call('look',{'mode':'angles','target':['Cube'],'views':['front','right','top','three_quarter'],'shading':'solid','max_size':900},'angles_original')
   try:
    await call('execute_blender_code',{'code':CREATE},'create_edit_test_scene')
    await call('get_scene_info',{'fields':['details','materials','modifiers','topology','settings']},'test_scene_info')
    await call('look',{'mode':'angles','target':['MCP_Test_Mesh'],'shading':'solid','max_size':900},'test_angles_solid')
    await call('look',{'mode':'angles','target':['MCP_Test_Mesh'],'shading':'wireframe','max_size':900},'test_angles_wireframe')
    render="import bpy\nbpy.context.scene.render.filepath="+repr(str(OUT/'test-render.png'))+"\nbpy.ops.render.render(write_still=True)\nprint('RENDER_PASS', bpy.context.scene.render.filepath)\nbpy.ops.wm.save_as_mainfile(filepath="+repr(str(OUT/'integration-test-copy.blend'))+",copy=True)"
    await call('execute_blender_code',{'code':render},'render_test')
    await call('look',{'image':'Render Result','max_size':600},'render_result')
    await call('execute_blender_code',{'code':'import os\nprint(os.getcwd())'},'safe_mode_negative')
   finally:
    await call('execute_blender_code',{'code':CLEANUP},'cleanup')
    after=await call('execute_blender_code',{'code':SNAPSHOT},'original_after')
    equal=before==after
    (OUT/'original_unchanged.json').write_text(json.dumps({'unchanged':equal},indent=2))
    print('ORIGINAL_UNCHANGED',equal,flush=True)
asyncio.run(main())
