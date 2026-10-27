"""Reject the misleading lip-centroid fit. Fit the actual central skin profile."""
from pathlib import Path
import sys,json,math,bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-11-profile-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];mi=face.matrix_world.inverted()
with bpy.data.libraries.load(str(ROOT/'models/researcher-a-reconstruction-10-cleanup-v0.3.blend'),link=False) as (s,d):d.meshes=['Face.baked']
original=d.meshes[0];basis_original=original.shape_keys.key_blocks[0];deltas=[]
for p in basis_original.data:
    x,y,z=face.matrix_world@p.co;front=max(0,min(1,(-y-.025)/.04));left=math.exp(-((x+.04)/.027)**4-((z-1.448)/.023)**4)*front
    mouth=math.exp(-(x/.026)**4-((z-1.3855)/.014)**4)*front
    deltas.append(Vector((-.0018*left,0,.0015*mouth-.0024*left)))
for key in face.data.shape_keys.key_blocks:
    for i,p in enumerate(original.shape_keys.key_blocks[key.name].data):key.data[i].co=mi@(face.matrix_world@p.co+deltas[i])
bpy.data.meshes.remove(original);bpy.context.view_layer.update()
ev=face.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();skinid=next(i for i,m in enumerate(me.materials) if 'Face_00_SKIN' in m.name)
ids={i for p in me.polygons if p.material_index==skinid for i in p.vertices};skin=np.array([ev.matrix_world@me.vertices[i].co for i in ids]);ev.to_mesh_clear()
# Native reference colour-mask outline, hand checked against the source drawing.
# These are side silhouette samples, not the centre of a lip material patch.
samples=[(255,55),(260,54),(270,63),(280,69),(285,72),(290,73),(295,80),(300,83),(305,81),(310,84),(320,90),(330,92),(340,93)]
scale=json.loads((ROOT/'previews/v0.3/reference-calibration.json').read_text())['meters_per_reference_pixel'];eye_z=1.446197748184204
zvals=[];differences=[]
for yy,xx in samples:
    z=eye_z-(yy-222)*scale;candidate=skin[(abs(skin[:,2]-z)<.0016)&(abs(skin[:,0])<.075)]
    if len(candidate):
        zvals.append(z);differences.append(float(np.clip((xx-200)*scale-candidate[:,1].min(),-.003,.010)))
order=np.argsort(zvals);zvals=np.array(zvals)[order];differences=np.array(differences)[order]
differences=np.convolve(np.pad(differences,(1,1),mode='edge'),np.array([.2,.6,.2]),mode='valid')
delta=[]
for p in face.data.shape_keys.key_blocks[0].data:
    world=face.matrix_world@p.co;x,y,z=world
    correction=float(np.interp(z,zvals,differences,left=0,right=0))
    front=max(0,min(1,(-y-.025)/.035));across=math.exp(-(x/.069)**6)
    delta.append(Vector((0,correction*front*across,0)))
for key in face.data.shape_keys.key_blocks:
    for i,p in enumerate(key.data):p.co=mi@(face.matrix_world@p.co+delta[i])
directory=render_iteration('12-profile-contour')
(directory/'changes.json').write_text(json.dumps({'acceptance_before_phase':['Reject point alignment if full side contour worsens','Improve the lower-face side contour without a protruding muzzle','Preserve all expression deltas; verify blink/speech again'],'rejected_iteration':'11 perioral forward shift: lower anchor error but worse silhouette','geometry_changes':['Reverted the 9 mm perioral advance from 11','Kept the small reference eye asymmetry','Perioral front height raised only 1.5 mm','Direct facial surface correction from 13 checked side-contour samples, smoothed and propagated identically to all keys'],'profile_samples_reference_pixels':samples,'profile_correction_z_m':zvals.tolist(),'profile_delta_y_m':differences.tolist(),'tertiary_details_added':0,'artistic_status':'Pending visual inspection; not a whole-character artistic pass'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-12-contour-v0.3.blend'))
