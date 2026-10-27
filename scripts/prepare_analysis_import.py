from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';payload=json.loads((out/'head-002-payload.json').read_text())
code='''import bpy,json
assert bpy.context.scene.name=='Reconstruction_V2_MCP'
unfinished=bpy.data.meshes.get('V2_Head_Skin_NEW_MCP_Data')
if unfinished and unfinished.users==0:bpy.data.meshes.remove(unfinished)
assert bpy.data.objects.get('V2_Head_Skin_NEW') is None
properties=bpy.ops.wm.obj_import.get_rna_type().properties
assert 'NEGATIVE_Z' in [i.identifier for i in properties['forward_axis'].enum_items]
result=bpy.ops.wm.obj_import(filepath='/Users/graind/Documents/ChatGPT/vTuber/artifacts/reconstruction-v2-mcp/head-002-analysis.obj',forward_axis='NEGATIVE_Z',up_axis='Y')
print('IMPORTED_FROZEN_V2_FOR_ANALYSIS',result,[(o.name,len(o.data.vertices),len(o.data.polygons)) for o in bpy.context.scene.objects if o.type=='MESH'])
'''
calls=[{'tool':'execute_blender_code','arguments':{'code':code},'label':'import-frozen-head-for-analysis'}]
for spec in payload['objects']:
    if spec['type'] not in ['CAMERA','LIGHT']:continue
    text='import bpy\nfrom mathutils import Matrix\nspec='+repr(spec)+'\n'
    if spec['type']=='CAMERA':text+="data=bpy.data.cameras.new(spec['name']+'_Analysis')\ndata.type='ORTHO'\ndata.ortho_scale=spec['ortho_scale']\n"
    else:text+="data=bpy.data.lights.new(spec['name']+'_Analysis','AREA')\ndata.energy=spec['energy']\ndata.shape='DISK'\ndata.size=spec['size']\n"
    text+="ob=bpy.data.objects.new(spec['name'],data)\nbpy.context.scene.collection.objects.link(ob)\nob.matrix_world=Matrix(spec['matrix'])\nprint('ANALYSIS_SETUP',ob.name)"
    calls.append({'tool':'execute_blender_code','arguments':{'code':text},'label':'analysis-setup-'+spec['name']})
calls.append({'tool':'execute_blender_code','arguments':{'code':"import bpy,json\nbpy.context.scene.camera=bpy.data.objects['REF_quarter']\nprint(json.dumps({'matcaps':[s.name for s in bpy.context.preferences.studio_lights if s.type=='MATCAP'],'mesh_filter_properties':[p.identifier for p in bpy.ops.sculpt.mesh_filter.get_rna_type().properties],'file':bpy.data.filepath,'scene':bpy.context.scene.name}))\nbpy.ops.wm.save_as_mainfile(filepath='/Users/graind/Documents/ChatGPT/vTuber/models/reconstruction-v2/head-002-mcp-failure-baseline.blend',copy=True)"},'label':'analysis-preserved-baseline'})
calls.append({'tool':'get_scene_info','arguments':{'fields':['details','materials','modifiers','topology','settings'],'limit':30},'label':'analysis-geometry-inventory'})
(out/'analysis-import-request.json').write_text(json.dumps(calls))
