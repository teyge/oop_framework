import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.gegenstand import Gegenstand
from framework.held import Held
from framework.villager import Questgeber

# Dummy framework where movement check always returns True
class DummySpielfeld:
    def kann_betreten(self, obj, x, y):
        return True

class DummyFramework:
    def __init__(self):
        self.spielfeld = DummySpielfeld()

fw = DummyFramework()
held = Held(fw, steuerung_aktiv=False)

# Item-Quest: Villager requires two items
quest = Questgeber(fw, x=1, y=1, modus='items', wuensche=['Ring','Apple'])
# give held the items
ring = Gegenstand('Ring', 5)
apple = Gegenstand('Apple', 3)
held.inventar.hinzufuegen(ring)
held.inventar.hinzufuegen(apple)
# stub weiche_aus to avoid relying on setze_position
moved = {'v': False}
def fake_weiche():
    moved['v'] = True
quest.weiche_aus = fake_weiche
ok = quest.pruefe_abgabe(held)
assert ok is True, 'Expected successful hand-in'
# items removed
assert ring not in list(held.inventar) and apple not in list(held.inventar), 'Items should be removed from held inventory'
assert moved['v'] is True, 'Questgeber should have moved (weiche_aus called)'

# Puzzle-Quest
q2 = Questgeber(fw, x=2, y=2, modus='raetsel')
frage = q2.raetsel_geben()
# compute expected answer (strip trailing '=')
expr = frage.rstrip('=')
expected = str(eval(expr))
ok2 = q2.raetsel_loesn(expected)
assert ok2 is True, 'Expected puzzle to be solved with correct answer'

print('QUEST TESTS OK')
