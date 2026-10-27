import asyncio,json,os,base64
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
    result=await c.call_tool('look',{'mode':'viewport','max_size':900,'user_prompt':'ได้ต่อ mcp ใช้งานอยู่มั้ยเนี่ย'});parts=[]
    for i,part in enumerate(result.content):
     if part.type=='image':
      path=O/f'live-viewport-{i}.png';path.write_bytes(base64.b64decode(part.data));parts.append({'image':str(path)})
     elif part.type=='text':parts.append({'text':part.text})
    (O/'look-result.json').write_text(json.dumps({'isError':result.isError,'parts':parts},indent=2));print('RESULT',json.dumps(parts))
asyncio.run(main())
