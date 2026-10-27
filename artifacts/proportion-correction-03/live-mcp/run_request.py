import asyncio,base64,json,os,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
O=Path(__file__).resolve().parent
async def main():
 request=json.loads(Path(sys.argv[1]).read_text());env=dict(os.environ,BLENDER_HOST='127.0.0.1',BLENDER_PORT='9876',BLENDER_MCP_SAFE_MODE='1',DISABLE_TELEMETRY='true')
 with (O/'server.log').open('a') as err:
  async with stdio_client(StdioServerParameters(command='/opt/homebrew/bin/uvx',args=['mcp-for-blender'],env=env),errlog=err) as (rd,wr):
   async with ClientSession(rd,wr) as c:
    await c.initialize()
    for req in request:
     result=await asyncio.wait_for(c.call_tool(req['tool'],req['arguments']),timeout=55);parts=[]
     for i,p in enumerate(result.content):
      if p.type=='image':
       path=O/(req['label']+f'-{i}.png');path.write_bytes(base64.b64decode(p.data));parts.append({'image':str(path)})
      elif p.type=='text':parts.append({'text':p.text})
     out={'tool':req['tool'],'isError':result.isError,'parts':parts};(O/(req['label']+'.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False),flush=True)
     if result.isError or any(p.get('text','').startswith(('Error executing code:','Rejected by safe mode','Error:')) for p in parts):raise RuntimeError(req['label'])
asyncio.run(main())
