"""Fixed cameras/lights shared by every before/after and phase inspection."""
from pathlib import Path
import math,json
import bpy
from mathutils import Vector,Quaternion

VIEWS={
    'front':(0,1.35,.68), 'quarter':(45,1.35,.68), 'side':(90,1.35,.68),
    'face':(0,1.445,.43), 'hair':(135,1.48,.35), 'full':(0,.80,1.76),
}

def setup():
    scene=bpy.context.scene
    for ob in list(bpy.data.objects):
        if ob.name.startswith('Studio_'):bpy.data.objects.remove(ob,do_unlink=True)
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=scene.render.resolution_y=1280
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='Standard'
    world=bpy.data.worlds.new('Studio_World');scene.world=world
    nodes=world.node_tree.nodes
    bg=next(n for n in nodes if n.type=='BACKGROUND')
    bg.inputs[0].default_value=(.8,.82,.85,1);bg.inputs[1].default_value=.7
    for name,location,energy,size in [('Key',(-2,-3,4),400,4),('Fill',(3,-1,2),150,3)]:
        data=bpy.data.lights.new('Studio_'+name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
        ob=bpy.data.objects.new('Studio_'+name,data);scene.collection.objects.link(ob);ob.location=location
        ob.rotation_euler=(Vector((0,0,1.35))-ob.location).to_track_quat('-Z','Y').to_euler()
    arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    for side,angle in [('L',1.22),('R',-1.22)]:
        pb=arm.pose.bones['J_Bip_'+side+'_UpperArm'];r=pb.bone.matrix_local.to_quaternion()
        pb.rotation_mode='QUATERNION';pb.rotation_quaternion=r.inverted()@Quaternion((0,1,0),angle)@r
    data=bpy.data.cameras.new('Studio_Camera');data.type='ORTHO'
    camera=bpy.data.objects.new('Studio_Camera',data);scene.collection.objects.link(camera);scene.camera=camera
    return camera

def render_views(directory,views=None,pose_callback=None):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    camera=setup()
    if pose_callback:pose_callback()
    manifest=json.loads((directory/'cameras.json').read_text()) if (directory/'cameras.json').exists() else {}
    for name in views or VIEWS:
        angle,z,scale=VIEWS[name];angle=math.radians(angle)
        target=Vector((0,0,z));camera.data.ortho_scale=scale
        camera.location=(2.5*math.sin(angle),-2.5*math.cos(angle),z+.06)
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        path=directory/(name+'.png');bpy.context.scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        manifest[name]={'angle_degrees':math.degrees(angle),'target':list(target),'ortho_scale':scale,'camera':list(camera.location),'path':str(path)}
    (directory/'cameras.json').write_text(json.dumps(manifest,indent=2))
    return manifest

def reset_pose():
    for ob in bpy.data.objects:
        if ob.type=='ARMATURE':
            for pb in ob.pose.bones:pb.matrix_basis.identity()
        if ob.type=='MESH' and ob.data.shape_keys:
            for k in ob.data.shape_keys.key_blocks:k.value=0
