from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;R=P.parent.parent
ref=np.asarray(Image.open(R/'assets/references/alignment-v0.3/side.png').convert('RGB'),dtype=float)
skin=(ref[:,:,0]>180)&(ref[:,:,1]>120)&(ref[:,:,2]>85)&(ref[:,:,0]>ref[:,:,1]+12)&(ref[:,:,1]>ref[:,:,2]+5)
rows=[250,257,265,275,285,295,305,315,325,335,340];trace=[]
for r in rows:
 xs=np.where(skin[r,40:150])[0]
 if len(xs):trace.append({'row':r,'reference_u':int(xs.min()+40-1)})
results={};controls=[]
for tag in ['baseline','repair','clean']:
 im=Image.open(P/f'renders/{tag}/mask-side.png').convert('RGBA').resize((400,450),Image.Resampling.LANCZOS);arr=np.asarray(im);alpha=arr[:,:,3]>127;points=[]
 for t in trace:
  xs=np.where(alpha[t['row']])[0]
  u=int(xs.min()) if len(xs) else None;points.append(dict(t,model_u=u,error_px=u-t['reference_u'] if u is not None else None))
 err=[x['error_px'] for x in points if x['error_px'] is not None];results[tag]={'side_exposed_skin_trace':points,'mean_abs_error_px':float(np.mean(np.abs(err))),'rms_error_px':float(np.sqrt(np.mean(np.array(err)**2))),'trace_uncertainty_px':2,'scope':'sampled visible facial profile only; hair-covered skull excluded, not a likeness score'}
 refim=Image.open(R/'assets/references/alignment-v0.3/side.png').convert('RGB');edge=alpha & ~np.roll(alpha,1,axis=1);pix=refim.load()
 for yy,xx in zip(*np.where(edge)):
  if 242<=yy<=344:pix[int(xx),int(yy)]=(0,220,240)
 dr=ImageDraw.Draw(refim)
 for t in points:dr.ellipse((t['reference_u']-1,t['row']-1,t['reference_u']+1,t['row']+1),fill=(255,30,140))
 refim.resize((800,900)).save(P/f'{tag}-profile-overlay.png')
 controls.append(json.loads((P/f'renders/{tag}/controls.json').read_text()))
results['control_match']=all(x==controls[0] for x in controls)
a=np.array(json.loads((P/'current-mesh-data.json').read_text())['vertices']);b=np.array(json.loads((P/'repair-mesh-data.json').read_text())['vertices']);results['repair_coordinate_max_difference_m']=float(np.max(np.linalg.norm(a-b,axis=1)))
(P/'comparison-measurements.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:{q:v[q] for q in ['mean_abs_error_px','rms_error_px']} if isinstance(v,dict) and 'mean_abs_error_px' in v else v for k,v in results.items()},indent=2))
reg=[]
for f in [R/'models/root-cause-audit-05/current-live-source.blend',R/'models/root-cause-audit-05/repair.blend',R/'models/root-cause-audit-05/clean.blend',P/'sources/rain/rain_v3.2.blend',P/'sources/snow/snow_v4.2.blend',R/'assets/references/alignment-v0.3/front.png',R/'assets/references/alignment-v0.3/side.png']:
 reg.append({'path':str(f.resolve()),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(P/'source-register.json').write_text(json.dumps(reg,indent=2))
