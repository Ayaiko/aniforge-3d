import bpy,json,math
h=bpy.data.objects['Anime013_Head']
win=bpy.context.window_manager.windows[0];area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
with bpy.context.temp_override(window=win,area=area,region=region):
    if h.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
mask=h.data.attributes.get('.sculpt_mask')
if mask is None:mask=h.data.attributes.new('.sculpt_mask','FLOAT','POINT')
counts={}
for p in h.data.polygons:
    ids=list(p.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):
        key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1
boundary={i for e,n in counts.items() if n==1 for i in e}
for i,v in enumerate(h.data.vertices):
    x,y,z=v.co
    lip=math.exp(-(x/.032)**4-((z-1.389)/.014)**4)
    nose=math.exp(-(x/.015)**4-((z-1.419)/.018)**4)
    chin=math.exp(-(x/.023)**4-((z-1.359)/.012)**4)
    weight=max(lip,nose,chin)
    if y>-.035 or i in boundary:weight=0
    mask.data[i].value=1-weight
space=area.spaces.active;space.region_3d.view_rotation=bpy.data.objects['REF_front'].matrix_world.to_quaternion();space.region_3d.view_location=(0,0,1.44);space.region_3d.view_distance=.35;space.region_3d.view_perspective='ORTHO'
with bpy.context.temp_override(window=win,area=area,region=region):
    bpy.ops.object.mode_set(mode='SCULPT')
    result=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth')
print(json.dumps({'stage':'primary-surface-brush-ready','mode':h.mode,'brush':bpy.context.tool_settings.sculpt.brush.name,'boundary_count':len(boundary)}))
