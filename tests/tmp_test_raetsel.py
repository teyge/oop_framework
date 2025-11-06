import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.spielfeld import Spielfeld

lvl = {
 'tiles':["www","wQw","www"],
 'settings':{
   'initial_gold': 10,
   'quest_mode': 'raetsel'
 }
}
path = 'tests/tmp_level_for_raetsel_test.json'
with open(path,'w',encoding='utf-8') as f:
    json.dump(lvl,f,ensure_ascii=False,indent=2)

class DummyFW:
    def __init__(self):
        self.weiblich = False

fw = DummyFW()
sp = Spielfeld(path, fw, feldgroesse=16)
from framework.villager import Questgeber
qs = [o for o in sp.objekte if isinstance(o, Questgeber)]
assert len(qs) > 0, 'No Questgeber spawned'
q = qs[0]
print('frage:', getattr(q, '_vorgegebene_frage', None))
print('loesung:', getattr(q, '_letzte_raetsel', None))
