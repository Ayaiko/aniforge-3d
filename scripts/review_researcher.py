"""Reproducible geometry report and head review; never changes the source file."""
from pathlib import Path
import sys,json
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
enable_vrm()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a.blend'))
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'))
import qa_check,review_shots
objects=[o.name for o in bpy.data.objects if o.type=='MESH']
report=qa_check.run(objects=objects,profile='render',eps=.0002,tol=.002)
(ROOT/'previews/researcher-qa.json').write_text(json.dumps(report,indent=2))
print('QA',report.get('pass'),len(report.get('errors',[])),len(report.get('warnings',[])),flush=True)
strict=qa_check.run(objects=objects,profile='game',eps=.0002,tol=.002)
(ROOT/'previews/researcher-qa-game.json').write_text(json.dumps(strict,indent=2))
print('Game QA',strict.get('pass'),len(strict.get('errors',[])),len(strict.get('warnings',[])),flush=True)
head=[o.name for o in bpy.data.objects if o.type=='MESH' and o.name not in ['Body'] and min((o.matrix_world@v.co).z for v in o.data.vertices)>1.33]
for mode in ['material','wire']:
    print(review_shots.run(objects=head,out=str(ROOT/f'previews/researcher-head-{mode}.png'),views=['front','right','back','three_quarter'],mode=mode,res=640),flush=True)
