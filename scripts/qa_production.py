from pathlib import Path
import sys,json,hashlib
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
version=args[0] if args else 'master'
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/f'models/researcher-a-{version}-v0.2.blend'));reset_pose()
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'))
import qa_check
obs=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
report=qa_check.run(objects=obs,profile='game',eps=.0002,tol=.002)
audit=json.loads((ROOT/'previews/v0.2/audit-before.json').read_text())
arm=bpy.data.objects['Armature'];before=audit['rigs']['Armature']['bones']
rig={'same_bone_names':set(before)==set(b.name for b in arm.data.bones),'same_rest_bones':all(np.allclose(before[b.name]['head'],b.head_local,atol=1e-8) and np.allclose(before[b.name]['tail'],b.tail_local,atol=1e-8) for b in arm.data.bones),'shape_keys':{},'weights_not_normalized':{},'source_unchanged':hashlib.sha256(Path(audit['source']).read_bytes()).hexdigest()==audit['source_sha256']}
for name in ['Face','Researcher_Glasses']:
    ob=bpy.data.objects[name];keys=ob.data.shape_keys.key_blocks;basis=np.array([p.co[:] for p in keys[0].data]);before_keys=audit['meshes'][name]['shape_keys']
    status={'same_names':set(before_keys)==set(k.name for k in keys),'keys':{}}
    for k in keys:
        d=np.linalg.norm(np.array([p.co[:] for p in k.data])-basis,axis=1)
        status['keys'][k.name]={'moved':int((d>1e-6).sum()),'max_delta':float(d.max()),'was_moving':before_keys[k.name]['moved_vertices']>0}
    status['active_keys_preserved']=all(v['moved']>0 for v in status['keys'].values() if v['was_moving'])
    rig['shape_keys'][name]=status
for name in obs:
    ob=bpy.data.objects[name];deform={g.index for g in ob.vertex_groups if arm.data.bones.get(g.name) and arm.data.bones[g.name].use_deform}
    count=sum(abs(sum(g.weight for g in v.groups if g.group in deform)-1)>.005 for v in ob.data.vertices)
    if count:rig['weights_not_normalized'][name]=count
rig['pass']=rig['same_bone_names'] and rig['same_rest_bones'] and rig['source_unchanged'] and not rig['weights_not_normalized'] and all(s['same_names'] and s['active_keys_preserved'] for s in rig['shape_keys'].values())
out=ROOT/'previews/v0.2';(out/f'qa-{version}.json').write_text(json.dumps(report,indent=2));(out/f'rig-{version}.json').write_text(json.dumps(rig,indent=2))
print('GEOMETRY PASS',report['pass'],'ERRORS',json.dumps(report['errors']),flush=True)
print('WARNINGS',json.dumps(report['warnings']),flush=True)
print('RIG PASS',rig['pass'],'BAD WEIGHTS',rig['weights_not_normalized'],flush=True)
