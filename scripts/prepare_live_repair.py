from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp'
code=(out/'repair-patches.py').read_text()
requests=[{'tool':'execute_blender_code','arguments':{'code':code},'label':'repair-live-topology'},
{'tool':'look','arguments':{'mode':'angles','target':['V2_Head_Skin_NEW','V2_Ear_L','V2_Ear_R','V2_Eyeball_viewer_left','V2_Eyeball_viewer_right','V2_Iris_viewer_left','V2_Iris_viewer_right','V2_Pupil_viewer_left','V2_Pupil_viewer_right'],'views':['front','right','three_quarter'],'shading':'solid','max_size':1200},'label':'repaired-head-solid'},
{'tool':'execute_blender_code','arguments':{'code':"import bpy,json\nprint(json.dumps({'mesh_filter_properties':[p.identifier for p in bpy.ops.sculpt.mesh_filter.get_rna_type().properties],'types':[i.identifier for i in bpy.ops.sculpt.mesh_filter.get_rna_type().properties['type'].enum_items],'view_areas':[a.type for a in bpy.context.screen.areas]}))"},'label':'sculpt-api'}]
(out/'repair-live-request.json').write_text(json.dumps(requests))
