import bpy,sys,json
from pathlib import Path
R=Path('/Users/graind/Documents/ChatGPT/vTuber');sys.path.insert(0,str(R/'.agents/skills/scenario-blender-expert/scripts'));import bx_review
names=['Anime013_Head','Anime013_Eye_L','Anime013_Eye_R','Anime013_MouthCavity'];result=bx_review.review([bpy.data.objects[n] for n in names],str(R/'artifacts/anime-face-learning/validation/wire-review'),views=('front','right','threequarter'),modes=('wire',),res=400)
print('WIRE_REVIEW',json.dumps(result,default=str))
