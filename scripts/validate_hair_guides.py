"""Independent native data, root, skin-clearance and rig-follow checks."""
from pathlib import Path
import sys,json,math,hashlib,bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import interpolate_bezier
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
enable_vrm();path=ROOT/'models/researcher-a-hair-guides-v0.5.blend';bpy.ops.wm.open_mainfile(filepath=str(path));out=ROOT/'previews/v0.5'
report=json.loads((out/'guide-manifest.json').read_text());verts=[];faces=[]
for name in ['Body','Face']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();offset=len(verts);verts.extend([ev.matrix_world@v.co for v in me.vertices])
    for p in me.polygons:
        if any(s in me.materials[p.material_index].name for s in ['SKIN','Body_00']) and min(verts[offset+i].z for i in p.vertices)>1.30:faces.append(tuple(offset+i for i in p.vertices))
    ev.to_mesh_clear()
surface=BVHTree.FromPolygons(verts,faces);checks={}
for r in report['guides']:
    ob=bpy.data.objects[r['object']];sp=ob.data.splines[0];points=sp.bezier_points
    root=ob.matrix_world@points[0].co;hit,normal,index,dist=surface.find_nearest(root)
    # Probe only the visible portion. Inward buried root stems are intentional.
    samples=[]
    for i in range(r['visible_start_index'],len(points)-1):
        a,b=points[i],points[i+1]
        for local in interpolate_bezier(a.co,a.handle_right,b.handle_left,b.co,16):
            p=ob.matrix_world@local;h,n,_,d=surface.find_nearest(p);signed=(p-h).dot(n)
            samples.append({'point_m':list(p),'nearest_distance_m':d,'signed_distance_m':signed})
    inside=[s for s in samples if s['signed_distance_m']<-.0015]
    anchor=bpy.data.objects['ROOT_'+r['id']];anchor_error=(anchor.matrix_world.translation-root).length
    checks[r['id']]={'native_type':ob.type,'spline_type':sp.type,'control_points':len(points),'free_handles':all(p.handle_left_type=='FREE' and p.handle_right_type=='FREE' for p in points),'head_bone_parent':ob.parent_bone,'root_distance_m':dist,'root_anchor_alignment_error_m':anchor_error,'min_signed_skin_clearance_m':min((s['signed_distance_m'] for s in samples),default=0),'visible_samples_below_skin':len(inside),'skin_probe_samples':len(samples),'penetration_samples':inside}
new_mesh=list(bpy.data.collections['03_HAIR_MESH_NOT_GENERATED'].objects)
result={'guide_count':len(checks),'new_hair_mesh_count':len(new_mesh),'root_pass':all(c['root_distance_m']<=.0005 and c['root_anchor_alignment_error_m']<1e-6 for c in checks.values()),'native_editable_bezier_pass':all(c['native_type']=='CURVE' and c['spline_type']=='BEZIER' and c['free_handles'] for c in checks.values()),'visible_skin_clearance_pass':not any(c['visible_samples_below_skin'] for c in checks.values()),'checks':checks,'clearance_limitations':'Nearest oriented surface test is diagnostic on the existing partly open layered head skin, not a watertight signed-distance proof.'}
(out/'guide-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'}),flush=True)
for gid,c in checks.items():print(gid,'root_mm',round(c['root_distance_m']*1000,3),'clearance_mm',round(c['min_signed_skin_clearance_m']*1000,3),'inside_samples',c['visible_samples_below_skin'],flush=True)
