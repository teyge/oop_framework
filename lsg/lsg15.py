from framework.grundlage import level
level.lade(15,weiblich=False)
from framework.grundlage import *

# Ab hier darfst du programmieren:
while held.verbleibende_herzen()>0:
    if held.herzen_vor_mir()==0:
        held.links()
    elif held.ist_auf_herz():
        held.nimm_herz()
    else:
        held.geh()
        

# Dieser Befehl muss immer am Ende stehen
framework.starten()