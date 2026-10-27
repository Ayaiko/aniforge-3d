from pathlib import Path
import json,cv2,numpy as np
from PIL import Image,ImageDraw
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-learning';V=O/'validation'
ref=np.array(Image.open(R/'artifacts/skills-workflow-upgrade/source_analysis/front-eye-reference-mask.png').convert('RGBA'))[:,:,3]>0
rows=[]
for stage in ['before','relax-only','eyes-only','combined','eye-depth-2mm','eye-depth-4mm','eye-depth-6mm']:
 im=np.array(Image.open(V/f'{stage}-eyes.png').convert('RGB').resize((400,450),Image.Resampling.NEAREST));channels=im.astype(float); red=(channels[:,:,0]>30)&(channels[:,:,0]>1.4*channels[:,:,1])&(channels[:,:,0]>1.4*channels[:,:,2]); green=(channels[:,:,1]>30)&(channels[:,:,1]>1.4*channels[:,:,0])&(channels[:,:,1]>1.4*channels[:,:,2]); mask=red|green;inter=(mask&ref).sum();union=(mask|ref).sum();outside=(mask&~ref).sum()
 row={'stage':stage,'iou':float(inter/union),'outside_ratio':float(outside/max(1,mask.sum())),'visible_eye_area_px':int(mask.sum()),'expected_eye_area_px':int(ref.sum()),'outside_px':int(outside),'detected_left_eye_area_px':int(red.sum()),'detected_right_eye_area_px':int(green.sum())};assert red.sum()>200 and green.sum()>200, 'Both eye labels must be detected'; rows.append(row)
 overlay=np.zeros((450,400,3),np.uint8);overlay[ref]=[70,140,255];overlay[mask]=[255,100,70];overlay[ref&mask]=[80,220,140];Image.fromarray(overlay).save(V/f'{stage}-eye-mask-overlay.png')
(O/'eye-trial-metrics.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
# Same-scale crop comparison, 3 views per stage.
stages=['before','eyes-only','eye-depth-2mm','eye-depth-4mm','eye-depth-6mm'];sheet=Image.new('RGB',(400*3,450*len(stages)),(20,20,20));d=ImageDraw.Draw(sheet)
for row,stage in enumerate(stages):
 for col,view in enumerate(['front','side','quarter']):
  im=Image.open(V/f'{stage}-{view}.png').convert('RGB').resize((400,450));sheet.paste(im,(col*400,row*450));d.text((col*400+8,row*450+8),f'{stage} | {view}',fill='white')
sheet.save(V/'eye-depth-comparison.jpg',quality=92)
