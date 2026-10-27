"""Parse CC0 GLB as numeric data; do not execute/import model code."""
from pathlib import Path
import struct,json
root=Path(__file__).resolve().parents[1];folder=root/'assets/base/vroid-cc0';b=(folder/'base_female.vrm').read_bytes();ln=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+ln]);at=20+ln;blen=struct.unpack_from('<I',b,at)[0];binary=b[at+8:at+8+blen]
def acc(i):
    a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];n={'VEC3':3,'VEC2':2,'VEC4':4,'SCALAR':1}[a['type']];step=v.get('byteStride',struct.calcsize(fmt)*n);off=v.get('byteOffset',0)+a.get('byteOffset',0)
    return [list(struct.unpack_from('<'+fmt*n,binary,off+i*step)) for i in range(a['count'])]
mesh=g['meshes'][0];positions=acc(mesh['primitives'][0]['attributes']['POSITION']);groups=g['extensions']['VRM']['blendShapeMaster']['blendShapeGroups']
print('VRM_MORPHS',[(v['name'],[(x['index'],x['weight']) for x in v['binds']]) for v in groups])
for i,p in enumerate(mesh['primitives']):
    ids=[x[0] for x in acc(p['indices'])];used=sorted(set(ids));vs=[positions[j] for j in used]
    print('VRM_PRIMITIVE',i,g['materials'][p['material']]['name'],len(used),[(min(v[k] for v in vs),max(v[k] for v in vs)) for k in range(3)])
output={'positions':positions,'primitives':[{'name':g['materials'][p['material']]['name'],'indices':[x[0] for x in acc(p['indices'])]} for p in mesh['primitives']],
        'targets':[{key:acc(value) for key,value in t.items()} for t in mesh['primitives'][0].get('targets',[])],
        'morph_groups':groups,'uv':acc(mesh['primitives'][0]['attributes']['TEXCOORD_0'])}
(root/'artifacts/reconstruction-v2-mcp/vroid-anime-payload.json').write_text(json.dumps(output));print('PARSED_CC0_ANIME_HEAD_DATA')
