import bpy,sys,json
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/face-likeness-02';sys.path.insert(0,str(R/'.agents/skills/blender-asset-qa/scripts'));import qa_check
sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_audit
h=bpy.data.objects['Anime013_Head'];q=qa_check.run(objects=[h.name],profile='render');a=bx_audit.audit(h);(O/'local-patch-audit.json').write_text(json.dumps({'qa':q,'audit':a},indent=2));print(json.dumps({'qa':q,'topology':{k:a[k] for k in ['verts','faces','non_manifold_edges','flipped_faces','self_intersections','boundary_loops']}},indent=2))
