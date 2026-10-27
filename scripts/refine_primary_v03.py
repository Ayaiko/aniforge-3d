"""Iteration 03: correct the failures seen in actual iteration-02 overlays."""
from pathlib import Path
import sys,math,json
import bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from reconstruction_review import render_iteration
from character_studio import reset_pose,setup
from production_common import recalc
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-02-hair-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];globe_names=['EyeGlobe_L','EyeGlobe_R']
mesh_names=[bpy.data.objects[n].data.name for n in ['Face']+globe_names]
with bpy.data.libraries.load(str(ROOT/'models/researcher-a-reference-audit-v0.3.blend'),link=False) as (source,destination):
    assert all(n in source.meshes for n in mesh_names);destination.meshes=mesh_names
loaded=destination.meshes
def g(x,c,r):return math.exp(-((x-c)/r)**2)
iris_ids={v for p in face.data.polygons if any(s in face.data.materials[p.material_index].name for s in ['EyeIris','Corneal']) for v in p.vertices}
eye_z=1.446197748184204
def edit(p,iris=False):
    x,y,z=p;oz=z;ax=abs(x);front=max(0,min(1,(-y-.015)/.03))
    eye=g(ax,.04025,.025)*g(z,eye_z,.026)*front;mouth=g(x,0,.029)*g(z,1.385,.012)*front
    narrow=.16*g(z,1.414,.043)+.025*g(z,1.48,.035)
    # Ear and lateral skull are retained; narrow the actual facial planes.
    x*=1-narrow*(1-max(.92*eye,.90*mouth))*front
    z-=.32*(z-eye_z)*eye;z+=.0015*((ax-.04025)/.021)*eye
    if iris:
        cx=.040 if x>0 else -.0405;x=cx+(x-cx)*.61;z=eye_z+(z-eye_z)*.86
    y-=front*(.010*g(ax,0,.044)*g(oz,1.357,.017)+.0045*g(x,0,.012)*g(oz,1.410,.011))
    x*=1+.19*mouth;z+=.0007*(x/.016)*mouth+.00055*g(ax,.014,.005)*mouth
    return Vector((x,y,z))
inverse=face.matrix_world.inverted()
for key in face.data.shape_keys.key_blocks:
    original=loaded[0].shape_keys.key_blocks[key.name]
    for i,p in enumerate(original.data):key.data[i].co=inverse@edit(face.matrix_world@p.co,i in iris_ids)
for i,name in enumerate(globe_names):
    ob=bpy.data.objects[name];mi=ob.matrix_world.inverted()
    for p,original in zip(ob.data.vertices,loaded[i+1].vertices):p.co=mi@edit(ob.matrix_world@original.co)
for data in loaded:bpy.data.meshes.remove(data)

# Reshape existing controlled surfaces directly. Row centres and section widths
# are measured from the actual edited mesh; no subdivision is added.
hair_records=[]
for ob in [o for o in bpy.data.objects if o.get('reconstruction_tier')=='Primary form']:
    rows=ob['rows'];cols=ob['cols'];layer=rows*cols
    a=np.array([v.co[:] for v in ob.data.vertices]).reshape(2,rows,cols,3)
    centres=(a[0].mean(axis=1)+a[1].mean(axis=1))/2
    for row,c in enumerate(centres):
        t=row/(rows-1)
        # Preserve width until the last 12%: short rounded/bent tips replace teeth.
        if t>.75:
            lastfull=int(.75*(rows-1));src=a[:,lastfull]-centres[lastfull]
            end=max(.008,1-((t-.75)/.25)**4)
            # Reorient the section progressively into the existing tip direction.
            a[:,row]=c+src*end
        for back in [0,1]:
            for col in range(cols):
                p=a[back,row,col];z=p[2]
                # Round the head rather than broadening the crown into a flat shelf.
                p[0]*=.965
                if z>1.55:p[2]+=.005*math.exp(-((p[0]-.022)/.04)**2)*min(1,(z-1.55)/.045)
                # Keep long far-side hair behind the cheek in side view.
                if ob.name in ['Hair_SweptInner','Hair_SweptMiddle','Hair_SweptOuter']:
                    lower=max(0,min(1,(1.48-z)/.075));p[1]+=.043*lower
                if ob.name in ['Hair_RightBob','Hair_BehindEar','Hair_RearMass_00']:
                    p[1]+=.040*math.exp(-((z-1.443)/.049)**2)
                # Lower tips curl inward; do not leave long separated wedges.
                if t>.78:
                    f=(t-.78)/.22;p[2]+=.003*math.sin(f*math.pi/2)
        if ob.name=='Hair_FringeMain' and t>.65:a[:,row,:,2]+=.004*((t-.65)/.35)
        if ob.name=='Hair_FringeAccent' and t>.65:
            a[:,row,:,2]+=.008*((t-.65)/.35);a[:,row,:,0]-=.003*((t-.65)/.35)
        if ob.name=='Hair_EarTuck' and t>.55:a[:,row,:,2]+=.017*((t-.55)/.45)
    for v,p in zip(ob.data.vertices,a.reshape(-1,3)):v.co=p
    recalc(ob);hair_records.append({'name':ob.name,'vertices_moved':len(ob.data.vertices)})
cap=bpy.data.objects['Researcher_BobCap']
for v in cap.data.vertices:
    x,y,z=v.co;v.co.x*=.965
    if z<1.405:v.co.z-=.011*max(0,(1.405-z)/.06)
# Real coverage opening for the exposed ear, cut only in the hidden scalp shell.
bm=bmesh.new();bm.from_mesh(cap.data)
remove=[]
for f in bm.faces:
    p=f.calc_center_median()
    if p.x>.065 and ((p.y-.005)/.040)**2+((p.z-1.444)/.036)**2<1:remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(cap.data);bm.free()
glasses=bpy.data.objects['Researcher_Glasses'];mi=glasses.matrix_world.inverted()
for key in glasses.data.shape_keys.key_blocks:
    for v in key.data:
        p=glasses.matrix_world@v.co
        if abs(p.x)>.012:
            center=.040 if p.x>0 else -.0405;p.x=center+(p.x-center)*.92
        p.z=1.451+(p.z-1.451)*.86-.006
        # Nose pads/frame bridge stay in front of the nose after the lower fit.
        p.y-=.002*math.exp(-(p.x/.017)**2)
        v.co=mi@p
directory=render_iteration('03-primary-correction')
(directory/'changes.json').write_text(json.dumps({'geometry_changes':['Ear/skull restored from source with narrowing limited to front facial planes','All 42 face keys recomputed from original coordinates','Glasses frame height reduced 14 percent and lowered 6 mm','18 hair surfaces reshaped: shorter taper, curled tips, far-side depth, ear clearance','Hidden scalp coverage cut around visible left ear'],'hair_surfaces':hair_records,'subdivision_levels_added':0,'new_tertiary_details':0,'artistic_status':'Pending visual review'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-03-primary-v0.3.blend'))
print('PRIMARY CORRECTION SAVED',flush=True)
