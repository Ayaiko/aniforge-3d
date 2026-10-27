from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';payload=json.loads((out/'head-002-payload.json').read_text())
setup='''import bpy, json
from mathutils import Matrix
assert bpy.data.scenes.get('Reconstruction_V2_MCP') is None, 'V2 scene already exists; inspect before changing it'
bpy.ops.wm.save_as_mainfile(filepath='/Users/graind/Documents/ChatGPT/vTuber/models/legacy-baseline-v2-start/live-scene-before-v2-mcp.blend',copy=True)
scene=bpy.data.scenes.new('Reconstruction_V2_MCP')
bpy.context.window.scene=scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='AgX'
scene.world=bpy.data.worlds.new('V2_MCP_World')
background=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
background.inputs['Color'].default_value=(0.16,0.17,0.19,1)
background.inputs['Strength'].default_value=0.45
print('V2_SCENE_CREATED',scene.name,'original scenes preserved',[s.name for s in bpy.data.scenes])
'''
setup+='\nmaterial_specs='+repr(payload['materials'])+'\n'
setup+='''for name,spec in material_specs.items():
    mat=bpy.data.materials.new(name+'_MCP')
    node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    node.inputs['Base Color'].default_value=spec['color']
    node.inputs['Roughness'].default_value=spec['roughness']
    mat.diffuse_color=spec['color']
'''
requests=[] if '--resume' in sys.argv else [{'tool':'execute_blender_code','arguments':{'code':setup},'label':'create-v2-scene'}]
for spec in payload['objects']:
    serialized=json.dumps(spec,separators=(',',':'));code='import bpy,json\nfrom mathutils import Matrix\nspec=json.loads('+repr(serialized)+')\n'
    if spec['type']=='MESH':code+='''data=bpy.data.meshes.new(spec['name']+'_MCP_Data')
data.from_pydata(spec['vertices'],[],spec['faces'])
data.update()
ob=bpy.data.objects.new(spec['name'],data)
bpy.context.scene.collection.objects.link(ob)
for name in spec['materials']:data.materials.append(bpy.data.materials[name+'_MCP'])
for p in data.polygons:p.use_smooth=True
for key,value in spec['properties'].items():
    if value:ob[key]=value
'''
    elif spec['type']=='CAMERA':code+='''data=bpy.data.cameras.new(spec['name']+'_MCP_Data')
data.type='ORTHO'
data.ortho_scale=spec['ortho_scale']
ob=bpy.data.objects.new(spec['name'],data)
bpy.context.scene.collection.objects.link(ob)
'''
    elif spec['type']=='LIGHT':code+='''data=bpy.data.lights.new(spec['name']+'_MCP_Data','AREA')
data.energy=spec['energy']
data.size=spec['size']
ob=bpy.data.objects.new(spec['name'],data)
bpy.context.scene.collection.objects.link(ob)
'''
    else:continue
    code+="ob.matrix_world=Matrix(spec['matrix'])\nprint('CREATED',ob.name,ob.type)"
    if len(code.encode())>180000 and spec['type']=='MESH':
        name=spec['name'];dn=name+'_MCP_Data';loop_count=sum(len(f) for f in spec['faces'])
        start="import bpy\nassert bpy.data.meshes.get("+repr(dn)+") is None\ndata=bpy.data.meshes.new("+repr(dn)+")\ndata.vertices.add("+str(len(spec['vertices']))+")\ndata.loops.add("+str(loop_count)+")\ndata.polygons.add("+str(len(spec['faces']))+")\nprint('ALLOCATED_NEW_MESH',data.name)"
        requests.append({'tool':'execute_blender_code','arguments':{'code':start},'label':'allocate-'+name})
        for first in range(0,len(spec['vertices']),1200):
            batch=spec['vertices'][first:first+1200];script="import bpy\ndata=bpy.data.meshes["+repr(dn)+"]\ncoordinates="+repr(batch)+"\nfor i,coordinate in enumerate(coordinates,"+str(first)+"):\n    data.vertices[i].co=coordinate\nprint('VERTEX_BATCH',"+str(first)+",len(coordinates))"
            requests.append({'tool':'execute_blender_code','arguments':{'code':script},'label':name+'-vertices-'+str(first)})
        offset=0
        for first in range(0,len(spec['faces']),900):
            batch=spec['faces'][first:first+900];script="import bpy\ndata=bpy.data.meshes["+repr(dn)+"]\nfaces="+repr(batch)+"\noffset="+str(offset)+"\nfor i,face in enumerate(faces,"+str(first)+"):\n    polygon=data.polygons[i]\n    polygon.loop_start=offset\n    polygon.loop_total=len(face)\n    for j,vertex in enumerate(face):data.loops[offset+j].vertex_index=vertex\n    offset+=len(face)\nprint('FACE_BATCH',"+str(first)+",len(faces))"
            requests.append({'tool':'execute_blender_code','arguments':{'code':script},'label':name+'-faces-'+str(first)});offset+=sum(len(f) for f in batch)
        last="import bpy,json\nfrom mathutils import Matrix\nspec=json.loads("+repr(json.dumps({k:v for k,v in spec.items() if k not in ['vertices','faces']}))+")\ndata=bpy.data.meshes["+repr(dn)+"]\ndata.update(calc_edges=True)\nob=bpy.data.objects.new(spec['name'],data)\nbpy.context.scene.collection.objects.link(ob)\nfor name in spec['materials']:data.materials.append(bpy.data.materials[name+'_MCP'])\nfor p in data.polygons:p.use_smooth=True\nfor key,value in spec['properties'].items():\n    if value:ob[key]=value\nob.matrix_world=Matrix(spec['matrix'])\nprint('MESH_LINKED',ob.name,len(data.vertices),len(data.polygons))"
        requests.append({'tool':'execute_blender_code','arguments':{'code':last},'label':'finish-'+name})
    else:requests.append({'tool':'execute_blender_code','arguments':{'code':code},'label':'create-'+spec['name']})
requests.append({'tool':'get_scene_info','arguments':{'fields':['details','topology','settings'],'limit':30},'label':'v2-imported-scene'})
assert all(len(c['arguments'].get('code','').encode())<180000 for c in requests)
(out/('resume-v2-request.json' if '--resume' in sys.argv else 'create-v2-request.json')).write_text(json.dumps(requests))
print('PREPARED',len(requests),'MCP actions')
