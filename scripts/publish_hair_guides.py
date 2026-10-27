from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'previews/v0.5';data=json.loads((OUT/'guide-manifest.json').read_text());W,H=400,450
try:font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',14)
except OSError:font=ImageFont.load_default()
try:small=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',11)
except OSError:small=font
def native(path):return Image.open(path).convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
def tile(im,label):
    out=Image.new('RGB',(W,H+32),'white');out.paste(im.convert('RGB'),(0,32));ImageDraw.Draw(out).text((7,9),label,font=font,fill=(20,25,40));return out
overview=Image.new('RGB',(W*3,(H+32)*3),'white');guide_sheet=Image.new('RGB',(W*3,H+32),'white');overlay_sheet=Image.new('RGB',(W*3,H+32),'white')
for row,view in enumerate(['front','side','back']):
    ref=native(ROOT/f'assets/references/alignment-v0.3/{view}.png');lines=native(OUT/f'focused-guides-{view}.png');all_lines=native(OUT/f'guides-{view}.png')
    overlay=Image.alpha_composite(ref,lines);all_overlay=Image.alpha_composite(ref,all_lines)
    draw=ImageDraw.Draw(overlay)
    for record in data['guides']:
        if view not in record['primary_visible_views']:continue
        points=record['projections'][view];idx=max(record['visible_start_index']+1,len(points)//2);x,y=points[idx]
        colour=tuple(int(255*min(1,max(0,c))) for c in record['colour'][:3]);label=record['id'];offset=-32 if x<200 else 7
        tx=max(2,min(366,x+offset));ty=max(3,min(432,y-5));box=draw.textbbox((tx,ty),label,font=small);draw.rectangle((box[0]-2,box[1]-2,box[2]+2,box[3]+2),fill=(255,255,255,220));draw.text((tx,ty),label,font=small,fill=(20,25,35));draw.line((x,y,tx,ty+6),fill=colour,width=1)
    overlay.convert('RGB').save(OUT/f'overlay-{view}.png');all_overlay.convert('RGB').save(OUT/f'all-guides-overlay-{view}.png')
    plain=Image.alpha_composite(Image.new('RGBA',(W,H),(246,247,250,255)),all_lines);plain.convert('RGB').save(OUT/f'guides-only-{view}.png')
    for col,(im,label) in enumerate([(ref,view+' / source'),(overlay,view+' / corresponding guides'),(all_overlay,view+' / all guides, including hidden')]):overview.paste(tile(im,label),(col*W,row*(H+32)))
    guide_sheet.paste(tile(plain,view+' / 14 native 3D curves'),(row*W,0));overlay_sheet.paste(tile(overlay,view+' / visible correspondence IDs'),(row*W,0))
overview.save(OUT/'reference-guide-comparison.png');guide_sheet.save(OUT/'guides-only-sheet.png');overlay_sheet.save(OUT/'reference-overlays.png')
context=Image.new('RGB',(W*4,H+32),'white')
for col,view in enumerate(['front','quarter','side','back']):context.paste(tile(native(OUT/f'context-{view}.png'),view+' / inherited head + guides'),(col*W,0))
context.save(OUT/'root-volume-context.png')
# Guide fitting targets and native projections are drawn separately. Interpolating
# these authored targets does not prove that the painting correspondence is right.
constraint_sheet=Image.new('RGB',(W*3,H+32),'white')
for col,view in enumerate(['front','side','back']):
    panel=Image.new('RGB',(W,H),(250,250,252));d=ImageDraw.Draw(panel)
    for r in data['guides']:
        if view not in r['primary_visible_views']:continue
        coords=r['projections'][view][r['visible_start_index']:];colour=tuple(int(255*c) for c in r['colour'][:3]);d.line([tuple(p) for p in coords],fill=colour,width=1)
        if r['source_view']==view:
            for x,y in r['reference_trace']:d.ellipse((x-2,y-2,x+2,y+2),outline=(210,30,65),width=1)
        if view=='side':
            for (_,y),x in zip(r['reference_trace'],r['side_u']):d.ellipse((x-2,y-2,x+2,y+2),outline=(210,30,65),width=1)
    constraint_sheet.paste(tile(panel,view+' / authored targets + projection'),(col*W,0))
constraint_sheet.save(OUT/'constraint-projections.png')
rows=['| ID | ช่อหลัก | มุมที่มี correspondence | ระยะ root–skin | ผลตรวจ/ข้อจำกัด |','| --- | --- | --- | ---: | --- |']
for r in data['guides']:
    rows.append(f"| {r['id']} | {r['label']} | {', '.join(r['primary_visible_views'])} | {r['root_distance_m']*1000:.3f} mm | {r['correspondence_note']} |")
text=f'''# Hair Guide System v0.5 — Phase 1

**ยังไม่สร้าง Hair Mesh ใหม่** มี native editable Bézier curves {data['guide_count']} เส้น และ root anchors แยกคอลเลกชัน รูปทรงผม v0.3 เก็บใน archive ปิดแสดงผล; ไฟล์ Master เดิมไม่เปลี่ยนแปลง

## ไฟล์และภาพ

- [Blender Hair Guides](models/researcher-a-hair-guides-v0.5.blend)
- [Front / Side / Back overlays](previews/v0.5/reference-overlays.png)
- [Reference / corresponding guides / all guides](previews/v0.5/reference-guide-comparison.png)
- [Guide-only native renders](previews/v0.5/guides-only-sheet.png)
- [Root และ volume context 4 มุม](previews/v0.5/root-volume-context.png)
- [Target/control projections](previews/v0.5/constraint-projections.png)
- [พิกัดจริง, source traces และ root measurements](previews/v0.5/guide-manifest.json)

## การจัดแนวและโครงสร้าง

ใช้ source crops Front / Side / Back เดิมจาก turnaround v3 โดยไม่ยืดภาพ กล้อง REF เดิมมี orthographic scale ร่วมกันและ pixel-to-world calibration เดิม ด้าน Side ใช้ฉบับ mirror ตาม calibration ที่บันทึกไว้ก่อนหน้า ขนาดวาดด้าน Back กว้างกว่า Front บางส่วน จึงยังมีความคลาดเคลื่อนที่ geometry เดียวไม่สามารถ match ทุกเส้นได้พอดี

แต่ละช่อมี ID, clump name, native Bézier points และ FREE handles ที่แก้ได้จริง Front/back ระบุ XZ; corresponding Side U ที่ระดับ Z เดียวกันระบุความลึก Y การจับคู่บางช่วงเป็นการตีความภาพวาดและถูกระบุไว้ ไม่ถือว่าเป็น ground-truth 3D reconstruction

01_HAIR_GUIDES_EDITABLE มี curves; 02_ROOT_ATTACHMENTS มี Empty anchors ผูกกับ Head bone; 03_HAIR_MESH_NOT_GENERATED ว่าง; 00_ORIGINAL_HAIR_v03_ARCHIVE เก็บ mesh เดิมที่ซ่อนอยู่ bevel 0.45 mm ใช้เพื่อ render เส้น guide ให้เห็นเท่านั้น ไม่ใช่ hair clump mesh

Root แต่ละเส้น snap กับ evaluated skin ของ Body/Face จริง มี offset ตาม normal 0.3 mm เกณฑ์ไม่เกิน 0.5 mm: **{data['root_attachment_pass']}** บางช่อมีช่วงสั้นจาก attachment ใต้ผิวทรงผมถึง visual part ของภาพ; visible_start_index แยกช่วงนี้ชัดเจน แหล่ง triangle ของผิวศีรษะและระยะจริงอยู่ใน manifest

## ผลรายช่อก่อนสร้าง geometry

{chr(10).join(rows)}

## Gate ด้านภาพ

ยังไม่ประกาศว่าทั้ง 14 ช่อผ่านเพียงเพราะ projected control points ตรงกับ target ที่ป้อนเข้าไป ต้องตรวจ native curve overlay จริง: แนวหน้าม้า F01/F02, พื้นที่รอบหู R01/R02, ความโค้ง side volume R03/B01 และ rear inward flow B02–B05 ก่อนเข้าสู่ Phase 2 เส้นที่ถูกบังในภาพมีทั้งภาพ render เฉพาะ correspondence และภาพ all-guide x-ray เพื่อไม่ซ่อนความคลาดเคลื่อนจากอีกด้าน

ขั้นสร้าง mesh/width/thickness/taper/twist ยังไม่เริ่ม; ขั้น secondary strands และ materials/highlights ยังไม่เริ่ม

Source v0.3 SHA-256: `{data['source_sha256']}` ตรงกับ backup และไม่ถูกเขียนทับ
'''
(ROOT/'HAIR_GUIDES_REPORT.md').write_text(text)
assert hashlib.sha256(Path(data['source']).read_bytes()).hexdigest()==data['source_sha256']
assert hashlib.sha256(Path(data['backup']).read_bytes()).hexdigest()==data['source_sha256']
print('GUIDE REPORT AND OVERLAYS WRITTEN',data['guide_count'],'curves, new hair meshes',data['new_hair_mesh_count'])
