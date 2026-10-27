import bpy,bmesh,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
scene=bpy.context.scene
assert scene.name=='Geometry_Failure_Analysis_V2'
def region(p):
    if p.z>1.49:return 'cranium'
    if p.z<1.34:return 'neck'
    if 1.424<p.z<1.474 and 0.014<abs(p.x)<0.078:return 'eyelid/socket'
    if 1.373<p.z<1.405 and abs(p.x)<0.034:return 'mouth/lip'
    if 1.395<p.z<1.447 and abs(p.x)<0.020:return 'nose/bridge'
    if p.z<1.385:return 'jaw/chin/underjaw'
    return 'cheek/temple'
def segment_triangle(p,q,a,b,c):
    d=q-p;e1=b-a;e2=c-a;h=d.cross(e2);det=e1.dot(h)
    if abs(det)<1e-14:return None
    inv=1/det;s=p-a;u=s.dot(h)*inv
    if u<0.000001 or u>0.999999:return None
    cross=s.cross(e1);v=d.dot(cross)*inv
    if v<0.000001 or u+v>0.999999:return None
    t=e2.dot(cross)*inv
    if t<=0.000001 or t>=0.999999:return None
    return p+d*t
def triangle_cross(a,b):
    for i in range(3):
        p=segment_triangle(a[i],a[(i+1)%3],b[0],b[1],b[2])
        if p is not None:return p
    for i in range(3):
        p=segment_triangle(b[i],b[(i+1)%3],a[0],a[1],a[2])
        if p is not None:return p
    return None
meshes={};records={};patches={}
for ob in scene.objects:
    if ob.type!='MESH':continue
    me=ob.data;bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table();bm.normal_update()
    loose=sum(not v.link_faces for v in bm.verts);overconnected=sum(len(e.link_faces)>2 for e in bm.edges);boundary=sum(len(e.link_faces)==1 for e in bm.edges)
    zero=[f for f in bm.faces if f.calc_area()<1e-12]
    winding=sum(len(e.link_faces)==2 and e.link_loops[0].vert==e.link_loops[1].vert for e in bm.edges)
    warped=[];folded=[];zero_edges=sum(e.calc_length()<1e-8 for e in bm.edges)
    for f in bm.faces:
        if len(f.verts)==4:
            a,b,c,d=[v.co for v in f.verts];n1=(b-a).cross(c-a);n2=(c-a).cross(d-a)
            if n1.length>1e-14 and n2.length>1e-14:
                dot=n1.normalized().dot(n2.normalized())
                if dot<0.25:warped.append({'face':f.index,'triangle_normal_dot':dot,'center':list(ob.matrix_world@f.calc_center_median()),'region':region(ob.matrix_world@f.calc_center_median())})
    for e in bm.edges:
        if len(e.link_faces)==2:
            dot=e.link_faces[0].normal.dot(e.link_faces[1].normal)
            if dot<0:
                p=ob.matrix_world@((e.verts[0].co+e.verts[1].co)/2)
                folded.append({'edge':[v.index for v in e.verts],'normal_dot':dot,'region':region(p),'center':list(p)})
    tmp=bm.copy();original=[f.normal.copy() for f in tmp.faces];bmesh.ops.recalc_face_normals(tmp,faces=list(tmp.faces));normal_changes=sum(a.dot(f.normal)<0 for a,f in zip(original,tmp.faces));tmp.free()
    patches[ob.name]={'warped_quad_regions':{},'folded_edge_regions':{}}
    for item in warped:patches[ob.name]['warped_quad_regions'][item['region']]=patches[ob.name]['warped_quad_regions'].get(item['region'],0)+1
    for item in folded:patches[ob.name]['folded_edge_regions'][item['region']]=patches[ob.name]['folded_edge_regions'].get(item['region'],0)+1
    meshes[ob.name]={'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'triangles':sum(len(p.vertices)-2 for p in me.polygons),'quads':sum(len(p.vertices)==4 for p in me.polygons),'ngons':sum(len(p.vertices)>4 for p in me.polygons),'boundary_edges':boundary,'nonmanifold_overconnected_edges':overconnected,'inconsistent_winding_edges':winding,'loose_vertices':loose,'zero_length_edges':zero_edges,'degenerate_faces':len(zero),'normals_that_would_flip_on_recalculate':normal_changes,'severely_warped_quads':len(warped),'adjacent_face_folds_over_90_degrees':len(folded),'warped_quad_examples':warped[:24],'folded_edge_examples':folded[:24],'modifiers':[m.type for m in ob.modifiers]}
    me.calc_loop_triangles();verts=[ob.matrix_world@v.co for v in me.vertices];triangles=[tuple(t.vertices) for t in me.loop_triangles];owners=[t.polygon_index for t in me.loop_triangles]
    records[ob.name]={'vertices':verts,'triangles':triangles,'owners':owners,'bvh':BVHTree.FromPolygons(verts,triangles,all_triangles=True)};bm.free()
intersections=[];names=list(records)
for ai,name in enumerate(names):
    one=records[name]
    for other_name in names[ai:]:
        two=records[other_name];potential=one['bvh'].overlap(two['bvh']);hits=[];tested=0
        for i,j in potential:
            if name==other_name:
                if i>=j or one['owners'][i]==two['owners'][j] or set(one['triangles'][i])&set(two['triangles'][j]):continue
            tested+=1
            a=[one['vertices'][v] for v in one['triangles'][i]];b=[two['vertices'][v] for v in two['triangles'][j]];p=triangle_cross(a,b)
            if p is not None:
                hits.append({'triangles':[i,j],'polygons':[one['owners'][i],two['owners'][j]],'point':list(p),'region':region(p)})
            if tested>=200000:break
        if hits:intersections.append({'objects':[name,other_name],'noncoplanar_crossing_pairs':len(hits),'tested_candidate_pairs':tested,'sampled':tested>=200000,'examples':hits[:20],'interpretation':'Self crossings indicate a defect. Cross-part eye/skin and ear/skin intersections also include intentionally buried attachment surfaces; compare matcap for visible faults.'})
result={'scene':scene.name,'inspection':'Frozen V2 head-002; read-only geometry analysis through live MCP','meshes':meshes,'regions':patches,'triangle_intersections':intersections,'thresholds':{'degenerate_area_m2':1e-12,'zero_edge_m':1e-8,'warped_quad_triangle_normal_dot':0.25,'fold_adjacent_normal_dot':0},'limitations':['Triangle test excludes shared-vertex adjacency and coplanar pairs; per-quad warp and edge-fold tests cover a different defect class.','Normals are checked on an in-memory copy; no normals or geometry were changed in the inspected scene.','Cross-part buried eye/ear contacts are not all visible defects.']}
print(json.dumps(result))
