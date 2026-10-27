from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'previews/v0.3';latest=OUT/'14-master-checkpoint';validation=OUT/'validation-master'
qa=json.loads((validation/'geometry-qa.json').read_text());rig=json.loads((validation/'rig.json').read_text());audit=json.loads((validation/'technical-audit.json').read_text())
assert qa['pass'] and rig['pass'],(qa['errors'],rig['pass'])
cal=json.loads((OUT/'reference-calibration.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(cal['source'])==cal['source_sha256']==sha(cal['backup'])
original_audit=json.loads((ROOT/'previews/v0.2/audit-before.json').read_text())
assert sha(original_audit['source'])==original_audit['source_sha256']
old=json.loads((OUT/'audit-existing.json').read_text())['geometry'];geo=audit['evaluated'];land=json.loads((latest/'landmarks.json').read_text())
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',15)
except OSError:font=ImageFont.load_default()
W,H=400,450
def load(p):return Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
def tile(im,label):
    r=Image.new('RGB',(W,H+30),'white');r.paste(im,(0,30));ImageDraw.Draw(r).text((8,7),label,fill=(25,30,45),font=font);return r
summary=Image.new('RGB',(W*3,H+30),'white');sheet=Image.new('RGB',(W*4,(H+30)*3),'white')
features={}
for row,view in enumerate(['front','side','back']):
    ref=load(ROOT/f'assets/references/alignment-v0.3/{view}.png');before=load(OUT/f'baseline/{view}.png');after=load(latest/(view+'.png'));overlay=Image.blend(ref,after,.5)
    for col,(im,label) in enumerate([(ref,'Reference'),(before,'Before: v0.2'),(after,'Current: v0.3 — WIP'),(overlay,'Aligned overlay — '+view)]):sheet.paste(tile(im,label),(col*W,row*(H+30)))
    if row==0:
        for col,(im,label) in enumerate([(ref,'Approved reference'),(before,'Before: v0.2'),(after,'Current: v0.3 — NOT artistic approval')]):summary.paste(tile(im,label),(col*W,0))
        def skinmask(im):
            a=np.array(im,dtype=float);r,g,b=np.moveaxis(a,-1,0);return (r>160)&(g>95)&(r>g*1.07)&(r>b*1.12)
        for nm,im in [('reference',ref),('before',before),('current',after)]:
            m=skinmask(im);apex=[]
            for y in range(50,190):
                xs=np.where(m[y,210:270])[0]
                if len(xs)>=3:apex=[float(xs.mean()+210),y];break
            a=np.array(im,dtype=float);r,g,b=np.moveaxis(a,-1,0);white=(r>200)&(g>190)&(b>180)&(r-g<17)&(r-b<30)
            eyes={}
            for side,(x0,y0,x1,y1) in {'viewer_left':(115,203,176,242),'viewer_right':(222,202,278,241)}.items():
                yy,xx=np.where(white[y0:y1,x0:x1]);eyes[side]=[int(xx.min()+x0),int(yy.min()+y0),int(xx.max()+x0),int(yy.max()+y0)] if len(xx) else None
            features[nm]={'approximate_hairline_apex_400x450':apex,'sclera_colour_mask_bounds_400x450':eyes}
summary.save(OUT/'final-comparison.png');sheet.save(OUT/'final-reference-comparison.png')
(OUT/'feature-comparison.json').write_text(json.dumps({'features':features,'limitations':'Colour-mask bounds are diagnostic proxies. Eyelashes, occlusion, anti-aliasing and shading affect them; they cannot declare artistic success.'},indent=2))
overlay=Image.open(latest/'overlay-front.png').convert('RGB');draw=ImageDraw.Draw(overlay)
for number,name in enumerate(['pupil_left','pupil_right','mouth_center','chin'],1):
    for point,col in [(land['reference_annotations_400x450'][name],(230,35,70)),(land['views']['front'][name],(0,145,205))]:
        x,y=point;draw.line((x-4,y,x+4,y),fill=col,width=1);draw.line((x,y-4,x,y+4),fill=col,width=1);draw.text((x+5,y+3),str(number),fill=col,font=font)
overlay.save(OUT/'landmark-overlay.png')
hero=OUT/'hero-comparison'
if (hero/'after.png').exists():
    ref=Image.open(ROOT/'assets/concepts/researcher-a-refined-v3.png').convert('RGB').crop((180,10,820,680));canvas=Image.new('RGB',(1920,705),'white');d=ImageDraw.Draw(canvas)
    for col,(im,label) in enumerate([(ref,'Hero reference'),(Image.open(hero/'before.png'),'Before — same approximate portrait camera'),(Image.open(hero/'after.png'),'Current — WIP, same camera')]):canvas.paste(im.convert('RGB'),(col*640,35));d.text((col*640+10,10),label,font=font,fill=(25,30,45))
    canvas.save(OUT/'hero-comparison.png')

iterations=[
('01-face','Face: cheeks narrower, aperture flatter. Ear/skull over-narrowed; still broad forehead.','Geometry','Protect ears, replace hair forms.'),
('02-hair','Swept fringe reaches eye line. Long triangular tips and ear occlusion are worse.','Geometry','Revise taper and depth; do not add strands.'),
('03-primary-correction','Ear volume and frame fit improved. Cut shell has jagged edges; copied terminal sections create kinks.','Geometry','Rebuild controlled width interpolation; smooth coverage boundary.'),
('04-hair-refinement','Ends shorter and smoother. Ear appears through a hole; a local behind-ear lock was incorrectly rooted at crown.','Geometry','Refit coverage shell and restore local root.'),
('05-identity-refinement','Straight brows and nose plane read. Chin/ear colour blocks too strong, crown and side cuts remain crude.','Geometry/material','Reject block shadows; recess coverage surface.'),
('06-surface-correction','Jagged exposed shell edge reduced. Crown roots float/overlap, forehead apex too high.','Geometry','Refit local lock and crown; compare full silhouette.'),
('07-root-and-proportion','Cheek contour closer; local ear lock restored. Crown roots form spikes/floating surface.','Geometry','Fit roots into shared part; add primary forehead transition.'),
('08-primary-resolution','Forehead apex substantially closer; crown spikes reduced. A duplicate side/rear path and hidden root overlap remain.','Geometry','Remove redundant path and trim covered fringe root.'),
('09-root-clearance','Local layer separation retains silhouette but introduces overlap with neighbouring paths.','Geometry','Delete duplicate geometry rather than repeat offsets.'),
('10-root-cleanup','Redundant rear mass removed, covered fringe root capped. Better stable side profile, but artistic likeness still unapproved.','Geometry','Use semantically correct landmarks; test eye asymmetry.'),
('11-profile-landmarks','Eye anchors align better. Lip-centroid fit creates a protruding muzzle despite lower point error: REJECT that change.','Geometry/measurement semantics','Retain eye adjustment, reject perioral forward shift.'),
('12-profile-contour','Sampled profile cage creates an unnatural lip/chin concavity: REJECT that change.','Geometry','Restore strongest reviewed profile; manual sculpt required for remaining planes.'),
('13-reviewed-master','Stable profile restored; eye alignment retained; hair side-wall UVs separated. One cut-cap UV triangle remains degenerate.','UV/technical','Fix only that UV triangle; preserve forms.'),
('14-master-checkpoint','UV triangle fixed. Official geometry/rig checks pass; artwork likeness remains below reference.','Artistic forms/materials','Next: focused Sculpt/Edit pass on crown, hair sections, eyebrows and cheek/lip planes; no tertiary pass yet.')]
rows=['| Iteration | Result from actual renders | Cause | Next action |','| --- | --- | --- | --- |']
for name,result,cause,nextaction in iterations:
    rows.append(f'| [{name}](previews/v0.3/{name}/reference-comparison.png) | {result} | {cause} | {nextaction} |')
warningrows=[]
for warning in qa['warnings']:
    if 'UV overlap' in warning:reason='Original material-separated/mirrored UV layout retained. Not approved for a unified unique-UV bake; source keys/materials need a deliberate retopology/UV handoff.'
    elif 'duplicate verts' in warning:reason='Inherited UV/material seam vertices; not loose. Avoid blind merging across facial morph/material boundaries.'
    elif 'n-gons' in warning:reason='Rigid planar glasses end caps; the whole frame slides without local bending. Triangulate on final export if required.'
    else:reason='Hidden opposing interfaces in layered lids/eyes, thin hair shells or coat/lapels. Accepted for this WIP render checkpoint, not certified as final retopology.'
    warningrows.append(f'| {warning} | {reason} |')
meshrows=['| Mesh | Base vertices | Base polygons | Evaluated triangles | Material slots | UV maps |','| --- | ---: | ---: | ---: | ---: | ---: |']
for name,s in sorted(geo.items()):meshrows.append(f"| {name} | {s['vertices']:,} | {s['faces']:,} | {s['triangles']:,} | {s['materials']} | {len(audit['meshes'][name]['uv_maps'])} |")
report=f'''# Reference-driven reconstruction v0.3 — reviewed work in progress

**สถานะ: ยังไม่ผ่าน Artistic Validation และยังไม่ใช่ Professional Anime Character ที่เสร็จแล้ว**

แก้ Geometry จริงและตรวจภาพวนกลับ 14 checkpoints โดยใช้ Direct Mesh Editing / Controlled Surface Modeling ไม่มีการเพิ่ม Subdivision levels เพื่อปิดบังรูปทรงผิด และยังไม่เพิ่ม tertiary strands, noise หรือรายละเอียดเสื้อใหม่ การปรับอัตโนมัติที่ทำให้ภาพแย่ลงในรอบ 11–12 ถูกยกเลิก เหลือเฉพาะการแก้ตาที่ตรวจแล้วและรูปทรงมุมข้างที่นิ่งกว่า

## ไฟล์หลักและภาพยืนยัน

- [Master checkpoint .blend](models/researcher-a-reconstruction-master-v0.3.blend) — เปิดแก้ต่อได้, packed reference backgrounds, cameras, shape keys และ texture อยู่ในไฟล์
- [เปรียบเทียบ Reference / Before / Current](previews/v0.3/final-comparison.png)
- [Front / Side / Back พร้อม Overlay](previews/v0.3/final-reference-comparison.png)
- [Front / 45° / Side / Back ก่อน–หลังรอบล่าสุด](previews/v0.3/14-master-checkpoint/before-after.png)
- [Clay geometry 4 มุม](previews/v0.3/14-master-checkpoint/clay-sheet.png)
- [เส้นขอบ Reference สีแดง / Model สีฟ้า](previews/v0.3/14-master-checkpoint/contour-difference-front.png)
- [Landmark overlay](previews/v0.3/landmark-overlay.png), [ค่าพิกัด geometry](previews/v0.3/14-master-checkpoint/landmarks.json)
- [ภาพเทียบ Hero ใน pose ใกล้เคียง](previews/v0.3/hero-comparison.png) — กล้อง portrait ประมาณ yaw 15°, roll −9.5°; เป็นการเทียบเชิงภาพ ไม่ใช่ reference orthographic 45° ที่ไม่มีในชุดต้นฉบับ
- [Wire review](previews/v0.3/validation-master/head-wire.png), [ตรวจแยกชิ้นด้วยสี](previews/v0.3/validation-master/head-parts.png)
- [หลับตา](previews/v0.3/validation-master/blink.png), [พูดพร้อมยิ้ม](previews/v0.3/validation-master/speech-smile.png), [แว่นเลื่อน](previews/v0.3/validation-master/glasses-slide.png)
- [หันหัวพร้อม eye look](previews/v0.3/validation-master/head-eye-look-front.png), [มุม 45° ของ pose นี้](previews/v0.3/validation-master/head-eye-look-quarter.png)
- [Full body ก่อน](previews/v0.3/full-body/before/full.png), [Full body ปัจจุบัน](previews/v0.3/full-body/after/full.png) — ส่วนล่างยังเป็นฐานเดิม ไม่ใช่ costume ที่ผ่านการอนุมัติใหม่

## Audit และการเลือกเก็บ/สร้างใหม่

Face เดิมใช้ต่อบางส่วน เพราะมี eye/mouth deformation loops, 42 keys รวม Basis และ eye bones ที่ใช้งานอยู่ ปัญหาหลักจากภาพคือแก้มกว้าง ช่องตากลม ม่านตาใหญ่ และ face planes อ่านไม่ชัด แก้ surface coordinates ของทุก key โดยไม่ทำลายชื่อ/โครง rig เก็บ side profile ที่นิ่งกว่าไว้หลังพบว่าการบังคับ fit จุดปากทำให้รูปทรงแย่ลง

Hair visible surfaces สร้างใหม่ด้วย controlled quad ribbons มีความหนา/ความโค้งจริง ใช้ centerline, width และ camber ที่ออกแบบไว้ ไม่ใช่ primitive ต่อกันแล้วเพิ่ม subdivision เก็บ coverage shell ไว้ด้านในและปรับ scalp ที่ซ่อนอยู่ให้พอดี ลบช่อซ้ำที่สร้าง overlap และแยก front/back/side-wall UV ส่วนผมยังแข็งและแบ่งจังหวะไม่เหมือนงานวาด จึงยังไม่อนุญาตให้เข้าสู่ tertiary detail pass

Glasses เป็น 3D frame/bridge/temples/pads เดิมที่ใช้ต่อได้ ปรับความสูง ความกว้าง และตำแหน่งสัมพันธ์กับตา เสื้อและ rig ใช้ต่อ ยกขอบคอเสื้อ 10 mm เพื่อให้คอใกล้แบบขึ้น งานเสื้อส่วนอื่นยังไม่ได้ผ่าน likeness gate

[Audit baseline แบบละเอียด](previews/v0.3/audit-baseline-detailed.json) มี per-mesh vertices/faces/triangles, modifiers, materials/images, UV, morphs, influences และ bone structure; [audit สถิติ/face-material bounds](previews/v0.3/audit-existing.json), [camera calibration](previews/v0.3/reference-calibration.json)

## Artistic Validation — ยังไม่ผ่าน

| ประเด็น | สิ่งที่ใกล้ขึ้น | สิ่งที่ยังต่าง / สาเหตุ | สิ่งที่ต้องทำต่อ |
| --- | --- | --- | --- |
| Head / cheek / chin | แก้มและคางแคบขึ้น, ตำแหน่งคางตรง anchor | jaw/cheek planes และ lower-face profile ยังไม่เหมือนเต็มเส้น / geometry | Sculpt/Edit บนสำเนา skin surface: cheek-to-jaw transition, philtrum และใต้ริมฝีปาก ตรวจ front+side+clay พร้อมกัน |
| Eyes | ช่องตาแบนลง, iris ลดขนาด, eye asymmetry ใกล้ reference | ขอบตาและน้ำหนักขนตายังดูเป็นฐานเดิม; iris/cornea ใช้ optical approximation / geometry+texture | จัด upper-lid loop และ cantus ด้วย Edit Mode, ตรวจ blink/look; ห้ามตัดสินจาก iris-centre เพียงจุดเดียว |
| Nose / mouth | จมูกมี volume ใน clay และ side, ปากตรงตำแหน่ง front มากขึ้น | Nose plane กับ lip contour ยังต้องเก็บด้วยมือ; lip-material centroid ไม่ใช่ mouth silhouette / geometry+shading | local plane sculpt และ painted shadow ที่อธิบายรูปทรง ไม่ใช้ Gaussian/point fitting แทนทั้ง profile |
| Hairline / silhouette | ลด forehead wedge, หน้าม้าถึงแนวแว่น, crown floating spikes แก้แล้ว | ช่อขวาหนา, หูซ้ายยังเห็นไม่สม่ำเสมอระหว่าง front/side, crown ยังเป็น section, tips/flow เรียบและแข็งกว่าภาพ / geometry | ปรับ editable surface sections เป็นช่อที่บิดและซ้อนตามภาพทีละช่อ จัดช่องเปิดหูให้ถูกทั้ง front/45°/side และตรวจ back |
| Glasses | frame ย่อและลดตำแหน่ง, eyes อ่านง่าย | frame angle/temple fit ยังไม่ใช่ final; แว่นซ้ายต้องตรวจ ear relation ใน pose / geometry | Fit หลังตาและ temple surface final; เก็บ slide target ตามรูปร่างใหม่ |
| Neck / shoulders | collar สูงขึ้นใกล้ตำแหน่งภาพ | ปก/ไหล่/คอเสื้อยังแข็งและผ้าต่างจากภาพ / geometry+material | หลังหัวผ่าน จัดปก/ไหล่/คอด้วย reference section ก่อนตะเข็บ |
| Anime aesthetic | ใช้สีเรียบและ broad bands, ไม่ใช้ noise | คิ้วยังเป็นเส้นเรียบ บุคลิกและ hierarchy ยังไม่เท่าภาพ, hair bands สูตรคล้ายกัน / material+forms | ปรับรูปทรงคิ้ว/ช่อหลักก่อน hand-painted band pass |

Anchor errors ที่กล้อง front 400×450: iris-centre proxy ซ้าย {land['front_anchor_errors_pixels']['pupil_left']:.2f}px, ขวา {land['front_anchor_errors_pixels']['pupil_right']:.2f}px, mouth-material centre {land['front_anchor_errors_pixels']['mouth_center']:.2f}px, chin {land['front_anchor_errors_pixels']['chin']:.2f}px. จุดเหล่านี้อยู่ใน/ใกล้ช่วง annotation uncertainty ±3px แต่ **ไม่ใช่คะแนนความเหมือนทั้งตัวละคร** และไม่ทำให้ Artistic gate ผ่าน

Reference ด้านข้างถูก mirror อย่างระบุไว้เพื่อให้ตรงฝั่งหูซ้ายของโมเดล ภาพ back วาดผมกว้างกว่า front; ใช้ front identity เป็นหลักและ reconcile volume ใน 3D กล้อง/แสง/scale ถูกล็อกตลอด iteration ไม่เปลี่ยนให้ผลดูเข้ารูป ภาพ overlay และ colour-mask contour เป็นตัวช่วยวินิจฉัย ไม่ใช้ whole-image pixel difference ตัดสินคุณภาพ

## ผลตรวจแต่ละ iteration

{chr(10).join(rows)}

ทุกโฟลเดอร์ iteration มี raw front / quarter / side / back, clay 4 มุม, before-after, overlays, contour differences, cameras.json, geometry.json และ changes.json ไม่มีภาพเรนเดอร์ที่ถูก AI วาดแก้

## Technical Validation

Official game-profile QA: **{qa['pass']}**, errors **{len(qa['errors'])}**, warnings **{len(qa['warnings'])}** ที่ eps 0.2mm, contact tolerance 2mm; ไม่แก้ checker หรือเปลี่ยน profile ให้ผ่าน [ผล QA](previews/v0.3/validation-master/geometry-qa.json)

Rig/morph/weights preservation: **{rig['pass']}**, bone names/rest coordinates คงเดิม, Face keys 42 และ glasses keys 2 ชื่อเดิม, ทุก key ที่เคยขยับยังมี delta, weights normalize. [ผล rig](previews/v0.3/validation-master/rig.json). ภาพ blink/wink/speech/glasses ถูก render ตรวจจริง; ยังไม่ใช่ผลจับ webcam และยังไม่มี benchmark runtime/OBS 5 นาที

| รุ่น | Meshes | Base vertices | Base polygons | Evaluated triangles |
| --- | ---: | ---: | ---: | ---: |
| v0.2 baseline | {len(old)} | {sum(x['vertices'] for x in old.values()):,} | {sum(x['faces'] for x in old.values()):,} | {sum(x['triangles'] for x in old.values()):,} |
| v0.3 master checkpoint | {len(geo)} | {sum(x['vertices'] for x in geo.values()):,} | {sum(x['faces'] for x in geo.values()):,} | {sum(x['triangles'] for x in geo.values()):,} |

เพิ่มจำนวน triangles ไม่ใช่เกณฑ์ artistic pass รูปทรงเปลี่ยนจากการแก้พิกัดและสร้าง surface ที่ควบคุม flow/section ใหม่ ไม่ได้เพิ่มความละเอียดภาพแทนโมเดล

มี referenced image datablocks {len(audit['textures'])} รายการ รวม source/reference และ textures; skin plane map 2048, brows 1024, iris เดิม 1024, broad hair colour bands 512 ต่อ mass รายละเอียดขนาด/packed state และ modifier ทุกชิ้นอยู่ใน [technical audit](previews/v0.3/validation-master/technical-audit.json) ผิว/ผม/ตา/กรอบ/เลนส์/เสื้อแยกวัสดุ ใช้ MToon เป็นหลัก ไม่มี final unique-UV bake หรือ export/optimization ใหม่ในรอบนี้

### คำเตือนที่ยอมรับใน checkpoint นี้

| Warning จาก checker | เหตุผลและขอบเขตการยอมรับ |
| --- | --- |
{chr(10).join(warningrows)}

Basic QA pass ไม่ใช่การรับรอง final production topology: ยังต้อง retopology/unique UV ตามปลายทาง, ตรวจ extreme eye look/poses หลังรูปทรง final และวัด performance จริง ไม่ส่งออก realtime ใหม่ขณะที่ artistic forms ยังไม่ผ่าน รุ่น realtime v0.2 เดิมไม่ถูกเขียนทับ

## ข้อจำกัดและ Sculpt/Edit handoff

รอบนี้เป็น direct mesh/surface work ผ่าน bpy **ไม่มีการใช้แปรง Sculpt Mode** และยังไม่เทียบเท่าการเก็บผิวและการตัดสินรูปทรงโดย character sculptor [blender-sculpting skill ที่ใช้](.agents/skills/blender-sculpting/SKILL.md) ระบุ “Never enter Sculpt Mode headless.” และแนะนำ “Hand detailed brushwork to the human.” ข้อแรกใช้กับ background process เท่านั้น ไม่ใช่ข้อห้ามแก้ใน Blender UI และไม่ใช่ขั้นขออนุมัติ ข้อจำกัดที่ยังเหลือจริงคือผลรูปทรงอัตโนมัติยังไม่ถึงเกณฑ์ artistic ที่ผู้ใช้กำหนด การลอง profile fitting สองแบบที่ไม่สวยถูกปฏิเสธจากภาพ ไม่ถือว่า script สำเร็จแล้วงานผ่าน

ขั้นถัดไปที่ต้องใช้ Sculpt/Edit Mode จริง: duplicate เฉพาะ skin surface เป็น sculpt working copy; ใช้ Grab/Elastic Deform ปรับ cheek/jaw silhouette, Clay/Flatten ปรับ nose/philtrum/lip planes, Smooth แบบจำกัดบริเวณ และ Edit Mode จัด lid loops/temple ต่อด้วยปรับ surface sections ของ crown/fringe ให้มีมวลซ้อนตามภาพ หลัง primary forms ผ่านจึงทำ secondary eyelid/ear/hair clumps แล้ว retopo/transfer morphs และตรวจ deformation ใหม่ ไม่เพิ่มความละเอียดเพื่อกลบ primary forms และยังไม่เรียกไฟล์นี้ว่า completed high-detail hand sculpt

## สถิติแต่ละ mesh

{chr(10).join(meshrows)}

Original v0.1, v0.2 และ backup ไม่ถูกเขียนทับ ตรวจ SHA-256 baseline/backup ตรงกับก่อนเริ่ม reconstruction แล้ว ไฟล์ master ใหม่และไฟล์แต่ละ checkpoint อยู่คนละ path [manifest](previews/v0.3/delivery-manifest.json)
'''
(ROOT/'RECONSTRUCTION_REPORT.md').write_text(report)
manifest={'status':'work_in_progress_artistic_gate_not_passed','technical_basic_qa_pass':qa['pass'],'rig_preservation_pass':rig['pass'],'original_v01_unchanged':True,'original_v02_unchanged':True,'files':{},'cameras_locked_across_iterations':True}
paths=[ROOT/'models/researcher-a-reconstruction-master-v0.3.blend',ROOT/'RECONSTRUCTION_REPORT.md',ROOT/'RECONSTRUCTION_PLAN.md',OUT/'final-comparison.png',OUT/'final-reference-comparison.png']
for p in paths:assert p.exists() and p.stat().st_size>0;manifest['files'][str(p.relative_to(ROOT))]={'bytes':p.stat().st_size,'sha256':sha(p)}
base=json.loads((OUT/'baseline/cameras.json').read_text())
for name,*_ in iterations:
    d=OUT/name
    for v in ['front','quarter','side','back']:
        assert (d/(v+'.png')).stat().st_size>0 and (d/('clay-'+v+'.png')).stat().st_size>0
    for p in ['before-after.png','reference-comparison.png','overlay-front.png','contour-difference-front.png']:
        assert (d/p).stat().st_size>0,(d,p)
    cams=json.loads((d/'cameras.json').read_text());assert all(np.allclose(cams[v]['matrix_world'],base[v]['matrix_world'],atol=1e-8) and abs(cams[v]['ortho_scale']-base[v]['ortho_scale'])<1e-8 for v in base)
(OUT/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2))
print('REPORT WRITTEN; master tris',sum(x['triangles'] for x in geo.values()),'artistic pass: FALSE; technical QA',qa['pass'])
