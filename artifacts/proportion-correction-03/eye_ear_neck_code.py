import bpy,json,math

def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
eyes=[]
for name,target_u in [('Anime013_Eye_L',150.1),('Anime013_Eye_R',245.0)]:
    o=bpy.data.objects[name]
    iris={i for p in o.data.polygons if p.material_index in [1,2] for i in p.vertices}
    pupil={i for p in o.data.polygons if p.material_index==2 for i in p.vertices}
    cx=(min(o.data.vertices[i].co.x for i in iris)+max(o.data.vertices[i].co.x for i in iris))/2
    cz=(min(o.data.vertices[i].co.z for i in iris)+max(o.data.vertices[i].co.z for i in iris))/2
    ri=max(math.hypot(o.data.vertices[i].co.x-cx,o.data.vertices[i].co.z-cz) for i in iris)
    rp=max(math.hypot(o.data.vertices[i].co.x-cx,o.data.vertices[i].co.z-cz) for i in pupil)
    shift=(target_u-200)*.0007797915761063738-cx
    old=[v.co.copy() for v in o.data.vertices]
    for v,c in zip(o.data.vertices,old):
        dx=c.x-cx;dz=c.z-cz;r=math.hypot(dx,dz)
        front=ease((-.068-c.y)/.007)
        factor=.75+.25*ease((r-rp)/max(ri-rp,.0001))
        factor=1+(factor-1)*front
        cap=1-ease((r-(ri+.0005))/(.020-ri-.0005))
        v.co.x=cx+dx*factor+shift*cap*front
        v.co.z=cz+dz*factor
        v.co.y=c.y+.00025*math.exp(-(r/max(rp,1e-6))**4)*front
    o.data.update()
    eyes.append({'name':name,'target_iris_u_px':target_u,'iris_shift_x_m':shift,'pupil_radius_scale':.75,'max_move_m':max((v.co-c).length for v,c in zip(o.data.vertices,old))})
h=bpy.data.objects['Anime013_Head'];old=[v.co.copy() for v in h.data.vertices];ear_count=0;neck_count=0
for v,c in zip(h.data.vertices,old):
    x,y,z=c
    if 1.402<z<1.469 and abs(x)>.075:
        w=ease((abs(x)-.075)/.010)*ease((1.469-z)/.006)
        v.co.x=x-(1 if x>0 else -1)*.004*w
        v.co.z=z-(z-1.438)*.08*w
        if w>0:ear_count+=1
    if z<1.405 and y>-.035:
        w=ease((1.405-z)/.065)*ease((y+.035)/.015)
        v.co.z+=.012*w
        v.co.x*=1-.15*w
        if w>0:neck_count+=1
h.data.update()
print(json.dumps({'stage':'reference-gaze-ear-neck-proportion','eyes':eyes,'ear_vertices':ear_count,'neck_vertices':neck_count,'head_max_move_m':max((v.co-c).length for v,c in zip(h.data.vertices,old)),'colors_changed':False}))
# Prepare a local scalp/ear-root mask. Actual strokes run on the next MCP call
# after Blender has initialized Sculpt Mode and the selected brush asset.
win=bpy.context.window_manager.windows[0];area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
mask=h.data.attributes.get('.sculpt_mask')
if mask is None:mask=h.data.attributes.new('.sculpt_mask','FLOAT','POINT')
for i,v in enumerate(h.data.vertices):
    x,y,z=v.co
    w=math.exp(-((y-.014)/.045)**4-((z-1.490)/.027)**4)*ease((abs(x)-.060)/.015)
    if z<1.467 or z>1.530 or y<-.035 or y>.075:w=0
    mask.data[i].value=1-w
h.data.use_mirror_x=True
space=area.spaces.active;space.region_3d.view_rotation=bpy.data.objects['REF_side'].matrix_world.to_quaternion();space.region_3d.view_location=(0,0,1.45);space.region_3d.view_distance=.35;space.region_3d.view_perspective='ORTHO'
with bpy.context.temp_override(window=win,area=area,region=region):
    bpy.ops.object.mode_set(mode='SCULPT')
    bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth')
print('EAR_ROOT_SCULPT_READY')
