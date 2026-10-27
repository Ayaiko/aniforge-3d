"""Compose actual MCP renders and vector landmark/contour comparisons; no AI imagery."""
import json,shutil,math,sys
from pathlib import Path
from collections import defaultdict
from PIL import Image,ImageDraw,ImageFont,ImageFilter
root=Path(__file__).resolve().parents[1];a=root/'artifacts/reconstruction-v2-mcp';out=root/'previews/reconstruction-v2/failure-analysis';out.mkdir(parents=True,exist_ok=True)
version=sys.argv[1] if len(sys.argv)>1 else '007'
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',16)
small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',12)
def panel(im,title):
    canvas=Image.new('RGB',(400,480),'#f2f3f6');ImageDraw.Draw(canvas).text((10,8),title,fill='#172030',font=font)
    im=im.resize((400,450),Image.Resampling.LANCZOS)
    if im.mode=='RGBA':
        bg=Image.new('RGBA',(400,450),(94,98,103,255));bg.alpha_composite(im);canvas.paste(bg.convert('RGB'),(0,30))
    else:canvas.paste(im.convert('RGB'),(0,30))
    return canvas
def render(name):return Image.open(a/name).copy()
sheet=Image.new('RGB',(1200,1000),'#f2f3f6')
for row,view in enumerate(['front','side']):
    ref=Image.open(root/f'assets/references/alignment-v0.3/{view}.png')
    for col,(im,title) in enumerate([(ref,f'{view.title()} reference'),(render(f'matcap-{view}-0.png'),'Before: head-002 / rejected'),(render(f'clean-{version}-{view}-0.png'),f'New base {version} / likeness NOT passed')]):sheet.paste(panel(im,title),(400*col,480*row))
ImageDraw.Draw(sheet).text((10,974),'Same REF orthographic cameras. Matcap ignores scene lights, materials and textures. No hair or subdivision.',fill='#172030',font=small)
sheet.save(out/'before-after-front-side.png')
quarter=Image.new('RGB',(800,480),'#f2f3f6');quarter.paste(panel(render('matcap-quarter-0.png'),'Before: 3/4 matcap'),(0,0));quarter.paste(panel(render('clean-'+version+'-quarter-0.png'),f'New base {version}: 3/4 matcap'),(400,0));quarter.save(out/'before-after-quarter.png')
proof=json.loads((a/f'clean-{version}-geometry-proof-parsed.json').read_text());head=next(o for o in proof['objects'] if o['name']=='V2_Clean_Head');verts=head['vertices'];faces=head['faces'];fs=json.loads((a/'cc0-face-sets.json').read_text())
S=.0007797915761063738;EYE=1.446197748184204
def project(p,view):
    x,y,z=p;return (200+(x if view=='front' else y)/S,222-(z-EYE)/S)
edge_tags=defaultdict(list)
for face,tag in zip(faces,fs):
    for x,y in zip(face,face[1:]+face[:1]):edge_tags[tuple(sorted((x,y)))].append(tag)
lid=[e for e,t in edge_tags.items() if 28 in t and 37 in t]
target_lid=[[(120,216),(134,211),(155,212),(168,223),(152,233),(133,232),(120,216)],[(225,222),(236,212),(257,208),(274,212),(263,229),(239,234),(225,222)]]
jaw=[(107,239),(114,273),(141,308),(173,330),(198,346),(225,333),(254,308),(278,272),(289,241)]
skin_by_set=defaultdict(set)
for f,tag in zip(faces,fs):skin_by_set[tag].update(f)
nose=min((verts[i] for i in skin_by_set[45]),key=lambda p:p[1])
chin=min((p for p in verts if abs(p[0])<.006 and p[1]<-.058 and p[2]>1.33),key=lambda p:p[2])
mouth=min((p for p in verts if abs(p[0])<.003 and 1.384<p[2]<1.391),key=lambda p:p[1])
eyes=[]
for o in proof['objects']:
    if '.eye.' in o['name']:eyes.append([sum(v[i] for v in o['vertices'])/len(o['vertices']) for i in range(3)])
eyes.sort(key=lambda p:p[0])
landmarks={'eye_left':eyes[0],'eye_right':eyes[1],'nose_tip':nose,'mouth_surface':mouth,'chin':chin}
targets={'front':{'eye_left':(146,224),'eye_right':(249,220),'nose_tip':(200,257),'mouth_surface':(200,297),'chin':(200,345)},'side':{'nose_tip':(53,257),'chin':(100,344)}}
measurements={};overlay_sheet=Image.new('RGB',(800,500),'#f2f3f6')
for col,view in enumerate(['front','side']):
    ref=Image.open(root/f'assets/references/alignment-v0.3/{view}.png').convert('RGBA')
    im=render(f'clean-{version}-{view}-0.png').resize((400,450),Image.Resampling.LANCZOS).convert('RGBA')
    alpha=im.getchannel('A');im.putalpha(alpha.point(lambda v:int(v*.33)))
    overlay=Image.alpha_composite(ref,im).convert('RGB');draw=ImageDraw.Draw(overlay)
    edge=alpha.filter(ImageFilter.FIND_EDGES);cyan=Image.new('RGB',(400,450),'#00bad4');overlay.paste(cyan,(0,0),edge);draw=ImageDraw.Draw(overlay)
    if view=='front':
        draw.line(jaw,fill='#ff8b19',width=2)
        for contour in target_lid:draw.line(contour,fill='#ff8b19',width=2)
        for va,vb in lid:draw.line([project(verts[va],view),project(verts[vb],view)],fill='#00cbe8',width=2)
    measurements[view]={}
    for key,target in targets[view].items():
        actual=project(landmarks[key],view);distance=math.dist(actual,target)
        measurements[view][key]={'reference':list(target),'mesh':list(actual),'distance_px':distance,'note':'Diagnostic projected anatomical handle; front nose and mouth surface have ambiguous 2D semantics; not a likeness score.'}
        draw.line([target,actual],fill='#d82747',width=2)
        for point,color in [(target,'#ff8b19'),(actual,'#00bad4')]:
            x,y=point;draw.ellipse((x-3,y-3,x+3,y+3),fill=color)
    overlay.save(out/f'reference-overlay-{view}.png');overlay_sheet.paste(panel(overlay,f'{view.title()}: orange reference / cyan mesh'),(400*col,0))
ImageDraw.Draw(overlay_sheet).text((10,484),'Red: landmark displacement. Hair-covered skull is inferred. Reference expression/asymmetry remains unmatched.',fill='#172030',font=small)
overlay_sheet.save(out/'reference-overlay-contours.png')
(out/'landmark-diagnostics.json').write_text(json.dumps(measurements,indent=2))
for name in ['clean-'+version+'-front-0.png','clean-'+version+'-side-0.png','clean-'+version+'-quarter-0.png','clean-'+version+'-wireframe-0.png']:shutil.copy2(a/name,out/name)
for src,dst in [(f'/tmp/vtuber-head-{version}-clean-primary.blend',f'head-{version}-clean-primary.blend')]:shutil.copy2(src,root/'models/reconstruction-v2'/dst)
print('Saved comparison, contour overlays, actual render panels and versioned blend.')
