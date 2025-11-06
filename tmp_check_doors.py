import sys, os
sys.path.insert(0, r'D:\git\oop_framework')
from framework import grundlage

for i in range(1,27):
    try:
        grundlage.level.lade(i)
        sp = grundlage.level.framework.spielfeld
        has_tuer = any(getattr(o,'typ',None)=='Tuer' or o.__class__.__name__=='Tuer' for o in sp.objekte)
        print(f'level {i}: has_tuer={has_tuer}, required={getattr(sp,"_required_spawn_classes", None)}, spawned={[getattr(o,"typ",o.__class__.__name__) for o in sp.objekte]}')
    except Exception as e:
        print(f'level {i}: ERROR {e}')
