import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.spielfeld import Spielfeld
p = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tmp_level_hind.json'))
print('Using level file:', p)
sp = Spielfeld(p, framework=None, auto_erzeuge_objekte=False)
print('Level settings:', sp.level.settings)
# Check that the settings include Hindernis privacy info
print('Hindernis entry in level.settings:', sp.level.settings.get('Hindernis'))
# Now simulate spawn with auto_erzeuge_objekte True by calling _spawn_aus_level
sp.auto_erzeuge_objekte = True
try:
    sp._spawn_aus_level()
    print('Spawn ran; object count:', len(sp.objekte))
    # report any Hindernis-like objects
    hind = [o for o in sp.objekte if getattr(o,'typ',None) in ('Busch','Baum','Berg','Hindernis')]
    print('Hindernis-like objects found:', len(hind))
except Exception as e:
    print('Spawn error:', e)
