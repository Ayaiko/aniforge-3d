"""Direct eye-contour fitting against reference, anchored ear scaling and skin stitching."""
from pathlib import Path
import json,math,collections
import numpy as np
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp'
parts=json.loads((out/'anime-011-numeric-fit.json').read_text());source=json.loads((out/'vroid-anime-payload.json').read_text())
skin=parts[0];verts=skin['vertices'];edge_count=collections.Counter(tuple(sorted((a,b))) for f in skin['faces'] for a,b in zip(f,f[1:]+f[:1]));adj=collections.defaultdict(list)
for (a,b),n in edge_count.items():
    if n==1:adj[a].append(b);adj[b].append(a)
seen=set();loops=[]
for start in adj:
    if start in seen:continue
    comp=[];stack=[start]
    while stack:
        v=stack.pop()
        if v in seen:continue
        seen.add(v);comp.append(v);stack.extend(adj[v])
    if len(comp)==24 and min(verts[i][2] for i in comp)>1.425 and max(verts[i][2] for i in comp)<1.47:loops.append(comp)
assert len(loops)==2
S=.0007797915761063738;EYE=1.446197748184204
reference=[([120,216],[134,211],[155,212],[168,223]),([120,216],[133,232],[152,233],[168,223]),([225,222],[236,212],[257,208],[274,212]),([225,222],[239,234],[263,229],[274,212])]
controls={};targets={};eye_vertex_ids=[]
def bezier(points,t):return [sum(points[k][j]*[(1-t)**3,3*t*(1-t)**2,3*t*t*(1-t),t**3][k] for k in range(4)) for j in range(2)]
for component in loops:
    start=min(component,key=lambda i:verts[i][0]);end=max(component,key=lambda i:verts[i][0]);order=[start];previous=None;current=start
    while True:
        following=next(v for v in adj[current] if v!=previous)
        if following==start:break
        order.append(following);previous,current=current,following
    k=order.index(end);paths=[order[:k+1],[order[0]]+list(reversed(order[k:]))]
    paths.sort(key=lambda path:sum(verts[i][2] for i in path)/len(path),reverse=True)
    left=sum(verts[i][0] for i in component)<0;base=0 if left else 2
    xmin,xmax=verts[start][0],verts[end][0]
    for which,path in enumerate(paths):
        for i in path:
            t=(verts[i][0]-xmin)/(xmax-xmin);u,v=bezier(reference[base+which],t)
            controls[i]=[verts[i][0],verts[i][2]];targets[i]=[(u-200)*S,EYE+(222-v)*S]
    eye_vertex_ids.extend(component)
controls_list=list(controls);A=np.array([controls[i] for i in controls_list]);D=np.array([np.array(targets[i])-controls[i] for i in controls_list])
anchors=np.array([[-.095,1.35],[0,1.35],[.095,1.35],[-.095,1.395],[0,1.395],[.095,1.395],[-.095,1.49],[0,1.49],[.095,1.49],[-.09,1.59],[0,1.59],[.09,1.59],[0,1.44]])
A=np.vstack([A,anchors]);D=np.vstack([D,np.zeros_like(anchors)])
# Thin-plate deformation field with fixed mouth, nose, jaw and crown anchors.
origin=np.array([0,1.446]);scale=.04;An=(A-origin)/scale
def kernel(distance):return distance**2*np.log(np.maximum(distance,1e-15))
K=kernel(np.linalg.norm(An[:,None]-An[None,:],axis=2));P=np.column_stack([np.ones(len(A)),An]);M=np.block([[K+np.eye(len(A))*1e-9,P],[P.T,np.zeros((3,3))]])
coeff=np.linalg.solve(M,np.vstack([D,np.zeros((3,2))]))
def deform(co):
    x,y,z=co;point=(np.array([x,z])-origin)/scale;r=np.linalg.norm(An-point,axis=1);delta=np.r_[kernel(r),1,point]@coeff
    t=max(0,min(1,(.020-y)/.070));front=t*t*(3-2*t)
    x+=float(delta[0])*front;z+=float(delta[1])*front
    y-=.009*math.exp(-((z-1.445)/.042)**2)*front
    return [round(v,7) for v in (x,y,z)]
# Restore original ear-root positions, then shrink only the part away from the root.
def original_ear(co):
    x,y,z=-(co[0]-.00025545)*.91,co[2],co[1]
    front=1/(1+math.exp((y+.035)/.012));eye=math.exp(-((z-1.4462)/.026)**2)*math.exp(-((abs(x)-.040)/.032)**2)*front;z+=.12*(abs(x)-.040)*eye
    nose=math.exp(-(x/.019)**2-((z-1.414)/.019)**2)*front;z+=.005*nose
    mouth=math.exp(-(x/.033)**2-((z-1.389)/.014)**2)*front;x*=1-.23*mouth;y+=.007/(1+math.exp((z-1.385)/.012))*front;z-=.0035*math.exp(-((z-1.355)/.023)**2)*front
    return [round(v,7) for v in (x,y,z)]
ids=source['primitives'][8]['indices'];used=sorted(set(ids));remap={v:i for i,v in enumerate(used)};ear_faces=[[remap[v] for v in ids[i:i+3]] for i in range(0,len(ids),3)];ears=[original_ear(source['positions'][i]) for i in used]
roots=[i for i,co in enumerate(ears) if min(math.dist(co,h) for h in verts)<1e-6];assert len(roots)>=20
eadj=collections.defaultdict(set)
for f in ear_faces:
    for a,b in zip(f,f[1:]+f[:1]):eadj[a].add(b);eadj[b].add(a)
bins=collections.defaultdict(list)
for i,co in enumerate(ears):bins[tuple(round(v,6) for v in co)].append(i)
for group in bins.values():
    for i in group:eadj[i].update(set(group)-{i})
distance={i:0 for i in roots};queue=collections.deque(roots)
while queue:
    i=queue.popleft()
    for j in eadj[i]:
        if j not in distance:distance[j]=distance[i]+1;queue.append(j)
for i,co in enumerate(ears):
    x,y,z=co;sign=1 if x>0 else -1;t=min(1,distance.get(i,5)/4);w=t*t*(3-2*t)
    desired=[sign*.078+(x-sign*.078)*.75,.010+(y-.010)*.8,1.438+(z-1.438)*.8]
    ears[i]=[co[k]+(desired[k]-co[k])*w for k in range(3)]
offset=len(verts);head={'name':'Anime012_Head','vertices':[deform(co) for co in verts+ears],'faces':skin['faces']+[[v+offset for v in f] for f in ear_faces]}
newparts=[head]+[{'name':o['name'].replace('Anime011','Anime012'),'vertices':[deform(co) for co in o['vertices']],'faces':o['faces']} for o in parts if o['name'] in ['Anime011_EyeWhite','Anime011_MouthInterior']]
calls=[]
setup="""import bpy
bpy.ops.wm.save_as_mainfile(filepath='/tmp/vtuber-anime-head-011-before-contours.blend',copy=True)
scene=bpy.data.scenes.new('Anime_Reference_012')
bpy.context.window.scene=scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
shade=scene.display.shading
shade.light='MATCAP'
shade.studio_light='clay_studio.exr'
shade.color_type='SINGLE'
shade.show_cavity=False
shade.show_shadows=False
for ob in bpy.data.scenes['Geometry_Failure_Analysis_V2'].objects:
    if ob.type=='CAMERA':scene.collection.objects.link(ob)
print('REFERENCE_CONTOUR_FIT_012_NEW_VERSION')
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='anime-012-scene'))
for part in newparts:
    on=part['name'];coords=part['vertices'];faces=part['faces']
    code=f"import bpy\ncoords={coords!r}\nfaces={faces!r}\nme=bpy.data.meshes.new({on+'_Mesh'!r})\nme.from_pydata(coords,[],faces)\nme.update()\nob=bpy.data.objects.new({on!r},me)\nbpy.context.scene.collection.objects.link(ob)\nfor poly in me.polygons:poly.use_smooth=True\nob['primary_changes']='Reference eye contours; anchored cheek/nose/jaw; shallower orbit; anchored ear reduction'\nprint('REFERENCE_SURFACE_CREATED',ob.name)"
    calls.append(dict(tool='execute_blender_code',arguments={'code':code},label='anime-012-'+on))
cleanup="""import bpy,bmesh
from mathutils import Vector
ob=bpy.data.objects['Anime012_Head']
bm=bmesh.new()
bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,1.325),plane_no=(0,0,1),dist=.0000001,clear_inner=True,clear_outer=False)
cut=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-1.325)<.000001 for v in e.verts)]
if cut:
    filled=bmesh.ops.holes_fill(bm,edges=cut,sides=0)['faces']
    bmesh.ops.triangulate(bm,faces=filled)
bmesh.ops.join_triangles(bm,faces=list(bm.faces),angle_face_threshold=.4,angle_shape_threshold=.8)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(ob.data)
bm.free()
ob.data.update()
print('ROOT_SEAMS_WELDED_AND_NECK_CUT_CAPPED',len(ob.data.vertices),len(ob.data.polygons))
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':cleanup},label='anime-012-root-neck-cleanup'))
for view in ['front','side','quarter']:
    code=f"import bpy\nscene=bpy.context.scene\nscene.camera=bpy.data.objects['REF_{view}']\nscene.render.filepath='/tmp/vtuber-anime-012-{view}.png'\nbpy.ops.render.render(write_still=True)"
    calls.extend([dict(tool='execute_blender_code',arguments={'code':code},label='render-anime-012-'+view),dict(tool='look',arguments={'image':'Render Result','max_size':900},label='anime-012-'+view)])
(out/'anime-012-fit-controls.json').write_text(json.dumps({'eye_handles':{str(i):{'source':controls[i],'target':targets[i]} for i in controls},'anchors':anchors.tolist(),'ear_root_vertices':roots,'primary_gate':'Eye shape is checked against actual reference contours, not generic human proportions.'},indent=2))
(out/'anime-012-numeric-fit.json').write_text(json.dumps(newparts));(out/'anime-012-request.json').write_text(json.dumps(calls));print(len(calls),'MCP steps; reference eye handles',len(controls),'ear anchors',len(roots))
