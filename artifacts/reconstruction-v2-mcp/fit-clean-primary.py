import bpy,math,json
assert bpy.context.scene.name=='Clean_Head_Base_V2'
def g(value,width):return math.exp(-(value/width)**2)
for ob in bpy.context.scene.objects:
    if ob.type!='MESH':continue
    backup=ob.data.copy()
    backup.name=ob.name+'_BeforePrimaryFit'
    for v in ob.data.vertices:
        x,y,z=v.co
        # Broad proportional edits on an existing face cage; no new geometry.
        ax=abs(x)
        frontal=1/(1+math.exp((y+.039)/.009))
        lower=g(z-1.410,.052)
        nx=x*(1-.075*lower)
        nz=z
        ny=y
        # Reduce round opening height while preserving the concentric lid loops.
        eye=g(ax-.040,.027)*g(z-1.4462,.028)*frontal
        nz+=(1.4462-z)*.33*eye
        # Relax heavy supraorbital projection from the generic base.
        ny+=.005*g(ax-.041,.034)*g(z-1.468,.016)*frontal
        # Narrow nose wings and reduce nose-tip projection.
        nose=g(x,.028)*g(z-1.414,.022)*frontal
        nx*=1-.48*nose
        ny+=.010*nose
        # Small closed anime mouth: reduce lip width and fullness together.
        mouth=g(x,.032)*g(z-1.388,.014)*frontal
        nx*=1-.37*mouth
        ny+=.006*mouth
        nz+=(1.388-z)*.23*mouth
        # Preserve the ear's topology, reduce its protrusion and vertical size.
        ear=max(0,min(1,(ax-.083)/.021))
        nx+=(math.copysign(.091,x)-nx)*.72*ear
        nz+=(1.438-z)*.19*ear
        # Neck base: reduce the clavicle flare; do not stretch the jaw surface.
        neck=max(0,min(1,(1.328-z)/.025))
        nx*=1-.20*neck
        v.co=(nx,ny,nz)
    ob.data.update()
    ob['primary_fit']='Broad direct vertex deformation, eye/nose/mouth/ear/neck; no added polygons or subdivisions'
print('PRIMARY_FORM_EDIT_COMPLETE_NO_DETAIL_NO_HAIR')
