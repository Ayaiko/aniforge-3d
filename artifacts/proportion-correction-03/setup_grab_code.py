import bpy,json
h=bpy.data.objects['Anime013_Head']
win=bpy.context.window_manager.windows[0];area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
bpy.ops.wm.save_as_mainfile(filepath='/Users/graind/Documents/ChatGPT/vTuber/models/proportion-correction-03/before-lower-mass-grab.blend',copy=True)
mask=h.data.attributes.get('.sculpt_mask')
if mask is None:mask=h.data.attributes.new('.sculpt_mask','FLOAT','POINT')
def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
for i,v in enumerate(h.data.vertices):
    x,y,z=v.co
    w=ease((1.411-z)/.014)*ease((z-1.339)/.010)*ease((-y-.028)/.025)
    if abs(x)>.060:w=0
    mask.data[i].value=1-w
h.data.use_mirror_x=False
space=area.spaces.active;space.region_3d.view_rotation=bpy.data.objects['REF_side'].matrix_world.to_quaternion();space.region_3d.view_location=(0,0,1.44);space.region_3d.view_distance=.35;space.region_3d.view_perspective='ORTHO'
with bpy.context.temp_override(window=win,area=area,region=region):
    bpy.ops.object.mode_set(mode='SCULPT')
    result=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Grab')
print(json.dumps({'stage':'lower-mass-profile-grab-ready','mode':h.mode,'brush':bpy.context.tool_settings.sculpt.brush.name,'result':list(result)}))
