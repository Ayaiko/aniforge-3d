import cv2,json,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path('/Users/graind/Documents/ChatGPT/vTuber');OUT=ROOT/'artifacts/anime-face-full-review';OLD=ROOT/'artifacts/anime-face-learning/source-evidence'
# 10 s chronological overview everywhere; 5 s spacing in the hands-on modeling chapters.
ranges={1:[(46,1780),(2839,3039)],2:[(215,1370),(1792,3092)],3:[(240,594)]}
review=[]
for i in [1,2,3]:
 meta=json.loads((OLD/f'video{i}-metadata.json').read_text());video=Path(f'/tmp/anime-face-video{i}.mp4');cap=cv2.VideoCapture(str(video));fps=cap.get(cv2.CAP_PROP_FPS);frames=int(cap.get(cv2.CAP_PROP_FRAME_COUNT));duration=frames/fps
 times=set(range(0,math.floor(duration),10))
 for a,b in ranges[i]:times.update(range(a,min(math.floor(duration),b),5))
 times.update(int(c['start_time']) for c in meta['chapters']);times.add(max(0,math.floor(duration)-1));times=sorted(times)
 captions=json.loads((OLD/f'video{i}-ja-orig-captions-parsed.json').read_text());english=None
 en=OLD/f'video{i}-en-captions-parsed.json'
 if en.exists():english=json.loads(en.read_text())
 sheets=[];batch=[];sheet_index=0
 for t in times:
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
  if not ok:raise RuntimeError((i,t))
  im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).resize((320,180),Image.Resampling.LANCZOS);tile=Image.new('RGB',(320,202),'#131313');tile.paste(im,(0,22));d=ImageDraw.Draw(tile);d.text((6,4),f'{i}  {t//60:02d}:{t%60:02d}',fill='white');batch.append((t,tile))
  if len(batch)==30 or t==times[-1]:
   sheet_index+=1;name=f'video{i}-{sheet_index:02d}';sheet=Image.new('RGB',(1920,202*math.ceil(len(batch)/6)),'#131313')
   for k,(_,img) in enumerate(batch):sheet.paste(img,(k%6*320,k//6*202))
   imgpath=OUT/'chronological'/f'{name}.jpg';sheet.save(imgpath,quality=92)
   lo=batch[0][0];hi=min(duration,times[times.index(t)+1] if t!=times[-1] else duration)
   text={'video':i,'source':meta['webpage_url'],'sheet':name,'start':lo,'end':hi,'sampled_frame_seconds':[x[0] for x in batch],'ja':[x for x in captions if lo<=x['t']<hi]}
   if english:text['en']=[x for x in english if lo<=x['t']<hi]
   (OUT/'chronological'/f'{name}.json').write_text(json.dumps(text,ensure_ascii=False,indent=2));sheets.append({'sheet':name,'image':str(imgpath),'start':lo,'end':hi,'frames':[x[0] for x in batch],'reviewed':False});batch=[]
 cap.release();review.append({'video':i,'title':meta['title'],'source':meta['webpage_url'],'duration_seconds':duration,'source_metadata_seconds':meta['duration'],'fps':fps,'source_frames':frames,'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'review_frame_count':len(times),'maximum_review_gap_seconds':max(b-a for a,b in zip(times,times[1:])),'captions_segments':len(captions),'sheets':sheets});print(i,len(times),len(sheets),flush=True)
(OUT/'coverage-manifest.json').write_text(json.dumps({'method':'Chronological storyboard review at at most 10 s intervals, 5 s in modeling chapters, plus complete Japanese caption stream; operation details revisited separately. Not continuous playback or every-frame visual inspection.','videos':review},ensure_ascii=False,indent=2))
