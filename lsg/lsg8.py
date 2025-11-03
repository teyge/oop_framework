from framework.grundlage import level
level.lade(8)
from framework.grundlage import *
#framework = level.framework
#held = level.held

# Befehlsliste:
# geh, links, rechts, nehme_auf (für Herzen), attack, was_ist_vor_mir, gib_objekt_vor_dir, ist_auf_herz
# lese_code, code_eingeben

# Ab hier darfst du programmieren:
held.links()
for i in range(3):
    held.geh()
    held.nehme_auf()
    held.geh()
    held.geh()
    held.links()
    held.bediene_tor()
    held.geh()
    held.rechts()
held.geh()
held.nehme_auf()

    

# Dieser Befehl muss immer am Ende stehen
framework.starten()