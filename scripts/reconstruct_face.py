"""Reference-space direct editing of the existing deformable face, iteration 01.
No new primitives, remesh, subdivision levels or random surface detail.
"""
from pathlib import Path
import sys,math,json
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reference-audit-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];inv=face.matrix_world.inverted();keys=face.data.shape_keys.key_blocks
before_names=[k.name for k in keys];basis=[face.matrix_world@v.co for v in keys[0].data]
material_ids={}
for p in face.data.polygons:
    material_ids.setdefault(face.data.materials[p.material_index].name,set()).update(p.vertices)
iris_ids=set().union(*(v for n,v in material_ids.items() if 'EyeIris' in n or 'Corneal' in n))
skin_ids=next(v for n,v in material_ids.items() if 'Face_00_SKIN' in n)
eye_z=1.446197748184204
def g(x,c,r):return math.exp(-((x-c)/r)**2)
def edit(p,is_iris=False):
    x,y,z=p;original_z=z;ax=abs(x);front=max(0,min(1,(-y-.015)/.03))
    eye=g(ax,.04025,.025)*g(z,eye_z,.026)*front
    mouth=g(x,0,.029)*g(z,1.385,.012)*front
    narrowing=.16*g(z,1.414,.043)+.025*g(z,1.48,.035)
    protect=max(.92*eye,.90*mouth)
    x*=1-narrowing*(1-protect)
    # Actual eye opening changes, with the same continuous cage for all morphs.
    z-=.32*(z-eye_z)*eye
    z+=.0015*((ax-.04025)/.021)*eye
    if is_iris:
        cx=.040 if x>0 else -.0405
        x=cx+(x-cx)*.61;z=eye_z+(z-eye_z)*.86
    # Broad profile correction: chin forward, longer lower plane and restrained lips.
    y-=front*(.010*g(ax,0,.044)*g(original_z,1.357,.017)+.0045*g(x,0,.012)*g(original_z,1.410,.011))
    x*=1+.19*mouth
    # Rest mouth becomes a subtle straight deadpan smile, not a round pout.
    z+=.0007*(x/.016)*mouth+.00055*g(ax,.014,.005)*mouth
    return Vector((x,y,z))
changed=0;max_move=0
for key in keys:
    for i,v in enumerate(key.data):
        old=face.matrix_world@v.co;new=edit(old,i in iris_ids);v.co=inv@new
        if key==keys[0]:
            d=(new-old).length;changed+=d>1e-6;max_move=max(max_move,d)
for name in ['EyeGlobe_L','EyeGlobe_R']:
    ob=bpy.data.objects[name];mi=ob.matrix_world.inverted()
    for v in ob.data.vertices:v.co=mi@edit(ob.matrix_world@v.co)
face['reconstruction_method']='Direct surface cage editing of all existing expression targets, reference-aligned; no added subdivision.'
face['reconstruction_iteration']='01 face primary forms'
assert [k.name for k in keys]==before_names
directory=render_iteration('01-face')
(directory/'changes.json').write_text(json.dumps({'method':'Direct Mesh Editing','basis_vertices_moved':changed,'max_basis_move_m':max_move,'face_vertices_before_after':[len(basis),len(basis)],'shape_keys':len(keys),'subdivision_levels_added':0,'edits':['Cheek/temple width narrowed with protected eye and mouth anchors','Eye aperture flattened with outer-corner lift','Iris/cornea horizontal span reduced 39 percent','Chin advanced in profile and nose tip projection increased','Mouth slightly widened and made asymmetric'],'artistic_status':'Pending visual inspection, not inferred from script success'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-01-face-v0.3.blend'))
print('FACE ITERATION SAVED',changed,max_move,flush=True)
