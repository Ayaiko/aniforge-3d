"""Make evidence sheets from actual MCP renders. Never synthesize reference views."""
from pathlib import Path
import json,shutil,math
from PIL import Image,ImageDraw,ImageFont,ImageFilter
import numpy as np
root=Path(__file__).resolve().parents[1];a=root/'artifacts/reconstruction-v2-mcp';out=root/'previews/skills-workflow-upgrade';out.mkdir(exist_ok=True)
data=root/'artifacts/skills-workflow-upgrade';font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16);small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12)
def actual(stage,view):return Image.open(a/f'skills-{stage}-{view}-0.png').convert('RGBA')
def panel(im,title):
    result=Image.new('RGB',(400,480),'#f3f4f6');d=ImageDraw.Draw(result);d.text((10,8),title,fill='#182337',font=font);im=im.resize((400,450),Image.Resampling.LANCZOS).convert('RGBA');bg=Image.new('RGBA',im.size,(94,98,103,255));bg.alpha_composite(im);result.paste(bg.convert('RGB'),(0,30));return result
sheet=Image.new('RGB',(1200,1480),'#f3f4f6');overlays=Image.new('RGB',(1200,510),'#f3f4f6');features=json.loads((data/'source_analysis/facial-features.json').read_text())
def curve(points):
    p=np.array(points);return [tuple(np.array([(1-t)**3,3*t*(1-t)**2,3*t*t*(1-t),t**3])@p) for t in np.linspace(0,1,81)]
for row,view in enumerate(['front','side','hero']):
    path=root/f'assets/references/alignment-v0.3/{view}.png' if view!='hero' else data/'source_analysis/hero-reference.png'
    ref=Image.open(path).convert('RGBA');before=actual('before',view);after=actual('after02',view)
    title=f'{view}: reference' if view!='hero' else 'Hero reference: approximate 15 deg'
    for col,(im,label) in enumerate([(ref,title),(before,'Before / FAIL'),(after,'Checkpoint 02 / still FAIL')]):sheet.paste(panel(im,label),(400*col,480*row))
    aft=after.resize(ref.size,Image.Resampling.LANCZOS);alpha=aft.getchannel('A');aft.putalpha(alpha.point(lambda v:int(v*.36)));overlay=Image.alpha_composite(ref,aft).convert('RGB');outline=alpha.filter(ImageFilter.FIND_EDGES);overlay.paste(Image.new('RGB',ref.size,'#00d4e8'),(0,0),outline);draw=ImageDraw.Draw(overlay)
    if view=='front':
        for c in features['front_eye_beziers']:draw.line(curve(c),fill='#ff8700',width=2)
        draw.line([(107,239),(114,273),(141,308),(173,330),(198,346),(225,333),(254,308),(278,272),(289,241)],fill='#ff8700',width=2)
    if view=='side':
        for x,y in [[53,257],[100,344]]:draw.ellipse((x-3,y-3,x+3,y+3),fill='#ff8700')
    label=f'{view}: cyan mesh / orange reference'
    if view=='hero':label='Hero overlay: camera RMS 7.4 px / WARN'
    overlays.paste(panel(overlay,label),(row*400,0));overlay.save(out/f'overlay-{view}.png')
    for stage in ['before','after','after02']:shutil.copy2(a/f'skills-{stage}-{view}-0.png',out/f'{stage}-{view}.png')
ImageDraw.Draw(sheet).text((10,1453),'Actual Blender MCP renders. Same cameras before/after. No textures, hair, new character or added polygons. All model gates remain explicit.',fill='#182337',font=small);sheet.save(out/'before-after-reference.png')
ImageDraw.Draw(overlays).text((10,486),'Front/side cameras locked. Hero uses an approximate camera fit; it is not an exact 45-degree plate. Hair-covered skull is inferred.',fill='#182337',font=small);overlays.save(out/'reference-overlays.png')
quarter=Image.new('RGB',(800,480),'#f3f4f6');quarter.paste(panel(actual('before','quarter'),'Before: exact REF_quarter 45 deg'),(0,0));quarter.paste(panel(actual('after02','quarter'),'After02: 45 deg / no matching plate'),(400,0));quarter.save(out/'before-after-quarter45.png')
for stage in ['before','after','after02']:shutil.copy2(a/f'skills-{stage}-quarter-0.png',out/f'{stage}-quarter.png')
shutil.copy2(a/'skills-primary02-wireframe-0.png',out/'wireframe-front-side-quarter.png')
reference=np.array(Image.open(data/'source_analysis/front-eye-reference-mask.png'))[:,:,3]>8;metrics={}
for stage in ['before','after','after02']:
    mask=np.array(Image.open(data/f'validation/{stage}-eye-mask.png'))[:,:,3]>8
    metrics[stage]={'iou':float((mask&reference).sum()/(mask|reference).sum()),'outside_reference_ratio':float((mask&~reference).sum()/mask.sum())}
canvas=Image.new('RGB',(1200,280),'#f3f4f6')
for col,stage in enumerate(['before','after','after02']):
    mask=np.array(Image.open(data/f'validation/{stage}-eye-mask.png'))[:,:,3]>8;difference=np.zeros((450,400,3),np.uint8);difference[reference]=(0,200,220);difference[mask]=(220,200,0);difference[reference&mask]=(0,190,80);difference[reference^mask]=(230,30,50)
    im=Image.fromarray(difference).crop((90,180,310,260)).resize((400,146),Image.Resampling.NEAREST);canvas.paste(im,(400*col,45));d=ImageDraw.Draw(canvas);d.text((400*col+10,12),f'{stage}: IoU {metrics[stage]["iou"]:.3f} / FAIL',fill='#182337',font=font);d.text((400*col+10,205),f'Exposed outside reference: {metrics[stage]["outside_reference_ratio"]:.1%}',fill='#182337',font=font)
ImageDraw.Draw(canvas).text((10,251),'Green overlap; red disagreement. A near-correct centroid or high whole-image SSIM does not pass the visible-eye gate.',fill='#182337',font=small);canvas.save(out/'eye-coverage-gate.png')
(data/'validation/eye-coverage-history.json').write_text(json.dumps(metrics,indent=2));print('Evidence sheets and three-view overlays saved; no fabricated 45-degree reference.')
