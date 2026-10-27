from pathlib import Path
import json,numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator
R=Path.cwd();O=R/'artifacts/face-likeness-02';D=json.load(open(O/'baseline.json'));head=D['meshes']['Anime013_Head'];v=np.array(head['vertices']);c=v.copy();S=.0007797915761063738;ez=1.446197748184204;mouth=next(l for l in head['boundary_loops'] if len(l)==32);a=v[mouth];mx=(a[:,0].min()+a[:,0].max())/2;mz=(a[:,2].min()+a[:,2].max())/2;tz=ez+(222-297)*S
# Broader neutral lip line. Smooth spatial falloff, including neighbouring lip skin.
front=np.clip((-v[:,1]-.035)/.025,0,1);front=front*front*(3-2*front);w=np.exp(-((v[:,2]-mz)/.010)**4-((v[:,0]-mx)/.021)**4)*front
c[:,0]=mx+(v[:,0]-mx)*(1+.72*w)
c[:,2]=v[:,2]+w*((tz-mz)-.70*(v[:,2]-mz))
# Depth constraints come from the supplied side image, below the nose.
ref=np.array(Image.open(R/'assets/references/alignment-v0.3/side.png').convert('RGB')).astype(float);skin=(ref[:,:,0]>180)&(ref[:,:,1]>120)&(ref[:,:,2]>85)&(ref[:,:,0]>ref[:,:,1]+12)&(ref[:,:,1]>ref[:,:,2]+5)
rows=[280,286,290,295,297,300,305,310,315,320,325,330,335,340,342,343];targets=[];delta=[];initial=[]
tri=np.array([[f[0],f[k],f[k+1]] for f in head['faces'] for k in range(1,len(f)-1)])
def front_y(z):
 ys=[]
 for f in tri:
  p=c[f]
  if z<p[:,2].min() or z>p[:,2].max():continue
  for x,y in [(0,1),(1,2),(2,0)]:
   if (p[x,2]-z)*(p[y,2]-z)<=0 and abs(p[x,2]-p[y,2])>1e-9:
    t=(z-p[x,2])/(p[y,2]-p[x,2]);ys.append(p[x,1]+t*(p[y,1]-p[x,1]))
 return min(ys)
for row in rows:
 z=ez+(222-row)*S;f=front_y(z);xs=np.where(skin[row,40:160])[0];target=100 if row==343 else float(xs.min()+40-1)
 if row==280:target=200+f/S
 targets.append(target);initial.append(200+f/S);delta.append((target-200)*S-f)
# Keep the bridge and upper face exactly fixed. Below the chin, the Y-front mask
# fades to the neck; no artificial moving of the neck silhouette.
rz=np.array([ez+(222-r)*S for r in rows]);idx=np.argsort(rz);curve=PchipInterpolator(rz[idx],np.array(delta)[idx],extrapolate=False);dz=np.where((c[:,2]>=rz.min())&(c[:,2]<=rz.max()),curve(np.clip(c[:,2],rz.min(),rz.max())),0)
# Continue the final chin displacement over its underside, away from the neck.
low=(c[:,2]<rz.min())&(c[:,2]>1.342);dz[low]=delta[-1]*np.clip((c[low,2]-1.342)/(rz.min()-1.342),0,1)
fw=np.clip((-c[:,1]-.025)/.035,0,1);fw=fw*fw*(3-2*fw);c[:,1]+=dz*fw
# Explicitly retain all unaffected coordinates, avoiding numerical round-trip drift.
change=np.linalg.norm(c-v,axis=1)>1e-8;c[~change]=v[~change];payload={'vertices':c.tolist(),'changes':[[int(i),*c[i].tolist()] for i in np.where(change)[0]],'max_move_m':float(np.linalg.norm(c-v,axis=1).max()),'mouth_width_px_before':float(np.ptp(a[:,0])/S),'mouth_width_px_after':float(np.ptp(c[mouth,0])/S),'mouth_height_px_before':float(np.ptp(a[:,2])/S),'mouth_height_px_after':float(np.ptp(c[mouth,2])/S),'side_constraints':[{'row':r,'before_u':u,'target_u':t,'delta_y_m':y} for r,u,t,y in zip(rows,initial,targets,delta)]}
(O/'lower-face-coordinates.json').write_text(json.dumps(payload,indent=2));print(json.dumps({k:v for k,v in payload.items() if k not in ['vertices','changes']},indent=2));print('changed',len(payload['changes']))
contract={'input':str(R/'models/face-likeness-02/before-likeness.blend'),'goal':'Neutral, almost closed 39–41 px mouth, positioned near (200,297), and a coherent lip-to-chin side profile from the supplied drawing.','reference_trace_uncertainty_px':2,'protected':['eye aperture and eye geometry','nose tip','front cheek/jaw silhouette','original cameras','mesh connectivity'],'checks':{'mouth_width_px':[37,42],'mouth_height_px':[.3,.8],'profile_error_target_px':2,'no_new_nonmanifold':True,'no_self_crossings':True,'multi_view_artistic_review_required':True},'method':'Authored direct coordinate deformation, reference-driven; not a sculpt brush replay.'};(O/'lower-face-contract.json').write_text(json.dumps(contract,indent=2))
code='import bpy,json\nh=bpy.data.objects["Anime013_Head"]\nassert len(h.data.vertices)==946 and len(h.data.polygons)==1107\nchanges='+repr(payload['changes'])+'\nfor entry in changes:h.data.vertices[entry[0]].co=entry[1:]\nh.data.update()\nbpy.context.view_layer.update()\nprint(json.dumps({"changed_vertices":len(changes),"stage":"lower-face-primary-trial","faces":len(h.data.polygons)}))'
req=[{'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'apply-lower-face'}]
for view in ['front','side','quarter']:
 code="import bpy\ns=bpy.context.scene\ns.camera=bpy.data.objects['REF_"+view+"']\ns.render.filepath="+repr(str(O/'validation'/f'lower-face-{view}.png'))+"\nassert bpy.ops.render.render(write_still=True)=={'FINISHED'}\nprint('LOWER_FACE_"+view+"')";req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'render-lower-face-'+view})
code="import bpy\nbpy.context.scene.camera=bpy.data.objects['REF_quarter']\nbpy.ops.wm.save_as_mainfile(filepath="+repr(str(R/'models/face-likeness-02/lower-face-trial.blend'))+",copy=True)\nprint('TRIAL_SAVED')";req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':'ทำต่อให้มันเหมือน ref ดิ'},'label':'save-lower-face-trial'})
(O/'live-mcp/lower-face-request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2))
