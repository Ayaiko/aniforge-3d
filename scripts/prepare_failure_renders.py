from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';calls=[]
for view in ['front','side','quarter']:
    code="import bpy\nscene=bpy.context.scene\nscene.camera=bpy.data.objects['REF_"+view+"']\nscene.render.engine='BLENDER_WORKBENCH'\nshade=scene.display.shading\nshade.light='MATCAP'\nshade.studio_light='clay_studio.exr'\nshade.color_type='SINGLE'\nshade.show_cavity=False\nshade.show_shadows=False\nshade.show_specular_highlight=True\nshade.background_type='VIEWPORT'\nshade.background_color=(0.12,0.13,0.15)\nscene.render.filepath='/tmp/vtuber-v2-matcap-"+view+".png'\nbpy.ops.render.render(write_still=True)\nprint('MATCAP_NO_SCENE_LIGHTS_NO_CAVITY',scene.camera.name)"
    calls.append({'tool':'execute_blender_code','arguments':{'code':code},'label':'render-matcap-'+view})
    calls.append({'tool':'look','arguments':{'image':'Render Result','max_size':900},'label':'matcap-'+view})
calls.append({'tool':'execute_blender_code','arguments':{'code':"import bpy\nbpy.context.scene.render.engine='BLENDER_EEVEE'\nbpy.context.scene.camera=bpy.data.objects['REF_front']\nbpy.context.scene.render.filepath='/tmp/vtuber-v2-frozen-clay-front.png'\nbpy.ops.render.render(write_still=True)\nprint('SCENE_LIGHTING_CONTROL_RENDER')"},'label':'render-lighting-control'})
calls.append({'tool':'look','arguments':{'image':'Render Result','max_size':900},'label':'lighting-control-front'})
calls.append({'tool':'execute_blender_code','arguments':{'code':"import bpy\nbpy.context.scene.camera=bpy.data.objects['REF_quarter']\nbpy.ops.wm.save_as_mainfile(filepath='/tmp/vtuber-v2-failure-analysis.blend',copy=True)\nprint('PRESERVED_FAILURE_ANALYSIS_SCENE_WITHOUT_GEOMETRY_EDITS')"},'label':'preserve-failure-analysis'})
(out/'failure-render-request.json').write_text(json.dumps(calls))
