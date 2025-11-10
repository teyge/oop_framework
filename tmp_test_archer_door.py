from framework.grundlage import level
level.lade(0)
fw=level.framework
sp=fw.spielfeld
from framework.monster import Bogenschuetze
from framework.tuer import Tuer
from types import SimpleNamespace as NS
import pygame

# place archer at x, door at x+1 (closed), hero at x+2
# find a row where these tiles are within bounds and are 'Weg' and empty
for y in range(sp.level.hoehe):
    for x in range(sp.level.breite-3):
        ok=True
        # positions x (archer), x+1 (door), x+2 (victim)
        if sp.terrain_art_an(x,y)!='Weg' or sp.objekt_an(x,y) is not None:
            ok=False
        if sp.terrain_art_an(x+1,y)!='Weg' or sp.objekt_an(x+1,y) is not None:
            ok=False
        if sp.terrain_art_an(x+2,y)!='Weg' or sp.objekt_an(x+2,y) is not None:
            ok=False
        if ok:
            print('using coords', x,y)
            a=Bogenschuetze(x,y,'right')
            fw.objekt_hinzufuegen(a)
            # closed door between
            d=Tuer(x+1,y, code=None)
            d.offen = False
            fw.objekt_hinzufuegen(d)
            h=NS(); h.typ='Held'; h.name='Tester'; h.x=x+2; h.y=y; h.tot=False; h.sprite_pfad='sprites/held.png'
            fw.objekt_hinzufuegen(h)
            # run updates
            for o in list(fw.spielfeld.objekte):
                try:
                    o.update()
                except Exception:
                    pass
            projs = len(getattr(fw,'_projectiles', []))
            print('projectiles (should be 0):', projs)
            # Now open the door and update again; then archer should shoot
            d.offen = True
            d.update()
            for o in list(fw.spielfeld.objekte):
                try:
                    o.update()
                except Exception:
                    pass
            projs2 = len(getattr(fw,'_projectiles', []))
            print('projectiles after opening (should be 1):', projs2)
            raise SystemExit
print('no suitable place found')
