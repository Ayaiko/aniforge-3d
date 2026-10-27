"""Remove redundant overlapping geometry rather than repeatedly offsetting it."""
from pathlib import Path
import sys,json,bpy,bmesh
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from production_common import recalc
from reconstruction_review import render_iteration
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-09-clearance-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
removed=bpy.data.objects['Hair_RearMass_00'];bpy.data.objects.remove(removed,do_unlink=True)
ob=bpy.data.objects['Hair_FringeMain'];before=len(ob.data.vertices);bm=bmesh.new();bm.from_mesh(ob.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector((0,0,1.586)),plane_no=Vector((0,0,1)),dist=1e-7,clear_outer=True)
boundary=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-1.586)<1e-5 for v in e.verts)]
caps=bmesh.ops.holes_fill(bm,edges=boundary,sides=0)['faces'];uv=bm.loops.layers.uv.active
for f in caps:
    for loop in f.loops:loop[uv].uv=(.6+loop.vert.co.x*2,.84+loop.vert.co.y*2)
bmesh.ops.triangulate(bm,faces=caps);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob['reconstruction_tier']='Primary form - trimmed hidden root';ob['root_trim_z']=1.586
directory=render_iteration('10-root-cleanup')
(directory/'changes.json').write_text(json.dumps({'acceptance_before_phase':['Zero UV/normal errors','No coplanar hair overlap in official QA','Preserve visible fringe and bob silhouette'],'geometry_changes':['Removed Hair_RearMass_00, whose upper path duplicated Hair_RightBob','Trimmed covered root of FringeMain above z=1.586 m, capped and UV mapped the cut'],'fringe_vertices_before':before,'fringe_vertices_after':len(ob.data.vertices),'tertiary_details_added':0,'artistic_status':'Not approved: residual likeness differences remain'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-10-cleanup-v0.3.blend'))
