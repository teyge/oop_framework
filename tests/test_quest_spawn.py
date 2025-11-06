import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.spielfeld import Spielfeld
from framework.villager import Questgeber

# create a temporary level file
levelpath = os.path.join(os.path.dirname(__file__), 'tmp_level_quest.json')
level = {
    "tiles": [
        "www",
        "wQw",
        "www"
    ],
    "settings": {
        "quests": {
            "1,1": {"modus": "items", "wuensche": ["Ring"], "anzahl": 1}
        }
    }
}
with open(levelpath, 'w', encoding='utf-8') as f:
    json.dump(level, f, ensure_ascii=False, indent=2)

class DummyFramework:
    def __init__(self):
        self.weiblich = False

fw = DummyFramework()
# instantiate spielfeld which should spawn the questgiver
sp = Spielfeld(levelpath, fw, feldgroesse=32)
# find questgeber
found = [o for o in sp.objekte if isinstance(o, Questgeber)]
assert len(found) >= 1, 'Expected at least one Questgeber spawned'
print('SPAWN TEST OK')
