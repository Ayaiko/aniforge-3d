import cv2,json
from PIL import Image,ImageDraw
from pathlib import Path
out=Path(__file__).parent/'source-evidence'
sets={1:[70,170,300,430,565,680,845,1010,1450,1540,1690,2920],2:[230,390,590,830,1080,1310,1800,2160,2500,2800,3000],3:[245,285,370,430,462,490,510,550,590,1120]}
for i,times in sets.items():
 cap=cv2.VideoCapture(f'/tmp/anime-face-video{i}.mp4')
 if not cap.isOpened():print('MISSING_VIDEO',i);continue
 tiles=[]
 for t in times:
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
  if not ok:continue
  im=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));im.thumbnail((480,300)); tile=Image.new('RGB',(480,300),'#151515');tile.paste(im,((480-im.width)//2,25));ImageDraw.Draw(tile).text((8,5),f'Video {i} - {t//60:02d}:{t%60:02d}',fill='white');tiles.append(tile)
 cap.release()
 sheet=Image.new('RGB',(1440,300*((len(tiles)+2)//3)),'#151515')
 for n,tile in enumerate(tiles):sheet.paste(tile,(n%3*480,n//3*300))
 sheet.save(out/f'video{i}-sampled-frames.jpg',quality=92)
 print('SAMPLED',i,len(tiles))
