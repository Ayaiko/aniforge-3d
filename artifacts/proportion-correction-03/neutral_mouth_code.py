import bpy,json,math
h=bpy.data.objects['Anime013_Head']
assert h.mode=='OBJECT'
old=[v.co.copy() for v in h.data.vertices]
mx=.00000885
mz=(1.38603628+1.38728893)/2
tz=1.446197748184204+(222-297)*.0007797915761063738
changes=0
for v,c in zip(h.data.vertices,old):
    x,y,z=c
    front=max(0,min(1,(-y-.035)/.025));front=front*front*(3-2*front)
    w=math.exp(-((z-mz)/.010)**4-((x-mx)/.021)**4)*front
    if w<1e-8:continue
    nx=mx+(x-mx)*(1+.72*w)
    nz=z+w*((tz-mz)-.70*(z-mz))
    ny=y+15*((nx-mx)**2-(x-mx)**2)
    wrim=math.exp(-((z-mz)/.003)**4-((x-mx)/.018)**4)*front
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
