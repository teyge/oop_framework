from framework.grundlage import level
level.lade(7)
from framework.grundlage import *

# Ab hier darfst du programmieren:
held.bediene_tor()
held.geh()
held.geh()
held.lese_spruch()
for i in range(4):
    held.geh()
held.links()
held.spruch_sagen()
held.geh()
for i in range(4):
    held.geh()
    held.nimm_herz()
    held.links()
    held.geh()
    held.rechts()



# Dieser Befehl muss immer am Ende stehen
framework.starten()