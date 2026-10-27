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
    b=bpy.context.tool_settings.sculpt.brush;b.strength=.20;b.size=60;b.use_frontface=True
    strokes=[]
    paths=[([(-.023+j*.0038,1.393) for j in range(13)],.32,55),([(-.023+j*.0038,1.393) for j in range(13)],.32,55),([(-.023+j*.0038,1.381) for j in range(13)],.25,55),([(-.023+j*.0038,1.381) for j in range(13)],.25,55),([(0,1.410+j*.005) for j in range(4)],.20,35),([(-.014+j*.004,1.357) for j in range(8)],.15,45)]
    for path,strength,diameter in paths:
        b.strength=strength
        b.size=diameter
        elements=[]
        for i,(x,z) in enumerate(path):
            hit,loc,normal,index=h.ray_cast(Vector((x,-1,z)),Vector((0,1,0)))
            if not hit:continue
            clip=space.region_3d.perspective_matrix@Vector((loc.x,loc.y,loc.z,1))
            mouse=((clip.x/clip.w*.5+.5)*region.width,(clip.y/clip.w*.5+.5)*region.height)
            elements.append({'name':'','location':tuple(loc),'mouse':mouse,'mouse_event':mouse,'pressure':1.0,'size':diameter,'time':float(i)*.08,'x_tilt':0.0,'y_tilt':0.0,'is_start':not elements})
        result=bpy.ops.sculpt.brush_stroke(stroke=elements,mode='NORMAL')
        strokes.append({'result':list(result),'points':len(elements),'strength':strength,'diameter_px':diameter})
    bpy.ops.object.mode_set(mode='OBJECT')
moves=[(v.co-c).length for v,c in zip(h.data.vertices,old)]
maximum=max(moves)
reverted=False
if maximum>.0045:
    for v,c in zip(h.data.vertices,old):v.co=c
    h.data.update();reverted=True
for d in h.data.attributes['.sculpt_mask'].data:d.value=0
print(json.dumps({'channel':'LIVE GUI sculpt.brush_stroke through MCP','brush':'Smooth','strength':.20,'diameter_px':60,'strokes':strokes,'changed_vertices':sum(d>1e-8 for d in moves),'max_movement_m':maximum,'boundary_max_movement_m':max(moves[i] for i in boundary),'reverted':reverted}))
