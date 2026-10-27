import cv2,json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;S=P/'sources';O=P/'source-review';O.mkdir(exist_ok=True)
v=S/'planning.mp4';cap=cv2.VideoCapture(str(v));duration=cap.get(cv2.CAP_PROP_FRAME_COUNT)/cap.get(cv2.CAP_PROP_FPS);ts=list(range(0,int(duration),5));ledger=[]
for off in range(0,len(ts),30):
 batch=ts[off:off+30];sheet=Image.new('RGB',(1920,math.ceil(len(batch)/6)*202),'#202020')
 for k,t in enumerate(batch):
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read();assert ok
  im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).resize((320,180));sheet.paste(im,((k%6)*320,(k//6)*202+22));ImageDraw.Draw(sheet).text(((k%6)*320+8,(k//6)*202+3),f'{t//60:02}:{t%60:02}',fill='white')
 name=f'planning-{off//30+1:02}.jpg';sheet.save(O/name,quality=95);ledger.append({'image':name,'times':batch,'reviewed':False})
for t in [115,270,400,520]:
 cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read();assert ok;cv2.imwrite(str(O/f'detail-{t}.png'),f)
(S/'review-ledger.json').write_text(json.dumps({'source':'https://studio.blender.org/training/stylized-character-workflow/5e5407ec8faf011a381510d7/','creator':'Julien Kaspar / Blender Studio','duration':duration,'method':'5-second chronological storyboard plus all English captions, not continuous playback','sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'sheets':ledger},indent=2));print('SOURCE_SHEETS',duration,len(ts),len(ledger))
