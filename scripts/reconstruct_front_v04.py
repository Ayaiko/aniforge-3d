from pathlib import Path
import sys,json,shutil,hashlib,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from forms_v04_common import *
source=ROOT/'models/researcher-a-reconstruction-master-v0.3.blend';backup=ROOT/'models/backups/researcher-a-before-primary-v0.4.blend'
if not backup.exists():shutil.copy2(source,backup)
assert hashlib.sha256(source.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
initialize('models/researcher-a-reconstruction-master-v0.3.blend')
reconstruction_review.OUT=OUT;reconstruction_review.render_iteration('baseline');export_contours(OUT/'baseline')
remove=[o.name for o in bpy.data.objects if o.type=='MESH' and o.get('reconstruction_tier') and 'RearMass' not in o.name]
for n in remove:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
main=toon('Forms / hair primary','252C40','172035',.0003);under=toon('Forms / hair overlap','20283C','151E30',.0002)
specs=[
('Front_OuterSweep',[(220,20),(158,27),(95,77),(53,147),(27,217),(26,280),(47,326),(78,349)],[(223,28),(172,57),(128,103),(93,164),(69,231),(65,284),(66,326),(78,349)],[.005,-.018,-.055,-.065,-.045,-.012,.01,.035],main),
('Front_MiddleSweep',[(222,25),(170,39),(118,81),(91,133),(75,189),(61,250),(69,310),(103,343)],[(224,36),(193,56),(156,101),(125,158),(105,209),(92,258),(88,309),(103,343)],[-.005,-.04,-.078,-.094,-.085,-.052,-.01,.02],main),
('Front_InnerSweep',[(224,37),(188,57),(152,100),(130,149),(108,199),(95,247),(99,289),(119,328)],[(226,49),(210,81),(181,126),(155,170),(133,214),(122,257),(112,299),(119,328)],[-.015,-.06,-.095,-.11,-.104,-.065,-.025,.012],under),
('Front_FringeMain',[(226,48),(202,69),(180,110),(166,153),(149,191),(129,217)],[(229,65),(219,96),(205,137),(188,173),(164,202),(129,217)],[-.025,-.080,-.115,-.121,-.110,-.099],main),
('Front_FringeLayer',[(232,69),(221,107),(205,147),(186,184),(165,214)],[(236,79),(230,121),(218,161),(198,196),(165,214)],[-.045,-.101,-.125,-.125,-.105],main),
('Front_PartRight',[(230,48),(228,82),(227,111),(244,139),(261,176),(270,212)],[(235,48),(259,72),(277,110),(289,148),(288,184),(270,212)],[-.017,-.07,-.104,-.100,-.085,-.058],main),
('Front_EarTuck',[(237,38),(274,66),(298,107),(306,150),(301,187),(294,204)],[(250,42),(291,70),(316,112),(321,158),(312,188),(294,204)],[.015,-.015,-.025,-.015,.005,.020],under),
('Front_OuterRight',[(245,23),(295,49),(328,100),(347,157),(355,217),(350,280),(327,324),(299,346)],[(252,30),(307,62),(342,123),(361,182),(369,243),(363,296),(337,333),(299,346)],[.035,.06,.085,.09,.095,.075,.045,.02],main),
('Front_TempleLock',[(281,191),(285,225),(282,260),(276,291),(263,315)],[(289,190),(292,226),(290,266),(279,303),(263,315)],[-.026,-.030,-.036,-.020,.001],under)]
for name,left,right,ys,mat in specs:boundary_surface(name,left,right,ys,mat,bulge=.0032)
directory=finish('01-front-reconstruction','researcher-a-front-v0.4.blend',{'part':'Front hair','method':'Rebuilt nine surfaces from independent reference-space boundaries; unequal widths and ends','removed':remove,'created':[p[0] for p in specs],'acceptance':['Diagonal fringe direction and staggered upper-frame tips','Internal boundary flow corresponds to reference','Part/hairline and ear opening read in front, side and quarter'],'tertiary_details_added':0,'subdivision_levels_added':0,'artistic_status':'Pending actual visual review'})
face=bpy.data.objects['Face'];skin=next(i for i,m in enumerate(face.data.materials) if 'Face_00_SKIN' in m.name)
from collections import Counter,defaultdict
counts=Counter(e for p in face.data.polygons if p.material_index==skin for e in p.edge_keys);g=defaultdict(list)
for (a,b),count in counts.items():
    if count==1:g[a].append(b);g[b].append(a)
loops=[];visited=set();basis=face.data.shape_keys.key_blocks[0]
for seed in g:
    if seed in visited:continue
    seq=[];cur=seed;prev=None
    for i in range(2000):
        visited.add(cur);seq.append(cur);nxt=[a for a in g[cur] if a!=prev]
        if not nxt or nxt[0]==seed:break
        prev,cur=cur,nxt[0]
        if cur in visited:break
    pts=[face.matrix_world@basis.data[i].co for i in seq];c=sum(pts,Vector())/len(pts)
    loops.append({'indices':seq,'center':list(c),'points':[list(p) for p in pts]})
(OUT/'face-boundaries.json').write_text(json.dumps(loops,indent=2));print('FRONT RECONSTRUCTION SAVED',flush=True)
