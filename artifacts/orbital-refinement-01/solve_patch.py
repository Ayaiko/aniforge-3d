from pathlib import Path
import json,collections
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
O=Path('artifacts/orbital-refinement-01');d=json.load(open(O/'head-before.json'));v=np.array(d['vertices']);n=len(v);adj=collections.defaultdict(set)
for a,b in d['edges']:adj[a].add(b);adj[b].add(a)
loops=[l for l in d['boundary_loops'] if len(l)==24];distance={i:0 for l in loops for i in l};q=collections.deque(distance)
while q:
 i=q.popleft()
 if distance[i]>=6:continue
 for j in adj[i]:
  if j not in distance:distance[j]=distance[i]+1;q.append(j)
region=(v[:,1]<-.025)&(np.abs(v[:,0])<.090)&(v[:,2]>1.395)&(v[:,2]<1.505)
# Cotangent thin-plate energy in the locked front parameterization. This handles
# irregular ring spacing; uniform neighbour averaging does not preserve slopes.
rows=[];cols=[];vals=[];mass=np.zeros(n)
for f in d['faces']:
 for k in range(1,len(f)-1):
  tri=[f[0],f[k],f[k+1]]
  if not all(region[i] for i in tri):continue
  p=v[tri][:,[0,2]];twice=abs(np.linalg.det(np.stack([p[1]-p[0],p[2]-p[0]])))
  if twice<1e-12:continue
  for i in tri:mass[i]+=twice/6
  for a in range(3):
   b=(a+1)%3;c=(a+2)%3;cot=np.dot(p[b]-p[a],p[c]-p[a])/twice;w=cot/2;i,j=tri[b],tri[c]
   rows.extend([i,j,i,j]);cols.extend([i,j,j,i]);vals.extend([w,w,-w,-w])
L=coo_matrix((vals,(rows,cols)),shape=(n,n)).tocsr();B=diags(1/np.sqrt(np.maximum(mass,1e-12)))@L
free=np.array([i for i in range(n) if region[i] and 0<distance.get(i,99)<4 and .013<abs(v[i,0])<.065 and v[i,2]>1.428 and v[i,2]<1.477 and all(region[j] for j in adj[i])],dtype=int)
Q=(B.T@B).tocsc();fixed=np.setdiff1d(np.arange(n),free);A=Q[free][:,free];b=-Q[free][:,fixed]@v[fixed,1]
# Small screening retains the authored orbital volume while allowing a fair transition.
screen=.10*A.diagonal();A=A+diags(screen);b=b+screen*v[free,1]
y=spsolve(A,b);delta=y-v[free,1]
print('free',len(free),'range millimetres',float(delta.min()*1000),float(delta.max()*1000))
for strength in [.35,.70,1.0]:
 co=v.copy();co[free,1]+=delta*strength
 name='fair-'+str(round(strength*100));(O/(name+'-coordinates.json')).write_text(json.dumps({'vertices':co.tolist(),'free_indices':free.tolist(),'max_move_m':float(np.abs(delta*strength).max()),'method':'screened cotangent thin-plate depth fairing with fixed aperture and outer anchors'},indent=2))
print([(int(i),round(float(delta[k]*1000),3)) for k,i in enumerate(free) if abs(delta[k])>.003])
