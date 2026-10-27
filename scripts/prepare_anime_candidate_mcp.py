import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';calls=[]
barely=json.loads((out/'anime-barely-payload.json').read_text());cold=json.loads((out/'anime-cold-payload.json').read_text())
for label,specs in [('Barely',[s for s in barely if s['name'] in ['H.face','H.cornea']]),('ColdOne',[s for s in cold if s['name']=='Cube.004'])]:
    setup=f"import bpy\nscene=bpy.data.scenes.new('Anime_Base_Candidate_{label}')\nbpy.context.window.scene=scene\nscene.render.engine='BLENDER_WORKBENCH'\nscene.render.resolution_x=800\nscene.render.resolution_y=900\nscene.render.resolution_percentage=100\nscene.display.shading.light='MATCAP'\nscene.display.shading.studio_light='clay_studio.exr'\nscene.display.shading.color_type='SINGLE'\nscene.display.shading.show_cavity=False\nscene.display.shading.show_shadows=False\nfor ob in bpy.data.scenes['Geometry_Failure_Analysis_V2'].objects:\n    if ob.type=='CAMERA':scene.collection.objects.link(ob)\nprint('ANIME_SOURCE_CANDIDATE_SCENE_CREATED')"
    calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='candidate-'+label+'-scene'))
    names=[]
    for spec in specs:
        name='Anime_'+label+'_'+spec['name'];dn=name+'_Mesh';names.append(name)
        if label=='Barely':coords=[[x*.72,y*.85,1.446197748+(z-.134)*.85] for x,y,z in spec['vertices']]
        else:coords=[[x*.18,y*.25-.020,1.446197748+(z-2.79)*.23] for x,y,z in spec['vertices']]
        coords=[[round(v,7) for v in co] for co in coords]
        calls.append(dict(tool='execute_blender_code',arguments={'code':f"import bpy\ndata=bpy.data.meshes.new({dn!r})\ndata.vertices.add({len(coords)})"},label=name+'-allocate'))
        for first in range(0,len(coords),1200):
            code=f"import bpy\ndata=bpy.data.meshes[{dn!r}]\ncoordinates={coords[first:first+1200]!r}\nfor i,co in enumerate(coordinates,{first}):data.vertices[i].co=co"
            calls.append(dict(tool='execute_blender_code',arguments={'code':code},label=name+'-points-'+str(first)))
        for first in range(0,len(spec['faces']),1000):
            code=f"import bpy,bmesh\ndata=bpy.data.meshes[{dn!r}]\nbm=bmesh.new()\nbm.from_mesh(data)\nbm.verts.ensure_lookup_table()\nfaces={spec['faces'][first:first+1000]!r}\nfor face in faces:bm.faces.new([bm.verts[i] for i in face])\nbm.to_mesh(data)\nbm.free()"
            calls.append(dict(tool='execute_blender_code',arguments={'code':code},label=name+'-faces-'+str(first)))
        code=f"import bpy\ndata=bpy.data.meshes[{dn!r}]\ndata.update()\nob=bpy.data.objects.new({name!r},data)\nbpy.context.scene.collection.objects.link(ob)\nfor p in data.polygons:p.use_smooth=True\nob['source']='CC0 anime base candidate: OpenGameArt, {label}'\nprint('ANIME_CANDIDATE_LINKED',ob.name)"
        calls.append(dict(tool='execute_blender_code',arguments={'code':code},label=name+'-link'))
    calls.append(dict(tool='look',arguments={'mode':'angles','target':names,'views':['front','right','three_quarter'],'shading':'solid','max_size':1500},label='anime-'+label+'-assessment'))
    for view in ['front','side','quarter']:
        code=f"import bpy\nscene=bpy.context.scene\nscene.camera=bpy.data.objects['REF_{view}']\nscene.render.filepath='/tmp/vtuber-anime-{label}-{view}.png'\nbpy.ops.render.render(write_still=True)"
        calls.extend([dict(tool='execute_blender_code',arguments={'code':code},label='render-anime-'+label+'-'+view),dict(tool='look',arguments={'image':'Render Result','max_size':900},label='anime-'+label+'-'+view)])
(out/'anime-candidates-request.json').write_text(json.dumps(calls));print(len(calls),'candidate inspection actions')
