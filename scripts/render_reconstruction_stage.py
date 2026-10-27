from pathlib import Path
import sys,bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from vrm_env import ROOT,enable_vrm
from character_studio import reset_pose,setup
from reconstruction_review import render_iteration
args=sys.argv[sys.argv.index('--')+1:];enable_vrm();bpy.ops.wm.open_mainfile(filepath=str(ROOT/args[0]));reset_pose();setup()
bg=next(n for n in bpy.context.scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(1,1,1,1);bg.inputs[1].default_value=.5
render_iteration(args[1])
