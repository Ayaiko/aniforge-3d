import bpy,json
from pathlib import Path
out=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/anime-face-learning')
result={}
for name in ['Anime013_Eye_L','Anime013_Eye_R']:
 o=bpy.data.objects[name];me=o.data;entries=[]
 for slot,m in enumerate(me.materials):
  ids={v for p in me.polygons if p.material_index==slot for v in p.vertices};ps=[me.vertices[i].co for i in ids]
  entries.append({'index':slot,'name':m.name if m else None,'vertices':len(ids),'bounds':[[min(p[k] for p in ps),max(p[k] for p in ps)] for k in range(3)] if ps else None,'ids':sorted(ids)})
 result[name]={'materials':entries,'polygons_material':[p.material_index for p in me.polygons]}
(out/'eye-material-inspection.json').write_text(json.dumps(result,indent=2));print('EYE_INSPECTION',json.dumps({n:[{k:v for k,v in m.items() if k!='ids'} for m in d['materials']] for n,d in result.items()}))
