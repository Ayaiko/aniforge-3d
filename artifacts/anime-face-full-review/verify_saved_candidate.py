import bpy,sys,json,hashlib
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-full-review';sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit,bx_review
s=bpy.context.scene;names=['Anime013_Head','Anime013_Eye_L','Anime013_Eye_R','Anime013_MouthCavity'];assert s.name=='Anime_Reference_013' and len([o for o in s.objects if o.type=='MESH'])==4
h=bx_audit.audit(bpy.data.objects[names[0]]);assert h['verts']==946 and h['faces']==1107 and h['non_manifold_edges']==0 and h['boundary_loops']==[32,24,24]
assert not any(o.name.startswith('TutorialReview_') for o in s.objects)
allqa=bx_audit.deliverable([bpy.data.objects[n] for n in names],profile='render');(O/'whole-asset-qa.json').write_text(json.dumps(allqa,indent=2))
wire=bx_review.review([bpy.data.objects[n] for n in names],str(O/'validation/wire-review'),views=('front','right','threequarter','low'),modes=('wire',),res=400)
report={'reopen_pass':True,'scene':s.name,'mesh_count':4,'stats':{n:{'verts':len(bpy.data.objects[n].data.vertices),'faces':len(bpy.data.objects[n].data.polygons),'tris':sum(len(p.vertices)-2 for p in bpy.data.objects[n].data.polygons)} for n in names},'render_profile_pass':allqa['pass'],'raw_errors':allqa['errors'],'wire':wire,'sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'bytes':Path(bpy.data.filepath).stat().st_size}
(O/'saved-candidate-verification.json').write_text(json.dumps(report,indent=2,default=str));print('RESULT',json.dumps(report,default=str))
