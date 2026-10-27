import bpy,json,math
from mathutils import Vector
h=bpy.data.objects['Anime013_Head']
win=bpy.context.window_manager.windows[0]
area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(window=win,area=area,region=region):
    if h.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
old=[v.co.copy() for v in h.data.vertices]
mask=h.data.attributes.get('.sculpt_mask')
if mask is None:mask=h.data.attributes.new('.sculpt_mask','FLOAT','POINT')
boundary=set()
edgefaces={}
for p in h.data.polygons:
    ids=list(p.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):
        key=tuple(sorted((a,b)));edgefaces[key]=edgefaces.get(key,0)+1
for edge,n in edgefaces.items():
    if n==1:boundary.update(edge)
for i,v in enumerate(h.data.vertices):
    x,y,z=v.co
    w=math.exp(-((abs(x)-.032)/.024)**4-((z-1.404)/.036)**4)
    if y>-.035 or z>1.432 or z<1.362 or abs(x)>.059 or (abs(x)<.013 and z>1.397) or i in boundary:w=0
    mask.data[i].value=1-w
h.data.use_mirror_x=False
space=area.spaces.active
space.region_3d.view_rotation=bpy.data.objects['REF_front'].matrix_world.to_quaternion()
space.region_3d.view_location=(0,0,1.44)
space.region_3d.view_distance=.35
space.region_3d.view_perspective='ORTHO'
with bpy.context.temp_override(window=win,area=area,region=region):
    bpy.ops.object.mode_set(mode='SCULPT')
    bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth')
    b=bpy.context.tool_settings.sculpt.brush;b.strength=.20;b.size=60;b.use_frontface=True
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)
    strokes=[]
    paths=[[(s*.034,1.424-j*.005) for j in range(9)] for s in [-1,1]]
    paths += [[(s*.017,1.394-j*.004) for j in range(6)] for s in [-1,1]]
    for path in paths:
        elements=[]
        for i,(x,z) in enumerate(path):
            hit,loc,normal,index=h.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
            if not hit:continue
            clip=space.region_3d.perspective_matrix@Vector((loc.x,loc.y,loc.z,1))
            mouse=((clip.x/clip.w*.5+.5)*region.width,(clip.y/clip.w*.5+.5)*region.height)
            elements.append({'name':'','location':tuple(loc),'mouse':mouse,'mouse_event':mouse,'pressure':1.0,'size':60,'time':float(i)*.08,'x_tilt':0.0,'y_tilt':0.0,'is_start':not elements})
        result=bpy.ops.sculpt.brush_stroke(stroke=elements,mode='NORMAL')
        strokes.append({'result':list(result),'points':len(elements)})
    bpy.ops.object.mode_set(mode='OBJECT')
moves=[(v.co-c).length for v,c in zip(h.data.vertices,old)];maximum=max(moves)
reverted=False
if maximum>.006:
    for v,c in zip(h.data.vertices,old):v.co=c
    h.data.update();reverted=True
for d in h.data.attributes['.sculpt_mask'].data:d.value=0
print(json.dumps({'channel':'LIVE GUI sculpt.brush_stroke through MCP','brush':'Smooth','strength':.20,'diameter_px':60,'strokes':strokes,'changed_vertices':sum(d>1e-8 for d in moves),'max_movement_m':maximum,'boundary_max_movement_m':max(moves[i] for i in boundary),'reverted':reverted}))
