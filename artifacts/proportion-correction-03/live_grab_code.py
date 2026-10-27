import bpy,json
from mathutils import Vector
h=bpy.data.objects['Anime013_Head'];old=[v.co.copy() for v in h.data.vertices]
win=bpy.context.window_manager.windows[0];area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');space=area.spaces.active
candidate=[v for v in h.data.vertices if abs(v.co.x)<.013 and 1.366<v.co.z<1.376 and v.co.y<-.05]
def front_depth(v):return v.co.y
vertex=min(candidate,key=front_depth)
start=vertex.co.copy();finish=start+Vector((0,-.004,0));elements=[]
for i,loc in enumerate([start,finish]):
    clip=space.region_3d.perspective_matrix@Vector((loc.x,loc.y,loc.z,1));mouse=((clip.x/clip.w*.5+.5)*region.width,(clip.y/clip.w*.5+.5)*region.height)
    elements.append({'name':'','location':tuple(loc),'mouse':mouse,'mouse_event':mouse,'pressure':1.0,'size':180,'time':i*.25,'x_tilt':0.0,'y_tilt':0.0,'is_start':i==0})
with bpy.context.temp_override(window=win,area=area,region=region,region_data=space.region_3d,object=h,active_object=h,sculpt_object=h,selected_objects=[h],selected_editable_objects=[h]):
    assert bpy.ops.sculpt.brush_stroke.poll()
    b=bpy.context.tool_settings.sculpt.brush;b.strength=1.0;b.size=180;b.use_frontface=False
    result=bpy.ops.sculpt.brush_stroke(stroke=elements,mode='NORMAL')
    bpy.ops.object.mode_set(mode='OBJECT')
moves=[(v.co-c).length for v,c in zip(h.data.vertices,old)];reverted=False
if max(moves)>.006:
    for v,c in zip(h.data.vertices,old):v.co=c
    h.data.update();reverted=True
for value in h.data.attributes['.sculpt_mask'].data:value.value=0
print(json.dumps({'channel':'LIVE Sculpt Grab via MCP','start_vertex':vertex.index,'start':list(start),'requested_shift_y_m':-.004,'result':list(result),'changed_vertices':sum(m>1e-8 for m in moves),'max_move_m':max(moves),'reverted':reverted}))
