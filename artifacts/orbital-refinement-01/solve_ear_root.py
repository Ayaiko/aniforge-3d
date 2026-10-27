import json
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
O=Path('artifacts/orbital-refinement-01');d=json.load(open(O/'head-before.json'));v=np.array(json.load(open(O/'fair-70-coordinates.json'))['vertices']);n=len(v)
free=np.array([i for i in range(n) if i>=600 and .074<abs(v[i,0])<.087 and -.012<v[i,1]<.065 and 1.47<v[i,2]<1.49])
r=[];c=[];w=[];mass=np.zeros(n)
for f in d['faces']:
 for k in range(1,len(f)-1):
  ids=[f[0],f[k],f[k+1]];p=v[ids];a=np.linalg.norm(np.cross(p[1]-p[0],p[2]-p[0]))
  if a<1e-12:continue
  for i in ids:mass[i]+=a/6
  for j in range(3):
   l=(j+1)%3;m=(j+2)%3;cot=np.dot(p[l]-p[j],p[m]-p[j])/a;wt=cot/2;x,y=ids[l],ids[m];r.extend([x,y,x,y]);c.extend([x,y,y,x]);w.extend([wt,wt,-wt,-wt])
L=coo_matrix((w,(r,c)),shape=(n,n)).tocsr();B=diags(1/np.sqrt(np.maximum(mass,1e-12)))@L;Q=(B.T@B).tocsc();fixed=np.setdiff1d(np.arange(n),free);A=Q[free][:,free];screen=.1*A.diagonal();A=A+diags(screen);b=-Q[free][:,fixed]@v[fixed]+screen[:,None]*v[free];target=np.column_stack([spsolve(A,b[:,k]) for k in range(3)])
delta=target-v[free];print('free',free.tolist(),'moves_mm',np.round(np.linalg.norm(delta,axis=1)*1000,3).tolist())
for pct in [50,100]:
 co=v.copy();co[free]+=delta*(pct/100);(O/f'ear-root-{pct}-coordinates.json').write_text(json.dumps({'vertices':co.tolist(),'indices':free.tolist(),'max_move_m':float(np.linalg.norm(delta,axis=1).max()*pct/100),'method':'Local 3D cotangent thin-plate root fairing; ear shell and surrounding skull fixed'},indent=2))
