import json,numpy as np
from pathlib import Path
R=Path.cwd();O=R/'artifacts/proportion-correction-03';v=np.array(json.load(open(R/'artifacts/face-likeness-02/baseline.json'))['meshes']['Anime013_Head']['vertices']);c=v.copy()
def ease(x):x=np.clip(x,0,1);return x*x*(3-2*x)
zweight=ease((v[:,2]-1.460)/.012);c[:,2]-=.10*np.maximum(v[:,2]-1.460,0)*zweight
posterior=np.maximum(v[:,1],0);c[:,1]-=.16*posterior
upper=ease((v[:,2]-1.485)/.06);c[:,0]*=1-.012*upper;c[:,1]+=.03*np.maximum(-v[:,1]-.02,0)*upper
# Reset every coordinate changed by the superseded cranial trial as well.
old=set(json.load(open(O/'cranium-coordinates.json'))['changed_indices']);ids=sorted(old|set(np.where(np.linalg.norm(c-v,axis=1)>1e-8)[0]));changes=[[int(i),*c[i].tolist()] for i in ids];(O/'uniform-cranium-coordinates.json').write_text(json.dumps({'vertices':c.tolist(),'max_move_m':float(np.linalg.norm(c-v,axis=1).max())},indent=2))
prompt='ผมอยากให้ Codex ทำให้มันดูเหมือนตัวละครต้นฉบับแม้จะยังไม่มีสี ไม่มีผม และไม่มี Texture ก่อนครับ';code='import bpy,json\nh=bpy.data.objects["Anime013_Head"]\nchanges='+repr(changes)+'\nfor e in changes:h.data.vertices[e[0]].co=e[1:]\nh.data.update()\nprint(json.dumps({"stage":"uniform-cranial-proportion","changes":len(changes)}))';req=[{'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':prompt},'label':'apply-uniform-cranium'}]
code="import bpy,json\nh=bpy.data.objects['Anime013_Head']\nfor ob in bpy.context.selected_objects:ob.select_set(False)\nh.select_set(True)\nbpy.context.view_layer.objects.active=h\nwin=bpy.context.window_manager.windows[0]\narea=next(a for a in win.screen.areas if a.type=='VIEW_3D')\nregion=next(r for r in area.regions if r.type=='WINDOW')\nwith bpy.context.temp_override(window=win,area=area,region=region):\n    if h.mode!='SCULPT':bpy.ops.object.mode_set(mode='SCULPT')\n    result=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',asset_library_identifier='',relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/Smooth')\nb=bpy.context.tool_settings.sculpt.brush\nprint(json.dumps({'mode':h.mode,'brush':b.name if b else None,'result':list(result),'brush_properties':[p.identifier for p in b.bl_rna.properties if p.identifier in ['strength','size','use_frontface','use_smooth_pressure','sculpt_brush_type']]}))"
req.append({'tool':'execute_blender_code','arguments':{'code':code,'user_prompt':prompt},'label':'setup-live-smooth'})
(O/'live-mcp/uniform-cranium-request.json').write_text(json.dumps(req,ensure_ascii=False,indent=2))
