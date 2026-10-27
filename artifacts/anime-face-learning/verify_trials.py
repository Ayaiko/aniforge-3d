import bpy,json
import numpy as np
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');O=R/'artifacts/anime-face-learning';ob=bpy.data.objects['Anime013_Head'];source=json.load(open(O/'Anime013_Head-baseline-mesh.json'));co=np.array([v.co[:] for v in ob.data.vertices]);before=np.array(source['vertices']);edges={}
for f in source['faces']:
 for a,b in zip(f,f[1:]+f[:1]):
  key=tuple(sorted((a,b)));edges[key]=edges.get(key,0)+1
protected={v for e,n in edges.items() if n!=2 for v in e};delta=co-before
result={'relax_trial_boundary_max_drift_m':float(np.abs(delta[list(protected)]).max()),'relax_trial_front_projection_max_drift_m':float(np.abs(delta[:,[0,2]]).max()),'relax_trial_max_movement_m':float(np.linalg.norm(delta,axis=1).max()),'topology_identical':source['faces']==[list(p.vertices) for p in ob.data.polygons],'mirror_api_properties':{x:x in bpy.types.MirrorModifier.bl_rna.properties for x in ['use_clip','use_mirror_merge','merge_threshold']},'brush_asset_activate_api':list(bpy.ops.brush.asset_activate.get_rna_type().properties.keys())}
assert result['relax_trial_boundary_max_drift_m']==0 and result['relax_trial_front_projection_max_drift_m']==0
assert result['relax_trial_max_movement_m']<=.0020001 and result['topology_identical']
assert all(result['mirror_api_properties'].values())
(O/'helper-and-version-verification.json').write_text(json.dumps(result,indent=2));print('HELPER_AND_VERSION_PASS',json.dumps(result))
