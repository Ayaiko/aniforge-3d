from pathlib import Path
import json,numpy as np
from scipy.optimize import least_squares
from scipy.interpolate import UnivariateSpline
R=Path.cwd();O=R/'artifacts/face-likeness-02';D=json.load(open(O/'baseline.json'));H=D['meshes']['Anime013_Head'];v=np.array(H['vertices']);c=v.copy();S=.0007797915761063738;ez=1.446197748184204;mouth=next(l for l in H['boundary_loops'] if len(l)==32);mv=v[mouth];mx=(mv[:,0].min()+mv[:,0].max())/2;mz=(mv[:,2].min()+mv[:,2].max())/2;tz=ez+(222-297)*S
fr=np.clip((-v[:,1]-.035)/.025,0,1);w=np.exp(-((v[:,2]-mz)/.010)**4-((v[:,0]-mx)/.021)**4)*fr*fr*(3-2*fr);c[:,0]=mx+(v[:,0]-mx)*(1+.72*w);c[:,2]=v[:,2]+w*((tz-mz)-.70*(v[:,2]-mz))
tri=np.array([[f[0],f[k],f[k+1]] for f in H['faces'] for k in range(1,len(f)-1)]);p=c[tri];xz=p[:,:,[0,2]];d1=xz[:,1]-xz[:,0];d2=xz[:,2]-xz[:,0];den=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0];valid=np.abs(den)>1e-12
xz=xz[valid];p=p[valid];d1=d1[valid];d2=d2[valid];den=den[valid]
def front_surface(point):
 q=point-xz[:,0];u=(q[:,0]*d2[:,1]-q[:,1]*d2[:,0])/den;w=(d1[:,0]*q[:,1]-d1[:,1]*q[:,0])/den;mask=(u>=-1e-6)&(w>=-1e-6)&(u+w<=1+1e-6)
 if not mask.any():return None
 ys=p[:,0,1]+u*(p[:,1,1]-p[:,0,1])+w*(p[:,2,1]-p[:,0,1]);return float(ys[mask].min())
front=np.array([front_surface(x[[0,2]]) if front_surface(x[[0,2]]) is not None else x[1] for x in c]);visible=np.abs(c[:,1]-front)<1e-5
fit=visible&(v[:,1]<-.03)&(v[:,2]>1.348)&(v[:,2]<1.420)&(np.abs(v[:,0])<.065)
x=c[fit,0]/.05;t=(c[fit,2]-1.38)/.04;y=c[fit,1];A=np.column_stack([np.ones_like(t),t,t*t,t**3,t**4,x*x,x*x*t,x*x*t*t,x**4]);start=np.linalg.lstsq(A,y,rcond=None)[0];coef=least_squares(lambda q:A@q-y,start,loss='soft_l1',f_scale=.002).x
profile=json.load(open(O/'lower-face-coordinates.json'))['side_constraints'];z=np.array([ez+(222-x['row'])*S for x in profile]);yy=np.array([(x['target_u']-200)*S for x in profile]);ix=np.argsort(z);curve=UnivariateSpline(z[ix],yy[ix],s=len(z)*(1*S)**2)
t=(c[:,2]-1.38)/.04;k2=(coef[5]+coef[6]*t+coef[7]*t*t)/(.05**2);k2=np.clip(k2,10,30);k4=coef[8]/(.05**4);k4=np.clip(k4,-500,500)
a=curve(np.clip(c[:,2],z.min(),z.max()));desired=a+k2*c[:,0]**2+k4*c[:,0]**4
fw=np.clip((-v[:,1]-.030)/.020,0,1);fw=fw*fw*(3-2*fw);up=np.clip((1.412-c[:,2])/.013,0,1);up=up*up*(3-2*up);low=np.clip((c[:,2]-1.340)/.010,0,1);low=low*low*(3-2*low);weight=fw*up*low
c[:,1]=v[:,1]+weight*(desired-front)
# The lips use the same underlying facial depth, with tiny physical opening.
change=np.linalg.norm(c-v,axis=1)>1e-8;c[~change]=v[~change];maxmove=np.linalg.norm(c-v,axis=1).max();print('fit samples',int(fit.sum()),'k2 mouth',float(np.interp(1.388,np.sort(c[:,2]),k2[np.argsort(c[:,2])])),'k4',float(k4),'maxmove',float(maxmove));print('largest',[(int(i),round(float(np.linalg.norm(c-v,axis=1)[i])*1000,2)) for i in np.argsort(np.linalg.norm(c-v,axis=1))[-5:]])
assert maxmove<.025
previous=json.load(open(O/'lower-face-fair-coordinates.json'))['changes'];union=set(int(x[0]) for x in previous)|set(np.where(change)[0]);changes=[[int(i),*c[i].tolist()] for i in sorted(union)];(O/'lower-surface-coordinates.json').write_text(json.dumps({'vertices':c.tolist(),'changes':changes,'max_move_m':float(maxmove),'fitted_curvature_coefficients':coef.tolist(),'visible_fit_samples':int(fit.sum())},indent=2))
code='import bpy,json\nh=bpy.data.objects["Anime013_Head"]\nchanges='+repr(changes)+'\nfor entry in changes:h.data.vertices[entry[0]].co=entry[1:]\nh.data.update()\nbpy.context.view_layer.update()\nprint(json.dumps({"changed":len(changes),"stage":"lower-surface-reference"}))'
req=[{'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'apply-lower-surface'}]
for view in ['front','side','quarter']:
 code="import bpy\ns=bpy.context.scene\ns.camera=bpy.data.objects['REF_"+view+"']\ns.render.filepath="+repr(str(O/'validation'/f'lower-surface-{view}.png'))+"\nassert bpy.ops.render.render(write_still=True)=={'FINISHED'}\nprint('SURFACE_"+view+"')";req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'render-surface-'+view})
code="import bpy\nbpy.context.scene.camera=bpy.data.objects['REF_quarter']\nbpy.ops.wm.save_as_mainfile(filepath="+repr(str(R/'models/face-likeness-02/lower-surface-trial.blend'))+",copy=True)\nprint('SAVED')";req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'save-lower-surface'})
(O/'live-mcp/lower-surface-request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2))
