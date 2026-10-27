from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp'
calls=[{'tool':'execute_blender_code','arguments':{'code':(out/'audit-frozen-head.py').read_text()},'label':'geometry-failure-audit'},
{'tool':'look','arguments':{'mode':'angles','target':['V2_Head_Skin_NEW','V2_Ear_L','V2_Ear_R','V2_Eyeball_viewer_left','V2_Eyeball_viewer_right'],'views':['front','right','three_quarter'],'shading':'wireframe','max_size':1500},'label':'failure-wireframe'},
{'tool':'execute_blender_code','arguments':{'code':"import bpy,json\nprint(json.dumps({'matcaps':[s.name for s in bpy.context.preferences.studio_lights if s.type=='MATCAP'],'studio_properties':[p.identifier for p in bpy.types.View3DShading.bl_rna.properties]}))"},'label':'matcap-options'}]
(out/'failure-audit-request.json').write_text(json.dumps(calls))
