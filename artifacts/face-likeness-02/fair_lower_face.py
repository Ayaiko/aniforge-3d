from pathlib import Path
import json,numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from scipy.interpolate import PchipInterpolator
R=Path.cwd();O=R/'artifacts/face-likeness-02';D=json.load(open(O/'baseline.json'));H=D['meshes']['Anime013_Head'];v=np.array(H['vertices']);c=v.copy();n=len(v);S=.0007797915761063738;ez=1.446197748184204;mouth=next(l for l in H['boundary_loops'] if len(l)==32);mv=v[mouth];mx=(mv[:,0].min()+mv[:,0].max())/2;mz=(mv[:,2].min()+mv[:,2].max())/2;tz=ez+(222-297)*S
w=np.exp(-((v[:,2]-mz)/.010)**4-((v[:,0]-mx)/.021)**4);fr=np.clip((-v[:,1]-.035)/.025,0,1);w*=fr*fr*(3-2*fr);c[:,0]=mx+(v[:,0]-mx)*(1+.72*w);c[:,2]=v[:,2]+w*((tz-mz)-.70*(v[:,2]-mz))
# A fair depth field, instead of independently advancing each lip and jaw row.
region=(v[:,1]<-.022)&(v[:,2]>1.335)&(v[:,2]<1.435)&(np.abs(v[:,0])<.085);rows=[];cols=[];values=[];mass=np.zeros(n)
for f in H['faces']:
 for k in range(1,len(f)-1):
  ids=[f[0],f[k],f[k+1]]
  if not all(region[i] for i in ids):continue
  p=c[ids][:,[0,2]];twice=abs(np.linalg.det(np.stack([p[1]-p[0],p[2]-p[0]])))
  if twice<1e-12:continue
  for i in ids:mass[i]+=twice/6
  for j in range(3):
   b=(j+1)%3;d=(j+2)%3;cot=np.dot(p[b]-p[j],p[d]-p[j])/twice;wt=cot/2;x,y=ids[b],ids[d];rows.extend([x,y,x,y]);cols.extend([x,y,y,x]);values.extend([wt,wt,-wt,-wt])
L=coo_matrix((values,(rows,cols)),shape=(n,n)).tocsr();B=diags(1/np.sqrt(np.maximum(mass,1e-12)))@L;Q=(B.T@B).tocsc()
profile=json.load(open(O/'lower-face-coordinates.json'))['side_constraints'];z=np.array([ez+(222-x['row'])*S for x in profile]);y=np.array([(x['target_u']-200)*S for x in profile]);order=np.argsort(z);curve=PchipInterpolator(z[order],y[order])
controls=set(mouth);controls.update(i for i in range(n) if abs(c[i,0])<.006 and 1.348<c[i,2]<1.380 and v[i,1]<-.06)
for i in controls:
 c[i,1]=(-.093575 if i in mouth else float(curve(np.clip(c[i,2],z.min(),z.max()))))+20*c[i,0]**2
free=np.array([i for i in range(n) if i not in controls and region[i] and v[i,1]<-.035 and 1.344<v[i,2]<1.406 and abs(v[i,0])<.07 and mass[i]>1e-12]);fixed=np.setdiff1d(np.arange(n),free);A=Q[free][:,free];screen=.005*A.diagonal();rhs=-Q[free][:,fixed]@c[fixed,1]+screen*v[free,1];c[free,1]=spsolve(A+diags(screen),rhs)
oldbad=json.load(open(O/'lower-face-coordinates.json'))['changes'];union=set(int(x[0]) for x in oldbad)|set(np.where(np.linalg.norm(c-v,axis=1)>1e-8)[0]);changes=[[int(i),*c[i].tolist()] for i in sorted(union)];(O/'lower-face-fair-coordinates.json').write_text(json.dumps({'vertices':c.tolist(),'changes':changes,'controls':sorted(controls),'free':free.tolist(),'max_move_m':float(np.linalg.norm(c-v,axis=1).max())},indent=2));print('free',len(free),'controls',len(controls),'maxmove',float(np.linalg.norm(c-v,axis=1).max()))
code='import bpy,json\nh=bpy.data.objects["Anime013_Head"]\nchanges='+repr(changes)+'\nfor entry in changes:h.data.vertices[entry[0]].co=entry[1:]\nh.data.update()\nbpy.context.view_layer.update()\nprint(json.dumps({"changed":len(changes),"stage":"fair-lower-face"}))'
req=[{'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'apply-fair-lower-face'}]
for view in ['front','side','quarter']:
 code="import bpy\ns=bpy.context.scene\ns.camera=bpy.data.objects['REF_"+view+"']\ns.render.filepath="+repr(str(O/'validation'/f'lower-fair-{view}.png'))+"\nassert bpy.ops.render.render(write_still=True)=={'FINISHED'}\nprint('FAIR_"+view+"')";req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'render-fair-'+view})
code="import bpy\nbpy.context.scene.camera=bpy.data.objects['REF_quarter']\nbpy.ops.wm.save_as_mainfile(filepath="+repr(str(R/'models/face-likeness-02/lower-face-fair-trial.blend'))+",copy=True)\nprint('SAVED')";req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'save-lower-fair'})
(O/'live-mcp/lower-fair-request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2))
