import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
from render_control import setup,render_set
setup();render_set('baseline',levels=(0,1),wire=True)
