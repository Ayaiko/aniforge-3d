import bpy,math,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent

def material(name,color):
 m=bpy.data.materials.new(name);n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.72;m.diffuse_color=(*color,1);return m

def setup():
 s=bpy.context.scene
 for o in list(s.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 gray=material('AuditClay',(.42,.42,.42));white=material('AuditEye',(.64,.64,.64));dark=material('AuditPupil',(.018,.018,.018))
 for o in s.objects:
  if o.type!='MESH':continue
  if 'Head' in o.name:
   o.data.materials.clear();o.data.materials.append(gray)
   for f in o.data.polygons:f.material_index=0;f.use_smooth=True
  elif 'Eye' in o.name:
   mats=list(o.data.materials);o.data.materials.clear()
   for m in mats:
    color=tuple(m.diffuse_color[:3]) if m else (1,1,1)
    o.data.materials.append(dark if m and ('pupil' in m.name.lower() or max(color)<.15) else white)
  else:
   o.data.materials.clear();o.data.materials.append(dark)
 for name,loc,power,size in [('Key',(-.30,-.45,1.87),4.5,.38),('Fill',(.35,-.25,1.56),2.1,.35),('Rim',(.1,.35,1.8),3.6,.25)]:
  d=bpy.data.lights.new('Audit_'+name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1.45))-o.location).to_track_quat('-Z','Y').to_euler()
 s.world=bpy.data.worlds.new('AuditWorld');s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.12,.12,.12,1);s.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.25
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=20;s.cycles.use_denoising=True;s.cycles.max_bounces=4
 s.render.resolution_x=800;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
 s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=0;s.view_settings.gamma=1
 return s

def render_set(tag,levels=(0,1),wire=True,save=True):
 s=bpy.context.scene;h=bpy.data.objects['Anime013_Head'];out=P/'renders'/tag;out.mkdir(exist_ok=True,parents=True)
 sub=next((m for m in h.modifiers if m.type=='SUBSURF'),None)
 if not sub:sub=h.modifiers.new('Audit_Subdivision','SUBSURF')
 for level in levels:
  sub.show_viewport=level>0;sub.show_render=level>0;sub.levels=level;sub.render_levels=level
  for v in ['front','side','quarter']:
   s.camera=bpy.data.objects['REF_'+v];s.render.filepath=str(out/f'clay-sub{level}-{v}.png');bpy.ops.render.render(write_still=True)
  if wire:
   w=h.copy();w.data=h.data.copy();w.name='AUDIT_WIRE';s.collection.objects.link(w)
   for m in list(w.modifiers):w.modifiers.remove(m)
   black=material('AuditWire',(.006,.007,.008));w.data.materials.clear();w.data.materials.append(black)
   wf=w.modifiers.new('Base cage wire','WIREFRAME');wf.thickness=.00024;wf.offset=1;wf.use_replace=True;wf.use_even_offset=True
   # Base cage overlay on identical base surface; Subdivision row uses evaluated wire only as separate diagnostic.
   if level:
    su=w.modifiers.new('AuditWireSub','SUBSURF');su.show_render=False
   for v in ['front','side','quarter']:
    s.camera=bpy.data.objects['REF_'+v];s.render.filepath=str(out/f'wire-sub{level}-{v}.png');bpy.ops.render.render(write_still=True)
   bpy.data.objects.remove(w,do_unlink=True)
 sub.show_render=False;sub.show_viewport=False
 if save:bpy.ops.wm.save_as_mainfile(filepath=str(P.parent.parent/'models/root-cause-audit-05'/f'{tag}.blend'))
 (out/'controls.json').write_text(json.dumps({'cameras':{v:{'matrix':[list(r) for r in bpy.data.objects['REF_'+v].matrix_world],'ortho_scale':bpy.data.objects['REF_'+v].data.ortho_scale} for v in ['front','side','quarter']},'resolution':[800,900],'engine':s.render.engine,'samples':s.cycles.samples,'display':[s.view_settings.view_transform,s.view_settings.look],'lights':[{ 'name':o.name,'location':list(o.location),'energy':o.data.energy,'size':o.data.size} for o in s.objects if o.type=='LIGHT']},indent=2))
