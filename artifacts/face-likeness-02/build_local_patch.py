from pathlib import Path
import json,collections,numpy as np
from scipy.interpolate import UnivariateSpline
from PIL import Image,ImageDraw
R=Path.cwd();O=R/'artifacts/face-likeness-02';D=json.load(open(O/'baseline.json'));H=D['meshes']['Anime013_Head'];v=np.array(H['vertices']);F=H['faces'];mouth=next(l for l in H['boundary_loops'] if len(l)==32);adj=collections.defaultdict(set)
for f in F:
 for a,b in zip(f,f[1:]+f[:1]):adj[a].add(b);adj[b].add(a)
dist={i:0 for i in mouth};q=collections.deque(mouth)
while q:
 i=q.popleft()
 if dist[i]>=6:continue
 for j in adj[i]:
  if j not in dist:dist[j]=dist[i]+1;q.append(j)
patch_ids=[k for k,f in enumerate(F) if all(dist.get(i,99)<=6 for i in f)];patchF=[F[k] for k in patch_ids];ec=collections.Counter(tuple(sorted((a,b))) for f in patchF for a,b in zip(f,f[1:]+f[:1]));bd=[e for e,n in ec.items() if n==1];ba=collections.defaultdict(set)
for a,b in bd:ba[a].add(b);ba[b].add(a)
outer=set(ba)-set(mouth);assert len(outer)==38
center=np.array([0,1.446197748184204+(222-297)*.0007797915761063738]);S=.0007797915761063738
angles={i:float(np.arctan2((v[i,2]-center[1])/.04,v[i,0]/.05)%(2*np.pi)) for i in outer};order=sorted(outer,key=lambda i:angles[i]);assert all(order[(j+1)%len(order)] in ba[order[j]] for j in range(len(order))), 'Outer patch is not star-shaped'
# Preserve original surrounding topology. Apply only the previously measured broad
# lower-jaw depth shift outside this patch; new patch replaces the failed lip cage.
old_shift=np.array(json.load(open(O/'lower-face-coordinates.json'))['vertices']);co=v.copy()
for i in range(len(co)):
 if i not in {i for f in patchF for i in f} and v[i,2]<1.401:co[i,1]=old_shift[i,1]
for i in outer:
 if v[i,2]<1.401:co[i,1]=old_shift[i,1]
tri=np.array([[f[0],f[k],f[k+1]] for f in F for k in range(1,len(f)-1)]);p=v[tri];xz=p[:,:,[0,2]];d1=xz[:,1]-xz[:,0];d2=xz[:,2]-xz[:,0];den=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0];ok=abs(den)>1e-12;p=p[ok];xz=xz[ok];d1=d1[ok];d2=d2[ok];den=den[ok]
def old_front(x,z):
 d=np.array([x,z])-xz[:,0];u=(d[:,0]*d2[:,1]-d[:,1]*d2[:,0])/den;w=(d1[:,0]*d[:,1]-d1[:,1]*d[:,0])/den;ok=(u>=-1e-6)&(w>=-1e-6)&(u+w<=1+1e-6);ys=p[:,0,1]+u*(p[:,1,1]-p[:,0,1])+w*(p[:,2,1]-p[:,0,1]);return float(ys[ok].min()) if ok.any() else -.08
profile=json.load(open(O/'lower-face-coordinates.json'))['side_constraints'];zz=np.array([1.446197748184204+(222-r['row'])*S for r in profile]);yy=np.array([(r['target_u']-200)*S for r in profile]);ix=np.argsort(zz);curve=UnivariateSpline(zz[ix],yy[ix],s=len(zz)*S*S)
def surface(x,z):
 lower=float(curve(np.clip(z,zz.min(),zz.max())))+15*x*x
 if z<=1.399:return lower
 if z>=1.410:return old_front(x,z)
 a=(z-1.399)/.011;a=a*a*(3-2*a);return lower*(1-a)+old_front(x,z)*a
# Four ordered rings plus 32-point neutral aperture. Replaces a local patch only.
# Resample outer parameter order, keeping every original boundary vertex.
N=32;new=[];rings=[];outer_points=[];thetas=[]
for i in range(N):
 t=i*len(order)/N;j=int(t);a=t-j;point=co[order[j]]*(1-a)+co[order[(j+1)%len(order)]]*a;outer_points.append(point);thetas.append(float(np.arctan2((point[2]-center[1])/.04,point[0]/.05)))
for fraction in [0,.04,.24,.55,.85]:
 ring=[]
 for i,theta in enumerate(thetas):
  inner=np.array([.0156*np.cos(theta),center[1]+.00018*np.sin(theta)]);op=outer_points[i];xzpt=inner*(1-fraction)+op[[0,2]]*fraction;x,z=xzpt;y=surface(x,z);outer_error=op[1]-surface(op[0],op[2]);inner_y=-.093575+15*inner[0]**2;inner_error=inner_y-surface(inner[0],inner[1]);y+=outer_error*fraction**3+inner_error*(1-fraction)**3;ring.append(len(co)+len(new));new.append([float(x),float(y),float(z)])
 rings.append(ring)
# Retain the original nose tip as a real vertex in the nearest upper ring.
nose_candidates=[i for i in range(len(v)) if abs(v[i,0])<.010 and 1.411<v[i,2]<1.426];nose=min(nose_candidates,key=lambda i:v[i,1]);top=max(range(N),key=lambda j:new[rings[-1][j]-len(co)][2]);# Keep the ordered ring projection; source nose depth is sampled by surface().
newF=[]
for a,b in zip(rings,rings[1:]):
 for i in range(N):j=(i+1)%N;newF.append([a[i],b[i],b[j],a[j]])
for j in range(len(order)):
 i=round(j*N/len(order))%N;ni=round((j+1)*N/len(order))%N;a=order[j];b=order[(j+1)%len(order)];newF.append([rings[-1][i],a,b] if i==ni else [rings[-1][i],a,b,rings[-1][ni]])
remaining=[f for k,f in enumerate(F) if k not in set(patch_ids)];allco=co.tolist()+new;allF=remaining+newF;used=sorted({i for f in allF for i in f});remap={old:new for new,old in enumerate(used)};outco=[allco[i] for i in used];outF=[[remap[i] for i in f] for f in allF];assert len(outF)<=len(F)
report={'vertices':outco,'faces':outF,'removed_faces':len(patchF),'new_faces':len(newF),'old_vertices':len(v),'new_vertices':len(outco),'old_faces':len(F),'new_face_count':len(outF),'mouth_loop':[remap[i] for i in rings[0]],'outer_boundary_original':order,'original_to_new':remap,'retained_original_indices':[i for i in used if i<len(v)],'nose_tip_original':v[nose].tolist(),'local_patch_only':True}
(O/'local-patch-payload.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['vertices','faces','original_to_new','retained_original_indices','outer_boundary_original','mouth_loop']},indent=2))
im=Image.new('RGB',(900,750),(25,25,25));dr=ImageDraw.Draw(im)
def pt(i):x,y,z=outco[i];return (450+x*8000,375-(z-center[1])*8000)
for f in newF:
 ids=[remap[i] for i in f];dr.line([pt(i) for i in ids+[ids[0]]],fill=(180,180,180),width=1)
im.save(O/'validation/local-patch-plan.png')
