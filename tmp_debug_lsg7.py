import sys, os
sys.path.insert(0, r'D:\git\oop_framework')
os.environ['OOP_TEST'] = '1'
from framework.grundlage import level
level.lade(7)
sp = level.framework.spielfeld
held = sp.held
from framework.utils import richtung_offset

def dump(step):
    dx, dy = richtung_offset(getattr(held, 'richtung', 'down'))
    front = (getattr(held, 'x', None) + dx, getattr(held, 'y', None) + dy)
    objs_here = [ (getattr(o,'typ',o.__class__.__name__), getattr(o,'x',None), getattr(o,'y',None)) for o in sp.objekte if getattr(o,'x',None)==held.x and getattr(o,'y',None)==held.y]
    print(f"STEP {step}: held at {(held.x, held.y, held.richtung)} front={front} objects_here={objs_here}")

steps = [
    ('bediene_tor', (100,)),
    ('geh', (100,)),
    ('geh', (100,)),
    ('lese_spruch', (100,)),
]
# then loop: for i in range(4): held.geh(100)
for i in range(4):
    steps.append(('geh',(100,)))
steps += [
    ('links',(100,)),
    ('spruch_sagen', {'delay_ms':100}),
    ('geh',(100,)),
]
# final loop
for i in range(4):
    steps += [('geh',(100,)), ('nimm_herz',(100,)), ('links',(100,)), ('geh',(100,)), ('rechts',(100,))]

print('initial')
dump(0)

i = 1
for fn, args in steps:
    try:
        print('\n-- executing', fn, args)
        if isinstance(args, dict):
            getattr(held, fn)(**args)
        else:
            getattr(held, fn)(*args)
    except Exception as e:
        print('EXCEPTION during', fn, e)
    dump(i)
    i += 1

print('\nFinal objects:')
for o in sp.objekte:
    print(getattr(o,'typ',o.__class__.__name__), getattr(o,'x',None), getattr(o,'y',None))
