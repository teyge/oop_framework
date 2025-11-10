from framework.grundlage import level
level.lade(0)
fw=level.framework
sp=fw.spielfeld
from framework.monster import Bogenschuetze
from types import SimpleNamespace as NS
# find free spot
for y in range(sp.level.hoehe):
    for x in range(sp.level.breite-3):
        ok=True
        for dx in range(1,4):
            if sp.terrain_art_an(x+dx,y)!='Weg' or sp.objekt_an(x+dx,y) is not None:
                ok=False; break
        if ok:
            a=Bogenschuetze(x,y,'right')
            fw.objekt_hinzufuegen(a)
            h=NS(); h.typ='Held'; h.name='Tester'; h.x=x+2; h.y=y; h.tot=True; h.sprite_pfad='sprites/held.png'; fw.objekt_hinzufuegen(h)
            for o in list(fw.spielfeld.objekte):
                try: o.update()
                except: pass
            print('projectiles when victim.tot=True:', len(getattr(fw,'_projectiles',[])))
            # now set victim alive
            h.tot=False
            for o in list(fw.spielfeld.objekte):
                try: o.update()
                except: pass
            print('projectiles after reviving victim:', len(getattr(fw,'_projectiles',[])))
            raise SystemExit
print('none found')
