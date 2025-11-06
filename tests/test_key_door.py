import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.tuer import Tuer
from framework.schluessel import Schluessel as EntityKey
from framework.gegenstand import Schluessel as ItemKey

# Test 1: entity key color mismatch
door = Tuer(0,0, code=None, color='violet')
blue_key = EntityKey(0,0, color='blue')
assert not door.verwende_schluessel(blue_key), 'Blue entity key should NOT open violet door'
# matching
violet_key = EntityKey(0,0, color='violet')
assert door.verwende_schluessel(violet_key), 'Violet entity key should open violet door'

# Test 2: inventory item key (Gegenstand) should work
door2 = Tuer(1,1, code=None, color='blue')
item_blue = ItemKey('Schlüssel blau', 1, farbe='blue')
item_violet = ItemKey('Schlüssel violett', 1, farbe='violet')
assert door2.verwende_schluessel(item_blue), 'Item key blue should open blue door'
assert not door2.verwende_schluessel(item_violet), 'Item violet should not open blue door'

print('TEST_KEY_DOOR OK')
