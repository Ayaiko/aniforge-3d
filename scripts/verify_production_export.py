from pathlib import Path
import sys,struct,json,hashlib
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import render_views
p=ROOT/'models/researcher-a-realtime-v0.2.vrm';data=p.read_bytes();size=struct.unpack_from('<I',data,12)[0];gltf=json.loads(data[20:20+size]);vrm=gltf['extensions']['VRM']
assert data[:4]==b'glTF' and struct.unpack_from('<I',data,8)[0]==len(data)
expressions={}
for group in vrm['blendShapeMaster']['blendShapeGroups']:
    for bind in group['binds']:
        mesh=gltf['meshes'][bind['mesh']]
        assert any(bind['index']<len(primitive.get('targets',[])) for primitive in mesh['primitives']),group['name']
    expressions[group['name']]=len(group['binds'])
required={'hips','spine','head','leftUpperArm','rightUpperArm','leftLowerArm','rightLowerArm','leftHand','rightHand','leftUpperLeg','rightUpperLeg','leftLowerLeg','rightLowerLeg','leftFoot','rightFoot'}
assert required<={b['bone'] for b in vrm['humanoid']['humanBones']}
report={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'humanoid_bones':len(vrm['humanoid']['humanBones']),'expressions':expressions,'valid_expression_bindings':True}
bpy.ops.wm.read_factory_settings(use_empty=True);enable_vrm()
assert bpy.ops.import_scene.vrm(filepath=str(p))=={'FINISHED'}
for m in bpy.data.materials:
    g=m.vrm_addon_extension.mtoon1
    if g.enabled and g.alpha_mode=='BLEND':m.surface_render_method='BLENDED'
faces=[ob for ob in bpy.data.objects if ob.type=='MESH' and ob.data.shape_keys and len(ob.data.shape_keys.key_blocks)>=42]
assert len(faces)==1,'Face morph mesh not uniquely restored';face=faces[0]
report['imported_face_keys']=[k.name for k in face.data.shape_keys.key_blocks]
assert len(report['imported_face_keys'])==42
if face.name!='Face':face.name='Face'
render_views(ROOT/'previews/v0.2/vrm-reimport',['front','face'])
report['reimport_success']=True
(ROOT/'previews/v0.2/export-verification.json').write_text(json.dumps(report,indent=2))
print('Verified VRM JSON, morph bindings, real Blender reimport and rendered consumer result',flush=True)
