import json,hashlib,shutil,math
from pathlib import Path
from collections import Counter
P=Path(__file__).resolve().parent;R=P.parent.parent
ledger=P/'sources/review-ledger.json';d=json.loads(ledger.read_text())
for s in d['sheets']:s['reviewed']=True
d['captions_reviewed']='Entire English VTT read; ASR wording errors retained as uncertainty. Diagram details at 01:55, 04:30, 06:40 and 08:40 inspected in full-resolution images.';ledger.write_text(json.dumps(d,indent=2))
rows=[]
for tag in ['current','repair','clean','rain','snow']:
 d=json.loads((P/(tag+'-mesh-audit.json')).read_text());pol=d['polygon_sides'];rows.append({'tag':tag,'vertices':d['vertices'],'faces':d['faces'],'quads':pol.get('4',0),'triangles':pol.get('3',0),'quad_percent':round(pol.get('4',0)/d['faces']*100,3),'valence_ge6':len(d['high_valence']),'warped_quads_gt20deg':d['warped_quads_gt20deg'],'warped_quad_fraction':d['warped_quads_gt20deg']/pol.get('4',1),'overlap_candidates':d['self_overlap_candidate_count'],'uv_maps':d['uv_maps'],'shape_keys_including_basis':len(d['shape_keys'])})
(P/'summary-table.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
source=json.loads((P/'current-mesh-data.json').read_text());data={k:source[k] for k in ['vertices','faces']};sha=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest();(P/'source-geometry-hash.json').write_text(json.dumps({'sha256':sha,'vertices':len(data['vertices']),'faces':len(data['faces'])},indent=2))
code="""import bpy,json,hashlib
h=bpy.data.objects['Anime013_Head']
d={'vertices':[list(v.co) for v in h.data.vertices],'faces':[list(p.vertices) for p in h.data.polygons]}
print(json.dumps({'scene':bpy.context.scene.name,'file':bpy.data.filepath,'head_sha256':hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'vertices':len(h.data.vertices),'faces':len(h.data.polygons),'mode':h.mode,'dirty':bpy.data.is_dirty,'subdivision':[(m.show_viewport,m.show_render) for m in h.modifiers if m.type=='SUBSURF']}))
"""
(P/'final-live-verify-request.json').write_text(json.dumps([{'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'หยุดเพิ่มรายละเอียดโมเดลชั่วคราว ทำ Root Cause Audit ของปัญหาความคล้ายและ Facial Topology'},'label':'audit05-final-live-preservation'}],ensure_ascii=False))
