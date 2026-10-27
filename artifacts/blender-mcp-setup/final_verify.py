import asyncio,json,os
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
OUT=Path(__file__).parent
async def main():
 env=dict(os.environ,BLENDER_MCP_SAFE_MODE='1',BLENDER_HOST='127.0.0.1',BLENDER_PORT='9876',DISABLE_TELEMETRY='true')
 async with stdio_client(StdioServerParameters(command='/opt/homebrew/bin/uvx',args=['mcp-for-blender'],env=env)) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize()
   result=await s.call_tool('execute_blender_code',{'code':"import bpy, json\no=bpy.data.objects['Cube']\no.select_set(True)\nbpy.context.view_layer.objects.active=o\nprint(json.dumps({'scene':bpy.context.scene.name,'file':bpy.data.filepath,'unsaved_changes':bpy.data.is_dirty,'objects':[(o.name,o.type) for o in bpy.context.scene.objects],'mesh_vertices':len(o.data.vertices),'mesh_faces':len(o.data.polygons),'auto_start':bpy.context.scene.blendermcp_auto_start_server,'server_running':bpy.context.scene.blendermcp_server_running,'enabled_addon':'blender_mcp' in bpy.context.preferences.addons,'temporary_scene_removed':bpy.data.scenes.get('MCP_Integration_Test') is None,'temporary_objects_removed':not any(o.name.startswith('MCP_Test_') for o in bpy.data.objects)}))"})
   (OUT/'final_live_state.json').write_text(result.model_dump_json(indent=2))
   print(result.content[0].text)
asyncio.run(main())
