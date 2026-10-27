from pathlib import Path
import sys,json,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-13-reviewed-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
ob=bpy.data.objects['Hair_FringeMain'];uv=ob.data.uv_layers.active.data;fixed=[]
for p in ob.data.polygons:
    pts=[uv[li].uv.copy() for li in p.loop_indices]
    area=sum(pts[i].x*pts[(i+1)%len(pts)].y-pts[(i+1)%len(pts)].x*pts[i].y for i in range(len(pts)))
    if abs(area)<1e-12:
        assert len(pts)==3
        for li,co in zip(p.loop_indices,[(.10,.003),(.14,.003),(.12,.012)]):uv[li].uv=co
        fixed.append(p.index)
directory=render_iteration('14-master-checkpoint')
(directory/'changes.json').write_text(json.dumps({'geometry_changes':[],'uv_changes':{'Hair_FringeMain_zero_area_faces_fixed':fixed},'tertiary_details_added':0,'artistic_status':'NOT PASSED: work-in-progress reconstruction; professional hand surface/sculpt review still required'},indent=2))
scene=bpy.context.scene;scene['reconstruction_status']='Artistic gate NOT PASSED. Technical QA recorded separately in RECONSTRUCTION_REPORT.md.'
text=bpy.data.texts.get('RECONSTRUCTION_README') or bpy.data.texts.new('RECONSTRUCTION_README')
text.clear();text.write('Reference-driven reconstruction v0.3 — WORK IN PROGRESS\n\nOriginal/v0.2 files retained. This is the reviewed geometry checkpoint, not an approved professional sculpt.\nSee RECONSTRUCTION_REPORT.md and previews/v0.3/final-comparison.png.\nFront/side/back reference cameras and source images are packed.\nFace 42 shape keys and glasses slide retained. No live tracking validation performed.\n')
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_overlays=False
            space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=0
            space.camera=bpy.data.objects['REF_front']
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-master-v0.3.blend'))
print('MASTER CHECKPOINT',fixed,flush=True)
