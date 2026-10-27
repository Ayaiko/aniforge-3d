"""Authored reference-fit quad-cage prototype. No Rain/Snow coordinates or connectivity loaded."""
import numpy as np,json,math
from pathlib import Path
from scipy.interpolate import PchipInterpolator
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
P=Path(__file__).resolve().parent;S=.0007797915761063738;EZ=1.446197748184204
# Our plate landmarks; covered skull/ear/neck mass is an explicitly provisional inference.
width=PchipInterpolator([45,60,90,130,180,210,240,260,280,300,320,340,345,350,360,372],[.006,.028,.060,.076,.080,.079,.075,.067,.056,.044,.028,.011,.009,.024,.025,.025])
central=PchipInterpolator([45,60,90,130,180,210,230,240,250,257,265,276,283,290,297,305,320,340,345,350,360,372],[-.005,-.029,-.052,-.067,-.075,-.076,-.080,-.088,-.106,-.114,-.108,-.100,-.094,-.092,-.0905,-.090,-.087,-.082,-.080,-.024,-.023,-.022])
cheek=PchipInterpolator([45,60,90,130,180,210,240,260,280,297,320,340,345,350,360,372],[-.005,-.029,-.052,-.067,-.075,-.074,-.073,-.075,-.080,-.0905,-.087,-.082,-.080,-.024,-.023,-.022])
back=PchipInterpolator([45,60,90,130,180,210,240,260,280,300,320,340,345,350,360,372],[.012,.040,.071,.086,.090,.086,.079,.068,.052,.040,.031,.028,.028,.028,.028,.028])
vs=np.arange(60,373,6,dtype=float);M=len(vs);N=64
holes=[{'name':'eye_L','c0':6,'c1':14,'r0':26,'r1':30,'cx':-.0395,'v':224.5,'ax':[.025,.029],'az':[.0065,.0105],'sign':-1}, {'name':'eye_R','c0':18,'c1':26,'r0':26,'r1':30,'cx':.0395,'v':224.5,'ax':[.025,.029],'az':[.0065,.0105],'sign':1},{'name':'mouth','c0':12,'c1':20,'r0':38,'r1':40,'cx':0.,'v':297.,'ax':[.0156,.020,.027],'az':[.00030,.0038,.0100],'sign':0}]
keep=set((r,c) for r in range(M) for c in range(N))
for h in holes:
 for r in range(h['r0']+1,h['r1']):
  for c in range(h['c0']+1,h['c1']):keep.discard((r,c))
def coords(v,theta):
 lift=.008*np.exp(-((v-340)/22)**2)*np.sin(theta)**2
 z=EZ+(222-v)*S+lift
 actual=222-(z-EZ)/S
 wf=float(width(np.clip(actual,45,372)))
 x=wf*np.sin(theta)
 if np.cos(theta)>=-1e-8:
  u=abs(np.sin(theta));y=float(cheek(actual))+(float(central(actual))-float(cheek(actual)))*np.exp(-(x/.010)**2)
  y+=(.012-float(cheek(actual)))*(1-max(0,1-u**6)**(1/6))
  # Two orbital masses, independent of any production-example head proportions.
  y-=.0105*(np.exp(-((x-.0395)/.026)**4)+np.exp(-((x+.0395)/.026)**4))*np.exp(-((actual-224.5)/19)**4)
 else:y=.012+(float(back(np.clip(actual,45,372)))-.012)*(-np.cos(theta))
 # Very simple connected ear volumes only, no folds/details in this topology trial.
 ear=np.exp(-((actual-234)/20)**4)*np.exp(-((abs(theta)-np.pi/2)/.20)**4)
 x+=np.sign(x)*.009*ear
 return [x,y,z]
keys=sorted(keep);ids={k:i for i,k in enumerate(keys)};a=np.array([coords(vs[r],-np.pi/2+c*2*np.pi/N) for r,c in keys]);initial=a.copy();fixed={}
# Fixed side seams/top/bottom; harmonic displacement changes only the facial parameter grid.
front=[k for k in keys if k[1]<=32]
for r,c in front:
 if c in (0,32) or r in (0,M-1):fixed[(r,c)]=a[ids[(r,c)]][[0,2]].copy()
def rect_loop(r0,r1,c0,c1):
 return [(r0,c) for c in range(c0,c1)]+[(r,c1) for r in range(r0,r1)]+[(r1,c) for c in range(c1,c0,-1)]+[(r,c0) for r in range(r1,r0,-1)]
for h in holes:
 h['loops']=[]
 for j in range(len(h['ax'])):
  r0,r1,c0,c1=h['r0']-j,h['r1']+j,h['c0']-j,h['c1']+j
  ring=rect_loop(r0,r1,c0,c1);h['loops'].append(ring)
  for r,c in ring:
   phi=np.arctan2(((r0+r1)/2-r)/((r1-r0)/2),(c-(c0+c1)/2)/((c1-c0)/2))
   xx=h['cx']+h['ax'][j]*np.cos(phi);zz=EZ+(222-h['v'])*S+h['az'][j]*np.sin(phi)+h['sign']*.0014*np.cos(phi)
   if h['name']=='mouth':zz=EZ+(222-h['v'])*S+h['az'][j]*np.sin(phi)
   if (r,c) in fixed:raise RuntimeError(('Constraint collision',h['name'],j,r,c))
   fixed[(r,c)]=np.array([xx,zz])
free=[k for k in front if k not in fixed];fi={k:i for i,k in enumerate(free)};A=lil_matrix((len(free),len(free)));rhs=np.zeros((len(free),2))
for k in free:
 r,c=k;ns=[q for q in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)] if q in ids and q[1]<=32];i=fi[k];A[i,i]=len(ns)
 for q in ns:
  if q in fi:A[i,fi[q]]=-1
  else:rhs[i]+=fixed[q]-a[ids[q]][[0,2]]
dis=spsolve(A.tocsr(),rhs)
for k,i in fi.items():a[ids[k],0]+=dis[i,0];a[ids[k],2]+=dis[i,1]
for k,xz in fixed.items():a[ids[k],0]=xz[0];a[ids[k],2]=xz[1]
# Re-evaluate depth after planar layout fitting; preserve fixed camera coordinate contract.
for r,c in front:
 i=ids[(r,c)];x,y,z=a[i];v=222-(z-EZ)/S;w=max(.003,float(width(np.clip(v,45,372))));u=min(.999999,abs(x)/w)
 y=float(cheek(np.clip(v,45,372)))+(float(central(np.clip(v,45,372)))-float(cheek(np.clip(v,45,372))))*np.exp(-(x/.010)**2)
 y+=(.012-float(cheek(np.clip(v,45,372))))*(1-max(0,1-u**6)**(1/6))
 y-=.0105*(np.exp(-((x-.0395)/.026)**4)+np.exp(-((x+.0395)/.026)**4))*np.exp(-((v-224.5)/19)**4)
 a[i,1]=y
for h in holes[:2]:
 for j,ring in enumerate(h['loops']):
  for k in ring:
   i=ids[k];x,y,z=a[i]
   if j==0:a[i,1]=-.082+2.0*(x-h['cx'])**2
verts=a.tolist();faces=[]
for r in range(M-1):
 for c in range(N):
  n=(c+1)%N
  if any(h['r0']<=r<h['r1'] and h['c0']<=c<h['c1'] for h in holes):continue
  ks=[(r,c),(r+1,c),(r+1,n),(r,n)]
  if all(k in ids for k in ks):faces.append([ids[k] for k in ks])
# Rim thickness and attached mouth bag. No floating cavity object is substituted for lip geometry.
for h in holes:
 outer=[ids[k] for k in h['loops'][0]];prev=outer
 depths=[.0018] if h['name'].startswith('eye') else [.003,.012]
 center=np.array([h['cx'],-.082,EZ+(222-h['v'])*S])
 for j,depth in enumerate(depths):
  new=[]
  for ii in outer:
   p=np.array(verts[ii]);p[1]+=depth
   if h['name'].startswith('eye'):p[0]=center[0]+(p[0]-center[0])*.985;p[2]=center[2]+(p[2]-center[2])*.985
   else:p[2]=center[2]+(p[2]-center[2])*(3 if j==0 else 12)
   new.append(len(verts));verts.append(p.tolist())
  for k in range(len(prev)):faces.append([prev[k],prev[(k+1)%len(prev)],new[(k+1)%len(prev)],new[k]])
  prev=new
 if h['name']=='mouth':
  # A 8x2 quad patch closes the bag; interior poles avoided.
  boundary=rect_loop(0,2,0,8);grid=dict(zip(boundary,prev))
  for c in range(1,8):
   p=(np.array(verts[grid[(0,c)]])+np.array(verts[grid[(2,c)]]))*.5;p[1]+=.004;grid[(1,c)]=len(verts);verts.append(p.tolist())
  for r in range(2):
   for c in range(8):faces.append([grid[(r,c)],grid[(r,c+1)],grid[(r+1,c+1)],grid[(r+1,c)]])
# All-quad crown disk with 64 shared boundary vertices; remaining boundary is the intended neck exit.
B=16;ring=[ids[(0,c)] for c in range(N)];grid={};boundary=rect_loop(0,B,0,B)
# Ring starts at theta=-pi/2. Align square perimeter order with existing ring; Coons interpolation interior.
for k,key in enumerate(boundary):grid[key]=ring[k]
for r in range(1,B):
 for c in range(1,B):
  u=c/B;v=r/B
  top=np.array(verts[grid[(0,c)]]);bottom=np.array(verts[grid[(B,c)]]);left=np.array(verts[grid[(r,0)]]);right=np.array(verts[grid[(r,B)]])
  p=(1-v)*top+v*bottom+(1-u)*left+u*right-((1-u)*(1-v)*np.array(verts[grid[(0,0)]])+u*(1-v)*np.array(verts[grid[(0,B)]])+(1-u)*v*np.array(verts[grid[(B,0)]])+u*v*np.array(verts[grid[(B,B)]]))
  p[2]+=.012*np.sin(np.pi*u)*np.sin(np.pi*v);grid[(r,c)]=len(verts);verts.append(p.tolist())
for r in range(B):
 for c in range(B):faces.append([grid[(r,c)],grid[(r,c+1)],grid[(r+1,c+1)],grid[(r+1,c)]])
# Remove unused vertices and keep named loop groups after indexing.
used=sorted(set(i for f in faces for i in f));remap={old:i for i,old in enumerate(used)}
out={'vertices':[verts[i] for i in used],'faces':[[remap[i] for i in f] for f in faces],'groups':{h['name']+'_rim':[remap[ids[k]] for k in h['loops'][0]] for h in holes},'method':'Authored full symmetric cylindrical quad cage with harmonic face layout, loops constrained to our front/side plates. Production examples are structure references only. Skull and ear shapes are provisional.'}
(P/'clean-cage-data.json').write_text(json.dumps(out));print('CLEAN_CAGE',len(out['vertices']),len(out['faces']))
