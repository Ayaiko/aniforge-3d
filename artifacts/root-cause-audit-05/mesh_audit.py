import bpy,bmesh,json,math,sys,statistics
from pathlib import Path
from collections import Counter
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent

def audit(o):
 m=o.data;bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table();bm.edges.ensure_lookup_table();bm.faces.ensure_lookup_table();bm.normal_update()
 val=Counter(len(v.link_edges) for v in bm.verts);pol=Counter(len(f.verts) for f in bm.faces)
 boundary=[e for e in bm.edges if e.is_boundary];remaining=set(boundary);loops=[]
 while remaining:
  seed=remaining.pop();es={seed};stack=list(seed.verts);vs=set(stack)
  while stack:
   v=stack.pop()
   for e in v.link_edges:
    if e in remaining:
     remaining.remove(e);es.add(e)
     for w in e.verts:
      if w not in vs:vs.add(w);stack.append(w)
  loops.append({'edges':len(es),'vertices':[v.index for v in vs],'center':[sum(v.co[i] for v in vs)/len(vs) for i in range(3)],'min':[min(v.co[i] for v in vs) for i in range(3)],'max':[max(v.co[i] for v in vs) for i in range(3)]})
 warp=[];aspect=[]
 for f in bm.faces:
  if len(f.verts)==4:
   a,b,c,d=[v.co for v in f.verts];n1=(b-a).cross(c-a);n2=(c-a).cross(d-a)
   if n1.length and n2.length:warp.append((math.degrees(n1.angle(n2)),f.index))
  lengths=[e.calc_length() for e in f.edges]
  if min(lengths)>1e-10:aspect.append((max(lengths)/min(lengths),f.index))
 high=[{'index':v.index,'valence':len(v.link_edges),'co':list(v.co),'boundary':v.is_boundary} for v in bm.verts if len(v.link_edges)>=6]
 d={'object':o.name,'vertices':len(m.vertices),'edges':len(m.edges),'faces':len(m.polygons),'tris':sum(len(f.vertices)-2 for f in m.polygons),'polygon_sides':dict(pol),'valence':dict(val),'high_valence':high,'boundary_components':loops,'nonmanifold_gt2':sum(len(e.link_faces)>2 for e in bm.edges),'wire_edges':sum(e.is_wire for e in bm.edges),'loose_verts':sum(not v.link_edges for v in bm.verts),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'inconsistent_normals_edges':sum(e.is_manifold and not e.is_contiguous for e in bm.edges),'zero_length_edges':sum(e.calc_length()<1e-8 for e in bm.edges),'warped_quads_gt20deg':sum(x[0]>20 for x in warp),'worst_warped_quads':sorted(warp,reverse=True)[:20],'faces_edge_aspect_gt8':sum(x[0]>8 for x in aspect),'worst_aspect':sorted(aspect,reverse=True)[:10],'shape_keys':list(m.shape_keys.key_blocks.keys()) if m.shape_keys else [],'uv_maps':len(m.uv_layers),'custom_normals':m.has_custom_normals}
 coords=[v.co.copy() for v in bm.verts];polys=[tuple(v.index for v in f.verts) for f in bm.faces];tree=BVHTree.FromPolygons(coords,polys);pairs=tree.overlap(tree);seen=set();cross=[]
 for a,b in pairs:
  if a>=b or (a,b) in seen or set(polys[a])&set(polys[b]):continue
  seen.add((a,b));cross.append((a,b))
 d['nonadjacent_bvh_overlap_candidates']=cross;d['self_overlap_candidate_count']=len(cross)
 bm.free();return d

if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:];tag=args[0];name=args[1];o=bpy.data.objects[name];d=audit(o);(P/(tag+'-mesh-audit.json')).write_text(json.dumps(d,indent=2));(P/(tag+'-mesh-data.json')).write_text(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons],'matrix_world':[list(r) for r in o.matrix_world]}));print('AUDIT',tag,{k:d[k] for k in ['vertices','faces','polygon_sides','valence','nonmanifold_gt2','degenerate_faces','warped_quads_gt20deg','faces_edge_aspect_gt8','self_overlap_candidate_count']},flush=True)
