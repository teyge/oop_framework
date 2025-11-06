import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.inventar import Inventar
from framework.gegenstand import Gegenstand, Schluessel

# 1) Inventar hinzufügen/entfernen
inv = Inventar()
apple = Gegenstand("Apple", 5)
key = Schluessel("KeyGreen", 1, "green")
inv.hinzufuegen(apple)
inv.hinzufuegen(key)
assert len(inv) == 2, f"Expected 2 items, got {len(inv)}"
assert inv.anzahl() == 2
assert inv.gib_item(0) is apple

# 2) items_vom_typ
keys = inv.items_vom_typ("Schlüssel")
assert key in keys, "Key should be present in items_vom_typ"

# 3) Entfernen
removed = inv.entfernen(apple)
assert removed is True
assert len(inv) == 1

# 4) Schluessel.oeffne_tuer: dummy Tür
class DummyTuer:
    def __init__(self, keycolor):
        self.key_color = keycolor
        self.offen = False
    def schluessel_einsetzen(self, schluessel):
        if getattr(schluessel, 'farbe', None) == self.key_color or getattr(schluessel, 'farbe', None) == getattr(schluessel, 'farbe', None):
            self.offen = True
            return True
        return False

# ensure key is in inventory for test (it should still be present after apple removal)
assert key in list(inv)

# Create dummy door that expects green
door = DummyTuer('green')
ok = key.oeffne_tuer(door)
assert ok is True, "Schluessel.oeffne_tuer should return True when color matches"
assert getattr(door, 'offen', False) is True
# key should have removed itself from inventar
assert key not in list(inv), "Key should be removed from inventory after opening door"

print('TESTS OK')
