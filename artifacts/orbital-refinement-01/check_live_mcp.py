import asyncio,json,os
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
O=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/orbital-refinement-01/live-mcp');O.mkdir(exist_ok=True)
async def main():
 env=dict(os.environ,BLENDER_HOST='127.0.0.1',BLENDER_PORT='9876',BLENDER_MCP_SAFE_MODE='1',DISABLE_TELEMETRY='true')
 with (O/'server.log').open('a') as err:
  async with stdio_client(StdioServerParameters(command='/opt/homebrew/bin/uvx',args=['mcp-for-blender'],env=env),errlog=err) as (rd,wr):
   async with ClientSession(rd,wr) as c:
    init=await c.initialize();(O/'initialize.json').write_text(init.model_dump_json(indent=2));ts=await c.list_tools();(O/'tools.json').write_text(ts.model_dump_json(indent=2))
    print('SERVER',init.serverInfo.model_dump());print('TOOLS',[t.name for t in ts.tools])
    for t in ts.tools:
     if t.name in ['get_scene_info','look']:print('SCHEMA',t.name,json.dumps(t.inputSchema))
asyncio.run(main())
