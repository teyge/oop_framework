import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from framework.framework import Framework
import pygame

fw = Framework(levelnummer=0, auto_erzeuge_objekte=True, splash=False)
sp = fw.spielfeld
held = sp.held
print('Held at', held.x, held.y, 'sprite', held.sprite_pfad)
# (no need to compute nearby tile here; we'll inspect full object list)
print('\nObjects:')
for o in sp.objekte:
    try:
        print(type(o).__name__, getattr(o,'typ',None), getattr(o,'name',None), getattr(o,'x',None), getattr(o,'y',None), 'tot=', getattr(o,'tot',False))
    except Exception:
        pass

# pick any monster if present
mon = None
for o in sp.objekte:
    try:
        if getattr(o,'typ',None) == 'Monster':
            mon = o
            break
    except Exception:
        pass
if mon:
    print('Sample Monster at', mon.x, mon.y, 'sprite', mon.sprite_pfad)
if mon:
    print('Before attack: monster.tot=', mon.tot)
    held.attack(delay_ms=100)
    print('After hero attack: monster.tot=', mon.tot)
    print('Monster.bild is None?', getattr(mon,'bild',None) is None)
    # check for KO file existence
    import os
    base = getattr(mon,'sprite_pfad','').split('.png')[0]
    print('KO path', base + '_ko.png', 'exists', os.path.exists(base + '_ko.png'))

# Now simulate monster attacking hero by moving monster in front and calling attack
if mon:
    # rotate monster to face hero
    # find hero position
    mon.richtung = 'down'  # just set arbitrary
    print('Before monster attack: held.tot=', held.tot)
    mon.angriff(mon)
    print('After monster attack: held.tot=', held.tot)
    print('Held.bild is None?', getattr(held,'bild',None) is None)
    base_h = getattr(held,'sprite_pfad','').split('.png')[0]
    print('Held KO path', base_h + '_ko.png', 'exists', os.path.exists(base_h + '_ko.png'))

print('Done')
pygame.time.wait(1000)
pygame.quit()
