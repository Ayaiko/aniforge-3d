from pathlib import Path
import sys,json,hashlib,os
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import stats
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/(args[0] if args else 'models/researcher-a-reconstruction-06-surface-v0.3.blend')));reset_pose()
out=ROOT/os.environ.get('RECONSTRUCTION_PREVIEW_DIR','previews/v0.3')/(args[1] if len(args)>1 else 'validation');out.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'))
import qa_check,review_shots
obs=[o.name for o in bpy.data.objects if o.type=='MESH' and not o.hide_render]
qa=qa_check.run(objects=obs,profile='game',eps=.0002,tol=.002)
(out/'geometry-qa.json').write_text(json.dumps(qa,indent=2));print('QA',qa['pass'],'ERRORS',json.dumps(qa['errors']),flush=True)
audit=json.loads((ROOT/'previews/v0.2/audit-before.json').read_text());arm=bpy.data.objects['Armature'];before=audit['rigs']['Armature']['bones']
rig={'same_bone_names':set(before)==set(b.name for b in arm.data.bones),'same_rest_bones':all(np.allclose(before[b.name]['head'],b.head_local,atol=1e-8) and np.allclose(before[b.name]['tail'],b.tail_local,atol=1e-8) for b in arm.data.bones),'shape_keys':{},'weights_not_normalized':{},'source_v02_unchanged':hashlib.sha256((ROOT/'models/researcher-a-master-v0.2.blend').read_bytes()).hexdigest()==json.loads((ROOT/'previews/v0.3/reference-calibration.json').read_text())['source_sha256']}
for name in ['Face','Researcher_Glasses']:
    ob=bpy.data.objects[name];keys=ob.data.shape_keys.key_blocks;basis=np.array([p.co[:] for p in keys[0].data]);bk=audit['meshes'][name]['shape_keys']
    status={'same_names':set(bk)==set(k.name for k in keys),'keys':{}}
    for k in keys:
        d=np.linalg.norm(np.array([p.co[:] for p in k.data])-basis,axis=1);status['keys'][k.name]={'moved':int((d>1e-6).sum()),'max_delta':float(d.max()),'was_moving':bk[k.name]['moved_vertices']>0}
    status['active_keys_preserved']=all(v['moved']>0 for v in status['keys'].values() if v['was_moving']);rig['shape_keys'][name]=status
for name in obs:
    ob=bpy.data.objects[name];deform={g.index for g in ob.vertex_groups if arm.data.bones.get(g.name) and arm.data.bones[g.name].use_deform}
    count=sum(abs(sum(g.weight for g in v.groups if g.group in deform)-1)>.005 for v in ob.data.vertices)
    if count:rig['weights_not_normalized'][name]=count
rig['pass']=rig['same_bone_names'] and rig['same_rest_bones'] and rig['source_v02_unchanged'] and not rig['weights_not_normalized'] and all(s['same_names'] and s['active_keys_preserved'] for s in rig['shape_keys'].values())
(out/'rig.json').write_text(json.dumps(rig,indent=2));print('RIG',rig['pass'],flush=True)
details={}
for name in obs:
    ob=bpy.data.objects[name];details[name]={'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'base_triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),'uv_maps':[u.name for u in ob.data.uv_layers],'shape_keys':len(ob.data.shape_keys.key_blocks) if ob.data.shape_keys else 0,'modifiers':[{'name':m.name,'type':m.type,'viewport':m.show_viewport,'render':m.show_render} for m in ob.modifiers],'materials':[m.name if m else None for m in ob.data.materials]}
images=[{'name':i.name,'resolution':list(i.size),'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images if i.users and i.type=='IMAGE']
(out/'technical-audit.json').write_text(json.dumps({'meshes':details,'evaluated':stats(),'textures':images},indent=2))
head=['Face','Researcher_Glasses','Researcher_BobCap','EyeGlobe_L','EyeGlobe_R']+[o.name for o in bpy.data.objects if o.get('reconstruction_tier')]
review_shots.run(objects=head,out=str(out/'head-wire.png'),mode='wire',res=640)
review_shots.run(objects=head,out=str(out/'head-parts.png'),mode='random',res=640)
setup();scene=bpy.context.scene;scene.render.resolution_x=800;scene.render.resolution_y=900;scene.camera=bpy.data.objects['REF_front']
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face']
def setkey(suffix,v):next(k for k in face.data.shape_keys.key_blocks if k.name.endswith(suffix)).value=v
for name in ['blink','wink','speech-smile','glasses-slide']:
    reset_pose();setup();scene.render.resolution_x=800;scene.render.resolution_y=900;scene.camera=bpy.data.objects['REF_front']
    if name=='blink':setkey('Fcl_EYE_Close',1)
    elif name=='wink':setkey('Fcl_EYE_Close_L',1)
    elif name=='speech-smile':setkey('Fcl_MTH_A',.6);setkey('Fcl_MTH_Joy',.35)
    else:bpy.data.objects['Researcher_Glasses'].data.shape_keys.key_blocks['GlassesSlide'].value=1
    scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
print('VALIDATION WRITTEN',out,flush=True)
