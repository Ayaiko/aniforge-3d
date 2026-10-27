import bpy,json
from pathlib import Path
O=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/proportion-correction-03');h=bpy.data.objects['Anime013_Head'];(O/'pre-neck-head.json').write_text(json.dumps({'vertices':[list(v.co) for v in h.data.vertices]},indent=2));print('READ_NECK_SOURCE',len(h.data.vertices))
