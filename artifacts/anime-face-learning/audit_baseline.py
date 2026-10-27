import bpy,json,sys
from pathlib import Path
from mathutils import Vector
OUT=Path('/Users/graind/Documents/ChatGPT/vTuber/artifacts/anime-face-learning'); OUT.mkdir(exist_ok=True)
s=bpy.context.scene
scenes=[]
for sc in bpy.data.scenes:
 scenes.append({'name':sc.name,'objects':[o.name for o in sc.objects]})
obs=[]
for o in s.objects:
 d={'name':o.name,'type':o.type,'hidden':o.hide_render,'matrix_world':[list(r) for r in o.matrix_world]}
 if o.type=='MESH':
  d.update(vertices=len(o.data.vertices),edges=len(o.data.edges),faces=len(o.data.polygons),modifiers=[{'name':m.name,'type':m.type,'render':m.show_render,'viewport':m.show_viewport} for m in o.modifiers],shape_keys=[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],materials=[m.name if m else None for m in o.data.materials])
  (OUT/(o.name+'-baseline-mesh.json')).write_text(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'matrix_world':d['matrix_world']},indent=2))
 if o.type=='CAMERA':d.update(ortho_scale=o.data.ortho_scale,camera_type=o.data.type)
 obs.append(d)
report={'blender':bpy.app.version_string,'file':bpy.data.filepath,'active_scene':s.name,'scenes':scenes,'objects':obs,'render':{'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage]},'scene_custom':dict(s.items())}
(OUT/'baseline-audit.json').write_text(json.dumps(report,indent=2,default=str))
print('BASELINE_AUDIT',json.dumps({'scene':s.name,'meshes':[(o['name'],o.get('vertices'),o.get('faces')) for o in obs if o['type']=='MESH'],'cameras':[o['name'] for o in obs if o['type']=='CAMERA']}),flush=True)
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.render.image_settings.file_format='PNG';s.render.resolution_percentage=100
for v in ['front','side','quarter']:
 c=bpy.data.objects.get('REF_'+v);assert c and c.type=='CAMERA'
 s.camera=c;s.render.filepath=str(OUT/'validation'/f'before-{v}.png');bpy.ops.render.render(write_still=True)
print('BASELINE_RENDER_PASS',flush=True)
