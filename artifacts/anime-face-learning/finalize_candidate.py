import bpy,json,sys,hashlib
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-learning';V=O/'validation';s=bpy.context.scene
# Geometry is loaded from the reviewed 4 mm trial; no further sculpting.
s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='MATCAP';s.display.shading.studio_light='clay_studio.exr';s.display.shading.color_type='MATERIAL';s.render.image_settings.file_format='PNG'
for view in ['front','side','quarter','hero']:
 s.camera=bpy.data.objects['REF_hero_workflow' if view=='hero' else 'REF_'+view];s.render.filepath=str(V/f'after-{view}.png');bpy.ops.render.render(write_still=True)
s.camera=bpy.data.objects['REF_quarter'];s['anime_face_learning_status']='Experimental retained eye-depth correction only. Full facial likeness and head topology remain FAIL. Source checkpoint preserved.'
# Keep existing names, connectivity, object count and disabled subdivision preview.
head=bpy.data.objects['Anime013_Head'];head.show_wire=True;head.show_all_edges=True
s.render.filepath=str(V/'after-quarter.png');candidate=R/'models/anime-face-learning/anime-face-learning-retained.blend';bpy.ops.wm.save_as_mainfile(filepath=str(candidate),copy=True)
meshes=[o for o in s.objects if o.type=='MESH'];report={}
for o in meshes:
 report[o.name]={'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'triangles':sum(len(p.vertices)-2 for p in o.data.polygons)}
 (O/(o.name+'-retained-mesh.json')).write_text(json.dumps({'vertices':[v.co[:] for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons],'matrix_world':[list(r) for r in o.matrix_world]},indent=2))
(O/'retained-geometry-statistics.json').write_text(json.dumps(report,indent=2))
# QA on each eyeball as a separate asset. Do not misclassify a second eyeball as an unattached fragment.
sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
q={name:qa_check.run(objects=[name],profile='render') for name in ['Anime013_Eye_L','Anime013_Eye_R']};(O/'retained-eye-qa.json').write_text(json.dumps(q,indent=2));assert all(v['pass'] for v in q.values())
# Shared audit tests the original head too; pre-existing defects are not silently waived.
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
head_report=bx_audit.audit(head);(O/'retained-head-topology.json').write_text(json.dumps(head_report,indent=2))
print('RETAINED_CANDIDATE_SAVED',str(candidate));print('EYE_QA_PASS',all(v['pass'] for v in q.values()));print('HEAD_NONMANIFOLD',head_report.get('non_manifold_edges'))
