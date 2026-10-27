import bpy,json,math
h=bpy.data.objects['Anime013_Head']
assert h.mode=='OBJECT'
old=[v.co.copy() for v in h.data.vertices]
mx=.00000885
mz=(1.38603628+1.38728893)/2
tz=1.446197748184204+(222-297)*.0007797915761063738
counts={}
adj={i:set() for i in range(len(old))}
for p in h.data.polygons:
    ids=list(p.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):
        key=tuple(sorted((a,b)));counts[key]=counts.get(key,0)+1
        adj[a].add(b);adj[b].add(a)
rim=set()
for edge,n in counts.items():
    if n==1:
        for i in edge:
            if 1.38<old[i].z<1.395 and abs(old[i].x)<.03:rim.add(i)
lip=set(rim)
for i in rim:lip.update(adj[i])
changes=0
for index,(v,c) in enumerate(zip(h.data.vertices,old)):

    x,y,z=c
    front=max(0,min(1,(-y-.035)/.025));front=front*front*(3-2*front)
    w=math.exp(-((z-mz)/.010)**4-((x-mx)/.021)**4)*front
    if w<1e-8:continue
    nx=x+.00628*math.tanh((x-mx)/.006)/math.tanh(.0092/.006)*math.exp(-((x-mx)/.030)**4-((z-mz)/.010)**4)*front
    nz=z+w*((tz-mz)-.70*(z-mz))
    ny=y+15*((nx-mx)**2-(x-mx)**2)
    wrim=math.exp(-((z-mz)/.003)**4-((x-mx)/.018)**4)*front
    if index not in lip:wrim=0
    target=-.0868+15*(nx-mx)**2
    ny+=(target-ny)*wrim
    v.co=(nx,ny,nz)
    changes+=1
h.data.update()
moves=[(v.co-c).length for v,c in zip(h.data.vertices,old)]
reverted=False
if max(moves)>.008:
    for v,c in zip(h.data.vertices,old):v.co=c
    h.data.update();reverted=True
print(json.dumps({'stage':'neutral-mouth-width-and-closure','changed_vertices':changes,'max_move_m':max(moves),'reverted':reverted,'method':'Widen/close existing opening; compensate lateral curvature; no forward lip shelf or whole-chin push'}))
