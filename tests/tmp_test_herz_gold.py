import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.spielfeld import Spielfeld

lvl = {
 'tiles':["www","wPw","www"],
 'settings':{
   'initial_gold': 5
 }
}
path = 'tests/tmp_level_for_herz_test.json'
with open(path,'w',encoding='utf-8') as f:
    json.dump(lvl,f,ensure_ascii=False,indent=2)

class DummyFW:
    def __init__(self):
        self.weiblich = False
        self._aus_tastatur = True

    def taste_registrieren(self, *args, **kwargs):
        return None

    def _render_frame(self):
        return None

    def stoppe_programm(self, msg):
        print('stoppe_programm called', msg)

fw = DummyFW()
sp = Spielfeld(path, fw, feldgroesse=16)
fw.spielfeld = sp
held = sp.held
print('initial gold:', getattr(held,'gold',None))
# ensure there's a heart at hero position
from framework.herz import Herz
# put a heart at hero pos
h = Herz(held.x, held.y)
h.framework = fw
sp.objekte.append(h)
print('hearts before:', sp.anzahl_herzen())
held.nehme_auf(0)
print('hearts after:', sp.anzahl_herzen())
print('gold after pickup:', getattr(held,'gold',None))
