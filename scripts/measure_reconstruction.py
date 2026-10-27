"""Geometric landmarks projected into the locked reference cameras."""
from pathlib import Path
import json,sys,bpy,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
args=sys.argv[sys.argv.index('--')+1:];enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/args[0]))
from character_studio import reset_pose
reset_pose();bpy.context.view_layer.update();scene=bpy.context.scene;face=bpy.data.objects['Face'];ev=face.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
a=np.array([ev.matrix_world@v.co for v in me.vertices]);ids={}
for p in me.polygons:ids.setdefault(me.materials[p.material_index].name,set()).update(p.vertices)
skin=a[list(next(v for n,v in ids.items() if 'Face_00_SKIN' in n))]
iris=a[list(next(v for n,v in ids.items() if 'EyeIris' in n))]
lip=a[list(next(v for n,v in ids.items() if 'Lip vermilion' in n))]
def centre(v):return (v.min(0)+v.max(0))/2
chin=skin[(abs(skin[:,0])<.018)&(skin[:,1]<-.03)&(skin[:,2]<1.40)];chin=chin[chin[:,2].argmin()]
nose=skin[(abs(skin[:,0])<.014)&(skin[:,2]>1.395)&(skin[:,2]<1.45)];nose=nose[nose[:,1].argmin()]
landmarks={'pupil_left':centre(iris[iris[:,0]<0]),'pupil_right':centre(iris[iris[:,0]>0]),'nose_anterior_tip':nose,'mouth_center':centre(lip),'chin':chin}
reference_front={'pupil_left':[146,224],'pupil_right':[249,220],'mouth_center':[200,297],'chin':[200,345],'hairline_apex':[225,115],'nose_shadow_bottom':[194,276]}
results={'reference_annotations_400x450':reference_front,'annotation_uncertainty_pixels':3,'notes':['Model iris bounds center is a geometric proxy for pupil position; painted pupil/occlusion require the actual render.','Front nose shadow bottom and 3D nose anterior tip are different features; compare tip in side view, not by forcing one front landmark.','Eye shape, head/hair contours and hairline are checked using the paired renders and annotated masks, not a whole-image pixel score.'],'views':{}}
for view in ['front','side','back','quarter']:
    cam=bpy.data.objects['REF_'+view];projected={}
    for n,p in landmarks.items():
        q=world_to_camera_view(scene,cam,Vector(p));projected[n]=[q.x*400,(1-q.y)*450]
    results['views'][view]=projected
results['front_anchor_errors_pixels']={n:float(np.linalg.norm(np.array(results['views']['front'][n])-r)) for n,r in reference_front.items() if n in results['views']['front']}
results['side_reference_400x450']={'nose_anterior_tip':[53,257],'chin':[100,344]}
results['notes'].append('Lip-material centroid is NOT the side mouth silhouette; it was rejected as a fitting target after visual review of iteration 11.')
results['side_anchor_errors_pixels']={n:float(np.linalg.norm(np.array(results['views']['side'][n])-r)) for n,r in results['side_reference_400x450'].items()}
glass=bpy.data.objects['Researcher_Glasses'];ge=glass.evaluated_get(bpy.context.evaluated_depsgraph_get());gm=ge.to_mesh();v=np.array([ge.matrix_world@p.co for p in gm.vertices]);v=v[(abs(v[:,0])<.078)&(v[:,1]<-.07)]
results['front_frame_geometry_bounds_m']={'min':v.min(0).tolist(),'max':v.max(0).tolist()};ge.to_mesh_clear()
results['neck_shoulder_geometry_dimensions_m']={n:list(bpy.data.objects[n].dimensions) for n in ['Researcher_Knit','Researcher_Coat','Researcher_CoatSleeve_L','Researcher_CoatSleeve_R']}
results['world_landmarks_m']={n:p.tolist() for n,p in landmarks.items()};ev.to_mesh_clear()
out=ROOT/'previews/v0.3'/args[1];(out/'landmarks.json').write_text(json.dumps(results,indent=2));print(json.dumps(results['front_anchor_errors_pixels']),flush=True)
