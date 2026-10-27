from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-full-review';V=O/'validation'
for filename,views in [('fixed-camera-before-after.jpg',['front','side','quarter']),('supplemental-before-after.jpg',['twenty','high','low'])]:
 sheet=Image.new('RGB',(1200,948),(24,24,24));d=ImageDraw.Draw(sheet)
 for row,stage in enumerate(['before','after']):
  for col,view in enumerate(views):
   im=Image.open(V/f'{stage}-{view}.png').convert('RGB').resize((400,450));sheet.paste(im,(400*col,474*row+24));d.text((400*col+8,474*row+6),f'{stage} | {view}',fill='white')
 sheet.save(V/filename,quality=92)
checks=[]
for view in ['front','side','quarter','twenty','high','low']:
 a=np.array(Image.open(V/f'before-{view}.png').convert('RGBA'));b=np.array(Image.open(V/f'after-{view}.png').convert('RGBA'));delta=np.abs(a.astype(int)-b.astype(int));checks.append({'view':view,'changed_pixels':int(np.any(delta>0,axis=2).sum()),'max_rgb_delta':int(delta[:,:,:3].max()),'mean_abs_rgb_delta':float(delta[:,:,:3].mean()),'silhouette_changed_pixels':int(((a[:,:,3]>127)^(b[:,:,3]>127)).sum())})
ref=np.array(Image.open(R/'artifacts/skills-workflow-upgrade/source_analysis/front-eye-reference-mask.png').convert('RGBA'))[:,:,3]>0
im=np.array(Image.open(V/'after-eye-labels-standard.png').convert('RGB').resize((400,450),Image.Resampling.NEAREST));c=im.astype(float);red=(c[:,:,0]>127)&(c[:,:,1]<25)&(c[:,:,2]<25);green=(c[:,:,1]>127)&(c[:,:,0]<25)&(c[:,:,2]<25);assert red.sum()>200 and green.sum()>200
mask=red|green;metrics={'display':'Standard/None, flat object colors; measurement-specific pass','left_area':int(red.sum()),'right_area':int(green.sum()),'iou':float((mask&ref).sum()/(mask|ref).sum()),'outside_ratio':float((mask&~ref).sum()/mask.sum()),'limitation':'Edge antialiasing and threshold differ from historical AgX dominance pass; not presented as improvement over that score. Reference trace uncertainty 1–2 pixels.'}
(O/'visual-regression.json').write_text(json.dumps(checks,indent=2));(O/'standard-mask-validation.json').write_text(json.dumps(metrics,indent=2));print(json.dumps({'views':checks,'mask':metrics},indent=2))
source=json.load(open(R/'artifacts/anime-face-learning/source-checkpoint.json'));actual=hashlib.sha256(Path(source['source']).read_bytes()).hexdigest();assert actual==source['sha256'];(O/'source-preservation.json').write_text(json.dumps({'source':source['source'],'expected_sha256':source['sha256'],'actual_sha256':actual,'unchanged':True,'live_session_touched':False},indent=2))
