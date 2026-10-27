"""Phase 1 ONLY: genuine editable 3D Beziers with multi-view correspondence.
No new hair meshes or strand/detail geometry are generated.
"""
from pathlib import Path
import sys,math,json,shutil,hashlib
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
enable_vrm();source=ROOT/'models/researcher-a-reconstruction-master-v0.3.blend'
out=ROOT/'previews/v0.5';out.mkdir(exist_ok=True)
backup=ROOT/'models/backups/researcher-a-before-hair-guides-v0.5.blend'
if not backup.exists():shutil.copy2(source,backup)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(source)==digest(backup)
bpy.ops.wm.open_mainfile(filepath=str(source));reset_pose();setup()
scene=bpy.context.scene;scene.render.resolution_x=800;scene.render.resolution_y=900;scene.render.film_transparent=True
cal=json.loads((ROOT/'previews/v0.3/reference-calibration.json').read_text());scale=cal['meters_per_reference_pixel'];ez=cal['eye_z']
guidecol=bpy.data.collections.new('01_HAIR_GUIDES_EDITABLE');scene.collection.children.link(guidecol)
anchorcol=bpy.data.collections.new('02_ROOT_ATTACHMENTS');scene.collection.children.link(anchorcol)
meshcol=bpy.data.collections.new('03_HAIR_MESH_NOT_GENERATED');scene.collection.children.link(meshcol)
archive=bpy.data.collections.new('00_ORIGINAL_HAIR_v03_ARCHIVE');scene.collection.children.link(archive)
original_hair=[o for o in bpy.data.objects if o.type=='MESH' and (o.name.startswith(('Hair_','Front_')) or o.name=='Researcher_BobCap' or o.get('reconstruction_tier'))]
for ob in original_hair:
    for col in list(ob.users_collection):col.objects.unlink(ob)
    archive.objects.link(ob)
archive.hide_render=True;archive.hide_viewport=True
verts=[];polys=[];metadata=[]
for name in ['Body','Face']:
    ob=bpy.data.objects[name];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();start=len(verts)
    verts.extend([ev.matrix_world@v.co for v in me.vertices])
    for p in me.polygons:
        mat=me.materials[p.material_index]
        if any(s in mat.name for s in ['SKIN','Body_00']) and min(verts[start+i].z for i in p.vertices)>1.47:
            polys.append(tuple(start+i for i in p.vertices));metadata.append({'object':name,'evaluated_polygon':p.index})
    ev.to_mesh_clear()
assert polys,'No actual head skin found'
bvh=BVHTree.FromPolygons(verts,polys)

# Primary flow annotations: (XZ source trace, matching side U at the same Z).
# Side correspondence is explicitly inferred where a strand is hidden by the head.
specs=[
('F01','Main diagonal fringe','front',[(225,30),(205,80),(182,130),(162,180),(143,211)],[140,100,75,63,67],['front','side'],'Back projection is hidden by the head.'),
('F02','Inner fringe layer','front',[(230,63),(221,108),(205,152),(184,193),(165,214)],[131,92,73,66,76],['front','side'],'Ends stagger above the upper frame, not on the pupil.'),
('F03','Outer fringe sweep','front',[(222,25),(185,60),(145,113),(111,172),(101,224),(113,294),(132,332)],[163,121,95,99,119,151,184],['front'],'Most of this far-side clump is occluded in the right-side drawing.'),
('L01','Lateral middle bob','front',[(222,23),(160,46),(103,103),(72,188),(68,274),(88,340)],[177,145,118,126,158,200],['front'],'Side depth inferred under far-side overlap; needs volume review.'),
('L02','Lateral outer bob','front',[(220,16),(145,40),(75,124),(38,222),(45,305),(76,352)],[190,165,151,173,205,228],['front','back'],'Far-side path; back correspondence follows outer overlap, not the same painted line.'),
('R01','Short side of part','front',[(232,47),(260,85),(280,142),(285,184),(281,207)],[158,132,130,150,174],['front','side'],'Defines the right forehead edge and turns back toward the temple.'),
('R02','Ear tuck','front',[(236,26),(287,65),(311,131),(312,179),(297,202)],[180,163,175,198,217],['front','side'],'Must terminate above the exposed character-left ear.'),
('R03','Near-side bob outer volume','front',[(239,16),(302,61),(342,153),(354,249),(335,318),(305,347)],[210,290,366,382,358,305],['front','side','back'],'Primary side-volume guide; front/back drawing widths are not identical.'),
('B01','Rear left outer sweep','back',[(190,21),(117,55),(67,145),(43,247),(62,312),(118,345)],[225,300,368,383,350,285],['back','side'],'Front view hidden behind near-side bob.'),
('B02','Rear left middle layer','back',[(195,25),(150,74),(113,165),(110,259),(137,318),(169,341)],[230,313,357,363,335,277],['back','side'],'Curves inward toward the nape instead of descending straight.'),
('B03','Rear centre-left layer','back',[(198,26),(179,89),(165,184),(175,276),(192,326),(202,343)],[234,323,358,354,322,274],['back'],'Side correspondence inferred behind the outer layer.'),
('B04','Rear centre-right layer','back',[(203,28),(225,91),(238,181),(236,273),(221,324),(205,344)],[233,321,355,351,319,270],['back'],'Pairs with B03 as overlapping inward arcs, not equal vertical strips.'),
('B05','Rear right middle layer','back',[(208,26),(256,74),(288,165),(290,257),(264,317),(228,342)],[224,307,350,354,325,267],['back'],'Far-side depth is an inference and requires oblique review.'),
('B06','Rear right outer sweep','back',[(216,23),(294,61),(340,157),(359,253),(340,314),(291,344)],[210,292,350,359,331,276],['back','side'],'Unequal curvature/end position preserves the reference asymmetry.')]
palette=[(1,.22,.16,1),(1,.6,.04,1),(.95,.25,.65,1),(.3,.85,.2,1),(.0,.72,.72,1),(.2,.45,1,1),(.55,.3,1,1)]
materials=[]
for i,c in enumerate(palette):
    mat=bpy.data.materials.new('Guide colour %02d'%i);nodes=mat.node_tree.nodes;nodes.clear();output=nodes.new('ShaderNodeOutputMaterial');emission=nodes.new('ShaderNodeEmission');emission.inputs['Color'].default_value=c;emission.inputs['Strength'].default_value=.8;mat.node_tree.links.new(emission.outputs[0],output.inputs['Surface']);mat.diffuse_color=c;materials.append(mat)
arm=bpy.data.objects['Armature'];report=[]
def parent_head(ob):
    ob.parent=arm;ob.parent_type='BONE';ob.parent_bone='J_Bip_C_Head';bpy.context.view_layer.update();ob.matrix_world=Matrix.Identity(4);bpy.context.view_layer.update()
for index,(gid,label,view,trace,side_u,visible,note) in enumerate(specs):
    points=[]
    for (u,v),su in zip(trace,side_u):
        x=(u-200)*scale*(-1 if view=='back' else 1);points.append(Vector((x,(su-200)*scale,ez-(v-222)*scale)))
    desired=points[0];hit,normal,poly_index,distance=bvh.find_nearest(desired)
    assert hit is not None;root=hit+normal*.0003
    # The physical attachment is not falsely represented as the visible painted part.
    if (root-desired).length>.0015:points.insert(0,root);visible_start=1
    else:points[0]=root;visible_start=0
    data=bpy.data.curves.new(gid+'_BezierData','CURVE');data.dimensions='3D';data.resolution_u=24;data.bevel_depth=.00045;data.bevel_resolution=2;data.use_fill_caps=True
    spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for i,(p,co) in enumerate(zip(spline.bezier_points,points)):
        p.co=co;previous=points[max(0,i-1)];following=points[min(len(points)-1,i+1)];tangent=(following-previous)/6
        lengths=[(co-previous).length,(following-co).length];positive=[d for d in lengths if d>1e-8];limit=.40*min(positive)
        if tangent.length>limit:tangent.normalize();tangent*=limit
        p.handle_left_type=p.handle_right_type='FREE';p.handle_left=co-tangent;p.handle_right=co+tangent
    ob=bpy.data.objects.new(gid+'__'+label.replace(' ','_'),data);guidecol.objects.link(ob);data.materials.append(materials[index%len(materials)]);ob.show_in_front=True;parent_head(ob)
    ob['guide_id']=gid;ob['clump_name']=label;ob['source_view']=view;ob['visible_start_index']=visible_start;ob['primary_hair_guide']=True;ob['visible_in_reference']=','.join(visible);ob['correspondence_note']=note
    anchor=bpy.data.objects.new('ROOT_'+gid,None);anchorcol.objects.link(anchor);anchor.empty_display_type='SPHERE';anchor.empty_display_size=.0015;parent_head(anchor);anchor.matrix_world=Matrix.Translation(root);anchor['root_surface_object']=metadata[poly_index]['object'];anchor['root_surface_evaluated_polygon']=metadata[poly_index]['evaluated_polygon'];anchor.hide_render=True
    scene.view_layers[0].update();actual_root=ob.matrix_world@spline.bezier_points[0].co;nearest=bvh.find_nearest(actual_root)
    projections={}
    for angle in ['front','side','back','quarter']:
        camera=bpy.data.objects['REF_'+angle];coords=[]
        for point in spline.bezier_points:
            q=world_to_camera_view(scene,camera,ob.matrix_world@point.co);coords.append([q.x*400,(1-q.y)*450])
        projections[angle]=coords
    report.append({'id':gid,'object':ob.name,'label':label,'source_view':view,'reference_trace':trace,'side_u':side_u,'primary_visible_views':visible,'correspondence_note':note,'visible_start_index':visible_start,'control_points_world_m':[list(ob.matrix_world@p.co) for p in spline.bezier_points],'projections':projections,'root_distance_m':nearest[3],'root_surface':metadata[nearest[2]],'colour':list(palette[index%len(palette)])})

# Snapshot native guide curves only, with every projection present. Occluded
# correspondences are explicitly distinguished in the companion overlay legend.
hidden={o.name:o.hide_render for o in bpy.data.objects}
for ob in bpy.data.objects:
    if ob.type=='MESH':ob.hide_render=True
for view in ['front','side','back','quarter']:
    scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(out/('guides-'+view+'.png'));bpy.ops.render.render(write_still=True)
for view in ['front','side','back']:
    for record in report:bpy.data.objects[record['object']].hide_render=view not in record['primary_visible_views']
    scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(out/('focused-guides-'+view+'.png'));bpy.ops.render.render(write_still=True)
for record in report:bpy.data.objects[record['object']].hide_render=False
# Root/context images display the actual inherited head and guide volume.
for ob in bpy.data.objects:
    if ob.type=='MESH' and ob not in original_hair:ob.hide_render=hidden[ob.name]
scene.render.film_transparent=False
for view in ['front','side','back','quarter']:
    scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(out/('context-'+view+'.png'));bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['REF_quarter']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_overlays=True;space.region_3d.view_perspective='CAMERA';space.camera=scene.camera
scene['hair_workflow_phase']='Phase 1 only — editable multi-view hair guides; no hair meshes generated'
summary={'source':str(source),'source_sha256':digest(source),'backup':str(backup),'calibration_source':'previews/v0.3/reference-calibration.json','guide_count':len(report),'new_hair_mesh_count':0,'curve_display_bevel_m':.00045,'root_attachment_tolerance_m':.0005,'root_attachment_pass':all(r['root_distance_m']<=.0005 for r in report),'guides':report,'limits':['Correspondence between painted views is authored/inferred, not a measured unique 3D solution.','Front and back source widths differ; no reference image has been stretched to hide this conflict.','Guide projection matching at authored controls is not an automatic artistic pass.','Thin bevel is display-only curve visualization, not generated hair clump geometry.']}
(out/'guide-manifest.json').write_text(json.dumps(summary,indent=2));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'models/researcher-a-hair-guides-v0.5.blend'))
assert digest(source)==digest(backup);print('GUIDE SYSTEM SAVED',len(report),'ROOT PASS',summary['root_attachment_pass'],'NEW HAIR MESHES 0',flush=True)
