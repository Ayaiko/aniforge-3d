"""Reconstruct frozen read-only trial in MCP from bounded data batches.
No native file read, model edits, detail work, or unsafe-mode changes.
"""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';payload=json.loads((out/'head-002-payload.json').read_text())
setup='''import bpy,json
assert bpy.data.scenes.get('Geometry_Failure_Analysis_V2') is None
scene=bpy.data.scenes.new('Geometry_Failure_Analysis_V2')
bpy.context.window.scene=scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('Analysis_World')
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(0.16,0.17,0.19,1)
bg.inputs['Strength'].default_value=0.45
print('ANALYSIS_SCENE_READY',scene.name)
'''
setup+='\nmaterials='+repr(payload['materials'])+'\n'
setup+='''for name,spec in materials.items():
    mat=bpy.data.materials.new(name+'_Analysis')
    node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value=spec['color']
    node.inputs['Roughness'].default_value=spec['roughness']
    mat.diffuse_color=spec['color']
'''
calls=[{'tool':'get_addon_status','arguments':{},'label':'recovered-addon-status'},{'tool':'execute_blender_code','arguments':{'code':setup},'label':'create-failure-analysis-scene'}]
for spec in payload['objects']:
    name=spec['name'];dn=name+'_FrozenAnalysis'
    if spec['type']=='MESH':
        allocate="import bpy\ndata=bpy.data.meshes.new("+repr(dn)+")\ndata.vertices.add("+str(len(spec['vertices']))+")\nprint('POINT_CAGE_ALLOCATED',data.name)"
        calls.append({'tool':'execute_blender_code','arguments':{'code':allocate},'label':'analysis-allocate-'+name})
        for first in range(0,len(spec['vertices']),1200):
            coords=spec['vertices'][first:first+1200];code="import bpy\ndata=bpy.data.meshes["+repr(dn)+"]\ncoordinates="+repr(coords)+"\nfor i,coordinate in enumerate(coordinates,"+str(first)+"):\n    data.vertices[i].co=coordinate\nprint('ANALYSIS_VERTICES',"+str(first)+",len(coordinates))"
            calls.append({'tool':'execute_blender_code','arguments':{'code':code},'label':'analysis-'+name+'-verts-'+str(first)})
        for first in range(0,len(spec['faces']),1000):
            faces=spec['faces'][first:first+1000];code="import bpy,bmesh\ndata=bpy.data.meshes["+repr(dn)+"]\nbm=bmesh.new()\nbm.from_mesh(data)\nbm.verts.ensure_lookup_table()\nfaces="+repr(faces)+"\nfor face in faces:bm.faces.new([bm.verts[i] for i in face])\nbm.to_mesh(data)\nbm.free()\nprint('ANALYSIS_FACES',"+str(first)+",len(faces))"
            calls.append({'tool':'execute_blender_code','arguments':{'code':code},'label':'analysis-'+name+'-faces-'+str(first)})
        code="import bpy\nfrom mathutils import Matrix\ndata=bpy.data.meshes["+repr(dn)+"]\ndata.update()\nob=bpy.data.objects.new("+repr(name)+",data)\nbpy.context.scene.collection.objects.link(ob)\n"
        for mat in spec['materials']:code+="data.materials.append(bpy.data.materials["+repr(mat+'_Analysis')+"])\n"
        code+="for p in data.polygons:p.use_smooth=True\nob.matrix_world=Matrix("+repr(spec['matrix'])+")\nprint('FROZEN_ANALYSIS_MESH_LINKED',ob.name,len(data.vertices),len(data.polygons))"
    elif spec['type']=='CAMERA':
        code="import bpy\nfrom mathutils import Matrix\ndata=bpy.data.cameras.new("+repr(dn)+")\ndata.type='ORTHO'\ndata.ortho_scale="+repr(spec['ortho_scale'])+"\nob=bpy.data.objects.new("+repr(name)+",data)\nbpy.context.scene.collection.objects.link(ob)\nob.matrix_world=Matrix("+repr(spec['matrix'])+")\nprint('ANALYSIS_CAMERA',ob.name)"
    elif spec['type']=='LIGHT':
        code="import bpy\nfrom mathutils import Matrix\ndata=bpy.data.lights.new("+repr(dn)+",'AREA')\ndata.energy="+repr(spec['energy'])+"\ndata.size="+repr(spec['size'])+"\ndata.shape='DISK'\nob=bpy.data.objects.new("+repr(name)+",data)\nbpy.context.scene.collection.objects.link(ob)\nob.matrix_world=Matrix("+repr(spec['matrix'])+")\nprint('ANALYSIS_LIGHT',ob.name)"
    else:continue
    calls.append({'tool':'execute_blender_code','arguments':{'code':code},'label':'analysis-link-'+name})
calls.append({'tool':'execute_blender_code','arguments':{'code':"import bpy,json\nbpy.context.scene.camera=bpy.data.objects['REF_quarter']\nprint(json.dumps({'scene':bpy.context.scene.name,'matcaps':[s.name for s in bpy.context.preferences.studio_lights if s.type=='MATCAP'],'meshes':{o.name:{'vertices':len(o.data.vertices),'faces':len(o.data.polygons)} for o in bpy.context.scene.objects if o.type=='MESH'}}))\nbpy.ops.wm.save_as_mainfile(filepath='/tmp/vtuber-head-002-failure-baseline.blend',copy=True)"},'label':'memory-analysis-baseline'})
assert all(len(c['arguments'].get('code','').encode())<180000 for c in calls)
(out/'memory-analysis-request.json').write_text(json.dumps(calls));print('MCP bounded native data actions',len(calls))
