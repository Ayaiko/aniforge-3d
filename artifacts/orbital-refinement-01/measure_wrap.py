from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
O=Path('artifacts/orbital-refinement-01');V=O/'validation';ref=np.array(Image.open('artifacts/skills-workflow-upgrade/source_analysis/front-eye-reference-mask.png').convert('RGBA'))[:,:,3]>0
metrics=[]
for stage in ['before','fair-35-wrap','fair-70-wrap']:
 c=np.array(Image.open(V/f'{stage}-labels.png').convert('RGB').resize((400,450),Image.Resampling.NEAREST));a=c[:,:,0];b=c[:,:,1];z=c[:,:,2];left=(a>127)&(b<25)&(z<25);right=(b>127)&(a<25)&(z<25);mask=left|right;assert left.sum()>200 and right.sum()>200
 row={'stage':stage,'left_area':int(left.sum()),'right_area':int(right.sum()),'iou':float((mask&ref).sum()/(mask|ref).sum()),'outside_ratio':float((mask&~ref).sum()/mask.sum())};row['mask_gate_pass']=row['iou']>=.85 and row['outside_ratio']<=.05;metrics.append(row)
 overlay=np.zeros((450,400,3),np.uint8);overlay[ref]=[60,120,255];overlay[mask]=[255,70,70];overlay[mask&ref]=[60,200,130];Image.fromarray(overlay).save(V/f'{stage}-eye-overlay.png')
 im=Image.open(V/f'{stage}-front.png');im.crop((195,340,610,490)).resize((1245,450)).save(V/f'{stage}-eye-detail.png')
(O/'wrap-mask-results.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
sheet=Image.new('RGB',(1200,1422),(20,20,20));d=ImageDraw.Draw(sheet)
for r,stage in enumerate(['before','fair-35-wrap','fair-70-wrap']):
 for c,view in enumerate(['front','side','quarter']):
  im=Image.open(V/f'{stage}-{view}.png').convert('RGB').resize((400,450));sheet.paste(im,(400*c,474*r+24));d.text((400*c+8,474*r+7),f'{stage} | {view}',fill='white')
sheet.save(V/'wrap-trial-sheet.jpg',quality=93)
