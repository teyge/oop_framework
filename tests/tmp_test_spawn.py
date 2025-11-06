import os, json
from framework.spielfeld import Spielfeld

lvl = {
 'tiles':["www","wPw","www"],
 'settings':{
   'initial_gold': 50,
   'quest_max_kosten': 100,
   'quest_mode': 'items',
   'quest_items_needed': 3
 }
}
path = 'tests/tmp_level_for_quest_test.json'
with open(path,'w',encoding='utf-8') as f:
    json.dump(lvl,f,ensure_ascii=False,indent=2)

class DummyFW:
    def __init__(self):
        self.weiblich = False

fw = DummyFW()
sp = Spielfeld(path, fw, feldgroesse=16)
print('Held gold:', getattr(sp.held,'gold',None))
from framework.villager import Villager
# list villager offers
for o in sp.objekte:
    if isinstance(o, Villager):
        print('Villager offers:')
        for it in o.inventar:
            print(' -', it.name, it.wert)
