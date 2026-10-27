"""Local MCP stdio client for the installed Blender server. Keeps safe mode on.
Usage: uv run --offline --with mcp python scripts/blender_mcp_client.py request.json
The request is a list of {tool, arguments, label}. Images are saved, never dumped.
"""
import asyncio,base64,json,os,sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/reconstruction-v2-mcp';OUT.mkdir(exist_ok=True)
async def main():
    request=json.loads(Path(sys.argv[1]).read_text());env=dict(os.environ,BLENDER_HOST='127.0.0.1',BLENDER_PORT='9876',BLENDER_MCP_SAFE_MODE='1',DISABLE_TELEMETRY='true')
    debug=(OUT/'server-debug.log').open('a')
    async with stdio_client(StdioServerParameters(command='/opt/homebrew/bin/uvx',args=['mcp-for-blender'],env=env),errlog=debug) as (reader,writer):
        async with ClientSession(reader,writer) as session:
            init=await session.initialize();(OUT/'initialize.json').write_text(init.model_dump_json(indent=2))
            for call in request:
                args=call.get('arguments',{});prompt_file=OUT/'active-user-prompt.txt';args.setdefault('user_prompt',prompt_file.read_text() if prompt_file.exists() else 'ไปทำต่อใน mcp')
                result=await session.call_tool(call['tool'],args);parts=[]
                for i,part in enumerate(result.content):
                    if part.type=='image':
                        path=OUT/(call['label']+'-'+str(i)+'.png');path.write_bytes(base64.b64decode(part.data));parts.append({'image':str(path)})
                    elif part.type=='text':parts.append({'text':part.text})
                output={'tool':call['tool'],'isError':result.isError,'content':parts};(OUT/(call['label']+'.json')).write_text(json.dumps(output,indent=2))
                print(call['label'],json.dumps(output)[:12000],flush=True)
                if result.isError or any(p.get('text','').startswith(('Error','Rejected by safe mode')) for p in parts):raise RuntimeError(call['label'])
asyncio.run(main())
