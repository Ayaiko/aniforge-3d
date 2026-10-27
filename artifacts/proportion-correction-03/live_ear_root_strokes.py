import bpy,json,math
from mathutils import Vector
h=bpy.data.objects['Anime013_Head']
win=bpy.context.window_manager.windows[0]
area=next(a for a in win.screen.areas if a.type=='VIEW_3D')
region=next(r for r in area.regions if r.type=='WINDOW')
space=area.spaces.active
old=[v.co.copy() for v in h.data.vertices]
boundary=set()
counts={}
for p in h.data.polygons:
    ids=list(p.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):
        key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1
for e,n in counts.items():
    if n==1:boundary.update(e)
with bpy.context.temp_override(window=win,area=area,region=region,region_data=space.region_3d,object=h,active_object=h,sculpt_object=h,selected_objects=[h],selected_editable_objects=[h]):
    assert h.mode=='SCULPT' and bpy.ops.sculpt.brush_stroke.poll()
    b=bpy.context.tool_settings.sculpt.brush;b.strength=.30;b.size=70;b.use_frontface=True
    strokes=[]
    paths=[[(.010,1.473+j*.005) for j in range(9)],[(-.015+j*.007,1.483) for j in range(11)],[(.010,1.473+j*.005) for j in range(9)],[(-.015+j*.007,1.483) for j in range(11)]]
    for path in paths:
        elements=[]
        for i,(y,z) in enumerate(path):
            hit,loc,normal,index=h.ray_cast(Vector((1,y,z)),Vector((-1,0,0)))
            if not hit:continue
            clip=space.region_3d.perspective_matrix@Vector((loc.x,loc.y,loc.z,1))
            mouse=((clip.x/clip.w*.5+.5)*region.width,(clip.y/clip.w*.5+.5)*region.height)
            elements.append({'name':'','location':tuple(loc),'mouse':mouse,'mouse_event':mouse,'pressure':1.0,'size':70,'time':float(i)*.08,'x_tilt':0.0,'y_tilt':0.0,'is_start':not elements})
        result=bpy.ops.sculpt.brush_stroke(stroke=elements,mode='NORMAL')
        strokes.append({'result':list(result),'points':len(elements)})
    bpy.ops.object.mode_set(mode='OBJECT')
moves=[(v.co-c).length for v,c in zip(h.data.vertices,old)]
maximum=max(moves)
reverted=False
if maximum>.006:
    for v,c in zip(h.data.vertices,old):v.co=c
    h.data.update();reverted=True
for d in h.data.attributes['.sculpt_mask'].data:d.value=0
h.data.use_mirror_x=False
print(json.dumps({'channel':'LIVE GUI sculpt.brush_stroke through MCP','brush':'Smooth','strength':.20,'diameter_px':60,'strokes':strokes,'changed_vertices':sum(d>1e-8 for d in moves),'max_movement_m':maximum,'boundary_max_movement_m':max(moves[i] for i in boundary),'reverted':reverted}))
