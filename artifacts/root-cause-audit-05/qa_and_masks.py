import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent.parent/'.agents/skills/blender-asset-qa/scripts'));import qa_check
s=bpy.context.scene;tag=sys.argv[sys.argv.index('--')+1];h=bpy.data.objects['Anime013_Head'];report={}
for level in [0,1]:
 sub=next(m for m in h.modifiers if m.type=='SUBSURF');sub.show_render=level>0;sub.show_viewport=level>0;sub.levels=level;sub.render_levels=level;bpy.context.view_layer.update()
 report['sub'+str(level)]=qa_check.run(objects=[h.name],profile='render',eps=.0002,tol=.001)
(P/(tag+'-asset-qa.json')).write_text(json.dumps(report,indent=2,default=str))
sub.show_viewport=False;sub.show_render=False
for o in s.objects:
 if o.type=='MESH' and o!=h:o.hide_render=True
mat=bpy.data.materials.new('ID_head');mat.node_tree.nodes.clear();out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');em=mat.node_tree.nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1,1,1,1);mat.node_tree.links.new(em.outputs['Emission'],out.inputs['Surface']);h.data.materials.clear();h.data.materials.append(mat)
for f in h.data.polygons:f.material_index=0
s.render.film_transparent=True;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.cycles.samples=1;s.cycles.use_denoising=False;s.render.image_settings.color_mode='RGBA'
for v in ['front','side','quarter']:
 s.camera=bpy.data.objects['REF_'+v];s.render.filepath=str(P/'renders'/tag/f'mask-{v}.png');bpy.ops.render.render(write_still=True)
print('QA_MASK_DONE',tag,{k:{'pass':v['pass'],'errors':v['errors'],'warnings':v['warnings']} for k,v in report.items()},flush=True)
