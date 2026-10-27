"""New reference-profile head surface and feature loops. No legacy mesh reuse.
Direct quad modeling from authored front/side sections; no head primitives,
subdivision, noise, hair, rig or texturing.
"""
from pathlib import Path
import sys,json,math,hashlib,shutil
import bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT
revision='002' if '--patch-rebuild' in sys.argv else '001'
out=ROOT/('previews/reconstruction-v2/head-'+revision);out.mkdir(parents=True,exist_ok=True)
models=ROOT/'models/reconstruction-v2';models.mkdir(exist_ok=True)
legacy=ROOT/'models/legacy-baseline-v2-start';legacy.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
legacy_files={}
for name in ['researcher-a.blend','researcher-a-master-v0.2.blend','researcher-a-reconstruction-master-v0.3.blend','researcher-a-hair-guides-v0.5.blend']:
    p=ROOT/'models'/name;legacy_files[str(p.relative_to(ROOT))]={'sha256':sha(p),'bytes':p.stat().st_size}
source=ROOT/'models/researcher-a-reconstruction-master-v0.3.blend';backup=legacy/'researcher-a-legacy-master.blend'
if not backup.exists():shutil.copy2(source,backup)
assert sha(backup)==sha(source)
(legacy/'manifest.json').write_text(json.dumps({'status':'Legacy frozen; V2 head is new geometry','files':legacy_files},indent=2))
for p in ['assets/concepts/researcher-a-refined-v3.png','assets/references/researcher-a-turnaround-v3.png','assets/references/researcher-a-expressions-v3.png']:
    assert (ROOT/p).exists()
cal=json.loads((ROOT/'previews/v0.3/reference-calibration.json').read_text());S=cal['meters_per_reference_pixel'];EYE=cal['eye_z']
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=['REF_front','REF_side','REF_quarter','REF_back']
for ob in dst.objects:bpy.context.scene.collection.objects.link(ob)
scene=bpy.context.scene;scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('V2 Clay Studio');scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.16,.17,.19,1);bg.inputs['Strength'].default_value=.45
def material(name,col):
    m=bpy.data.materials.new(name);p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=.8;m.diffuse_color=(*col,1);return m
skinmat=material('V2 Clay / skin',(.32,.30,.28));white=material('V2 Clay / sclera',(.60,.61,.61));iris=material('V2 Clay / iris',(.10,.12,.13));pupil=material('V2 Clay / pupil',(.025,.027,.03));cavity=material('V2 Clay / mouth depth',(.075,.07,.07))
for name,loc,power,size in [('Key',(-.34,-.44,1.80),8,.35),('Fill',(.36,-.12,1.52),2,.30),('Rim',(.1,.35,1.80),5,.30)]:
    light=bpy.data.lights.new('V2_'+name,'AREA');light.energy=power;light.shape='DISK';light.size=size;ob=bpy.data.objects.new('V2_'+name,light);scene.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,1.45))-ob.location).to_track_quat('-Z','Y').to_euler()
def make(name,vertices,faces,mat):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update();ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);data.materials.append(mat)
    for p in data.polygons:p.use_smooth=True
    bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free();return ob
def interp(v,pairs):
    xs=np.array([p[0] for p in pairs],dtype=float);ys=np.array([p[1] for p in pairs],dtype=float)
    if revision=='001':return float(np.interp(v,xs,ys))
    if v<=xs[0]:return float(ys[0])
    if v>=xs[-1]:return float(ys[-1])
    sec=np.diff(ys)/np.diff(xs);m=np.zeros(len(xs));m[0]=sec[0];m[-1]=sec[-1]
    for j in range(1,len(xs)-1):m[j]=2*sec[j-1]*sec[j]/(sec[j-1]+sec[j]) if sec[j-1]*sec[j]>0 else 0
    j=int(np.searchsorted(xs,v)-1);h=xs[j+1]-xs[j];t=(v-xs[j])/h
    return float((2*t**3-3*t*t+1)*ys[j]+(t**3-2*t*t+t)*h*m[j]+(-2*t**3+3*t*t)*ys[j+1]+(t**3-t*t)*h*m[j+1])
def z_of(v):return EYE-(v-222)*S
def v_of(z):return 222-(z-EYE)/S
WIDTH=[(27,0),(35,22),(50,52),(75,81),(100,95),(125,105),(150,110),(175,104),(200,94),(220,89),(240,87),(260,84),(275,76),(290,67),(300,58),(310,50),(320,38),(330,25),(340,12),(345,2)]
FRONT=[(27,200),(35,185),(50,145),(75,120),(100,108),(125,99),(150,94),(175,91),(200,91),(215,96),(230,98),(245,99),(260,100),(275,98),(290,91),(300,90),(310,89),(320,92),(332,94),(345,100)]
PROFILE=[(220,96),(230,92),(240,82),(250,61),(258,53),(265,59),(275,69),(283,75),(290,82),(296,82),(300,87),(305,83),(310,87),(320,92),(345,100)]
BACK=[(27,200),(35,240),(50,270),(75,300),(100,316),(130,332),(170,342),(210,344),(250,340),(280,328),(310,302),(345,268)]
def g(x,c,r):return math.exp(-((x-c)/r)**2)
def bez(points,t):return (1-t)**3*Vector(points[0])+3*(1-t)**2*t*Vector(points[1])+3*(1-t)*t*t*Vector(points[2])+t**3*Vector(points[3])
eyes=[{'id':'viewer_left','cx':146,'cy':224,'top':[(120,216),(134,211),(155,212),(168,223)],'bottom':[(120,216),(133,232),(152,233),(168,223)]}, {'id':'viewer_right','cx':249,'cy':220,'top':[(225,222),(236,212),(257,208),(274,212)],'bottom':[(225,222),(239,234),(263,229),(274,212)]}]
def globe_front(x,z,e):
    cx=(e['cx']-200)*S;cz=z_of(e['cy']);q=((x-cx)/.0225)**2+((z-cz)/.0185)**2
    return -.0565-.0205*math.sqrt(max(0,1-q))
def front_y(x,v,cosine=None):
    w=max(.001,interp(v,WIDTH)*S);c=math.sqrt(max(0,1-min(.999999,abs(x)/w)**2)) if cosine is None else max(0,cosine);f=((c+.05)**.45-.05**.45)/(1.05**.45-.05**.45)
    base=(interp(v,FRONT)-200)*S;cy=.012;y=cy+(base-cy)*f
    if 220<v<320:
        target=(interp(v,PROFILE)-200)*S;delta=min(0,target-base);r=(interp(v,[(220,6),(240,7),(258,11),(278,13),(295,23),(307,22),(320,23)]))*S
        y+=delta*math.exp(-abs(x/max(.001,r))**2.4)
    y-=.0028*g(abs(x),.040,.020)*g(v,260,26)
    # Skin outside the aperture must cover the physical globe, not intersect it.
    for e in eyes:
        cx=(e['cx']-200)*S;cz=z_of(e['cy']);q=((x-cx)/.0225)**2+((z_of(v)-cz)/.0185)**2
        if q<1:y=min(y,globe_front(x,z_of(v),e)-.0011)
    return y

# A reference-section cage, not a scaled sphere. Jaw section height is lifted
# toward the back, then joined to an under-jaw/neck transition.
nc=128;vertical=np.linspace(35,345,125);vs=[];fs=[];uvs=[]
for j,v in enumerate(vertical):
    w=interp(v,WIDTH)*S;bottom=max(0,min(1,(v-275)/70));bottom=bottom*bottom*(3-2*bottom)
    for k in range(nc):
        theta=-math.pi+2*math.pi*k/nc;s=math.sin(theta);c=math.cos(theta)
        radius=w+(.032-w)*bottom*(s*s);x=radius*s;z=z_of(v)+.050*bottom*(1-c)/2
        if c>=0:y=front_y(x,v,c if revision=='002' else None)
        else:y=.012+((interp(v,BACK)-200)*S-.012)*(-c)
        vs.append((x,y,z));uvs.append((k/nc,j/(len(vertical)-1)))
for j in range(len(vertical)-1):
    for k in range(nc):
        f=(j*nc+k,j*nc+(k+1)%nc,(j+1)*nc+(k+1)%nc,(j+1)*nc+k);p=sum((Vector(vs[i]) for i in f),Vector())/4;u=200+p.x/S;v=v_of(p.z)
        front=p.y<.015
        hole=front and (any(((u-e['cx'])/31)**2+((v-e['cy'])/18)**2<1 for e in eyes) or ((u-200)/27)**2+((v-298)/10)**2<1)
        if not hole:fs.append(f)
top=len(vs);vs.append((0,.012,z_of(27)));uvs.append((.5,0))
for k in range(nc):fs.append((top,(k+1)%nc,k))
last=[Vector(vs[(len(vertical)-1)*nc+k]) for k in range(nc)]
for row in range(1,9):
    t=row/8
    for k in range(nc):
        theta=-math.pi+2*math.pi*k/nc;target=Vector((.032*math.sin(theta),.012-.038*math.cos(theta),1.292))
        p=last[k].lerp(target,t) if revision=='001' else Vector((target.x,target.y,1.342-.050*(row-1)/7))
        vs.append(tuple(p));uvs.append((k/nc,1+.20*t))
    start=len(vs)-nc;previous=(len(vertical)-1)*nc if row==1 else start-nc
    for k in range(nc):fs.append((previous+k,previous+(k+1)%nc,start+(k+1)%nc,start+k))
center=len(vs);vs.append((0,.012,1.292));uvs.append((.5,1.2))
start=center-nc
for k in range(nc):fs.append((center,start+k,start+(k+1)%nc))
used=sorted({i for f in fs for i in f});mapping={old:i for i,old in enumerate(used)};vs=[vs[i] for i in used];uvs=[uvs[i] for i in used];fs=[tuple(mapping[i] for i in f) for f in fs]

from collections import Counter,defaultdict
counts=Counter(tuple(sorted((f[i],f[(i+1)%len(f)]))) for f in fs for i in range(len(f)));graph=defaultdict(list)
for (a,b),n in counts.items():
    if n==1:graph[a].append(b);graph[b].append(a)
loops=[];visited=set()
for seed in graph:
    if seed in visited:continue
    seq=[];previous=None;current=seed
    for i in range(2000):
        visited.add(current);seq.append(current);nxt=[a for a in graph[current] if a!=previous]
        if not nxt or nxt[0]==seed:break
        previous,current=current,nxt[0]
    loops.append(seq)
features=[]
for seq in loops:
    center=sum((Vector(vs[i]) for i in seq),Vector())/len(seq);u=200+center.x/S;v=v_of(center.z);mouth=v>270
    e=None if mouth else min(eyes,key=lambda e:abs(e['cx']-u));cx=200 if mouth else e['cx'];cv=298 if mouth else e['cy'];rx=30 if mouth else 33;rz=13 if mouth else 21
    angles=[math.atan2((v_of(vs[i][2])-cv)/(10 if mouth else 18),(200+vs[i][0]/S-cx)/(27 if mouth else 31)) for i in seq]
    previous_ring=seq
    for row,blend in enumerate([0,.32,.63,1,1]):
        ring=[]
        for i,angle in enumerate(angles):
            outer=Vector((cx+rx*math.cos(angle),cv+rz*math.sin(angle)))
            t=(math.cos(angle)+1)/2
            if mouth:
                upper=[(180,298),(192,296.7),(208,296),(220,296)];lower=[(180,298),(192,298.6),(209,298.1),(220,296)]
                inner=bez(upper if math.sin(angle)<0 else lower,t)
            else:inner=bez(e['top'] if math.sin(angle)<0 else e['bottom'],t)
            if revision=='002':outer=Vector((200+vs[seq[i]][0]/S,v_of(vs[seq[i]][2])))
            q=outer.lerp(inner,blend);x=(q.x-200)*S;z=z_of(q.y);y=front_y(x,q.y)
            if not mouth:
                sphere_y=globe_front(x,z,e);y=(1-blend)*y+blend*(sphere_y-.0012)
                if row==2:y-=.00035 if revision=='002' else .0007
                if row==4:y+=.0008 if revision=='002' else .0018
            else:
                if row in [1,2]:y-=.0012*math.sin(math.pi*blend)
                if row==4:y+=.004
            pos=(x,y,z)
            if row==0:
                idx=seq[i]
                if revision=='001':vs[idx]=pos
            else:idx=len(vs);vs.append(pos);uvs.append((.5+x/.30,.70-(q.y-222)/450))
            ring.append(idx)
        if row>0:
            for i in range(len(seq)):fs.append((previous_ring[i],previous_ring[(i+1)%len(seq)],ring[(i+1)%len(seq)],ring[i]))
        previous_ring=ring
    if mouth:
        p=sum((Vector(vs[i]) for i in previous_ring),Vector())/len(previous_ring);p.y+=.012;idx=len(vs);vs.append(tuple(p));uvs.append((.5,.5))
        for i in range(len(seq)):fs.append((previous_ring[i],previous_ring[(i+1)%len(seq)],idx))
    features.append({'part':'mouth' if mouth else e['id'],'outer_loop_vertices':len(seq),'concentric_rings':5,'opening_indices':previous_ring,'landmark_opening_pixels':[[200+vs[i][0]/S,v_of(vs[i][2])] for i in previous_ring]})
head=make('V2_Head_Skin_NEW',vs,fs,skinmat);head['construction']='New reference-section quad skin with explicit socket/lid/lip rings; no legacy mesh, subdivision or primitive operators';head['stage']='Primary head/face direct-modeled sculpt base';head['feature_loops']=json.dumps(features)
uv=head.data.uv_layers.new(name='Sculpt preparation UV')
for p in head.data.polygons:
    for li in p.loop_indices:
        i=head.data.loops[li].vertex_index;u,v=uvs[i];uv.data[li].uv=(u,v/1.20)

def eye_sphere(e):
    cx=(e['cx']-200)*S;cz=z_of(e['cy']);nv=64;nr=32;vs=[(cx,-.0565,cz+.0185)];faces=[]
    for j in range(1,nr):
        phi=math.pi*j/nr
        for k in range(nv):
            a=2*math.pi*k/nv;vs.append((cx+.0225*math.sin(phi)*math.cos(a),-.0565+.0205*math.sin(phi)*math.sin(a),cz+.0185*math.cos(phi)))
    low=len(vs);vs.append((cx,-.0565,cz-.0185))
    for k in range(nv):faces.extend([(0,1+k,1+(k+1)%nv),(low,low-nv+(k+1)%nv,low-nv+k)])
    for j in range(nr-2):
        for k in range(nv):
            a=1+j*nv+k;b=1+j*nv+(k+1)%nv;faces.append((a,a+nv,b+nv,b))
    # Real iris aperture avoids buried disc/white z-fighting.
    faces=[f for f in faces if not (sum(vs[i][1] for i in f)/len(f)<-.0565 and sum(((vs[i][0]-cx)/.0083)**2+((vs[i][2]-cz)/.0083)**2 for i in f)/len(f)<1)]
    return make('V2_Eyeball_'+e['id'],vs,faces,white)
for e in eyes:
    eye_sphere(e);cx=(e['cx']-200)*S;cz=z_of(e['cy']);verts=[];faces=[]
    for j in range(8):
        radius=.00015+(.0087-.00015)*j/7
        for k in range(64):
            a=2*math.pi*k/64;x=cx+radius*math.cos(a);z=cz+radius*math.sin(a);verts.append((x,globe_front(x,z,e)-.0006,z))
    for j in range(7):
        for k in range(64):a=j*64+k;b=j*64+(k+1)%64;faces.append((a,b,b+64,a+64))
    make('V2_Iris_'+e['id'],verts,faces,iris)
    verts=[(cx,globe_front(cx,cz,e)-.0011,cz)];faces=[]
    for k in range(64):
        a=2*math.pi*k/64;x=cx+.0031*math.cos(a);z=cz+.0031*math.sin(a);verts.append((x,globe_front(x,z,e)-.0011,z))
    for k in range(64):faces.append((0,k+1,(k+1)%64+1))
    make('V2_Pupil_'+e['id'],verts,faces,pupil)

# New pinna surfaces with a raised helix and recessed concha, not flat ear cards.
ear_outline=[(220,205),(234,213),(245,229),(240,248),(228,262),(215,266),(207,252),(209,229)]
def smooth_closed(points,t):
    n=len(points);q=t*n;i=int(q)%n;u=q-int(q);a,b,c,d=[Vector(points[k%n]) for k in [i-1,i,i+1,i+2]];return .5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
for sign,label in [(-1,'R'),(1,'L')]:
    vv=[];ff=[];n=64;center=Vector((224,238));levels=[(.12,.072),(.38,.074),(.67,.079),(.86,.088),(1,.079)]
    for radius,x in levels:
        for k in range(n):
            p=center.lerp(smooth_closed(ear_outline,k/n),radius);xx=x
            if revision=='002':xx=.068+.010*max(0,math.sin(math.pi*(p.y-205)/61))**.7+(x-.075)*.7
            vv.append((sign*xx,(p.x-200)*S,z_of(p.y)))
    for j in range(len(levels)-1):
        for k in range(n):a=j*n+k;b=j*n+(k+1)%n;ff.append((a,b,b+n,a+n))
    ic=len(vv);vv.append((sign*.071,24*S,z_of(238)))
    for k in range(n):ff.append((ic,k,(k+1)%n))
    back=len(vv)
    for k in range(n):p=smooth_closed(ear_outline,k/n);vv.append((sign*.069,(p.x-200)*S,z_of(p.y)))
    bc=len(vv);vv.append((sign*.068,24*S,z_of(238)))
    for k in range(n):a=(len(levels)-1)*n+k;b=(len(levels)-1)*n+(k+1)%n;ff.extend([(a,b,back+(k+1)%n,back+k),(bc,back+k,back+(k+1)%n)])
    make('V2_Ear_'+label,vv,ff,skinmat)

scene['V2_status']='Head/face milestone only. New geometry. Artistic review pending. No hair/clothing/rig/texture.'
for view in ['front','side','quarter','back']:
    scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(out/('clay-'+view+'.png'));bpy.ops.render.render(write_still=True)
# Single-material studio inspection, separate from neutral eye values above.
scene.view_layers[0].material_override=skinmat
for view in ['front','side','quarter']:
    scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(out/('single-clay-'+view+'.png'));bpy.ops.render.render(write_still=True)
scene.view_layers[0].material_override=None;scene.camera=bpy.data.objects['REF_quarter']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_overlays=False;space.region_3d.view_perspective='CAMERA';space.camera=scene.camera
meshes={}
for ob in bpy.data.objects:
    if ob.type=='MESH':meshes[ob.name]={'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'triangles':sum(len(p.vertices)-2 for p in ob.data.polygons),'quads':sum(len(p.vertices)==4 for p in ob.data.polygons),'modifiers':[m.type for m in ob.modifiers]}
(out/'geometry-statistics.json').write_text(json.dumps({'meshes':meshes,'new_geometry':True,'legacy_mesh_imports':0,'subdivision_levels_added':0,'features':features,'reference_front_width_samples':WIDTH,'reference_side_base_samples':FRONT,'reference_nose_lip_chin_samples':PROFILE,'legacy_hashes':legacy_files},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(models/('researcher-a-head-'+revision+'.blend')))
for p,h in legacy_files.items():assert sha(ROOT/p)==h['sha256']
print('NEW V2 HEAD SAVED',sum(m['vertices'] for m in meshes.values()),sum(m['triangles'] for m in meshes.values()),'LOOPS',[(f['part'],f['outer_loop_vertices']) for f in features],flush=True)
