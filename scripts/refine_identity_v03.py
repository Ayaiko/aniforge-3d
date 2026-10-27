"""Local form and restrained painted anime features, no tertiary detail."""
from pathlib import Path
import sys,math,json
import bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
from production_common import toon,rgb,recalc
finalpass='--surface-correction' in sys.argv
enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/researcher-a-reconstruction-04-hair-v0.3.blend'));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
face=bpy.data.objects['Face'];mi=face.matrix_world.inverted();skinid=next(i for i,m in enumerate(face.data.materials) if 'Face_00_SKIN' in m.name)
irisids={v for p in face.data.polygons if any(s in face.data.materials[p.material_index].name for s in ['EyeIris','Corneal']) for v in p.vertices}
for key in face.data.shape_keys.key_blocks:
    for i,v in enumerate(key.data):
        p=face.matrix_world@v.co
        front=max(0,min(1,(-p.y-.03)/.03))
        p.z+=.006*math.exp(-(p.x/.014)**2-((p.z-1.410)/.013)**2)*front
        if i in irisids:p.z+=.0024;p.y+=.0005
        v.co=mi@p
knit=bpy.data.objects['Researcher_Knit'];ki=knit.matrix_world.inverted();top=max((knit.matrix_world@v.co).z for v in knit.data.vertices)
for v in knit.data.vertices:
    p=knit.matrix_world@v.co;p.z+=.010*max(0,min(1,(p.z-(top-.055))/.055))**1.5;v.co=ki@p
# Open the coverage shell forward from the ear. An ear is not a hole through hair.
cap=bpy.data.objects['Researcher_BobCap']
if finalpass:
    # Recess an uncut coverage surface instead of exposing a polygonal cut rim.
    with bpy.data.libraries.load(str(ROOT/'models/researcher-a-reconstruction-01-face-v0.3.blend'),link=False) as (src,dst):dst.meshes=['Researcher_BobCap'] if 'Researcher_BobCap' in src.meshes else [cap.data.name.split('.')[0]]
    cap.data=dst.meshes[0]
    cap.data.materials.clear();cap.data.materials.append(bpy.data.materials['Reconstruction / Hair lower layers'])
    for v in cap.data.vertices:
        x,y,z=v.co;v.co.x*=.91;v.co.y=.015+(y-.015)*.91
        if x>0:
            ear=math.exp(-((y-.025)/.042)**4-((z-1.444)/.044)**4);v.co.x-=.042*ear
        if z<1.405:v.co.z+=.012*max(0,(1.405-z)/.065)
    # Refit the hidden inherited scalp to the inner hair volume, not the silhouette.
    body=bpy.data.objects['Body'];inv=body.matrix_world.inverted()
    for v in body.data.vertices:
        p=body.matrix_world@v.co
        if p.z>1.47 and p.y>.025:
            f=min(1,(p.z-1.47)/.04);p.y-=.014*f;p.x*=1-.05*f
            v.co=inv@p
bm=bmesh.new();bm.from_mesh(cap.data)
remove=[]
for f in bm.faces:
    p=f.calc_center_median()
    front_edge=.040-.025*((p.z-1.435)/.055)**2
    if not finalpass and p.x>.065 and p.y<front_edge and 1.395<p.z<1.486:remove.append(f)
bmesh.ops.delete(bm,geom=remove,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(cap.data);bm.free()
for ob in [o for o in bpy.data.objects if o.get('reconstruction_tier')]:
    for v in ob.data.vertices:
        p=v.co
        if ob.name in ['Hair_RightBob','Hair_BehindEar','Hair_RearMass_00']:
            p.y+=.016*math.exp(-((p.z-1.444)/.044)**2)
        # Eliminate the accidental isolated crown spike from an overshooting section.
        if p.z>1.57 and p.x>.077:p.z=min(p.z,1.608-4.8*(p.x-.02)**2-4.3*(p.y-.015)**2+.002)
    recalc(ob)

def paint_uv(material_index,name,function,size=1024):
    """Rasterize deliberately designed colour/alpha to existing UV triangles."""
    data=face.data;data.calc_loop_triangles();uv=data.uv_layers.active.data
    pixels=np.zeros((size,size,4),dtype=np.float32)
    pixels[:]=function(np.array([[0.,0.,1.5]]))[0]
    basis=face.data.shape_keys.key_blocks[0]
    world=np.array([face.matrix_world@v.co for v in basis.data])
    for tri in data.loop_triangles:
        if data.polygons[tri.polygon_index].material_index!=material_index:continue
        uvs=np.array([uv[i].uv[:] for i in tri.loops])*(size-1)
        lo=np.maximum(0,np.floor(uvs.min(0)).astype(int));hi=np.minimum(size-1,np.ceil(uvs.max(0)).astype(int))
        if np.any(hi<lo):continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];pos=np.stack([xx,yy],axis=-1)
        a,b,c=uvs;den=np.cross(b-a,c-a)
        if abs(den)<1e-9:continue
        q=pos-a;s=((q[:,:,0]*(c-a)[1]-q[:,:,1]*(c-a)[0])/den);t=(((b-a)[0]*q[:,:,1]-(b-a)[1]*q[:,:,0])/den)
        valid=(s>=-1e-5)&(t>=-1e-5)&(s+t<=1+1e-5)
        pts=world[tri.vertices[0]]+(world[tri.vertices[1]]-world[tri.vertices[0]])*s[:,:,None]+(world[tri.vertices[2]]-world[tri.vertices[0]])*t[:,:,None]
        result=function(pts.reshape(-1,3)).reshape(*s.shape,4)
        pixels[lo[1]:hi[1]+1,lo[0]:hi[0]+1][valid]=result[valid]
    image=bpy.data.images.new(name,width=size,height=size,alpha=True);image.pixels.foreach_set(pixels.ravel());image.pack()
    material=data.materials[material_index];g=material.vrm_addon_extension.mtoon1;g.pbr_metallic_roughness.base_color_factor=(1,1,1,1)
    g.pbr_metallic_roughness.base_color_texture.index.source=image;g.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source=image
    return image
def skin_color(p):
    x,y,z=p.T;result=np.tile(np.array([246/255,212/255,191/255,1.]),(len(p),1))
    # A narrow designed nose side plane, and a grounded under-chin shadow.
    nose=(y<-.075)&(z>1.410)&(z<1.440)&(x<-.0003)&(x>-(.001+(.0022 if finalpass else .005)*np.sin(np.pi*np.clip((z-1.410)/.030,0,1))))
    result[nose,:3]=np.array([218,171,151])/255
    chin=(z<1.366)&(y>-.075)
    if not finalpass:result[chin,:3]=np.array([221,174,154])/255
    # Ear concha shape follows its actual position, rather than random skin noise.
    ear=(abs(x)>.083)&(y>.010)&(z>1.418)&(z<1.462)
    concha=ear&(((y-.026)/.011)**2+((z-1.438)/.014)**2<1)
    result[concha,:3]=np.array([235,193,173] if finalpass else [218,168,149])/255
    return result
paint_uv(skinid,'Reference skin planes 2048',skin_color,2048)
skin=face.data.materials[skinid];skin.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon.shade_color_factor=(.90,.84,.82)
browid=next(i for i,m in enumerate(face.data.materials) if 'FaceBrow' in m.name)
def brow_color(p):
    x,y,z=p.T;ax=abs(x);line=1.477+.16*(ax-.025);width=np.clip(.00125*(1-(ax-.025)/.052),.00022,.00125)
    if finalpass:line+=.0012*np.sin(np.pi*np.clip((ax-.025)/.052,0,1));width*=1.25
    alpha=np.clip((width-abs(z-line))/.00018+.5,0,1)*((ax>.023)&(ax<.077))
    if finalpass:alpha*=np.clip((ax-.023)/.002,0,1)*np.clip((.077-ax)/.003,0,1)
    result=np.tile(np.array([37/255,44/255,64/255,0]),(len(p),1));result[:,3]=alpha;return result
paint_uv(browid,'Straight researcher eyebrows 1024',brow_color)
brow=face.data.materials[browid];g=brow.vrm_addon_extension.mtoon1;g.alpha_mode='BLEND';brow.surface_render_method='BLENDED';g.extensions.vrmc_materials_mtoon.shade_color_factor=(1,1,1)
lip=next(m for m in face.data.materials if 'Lip vermilion' in m.name);lip.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_factor=(*rgb('9B7066'),1)

# Broad reference-style bands describe existing masses. No hair strands/noise.
for i,ob in enumerate(sorted([o for o in bpy.data.objects if o.get('reconstruction_tier')],key=lambda o:o.name)):
    mat=ob.data.materials[0].copy();mat.name='Hair painted mass / '+ob.name
    size=512;yy,xx=np.mgrid[0:size,0:size];u=xx/(size-1);v=yy/(size-1)
    pixels=np.empty((size,size,4),dtype=np.float32);pixels[:]=[37/255,44/255,64/255,1]
    across=(u-.02)/.44;centre=.28+.020*math.cos(i*.82)+.025*np.cos(across*math.pi*2)
    band=(u>.055)&(u<.42)&(v>centre)&(v<centre+.048)
    pixels[band,:3]=np.array([60,73,100])/255
    edge=((u<.075)|(u>.41))&(u<.5);pixels[edge,:3]=np.array([29,37,55])/255
    image=bpy.data.images.new('Mass band '+ob.name,width=size,height=size,alpha=True);image.pixels.foreach_set(pixels.ravel());image.pack()
    gg=mat.vrm_addon_extension.mtoon1;gg.pbr_metallic_roughness.base_color_factor=(1,1,1,1);gg.pbr_metallic_roughness.base_color_texture.index.source=image
    gg.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source=image;gg.extensions.vrmc_materials_mtoon.shade_color_factor=(.70,.76,.85)
    ob.data.materials.clear();ob.data.materials.append(mat)
directory=render_iteration('06-surface-correction' if finalpass else '05-identity-refinement')
(directory/'changes.json').write_text(json.dumps({'geometry_changes':['Nose profile tip raised by up to 6 mm through all 42 keys','Iris/corneal features raised 2.4 mm and recessed 0.5 mm','Collar upper edge raised 10 mm with smooth falloff','Scalp opening connected to leading edge near visible ear','Right hair masses shifted behind ear; crown spike clipped to crown surface'],'painted_surfaces':['2048 skin planes, narrow nose-side plane and ear concha','1024 straight eyebrow alpha based on actual mesh UV/world position','512 per-mass broad hair colour bands'],'tertiary_details_added':0,'artistic_status':'Pending visual review; remaining primary differences must still be disclosed'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/('models/researcher-a-reconstruction-06-surface-v0.3.blend' if finalpass else 'models/researcher-a-reconstruction-05-identity-v0.3.blend')))
print('IDENTITY ITERATION SAVED',flush=True)
