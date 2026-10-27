"""Diagnostic logging only. Official validation still calls qa_check unchanged."""
from pathlib import Path
import sys,inspect
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-master-v0.2.blend'))
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'))
import qa_check
source=inspect.getsource(qa_check.run)
source=source.replace('    zf = _describe(zf_pairs)', '''    for ii,jj in zf_pairs:
        names=[obs[tri_meta[k][0]].name for k in [ii,jj]]
        if 'Body' in names:
            print('CONTACT',names,[[round(sum(verts[v][axis] for v in tris[k])/3,6) for axis in range(3)] for k in [ii,jj]],flush=True)
    zf = _describe(zf_pairs)''')
namespace=dict(qa_check.__dict__);exec(source,namespace)
namespace['run'](objects=[o.name for o in bpy.data.objects if o.type=='MESH'],profile='game',eps=.0002,tol=.002,uv=False)
