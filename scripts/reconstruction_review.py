"""Locked-camera render/measurement evidence. Never returns an artistic pass."""
from pathlib import Path
import json,math
import bpy,bmesh,numpy as np
from mathutils import Vector
from vrm_env import ROOT
from production_common import stats

OUT=ROOT/'previews/v0.3'
def render_iteration(name):
    directory=OUT/name;directory.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=800;scene.render.resolution_y=900
    scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False;scene.view_settings.view_transform='Standard'
    front=bpy.data.objects['REF_front'];target=Vector((0,0,front.location.z))
    if not bpy.data.objects.get('REF_quarter'):
        data=front.data.copy();data.name='REF_quarter';data.show_background_images=False
        camera=bpy.data.objects.new('REF_quarter',data);scene.collection.objects.link(camera)
        camera.location=(math.sqrt(2),-math.sqrt(2),target.z)
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    cameras={}
    for view in ['front','quarter','side','back']:
        scene.camera=bpy.data.objects['REF_'+view]
        scene.render.filepath=str(directory/(view+'.png'));bpy.ops.render.render(write_still=True)
        c=scene.camera;cameras[view]={'matrix_world':[list(r) for r in c.matrix_world],'ortho_scale':c.data.ortho_scale,'resolution':[800,900]}
    # Geometry inspection includes glasses/hair, with no material camouflage.
    # Workbench ignores alpha on brow/lash cards and on lenses. Remove only
    # those cards from temporary evaluated copies, never from the real model.
    temporary=[];hidden=[]
    for obname in ['Face','Researcher_Glasses']:
        original=bpy.data.objects[obname];ev=original.evaluated_get(bpy.context.evaluated_depsgraph_get())
        data=bpy.data.meshes.new_from_object(ev);ob=bpy.data.objects.new('ClayOnly_'+obname,data)
        scene.collection.objects.link(ob);ob.matrix_world=ev.matrix_world.copy()
        bm=bmesh.new();bm.from_mesh(data)
        excluded=[f for f in bm.faces if any(s in data.materials[f.material_index].name for s in ['FaceBrow','FaceEyeline','FaceEyelash','Lens','lens','Corneal'])]
        bmesh.ops.delete(bm,geom=excluded,context='FACES');bm.to_mesh(data);bm.free()
        hidden.append((original,original.hide_render));original.hide_render=True;temporary.append(ob)
    scene.render.engine='BLENDER_WORKBENCH';sh=scene.display.shading
    sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='SINGLE';sh.single_color=(.54,.54,.54)
    sh.show_shadows=True;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_specular_highlight=False
    sh.background_type='WORLD';scene.world.color=(.22,.22,.22)
    for view in ['front','quarter','side','back']:
        scene.camera=bpy.data.objects['REF_'+view];scene.render.filepath=str(directory/('clay-'+view+'.png'));bpy.ops.render.render(write_still=True)
    for ob in temporary:
        data=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(data)
    for ob,state in hidden:ob.hide_render=state
    scene.render.engine='BLENDER_EEVEE';scene.camera=front
    (directory/'cameras.json').write_text(json.dumps(cameras,indent=2))
    (directory/'geometry.json').write_text(json.dumps(stats(),indent=2))
    # Geometry anchors can be reviewed alongside manually annotated image features.
    face=bpy.data.objects['Face'];ev=face.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    points=np.array([ev.matrix_world@v.co for v in me.vertices]);bounds={}
    for material in me.materials:
        ids={v for p in me.polygons if me.materials[p.material_index]==material for v in p.vertices}
        if ids:
            a=points[list(ids)];bounds[material.name]={'min':a.min(0).tolist(),'max':a.max(0).tolist()}
    ev.to_mesh_clear();(directory/'material-bounds.json').write_text(json.dumps(bounds,indent=2))
    return directory
