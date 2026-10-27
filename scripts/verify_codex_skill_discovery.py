"""Read Codex's own skill discovery API; no agent turns, messages or mutations."""
import subprocess,json,select,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/skills-workflow-upgrade'
error=(out/'codex-discovery-stderr.log').open('w')
process=subprocess.Popen(['codex','app-server','--stdio','-c','analytics.enabled=false'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error,text=True,bufsize=1,cwd=root)
def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
def response(identifier):
    until=time.monotonic()+45
    while time.monotonic()<until:
        ready,_,_=select.select([process.stdout],[],[],min(1,until-time.monotonic()))
        if not ready:continue
        line=process.stdout.readline()
        if not line:raise RuntimeError('Codex app-server exited')
        value=json.loads(line)
        if value.get('id')==identifier:return value
    raise TimeoutError('Read-only skill discovery timed out')
try:
    send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'vtuber_skill_verifier','version':'1.0'},'capabilities':{}}})
    initialized=response(1)
    if 'error' in initialized:raise RuntimeError(initialized['error'])
    send({'method':'initialized'})
    send({'id':2,'method':'skills/list','params':{'cwds':[str(root)],'forceReload':True}})
    result=response(2)
    (out/'codex-skills-list.json').write_text(json.dumps(result,indent=2))
    if 'error' in result:raise RuntimeError(result['error'])
    wanted={'reference-to-3d','orthographic-registration','reference-analysis-validator','scenario-blender-expert','scenario-blender-sculpting'}
    found=[]
    def walk(value):
        if isinstance(value,dict):
            if value.get('name') in wanted:found.append({k:v for k,v in value.items() if k in ['name','path','scope','enabled','isEnabled']})
            for v in value.values():walk(v)
        elif isinstance(value,list):
            for v in value:walk(v)
    walk(result)
    print(json.dumps({'discovered':found,'count':len(found)},indent=2))
    assert {v['name'] for v in found}==wanted,'Codex did not discover all requested skills'
finally:
    process.terminate()
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:process.kill();process.wait()
    error.close()
