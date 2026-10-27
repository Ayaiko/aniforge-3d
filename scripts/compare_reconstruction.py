"""Exact local image alignment/diagnostic graphics; never a likeness classifier."""
from pathlib import Path
import json,sys,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/os.environ.get('RECONSTRUCTION_PREVIEW_DIR','previews/v0.3')
name=sys.argv[1];before=sys.argv[2] if len(sys.argv)>2 else 'baseline'
destination=OUT/name;W,H=400,450
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',15)
except OSError:font=ImageFont.load_default()
def load(path):return Image.open(path).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
def masks(im):
    a=np.asarray(im,dtype=float);r,g,b=np.moveaxis(a,-1,0);y=np.indices((H,W))[0]
    hair=(r<105)&(b>r*1.035)&(b>=g*.98)&(y<355)
    skin=(r>160)&(g>95)&(r>g*1.07)&(r>b*1.12)&(y<355)
    return {'hair':hair,'skin':skin}
def edge(m):
    er=m.copy()
    for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:er&=np.roll(np.roll(m,dy,axis=0),dx,axis=1)
    return m&~er
def contours(ref,model):
    canvas=np.full((H,W,3),245,dtype=np.uint8)
    rm=masks(ref);mm=masks(model)
    for group in ['hair','skin']:
        r=edge(rm[group]);m=edge(mm[group]);canvas[r]=[220,40,75];canvas[m]=[0,155,200];canvas[r&m]=[55,35,70]
    return Image.fromarray(canvas)
def labeled(im,label):
    canvas=Image.new('RGB',(W,H+30),'white');canvas.paste(im,(0,30));ImageDraw.Draw(canvas).text((8,7),label,font=font,fill=(20,25,40));return canvas
sheet=Image.new('RGB',(W*5,(H+30)*3),'white')
measurements={}
for row,view in enumerate(['front','side','back']):
    ref=load(ROOT/f'assets/references/alignment-v0.3/{view}.png');old=load(OUT/before/f'{view}.png');after=load(destination/f'{view}.png')
    overlay=Image.blend(ref,after,.5);dif=contours(ref,after)
    overlay.save(destination/f'overlay-{view}.png');dif.save(destination/f'contour-difference-{view}.png')
    for col,(im,label) in enumerate([(ref,f'{view}: Reference'),(old,f'Before: {before}'),(after,f'After: {name}'),(overlay,'Aligned overlay 50/50'),(dif,'Ref red / model cyan')]):sheet.paste(labeled(im,label),(col*W,row*(H+30)))
    if view=='front':
        measurements['front_skin_outline_samples_reference_pixels']={}
        for yy in [270,280,290,300,310]:
            measurements['front_skin_outline_samples_reference_pixels'][yy]={}
            for nm,im in [('reference',ref),('before',old),('after',after)]:
                m=masks(im)['skin'];xx=np.where(m[yy]&(np.arange(W)>90)&(np.arange(W)<300))[0]
                measurements['front_skin_outline_samples_reference_pixels'][yy][nm]=[int(xx.min()),int(xx.max())] if len(xx) else None
sheet.save(destination/'reference-comparison.png')
# Four identical cameras are the before/after test, including the oblique check.
views=['front','quarter','side','back'];montage=Image.new('RGB',(W*4,(H+30)*2),'white')
for col,view in enumerate(views):
    for row,folder in enumerate([before,name]):
        path=OUT/folder/f'{view}.png'
        if path.exists():montage.paste(labeled(load(path),folder+' / '+view),(col*W,row*(H+30)))
montage.save(destination/'before-after.png')
clay=Image.new('RGB',(W*4,H+30),'white')
for col,view in enumerate(views):
    path=destination/f'clay-{view}.png'
    if path.exists():clay.paste(labeled(load(path),'Clay / '+view),(col*W,0))
clay.save(destination/'clay-sheet.png')
measurements['limitations']=['Colour masks provide an approximate contour diagnostic; dark line art, ears and neck may be included. They are not an automatic likeness score.','Pixel difference is not used to declare an artistic pass. Camera, form, materials and lighting require visual interpretation.','Quarter view is a 45-degree 3D continuity check. No exact 45-degree orthographic drawing exists.']
(destination/'comparison-measurements.json').write_text(json.dumps(measurements,indent=2))
print(destination/'reference-comparison.png')
