"""Extra logging in an in-memory diagnostic copy; official QA remains unchanged."""
from pathlib import Path
import sys,inspect,json,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/(args[0] if args else 'models/researcher-a-reconstruction-06-surface-v0.3.blend')))
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'));import qa_check
source=inspect.getsource(qa_check.run)
source=source.replace('    zf = _describe(zf_pairs)', '''    records=[]
    for ii,jj in zf_pairs:
        names=[obs[tri_meta[k][0]].name for k in [ii,jj]]
        records.append({'names':names,'centres':[[sum(verts[v][axis] for v in tris[k])/3 for axis in range(3)] for k in [ii,jj]]})
    Path(OUTPUT).write_text(json.dumps(records,indent=2))
    zf = _describe(zf_pairs)''')
namespace=dict(qa_check.__dict__);namespace.update(Path=Path,json=json,OUTPUT=str(ROOT/'previews/v0.3'/(args[1] if len(args)>1 else 'validation')/'contact-locations.json'));exec(source,namespace)
report=namespace['run'](objects=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render],profile='game',eps=.0002,tol=.002)
records=json.loads(Path(namespace['OUTPUT']).read_text());groups={}
for r in records:
    key=' / '.join(sorted(r['names']));groups.setdefault(key,[]).extend(r['centres'])
for key,pts in groups.items():print(key,'range',[[round(min(p[a] for p in pts),5),round(max(p[a] for p in pts),5)] for a in range(3)],flush=True)
