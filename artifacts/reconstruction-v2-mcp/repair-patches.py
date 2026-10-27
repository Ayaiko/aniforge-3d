import bpy, bmesh, json, math
from mathutils import Vector
scene=bpy.context.scene
assert scene.name=='Reconstruction_V2_MCP'
scene.camera=bpy.data.objects['REF_quarter']
bpy.ops.wm.save_as_mainfile(filepath='/Users/graind/Documents/ChatGPT/vTuber/models/reconstruction-v2/researcher-a-head-mcp-003-before.blend',copy=True)
head=bpy.data.objects['V2_Head_Skin_NEW']
features=json.loads(head['feature_loops'])
scale=0.0007797915761063738
eye_z=1.446197748184204
def z_of(v):
    return eye_z-(v-222)*scale
def point_on_bezier(points,t):
    return (1-t)**3*Vector(points[0])+3*(1-t)**2*t*Vector(points[1])+3*(1-t)*t*t*Vector(points[2])+t**3*Vector(points[3])
def sphere_front(x,z,cx,cz):
    q=((x-cx)/0.0225)**2+((z-cz)/0.0185)**2
    return -0.0565-0.0205*math.sqrt(max(0,1-q))
targets={
 'viewer_left':{'cx':146,'cy':224,'top':[(120,216),(134,211),(155,212),(168,223)],'bottom':[(120,216),(133,232),(152,233),(168,223)]},
 'viewer_right':{'cx':249,'cy':220,'top':[(225,222),(236,212),(257,208),(274,212)],'bottom':[(225,222),(239,234),(263,229),(274,212)]},
 'mouth':{'cx':200,'cy':298,'top':[(180,298),(192,296.7),(208,296),(220,296)],'bottom':[(180,298),(192,298.6),(209,298.1),(220,296)]}}
neighbors={}
for edge in head.data.edges:
    a,b=edge.vertices
    neighbors.setdefault(a,[]).append(b)
    neighbors.setdefault(b,[]).append(a)
repair=[]
for feature in features:
    target=targets[feature['part']]
    n=feature['outer_loop_vertices']
    opening=feature['opening_indices']
    first=min(opening)-3*n
    outer=[]
    for i in range(n):
        candidates=[v for v in neighbors[first+i] if v<first]
        assert len(candidates)==1,(feature['part'],i,candidates)
        outer.append(head.data.vertices[candidates[0]].co.copy())
    image=[Vector((200+p.x/scale,222-(p.z-eye_z)/scale)) for p in outer]
    area=sum(image[i].x*image[(i+1)%n].y-image[(i+1)%n].x*image[i].y for i in range(n))
    direction=1 if area>0 else -1
    angle0=math.atan2((image[0].y-target['cy'])/(10 if feature['part']=='mouth' else 18),(image[0].x-target['cx'])/(27 if feature['part']=='mouth' else 31))
    for row,blend in enumerate([0.32,0.63,1.0,1.0]):
        for i in range(n):
            angle=angle0+direction*2*math.pi*i/n
            t=(math.cos(angle)+1)/2
            q=point_on_bezier(target['top'] if math.sin(angle)<0 else target['bottom'],t)
            x=(q.x-200)*scale
            z=z_of(q.y)
            if feature['part']=='mouth':
                y=-0.091+0.003*(abs(x)/0.018)**2
            else:
                y=sphere_front(x,z,(target['cx']-200)*scale,z_of(target['cy']))-0.0012
            inner=Vector((x,y,z))
            p=outer[i].lerp(inner,blend)
            if feature['part']!='mouth':
                radius=((p.x-(target['cx']-200)*scale)/0.0225)**2+((p.z-z_of(target['cy']))/0.0185)**2
                if radius<1:p.y=min(p.y,sphere_front(p.x,p.z,(target['cx']-200)*scale,z_of(target['cy']))-0.0011)
            if row==1:p.y-=0.0003
            if row==3:p.y+=0.004 if feature['part']=='mouth' else 0.0008
            head.data.vertices[first+row*n+i].co=p
    repair.append({'part':feature['part'],'rings_rebuilt':4,'vertices':4*n,'method':'uniform angular topology flow replacing non-monotone polar mapping'})
# Adult stylized cranium under the future hair volume; facial landmarks preserved.
moved=0
for v in head.data.vertices:
    if v.co.z>1.49:
        t=max(0,min(1,(v.co.z-1.49)/0.11))
        v.co.z-=0.018*t*t*(3-2*t)
        moved+=1
bm=bmesh.new()
bm.from_mesh(head.data)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(head.data)
bm.free()
head.data.update()
head['mcp_reconstruction']='Eye/lip patch topology rebuilt in live Blender; upper cranium reshaped; no subdivision'
for ob in bpy.context.scene.objects:ob.select_set(False)
head.select_set(True)
bpy.context.view_layer.objects.active=head
for name in ['front','side','back']:
    camera=bpy.data.objects['REF_'+name]
    camera.data.show_background_images=True
    item=camera.data.background_images.new()
    item.image=bpy.data.images.load('/Users/graind/Documents/ChatGPT/vTuber/assets/references/alignment-v0.3/'+name+'.png',check_existing=True)
    item.alpha=0.35
    item.display_depth='BACK'
    item.frame_method='FIT'
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.camera=scene.camera
        area.spaces.active.shading.type='MATERIAL'
print(json.dumps({'repaired':repair,'crown_vertices_reshaped':moved,'scene':scene.name,'active':head.name,'subdivision_modifiers':len(head.modifiers)}))
