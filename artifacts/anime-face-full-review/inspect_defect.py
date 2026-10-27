import bpy,bmesh,json
from pathlib import Path
out=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/anime-face-full-review')
o=bpy.data.objects['Anime013_Head'];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table()
r=[]
for e in bm.edges:
 if len(e.link_faces)>2:
  r.append({'edge':e.index,'verts':[v.index for v in e.verts],'coordinates':[list(v.co) for v in e.verts],'faces':[{'index':f.index,'verts':[v.index for v in f.verts],'center':list(f.calc_center_median()),'area':f.calc_area(),'normal':list(f.normal)} for f in e.link_faces]})
(out/'overconnected-edges.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
print('SCENE',bpy.context.scene.name,'COUNTS',len(bm.verts),len(bm.edges),len(bm.faces),'SHAPEKEYS',bool(o.data.shape_keys),'MATERIALS',[m.name for m in o.data.materials]);bm.free()
