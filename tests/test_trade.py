import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.held import Held
from framework.villager import Villager
from framework.gegenstand import Gegenstand

# Dummy framework with spielfeld.settings
class DummySpielfeld:
    def __init__(self, settings=None):
        self.settings = settings or {}

class DummyFramework:
    def __init__(self, settings=None):
        self.spielfeld = DummySpielfeld(settings)

# Setup
fw = DummyFramework({'Held': {'gold': 50}})
held = Held(fw, x=0, y=0, steuerung_aktiv=False)
vill = Villager(fw, x=1, y=1, steuerung_aktiv=False)

# Villager offers an item
item = Gegenstand('Ring', 10)
idx = vill.biete_item_an(item, 20)
assert idx is not None

# Sell to held
ok = vill.verkaufe_item(held, idx)
assert ok is True
assert held.gold_gib() == 30, f"Held gold should be 30 after purchase, got {held.gold_gib()}"
assert item in list(held.inventar), "Held should have received the item"
print('TRADE TEST OK')
