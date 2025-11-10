import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.spielfeld import Spielfeld
from framework.knappe import Knappe as FWK
p = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tmp_level_k_subfolder.json'))
print('Using level file:', p)
sp = Spielfeld(p, framework=None, auto_erzeuge_objekte=False)
print('settings:', sp.settings)
cls = sp._get_entity_class('Knappe', FWK)
print('Got class for Knappe:', cls)
sp._spawn_aus_level()
print('Spawned knappe object type:', type(getattr(sp,'knappe', None)))
kn = getattr(sp,'knappe', None)
print('All spawned objects:')
for i,o in enumerate(sp.objekte):
    print(i, '->', type(o), repr(o))
    try:
        print('    typ=', getattr(o,'typ', None))
    except Exception as e:
        print('    typ access failed:', e)
if kn is not None:
    print('kn.class module:', kn.__class__.__module__, 'class name:', kn.__class__.__name__)
    print('kn.typ:', getattr(kn,'typ',None))
    attrs = {a: getattr(kn,a,None) for a in ('x','y','richtung','level','framework','name')}
    print('kn attributes sample:', attrs)
