from framework.grundlage import level
level.lade(9,weiblich=False)
from framework.grundlage import *

# Ab hier darfst du programmieren:
held.links()
for i in range(7):
    held.geh()
    if held.ist_auf_herz():
        held.nimm_herz()

# Dieser Befehl muss immer am Ende stehen
framework.starten()