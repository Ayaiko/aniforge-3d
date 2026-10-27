"""Keep the strongest reviewed forms; reject automatic profile distortions.
Finish UV side walls and rigid cap topology without adding surface detail.
"""
from pathlib import Path
import sys,json,math,bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-12-contour-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];mi=face.matrix_world.inverted()
with bpy.data.libraries.load(str(ROOT/'models/researcher-a-reconstruction-10-cleanup-v0.3.blend'),link=False) as (s,d):d.meshes=['Face.baked']
original=d.meshes[0];deltas=[]
for p in original.shape_keys.key_blocks[0].data:
    x,y,z=face.matrix_world@p.co;front=max(0,min(1,(-y-.025)/.04));left=math.exp(-((x+.04)/.027)**4-((z-1.448)/.023)**4)*front;mouth=math.exp(-(x/.026)**4-((z-1.3855)/.014)**4)*front
    deltas.append(Vector((-.0018*left,0,.0015*mouth-.0024*left)))
for key in face.data.shape_keys.key_blocks:
    for i,p in enumerate(original.shape_keys.key_blocks[key.name].data):key.data[i].co=mi@(face.matrix_world@p.co+deltas[i])
bpy.data.meshes.remove(original)
wall_changes={}
for ob in [o for o in bpy.data.objects if o.get('reconstruction_tier')]:
    uv=ob.data.uv_layers.active.data;count=0
    for p in ob.data.polygons:
        values=[uv[li].uv.x for li in p.loop_indices]
        if min(values)<.5<max(values):
            # Existing front/back faces are disjoint. Place connecting walls in
            # their own thin strips instead of spanning the entire front atlas.
            left=(min(values)+max(values))/2<.5
            for li in p.loop_indices:
                back=uv[li].uv.x>.5;uv[li].uv.x=(.475 if left else .985)+.010*back
            count+=1
        if ob.name=='Hair_FringeMain' and all(abs(ob.data.vertices[i].co.z-1.586)<1e-5 for i in p.vertices):
            coords=[ob.data.vertices[i].co for i in p.vertices];xmin=min(c.x for c in coords);xmax=max(c.x for c in coords);ymin=min(c.y for c in coords);ymax=max(c.y for c in coords)
            for li in p.loop_indices:
                c=ob.data.vertices[ob.data.loops[li].vertex_index].co
                uv[li].uv=(.52+.44*(c.x-xmin)/max(1e-7,xmax-xmin),.003+.009*(c.y-ymin)/max(1e-7,ymax-ymin))
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(ob.data);bm.free();wall_changes[ob.name]=count
directory=render_iteration('13-reviewed-master')
(directory/'changes.json').write_text(json.dumps({'acceptance_before_phase':['Retain the best reviewed side profile instead of a point-fit or silhouette-fit artifact','No zero UV-area faces or coplanar overlaps in official QA','Hair front/back/wall UV regions separated','Blink and speech remain functional'],'rejected_iterations':['11 perioral forward shift produced a protruding muzzle','12 sampled contour cage produced an unnatural lip/chin concavity; automatic silhouette fitting is insufficient'],'geometry_changes':['Restored the stable side-profile forms from 10','Retained eye asymmetry and restrained mouth height correction','Triangulated remaining rigid hair-cut n-gons'],'uv_side_wall_faces_remapped':wall_changes,'tertiary_details_added':0,'artistic_status':'NOT PASSED: crown flow, hair section design, eyebrows, facial plane refinement and clothing remain below the approved artwork'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-13-reviewed-v0.3.blend'))
