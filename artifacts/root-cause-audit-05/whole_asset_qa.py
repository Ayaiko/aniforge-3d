import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parent.parent/'.agents/skills/blender-asset-qa/scripts'));import qa_check
names=[o.name for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
r=qa_check.run(objects=names,profile='render',eps=.0002,tol=.001)
tag=sys.argv[sys.argv.index('--')+1];(P/(tag+'-whole-asset-qa.json')).write_text(json.dumps(r,indent=2,default=str));print('WHOLE_QA',tag,r['pass'],r['errors'],r['warnings'])
