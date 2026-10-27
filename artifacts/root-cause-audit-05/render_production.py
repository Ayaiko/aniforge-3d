import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent
for tag in ['rain','snow']:
 d=json.loads((P/f'{tag}-mesh-data.json').read_text());s=bpy.data.scenes.new('Audit_'+tag);bpy.context.window.scene=s
 me=bpy.data.meshes.new(tag+'_raw');me.from_pydata(d['vertices'],[],d['faces']);me.update();h=bpy.data.objects.new(tag+'_raw',me);s.collection.objects.link(h)
 for f in me.polygons:f.use_smooth=True
 mat=bpy.data.materials.new('ProductionClay');mat.diffuse_color=(.55,.55,.55,1);h.data.materials.append(mat)
 w=h.copy();w.data=h.data.copy();s.collection.objects.link(w);black=bpy.data.materials.new('Wire');black.diffuse_color=(.015,.015,.02,1);w.data.materials.clear();w.data.materials.append(black);wf=w.modifiers.new('Wire','WIREFRAME');wf.thickness=.00035;wf.offset=1
 center=Vector((0,0,(max(v[2] for v in d['vertices'])+min(v[2] for v in d['vertices']))/2));span=max(v[2] for v in d['vertices'])-min(v[2] for v in d['vertices']);out=P/'production-wire';out.mkdir(exist_ok=True)
 s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.display.shading.show_shadows=True;s.display.shading.show_cavity=False;s.display.shading.background_type='WORLD';s.world=bpy.data.worlds.new('gray');s.world.color=(.08,.08,.08);s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='Standard'
 for name,direction in [('front',(0,-1,0)),('side',(1,0,0)),('quarter',(1,-1,0))]:
  ca=bpy.data.cameras.new(tag+'_'+name);ca.type='ORTHO';ca.ortho_scale=span*1.18;o=bpy.data.objects.new(ca.name,ca);s.collection.objects.link(o);o.location=center+Vector(direction).normalized()*2;o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler();s.camera=o;s.render.filepath=str(out/f'{tag}-{name}.png');bpy.ops.render.render(write_still=True)
print('PRODUCTION_WIRE_DONE')
