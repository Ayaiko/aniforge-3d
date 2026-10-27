"""Reference fit of existing CC0 anime topology, not primitive assembly."""
import json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'artifacts/reconstruction-v2-mcp';p=json.loads((out/'vroid-anime-payload.json').read_text());back=json.loads((out/'vroid-scalp-payload.json').read_text());calls=[]
def fit(co,ear=False):
    x,y,z=-(co[0]-.00025545),co[2],co[1]
    x*=.91
    front=1/(1+math.exp((y+.035)/.012))
    eye=math.exp(-((z-1.4462)/.026)**2)*math.exp(-((abs(x)-.040)/.032)**2)*front
    z+=.12*(abs(x)-.040)*eye
    # Localized nose landmark movement; the source's small anime volume is retained.
    nose=math.exp(-(x/.019)**2-((z-1.414)/.019)**2)*front
    z+=.005*nose
    mouth=math.exp(-(x/.033)**2-((z-1.389)/.014)**2)*front
    x*=1-.23*mouth
    y+=.007/(1+math.exp((z-1.385)/.012))*front
    z-=.0035*math.exp(-((z-1.355)/.023)**2)*front
    if ear:
        sign=1 if x>0 else -1
        x=sign*.078+(x-sign*.078)*.75
        y=.010+(y-.010)*.8
        z=1.438+(z-1.438)*.8
    return [round(v,7) for v in (x,y,z)]
setup="""import bpy
scene=bpy.data.scenes.new('Anime_Primary_Fit_011')
bpy.context.window.scene=scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=800
scene.render.resolution_y=900
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
shade=scene.display.shading
shade.light='MATCAP'
shade.studio_light='clay_studio.exr'
shade.color_type='SINGLE'
shade.show_cavity=False
shade.show_shadows=False
for ob in bpy.data.scenes['Geometry_Failure_Analysis_V2'].objects:
    if ob.type=='CAMERA':scene.collection.objects.link(ob)
print('ANIME_REFERENCE_FIT_011_STARTED')
"""
calls.append(dict(tool='execute_blender_code',arguments={'code':setup},label='anime-011-scene'))
parts=[]
for pi,name in [(7,'Skin'),(8,'Ears'),(1,'EyeWhite'),(5,'Iris'),(0,'MouthInterior')]:
    ids=p['primitives'][pi]['indices'];used=sorted(set(ids));remap={v:i for i,v in enumerate(used)}
    coords=[]
    for v in used:
        co=[p['positions'][v][k]+.32*p['targets'][13]['POSITION'][v][k] for k in range(3)]
        coords.append(fit(co,pi==8))
    faces=[[remap[v] for v in ids[i:i+3]] for i in range(0,len(ids),3)]
    if pi==7:
        for spec in back:
            if 'HAIR' in spec['name']:continue
            offset=len(coords);coords.extend(fit(co) for co in spec['vertices']);faces.extend([[v+offset for v in f] for f in spec['faces']])
    parts.append({'name':'Anime011_'+name,'vertices':coords,'faces':faces})
    on='Anime011_'+name
    code=f"import bpy,bmesh\ncoords={coords!r}\nfaces={faces!r}\nme=bpy.data.meshes.new({on+'_Mesh'!r})\nme.from_pydata(coords,[],faces)\nme.update()\nob=bpy.data.objects.new({on!r},me)\nbpy.context.scene.collection.objects.link(ob)\nfor poly in me.polygons:poly.use_smooth=True\nob['source']='VRoid CC0 female anime base; head only, direct reference fit; no hair'\nprint('PRIMARY_FORM_PART_CREATED',ob.name,len(me.vertices),len(me.polygons))"
    calls.append(dict(tool='execute_blender_code',arguments={'code':code},label='anime-011-'+name))
    if pi in [7,8]:
        code=f"import bpy,bmesh,math\nob=bpy.data.objects[{on!r}]\nbm=bmesh.new()\nbm.from_mesh(ob.data)\nbmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)\nbmesh.ops.join_triangles(bm,faces=list(bm.faces),angle_face_threshold=.4,angle_shape_threshold=.4)\nbmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))\nbm.to_mesh(ob.data)\nbm.free()\nob.data.update()\nprint('RECOVERED_QUAD_CAGE',ob.name,len(ob.data.vertices),len(ob.data.polygons),sum(len(p.vertices)==4 for p in ob.data.polygons))"
        calls.append(dict(tool='execute_blender_code',arguments={'code':code},label='anime-011-quads-'+name))
for view in ['front','side','quarter']:
    code=f"import bpy\nscene=bpy.context.scene\nscene.camera=bpy.data.objects['REF_{view}']\nscene.render.filepath='/tmp/vtuber-anime-011-{view}.png'\nbpy.ops.render.render(write_still=True)"
    calls.extend([dict(tool='execute_blender_code',arguments={'code':code},label='render-anime-011-'+view),dict(tool='look',arguments={'image':'Render Result','max_size':900},label='anime-011-'+view)])
(out/'anime-011-numeric-fit.json').write_text(json.dumps(parts))
(out/'anime-011-request.json').write_text(json.dumps(calls));print(len(calls),'MCP actions')
