from pathlib import Path
import sys,json
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,render_views
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-master-v0.2.blend'));reset_pose()
render_views(ROOT/'previews/v0.2/after')
before=json.loads((ROOT/'previews/v0.2/before/cameras.json').read_text());after=json.loads((ROOT/'previews/v0.2/after/cameras.json').read_text())
for name in before:
    assert {k:v for k,v in before[name].items() if k!='path'}=={k:v for k,v in after[name].items() if k!='path'},'Camera changed '+name
reset_pose()
sys.path.insert(0,str(ROOT/'.agents/skills/blender-asset-qa/scripts'))
import review_shots
head=[o.name for o in bpy.data.objects if o.type=='MESH' and o.name!='Body' and min((o.matrix_world@v.co).z for v in o.data.vertices)>1.33]
for mode in ['material','wire']:
    review_shots.run(objects=head,out=str(ROOT/f'previews/v0.2/head-{mode}.png'),views=['front','right','back','three_quarter'],mode=mode,res=640)
# Exact rendered pixels are tiled, never regenerated or retouched.
def contact_sheet(view_names,name):
    size=640;canvas=np.ones((size*len(view_names),size*2,4),dtype=np.float32)
    for row,view in enumerate(view_names):
        for col,kind in enumerate(['before','after']):
            im=bpy.data.images.load(str(ROOT/f'previews/v0.2/{kind}/{view}.png'),check_existing=False);im.scale(size,size)
            a=np.empty(size*size*4,dtype=np.float32);im.pixels.foreach_get(a)
            y=(len(view_names)-1-row)*size;canvas[y:y+size,col*size:(col+1)*size]=a.reshape(size,size,4);bpy.data.images.remove(im)
    im=bpy.data.images.new('Comparison',width=size*2,height=size*len(view_names),alpha=True);im.pixels.foreach_set(canvas.ravel());im.file_format='PNG';im.filepath_raw=str(ROOT/f'previews/v0.2/{name}.png');im.save();bpy.data.images.remove(im)
contact_sheet(['front','quarter','side'],'before-after')
contact_sheet(['face','hair','full'],'before-after-details')
print('Matched cameras verified; material/wire review and untouched-pixel comparisons saved',flush=True)
