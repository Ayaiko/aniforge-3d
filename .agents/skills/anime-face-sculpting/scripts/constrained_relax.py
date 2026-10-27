"""Bounded data-level relaxation; Blender Object Mode, no topology or save operations."""
import numpy as np

def relax_region(obj, weights, *, steps=6, strength=0.3, max_move=0.0015, axis_mask=(0, 1, 0)):
    if obj.type != 'MESH' or obj.mode != 'OBJECT':
        raise ValueError('Expected an Object Mode mesh')
    if obj.data.shape_keys:
        raise ValueError('Shape-key mesh: use a separately planned key-preserving workflow')
    if steps < 0 or not 0 <= strength <= 1 or max_move < 0:
        raise ValueError('Invalid relaxation bounds')
    mesh = obj.data
    n = len(mesh.vertices)
    w = np.asarray(weights, dtype=float).copy()
    axes = np.asarray(axis_mask, dtype=float)
    if w.shape != (n,) or axes.shape != (3,) or not np.isfinite(w).all():
        raise ValueError('Weight/axis shape or numeric values invalid')
    w = np.clip(w, 0, 1)
    adjacent = [[] for _ in range(n)]
    edge_faces = {tuple(sorted(e.vertices)): 0 for e in mesh.edges}
    for p in mesh.polygons:
        ids = list(p.vertices)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            key = tuple(sorted((a, b)))
            edge_faces[key] = edge_faces.get(key, 0) + 1
    for e in mesh.edges:
        a, b = e.vertices
        adjacent[a].append(b)
        adjacent[b].append(a)
        if edge_faces[tuple(sorted((a, b)))] != 2:
            w[a] = w[b] = 0
    co = np.array([v.co[:] for v in mesh.vertices], dtype=float)
    origin = co.copy()
    for _ in range(steps):
        target = np.array([co[ns].mean(axis=0) if ns else co[i] for i, ns in enumerate(adjacent)])
        delta = (co + (target - co) * (strength * w[:, None]) * axes - origin)
        lengths = np.linalg.norm(delta, axis=1)
        delta *= np.minimum(1, max_move / np.maximum(lengths, 1e-15))[:, None]
        co = origin + delta
    for v, p in zip(mesh.vertices, co):
        v.co = p
    mesh.update()
    moved = np.linalg.norm(co - origin, axis=1)
    return {'vertices': n, 'faces': len(mesh.polygons), 'moved_vertices': int((moved > 1e-10).sum()),
            'max_movement_m': float(moved.max(initial=0)), 'boundary_vertices_locked': True,
            'axis_mask': list(axis_mask), 'topology_unchanged': True}
