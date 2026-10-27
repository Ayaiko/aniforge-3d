import asyncio, json, os
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
OUT=Path(__file__).parent
async def main():
    env=dict(os.environ,BLENDER_MCP_SAFE_MODE='1',BLENDER_HOST='127.0.0.1',BLENDER_PORT='9876',DISABLE_TELEMETRY='true')
    params=StdioServerParameters(command='/opt/homebrew/bin/uvx',args=['mcp-for-blender'],env=env)
    async with stdio_client(params) as (r,w):
        async with ClientSession(r,w) as s:
            init=await s.initialize()
            print('INIT',init.serverInfo.model_dump())
            ts=await s.list_tools()
            (OUT/'tools.json').write_text(json.dumps([t.model_dump() for t in ts.tools],indent=2))
            print('TOOLS', [t.name for t in ts.tools])
            for name,args,label in [
              ('get_scene_info',{'fields':['details','materials','modifiers','topology','settings'],'limit':100},'scene_initial'),
              ('execute_blender_code',{'code':"import bpy, json\nprint(json.dumps({'blender':bpy.app.version_string,'file':bpy.data.filepath,'dirty':bpy.data.is_dirty,'scene':bpy.context.scene.name,'addons':list(bpy.context.preferences.addons.keys()),'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'edges':len(o.data.edges),'faces':len(o.data.polygons),'materials':[m.name if m else None for m in o.data.materials],'modifiers':[{'name':m.name,'type':m.type} for m in o.modifiers]} for o in bpy.context.scene.objects if o.type=='MESH']}))"},'geometry_initial')]:
                res=await s.call_tool(name,args)
                (OUT/(label+'.json')).write_text(res.model_dump_json(indent=2))
                print(label,[(c.text if c.type=='text' else c.type) for c in res.content])
            (OUT/'init.json').write_text(init.model_dump_json(indent=2))
asyncio.run(main())
