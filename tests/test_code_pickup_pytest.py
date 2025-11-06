import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.spielfeld import Spielfeld
class DummyFW:
    def __init__(self):
        # minimal attributes used by Held/Spielfeld
        self.weiblich = False
        self.spielfeld = None
        # registry for keys (not used in test, but Held will call taste_registrieren)
        self._keyregs = {}

    def taste_registrieren(self, key, callback):
        # store callback but do not execute; sufficient for Held initialisation
        try:
            self._keyregs[key] = callback
        except Exception:
            pass

fw = DummyFW()
# small level where hero spawns at (1,1)
lvl = {'tiles':['www','wPw','www'],'settings':{}}
path = 'tests/tmp_level_for_code_test.json'
import json
with open(path,'w',encoding='utf-8') as f:
    json.dump(lvl,f)

sp = Spielfeld(path, fw, feldgroesse=16)
held = sp.held
from framework.code import Code
c = Code(held.x, held.y, c='MAGIC-CODE')
sp.objekte.append(c)
assert getattr(held, 'geheimer_code', None) is None
# call the Enter-style pickup
# replicate internal checks to see which branch would run
to_process = [o for o in list(sp.objekte) if getattr(o, 'x', None) == held.x and getattr(o, 'y', None) == held.y and o is not held]
for o in to_process:
    typ_heart = getattr(o, 'typ', '') or getattr(o, 'name', '')
    color = getattr(o, 'farbe', None) or getattr(o, 'color', None) or getattr(o, 'key_color', None)
    typ_lower = getattr(o, 'typ', '').lower() if getattr(o, 'typ', None) else ''

held.nehm_auf_alle()
assert getattr(held, 'geheimer_code', None) == 'MAGIC-CODE', 'Held should have received the code from pickup'
# ensure code object removed
codes = [o for o in sp.objekte if getattr(o,'typ','').lower()=='spruch']
assert len(codes) == 0, 'Code object should be removed from spielfeld'

print('TEST_CODE_PICKUP OK')
