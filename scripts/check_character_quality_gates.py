"""Explicit gates: a helper returning exit 0 or high background SSIM is not asset approval."""
from pathlib import Path
import json,sys
root=Path(__file__).resolve().parents[1];folder=root/'artifacts/skills-workflow-upgrade'
manifest=json.loads((folder/'reference_manifest.json').read_text());threshold=manifest['validation_thresholds']
history=json.loads((folder/'validation/eye-coverage-history.json').read_text());eye=history['after02']
topology=json.loads((folder/'scenario-head-topology.json').read_text());delivery=json.loads((folder/'scenario-after-delivery-gate.json').read_text());surface=json.loads((folder/'skills-primary02-audit-parsed.json').read_text());discovery=json.loads((folder/'codex-skills-list.json').read_text())
second_audit=json.loads((folder/'el4cteo-asset-qa.json').read_text())
wanted={'reference-to-3d','orthographic-registration','reference-analysis-validator','scenario-blender-expert','scenario-blender-sculpting'};found=set()
def walk(v):
    if isinstance(v,dict):
        if v.get('name') in wanted and v.get('enabled'):found.add(v['name'])
        for q in v.values():walk(q)
    elif isinstance(v,list):
        for q in v:walk(q)
walk(discovery)
gates={}
def gate(name,passed,evidence,scope='model'):
    gates[name]={'status':'PASS' if passed else 'FAIL','scope':scope,'evidence':evidence}
gate('skills_discovery',found==wanted,{'enabled':sorted(found),'source':'codex-skills-list.json'},'workflow')
gate('structural_part_count',set(surface['meshes'])==set(manifest['expected_primary_parts']['labels']),{'expected':4,'actual':len(surface['meshes'])})
gate('visible_eye_shape',eye['iou']>=threshold['visible_eye_mask_iou_min'] and eye['outside_reference_ratio']<=threshold['eye_surface_outside_reference_ratio_max'],{'history':history,'thresholds':{'iou_min':threshold['visible_eye_mask_iou_min'],'outside_ratio_max':threshold['eye_surface_outside_reference_ratio_max']}})
self_crossings=sum(x['noncoplanar_crossing_pairs'] for x in surface['triangle_intersections'] if x['objects'][0]==x['objects'][1]);warped=sum(m['severely_warped_quads'] for m in surface['meshes'].values());degenerate=sum(m['degenerate_faces'] for m in surface['meshes'].values())
gate('basic_surface',self_crossings==0 and warped==0 and degenerate==0,{'self_crossing_pairs':self_crossings,'severely_warped_quads':warped,'degenerate_faces':degenerate,'limits':'Exact crossing test excludes coplanar and shared-vertex neighbours; advanced audit is required separately.'})
gate('deformation_topology',topology['non_manifold_edges']==0 and topology['quads_pct']>=98 and topology['valence_6plus']==0,{'non_manifold_edges':topology['non_manifold_edges'],'quads_pct':topology['quads_pct'],'unreviewed_valence_6plus':topology['valence_6plus'],'second_audit_winding_edges':second_audit['objects']['Anime013_Head']['inconsistent_normals_edges'],'note':'The project requires local review of all high-valence poles, not deletion of every pole. Primary draft is not clean final retopology.'})
gate('asset_delivery',delivery['pass'],{'scenario_errors':delivery['errors'],'scenario_warnings':delivery['warnings'],'el4cteo_render_pass':second_audit['pass'],'el4cteo_warnings':second_audit['warnings'],'interpretation':'Cavity is detached but enclosed per second audit; classification differs with tolerance/open apertures. Raw Scenario FAIL retained for review. A lenient render-profile PASS does not establish production readiness.'})
gate('artistic_review',False,{'looked_at':['previews/skills-workflow-upgrade/after02-front.png','previews/skills-workflow-upgrade/after02-side.png','previews/skills-workflow-upgrade/after02-quarter.png','previews/skills-workflow-upgrade/overlay-hero.png'],'remaining':['Exposed eye patches outside eyelids','Uneven orbital surface around canthi','Profile and overall character likeness remain different','Hero camera registration is approximate, RMS 7.37 px']})
result={'schema':'vtuber.quality_gates.v1','workflow_installation_pass':gates['skills_discovery']['status']=='PASS','asset_pass':all(g['status']=='PASS' for g in gates.values() if g['scope']=='model'),'gates':gates,'hair_detail_and_final_export_allowed':False,'exit_code_contract':'0 only when the model passes all gates; 2 is an expected gate failure, not successful asset completion.'}
(folder/'quality-gates.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'workflow_installation_pass':result['workflow_installation_pass'],'asset_pass':result['asset_pass'],'gates':{n:g['status'] for n,g in gates.items()}},indent=2))
sys.exit(0 if result['asset_pass'] else 2)
