import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.spielfeld import Spielfeld
class DummyFW:
    def __init__(self):
        self.weiblich = False

fw = DummyFW()
# create a level with hero and code at same spot
lvl = {'tiles':['www','wPw','www'],'settings':{}}
path = 'tests/tmp_level_for_code_test.json'
with open(path,'w',encoding='utf-8') as f:
    json.dump(lvl,f)
sp = Spielfeld(path, fw, feldgroesse=16)
held = sp.held
# place a Code object on hero's tile
from framework.code import Code
c = Code(held.x, held.y, c='TEST-CODE')
sp.objekte.append(c)
print('Before, held.geheimer_code=', getattr(held,'geheimer_code',None))
held.nehm_auf_alle()
print('After, held.geheimer_code=', getattr(held,'geheimer_code',None))
# ensure code removed
codes = [o for o in sp.objekte if getattr(o,'typ','').lower()=='spruch']
print('Remaining code objects:', len(codes))
