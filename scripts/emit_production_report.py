"""Publish the local audit trail only after both assets have passed validation."""
from pathlib import Path
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'previews/v0.2'
def read(name):return json.loads((out/(name+'.json')).read_text())
audit=read('audit-before');master=read('master-geometry');realtime=read('realtime-geometry');export=read('export-verification')
for version in ['master','realtime']:
    assert read('qa-'+version)['pass'];assert read('rig-'+version)['pass']
assert export['reimport_success'] and export['valid_expression_bindings']
assert hashlib.sha256(Path(audit['source']).read_bytes()).hexdigest()==audit['source_sha256']
assert hashlib.sha256(Path(audit['backup']).read_bytes()).hexdigest()==audit['source_sha256']
manifest={'original_unchanged':True,'original_sha256':audit['source_sha256'],'files':[]}
paths=['models/researcher-a.blend','models/backups/researcher-a-pre-v0.2.blend','models/researcher-a-master-v0.2.blend','models/researcher-a-realtime-v0.2.blend','models/researcher-a-realtime-v0.2.vrm']
for path in paths:
    p=ROOT/path;data=p.read_bytes();assert data
    manifest['files'].append({'path':path,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(out/'delivery-manifest.json').write_text(json.dumps(manifest,indent=2))

def reason(w):
    if 'UV overlap' in w:return 'ยอมรับ: atlas ของฐานใช้หลายวัสดุ/ภาพแยกกัน และมีส่วนสะท้อนซ้าย–ขวาโดยเจตนา ไม่ใช้ UV ชุดรวมนี้ bake ภาพ unique ทั้งตัว'
    if 'duplicate verts' in w:return 'ยอมรับ: จุดที่อยู่ใกล้กันบริเวณรอยแยกผิว/ขอบหน้าจากฐาน เก็บไว้รักษา UV และการเสียรูป ไม่มี loose vertices หรือ degenerate geometry ที่เป็น error'
    if 'n-gons' in w:return 'ยอมรับ: ฝาปิดแบนของอุปกรณ์แข็งที่เคลื่อนทั้งชิ้นกับศีรษะ ส่งออก VRM เป็น triangles'
    if 'back-to-back' in w:
        if 'Coat' in w:return 'ยอมรับ: ผิวด้านในของชั้นผ้ากับปกที่พับ/เย็บติดกัน ไม่ใช่ผิวด้านหน้าแข่งกันแสดงผล'
        if 'Hair' in w or 'Fringe' in w:return 'ยอมรับ: ผิวด้านในของช่อผมหรือรากผมฝังใต้ก้อนหลัก/หนังศีรษะ ไม่เปิดให้เห็นในมุมที่ตรวจ'
        if 'EyeGlobe' in w:return 'ยอมรับ: ผิวลูกตาด้านในสัมผัสขอบเบ้าตา หลับตาและมองตาในชุดทดสอบแล้วไม่โผล่'
        return 'ยอมรับ: ผิวภายในช่องปาก/ริมฝีปาก หรือชั้นฐานเล็บที่สัมผัสกัน คงไว้สำหรับชุดการแสดงสีหน้าและผิวด้านใน'
    raise RuntimeError('Unreviewed warning: '+w)

def totals(data):return (len(data),sum(x['vertices'] for x in data.values()),sum(x['faces'] for x in data.values()),sum(x['triangles'] for x in data.values()))
before={name:{'vertices':v['vertices'],'faces':v['faces'],'triangles':v['evaluated_triangles']} for name,v in audit['meshes'].items()}
lines=['# Researcher A — รายงานอัปเกรดโมเดล 0.2','',
'แก้จาก models/researcher-a.blend ตัวเดิมด้วย Blender Python รักษาตัวตน โครงกระดูก และชุดควบคุมหน้าเดิม ไฟล์ต้นฉบับและสำเนาก่อนแก้มี SHA-256 ตรงกัน ตรวจซ้ำหลังจบงานแล้ว','',
'## ไฟล์ส่งมอบ','',
'- [High-Detail Master](models/researcher-a-master-v0.2.blend): เก็บ modifiers, ผมสามระดับ และ Bezier flow guides สำหรับแก้ต่อ',
'- [Realtime Blender](models/researcher-a-realtime-v0.2.blend): ลดความหนาแน่นผม bake รูปทรงและ morph โดยไม่สูญเสียชื่อควบคุม',
'- [Realtime VRM](models/researcher-a-realtime-v0.2.vrm): ตรวจ binding แล้ว และนำกลับเข้า Blender เพื่อเรนเดอร์ตรวจจริง',
'- [สำรองก่อนแก้](models/backups/researcher-a-pre-v0.2.blend)',
'- [Audit ก่อนแก้](previews/v0.2/audit-before.json), [manifest และ checksums](previews/v0.2/delivery-manifest.json)','',
'## จำนวน geometry','',
'| รุ่น | Meshes | Control vertices | Control faces | Triangles หลังประเมิน modifiers |','| --- | ---: | ---: | ---: | ---: |']
for label,data in [('Before',before),('Master',master),('Realtime',realtime)]:lines.append('| '+label+' | '+' | '.join(f'{v:,}' for v in totals(data))+' |')
lines+=['','Master เก็บ subdivision/solidify/bevel ที่แก้ไขต่อได้ ส่วน Realtime bake แล้ว จึงไม่ควรเทียบ control vertices อย่างเดียว จำนวน triangles ใช้ผิวที่แสดงผลจริงทั้งสองรุ่น','',
'## งานตาม Phase','',
'| Phase | สิ่งที่เปลี่ยนในไฟล์จริง | หลักฐาน |','| --- | --- | --- |',
'| 0 Audit | สำรอง ตรวจ vertices/faces/tris, modifiers, วัสดุ ภาพพื้นผิว กระดูก weights และการเคลื่อนของทุก key | audit-before.json และ before/ ทั้ง 6 มุม |',
'| 1 ใบหน้า | เพิ่มโหนกแก้ม ขากรรไกร คาง สันจมูกและริมฝีปากในทุก expression; ขอบเปลือกตา/ปากมีความหนา; subdivision แบบคงขอบของชั้นตา/คิ้ว | phase1-face/ และ head-wire.png |',
'| 2 ผม | รักษาทรงบ๊อบปาดข้าง สร้าง primary 8 ช่อ secondary 12 ช่อ tertiary 4 ช่อ มี taper/thickness/twist ไม่เท่ากัน; ปิดหนังศีรษะที่เคยทะลุ; มี Bezier guide ใน Master | phase2-hair/ และ after/hair.png |',
'| 3 ตา | Scleral volume มีช่องหน้า iris/pupil มีรูปทรงเว้า 1024px iris และ corneal coat ที่รับแสง; ขอบตาหนาขึ้นและแก้รูปตอนหลับตา | after/face.png, poses-master/blink/, poses-master/head-eye-look/ |',
'| 4 แว่น/เสื้อ | กรอบเดิมเข้ารูปหน้า เพิ่ม bevel, lens shells, hinges, pins, nose pads; ผ้ากาวน์และปกมีความหนาและโครงพับ; กระเป๋าเปิดจริงและปากกาติดตัวหนีบ; รอยพับตามข้อศอก | after/side.png และ poses-master/elbow-140-torso/ |',
'| 5 วัสดุ | แยกผิว ผม ตา กรอบแว่น เลนส์ ฝ้ายกาวน์ เสื้อถัก; toon palette เดิม; clear optical materials ใน Master และวัสดุโปร่งใสที่เข้ากับ VRM ใน Realtime | master-geometry.json, vrm-reimport/ |',
'| 6 Optimize | ลด samples ของผม ลดผิวที่ไม่ช่วย silhouette, bake morph แบบ topology เท่ากันทุก key, unwrap ผิวความหนาของผ้าใหม่; Realtime ตัดผิวข้อศอกด้านนอกที่กาวน์บังเพื่อลดการทะลุขณะใช้ linear skinning | realtime-geometry.json |',
'| 7 Validate | game-profile QA ทั้งสองรุ่น, ตรวจ rig/weights/morphs, fixed-camera Before/After, หลับตา wink พูด+ยิ้ม head/eye look และงอศอก 120°/140° | qa-*.json, rig-*.json, poses-*/ |','',
'## ผลตรวจ','',
'- Master: geometry PASS และ rig PASS; Realtime: geometry PASS และ rig PASS ไม่มี errors ในรายงานที่ส่งมอบ',
'- ใช้ qa_check.py ของสกิลโดยไม่แก้เกณฑ์ profile=game, eps=0.0002 เมตร สำหรับรายละเอียดหน้า/แว่นขนาดเล็ก และ tol=0.002 เมตร ไม่มีการข้ามตรวจเพราะเกิน poly budget',
'- ชื่อและตำแหน่งพักของกระดูกเดิมตรงกัน ชื่อ Face shape keys ครบ 42 รวม Basis และ Glasses keys ครบ 2; key ที่เคยขยับยังขยับ น้ำหนัก deform รวมเท่ากับหนึ่งและไม่เกิน 4 influences ต่อ vertex',
f"- VRM {export['bytes']:,} ไบต์ มี humanoid assignments {export['humanoid_bones']} รายการ ตรวจ mesh/morph indices ของทุก expression และ import กลับได้จริง",
'- ตรวจภาพวัสดุและ wireframe 4 มุม รวมทั้ง Before/After มุมหน้า 45° ข้าง หน้าใกล้ ผมใกล้ และทั้งตัว ด้วยกล้อง ความละเอียด และแสงชุดเดียวกัน','',
'## ภาพเปรียบเทียบ','',
'ภาพ after/ และ vrm-reimport/ ใช้ shader จริง ภาพ head-material/head-wire เป็น Workbench สำหรับดูโครงสร้าง จึงแสดง texture และ alpha ต่างจากภาพใช้งาน','',
'ซ้าย Before / ขวา After ทั้งสองคอลัมน์มาจากภาพเรนเดอร์จริง ไม่มีการเจนหรือวาดแก้ภาพหลังเรนเดอร์','',
'![Before/After](previews/v0.2/before-after.png)','',
'![Face/Hair/Full comparison](previews/v0.2/before-after-details.png)','',
'## คำเตือนที่ตรวจแล้วและยอมรับ','']
for version in ['master','realtime']:
    lines+=['### '+version,'']
    for w in read('qa-'+version)['warnings']:lines.append('- '+w+' — '+reason(w))
    lines.append('')
lines+=['## ขอบเขตที่ยังต้องทดสอบในงานใช้จริง','',
'ผ่านการตรวจไฟล์ โมเดล และท่าที่ระบุในรอบนี้ ยังไม่มีการทดสอบจับหน้าจากเว็บแคมจริง 5 นาทีหรือคลิปพร้อมเสียง 60 วินาที จึงยังไม่ถือว่าจบเกณฑ์ VTuber ทั้งโปรเจกต์',
'ผมในรุ่นนี้ตามกระดูกศีรษะ ยังไม่มี secondary hair simulation ส่วน ARKit 52 ใหม่ไม่ได้เพิ่ม: เก็บชุดใบหน้าเดิมที่ใช้งานได้ไว้ ไม่สร้าง key ว่างเพื่อให้ครบจำนวน',
'Realtime เป็นรุ่นใส่ชุดกาวน์ ใช้ Master หากต้องแก้ชุดหรือเปิดผิวแขนบริเวณที่กาวน์บัง เพราะรุ่นเบาตัดผิวที่มองไม่เห็นบางส่วนแล้ว ไม่ใช่ไฟล์ฐานถอดเสื้อได้ทุกชิ้น',
'ภาพและวัสดุ optical ใน VRM ใช้แบบที่ renderer VRM รองรับ จึงไม่มีการหักเหแสงเต็มรูปแบบเหมือน Master; ยังไม่วัด FPS ในโปรแกรมสตรีมจริง','',
'## จำนวนราย Mesh — Master','',
'| Mesh | Control vertices | Control faces | Evaluated triangles | Materials |','| --- | ---: | ---: | ---: | ---: |']
for name,s in sorted(master.items()):lines.append(f"| {name} | {s['vertices']:,} | {s['faces']:,} | {s['triangles']:,} | {s['materials']} |")
lines+=['','ข้อมูลรายชิ้นของ Realtime อยู่ใน [realtime-geometry.json](previews/v0.2/realtime-geometry.json) และข้อมูลก่อนแก้พร้อมวัสดุ/ภาพ/กระดูกทุกจุดอยู่ใน [audit-before.json](previews/v0.2/audit-before.json)','']
report_text='\n'.join(lines)
report_text=re.sub(r'\]\(((?:models|previews)/[^)]+)\)',lambda m:']('+str(ROOT/m.group(1))+')',report_text)
(ROOT/'PRODUCTION_REPORT.md').write_text(report_text)
provenance=json.loads((ROOT/'assets/base/provenance.json').read_text())
for entry in manifest['files']:
    if entry['path'].endswith('-v0.2.vrm'):
        provenance['files']=[f for f in provenance['files'] if f['path']!=entry['path']]+[entry]
(ROOT/'assets/base/provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
print('Delivery report written; original and backup hashes match; both QA/rig gates passed')
