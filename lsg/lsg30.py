from framework.grundlage import level
level.lade(30, weiblich=False)
from framework.grundlage import *

# Ab hier darfst du programmieren:
key = level.gib_objekt_bei(2,3)
key.set_farbe("violet")
door = held.gib_objekt_vor_dir()
door.verwende_schluessel(key)
held.geh()
held.geh()
held.nimm_herz()



# Dieser Befehl muss immer am Ende stehen
framework.starten()
