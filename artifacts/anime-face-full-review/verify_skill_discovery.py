import subprocess,json,select,time
from pathlib import Path
ROOT=Path('/Users/graind/Documents/ChatGPT/vTuber');OUT=ROOT/'artifacts/anime-face-full-review'
err=(OUT/'skill-discovery-stderr.log').open('w')
p=subprocess.Popen(['codex','app-server','--stdio','-c','analytics.enabled=false'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1,cwd=ROOT)
def send(x):p.stdin.write(json.dumps(x)+'\n');p.stdin.flush()
def get(i):
 until=time.monotonic()+45
 while time.monotonic()<until:
  if not select.select([p.stdout],[],[],1)[0]:continue
  line=p.stdout.readline()
  if not line:raise RuntimeError('app-server exited')
  d=json.loads(line)
  if d.get('id')==i:return d
 raise TimeoutError(i)
try:
 send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'anime_skill_verifier','version':'1.0'},'capabilities':{}}});a=get(1);assert 'error' not in a,a
 send({'method':'initialized'});send({'id':2,'method':'skills/list','params':{'cwds':[str(ROOT)],'forceReload':True}});d=get(2);assert 'error' not in d,d
 wanted={'anime-face-topology','anime-face-sculpting','anime-eye-modeling','blender-tutorial-to-practice'};found=[]
 def walk(x):
  if isinstance(x,dict):
   if x.get('name') in wanted:found.append({k:v for k,v in x.items() if k in ['name','path','scope','enabled','isEnabled']})
   for v in x.values():walk(v)
  elif isinstance(x,list):
   for v in x:walk(v)
 walk(d);assert {x['name'] for x in found}==wanted
 (OUT/'skill-discovery.json').write_text(json.dumps({'discovered':found,'pass':True},indent=2));print(json.dumps(found))
finally:
 p.terminate()
 try:p.wait(timeout=5)
 except subprocess.TimeoutExpired:p.kill();p.wait()
 err.close()
