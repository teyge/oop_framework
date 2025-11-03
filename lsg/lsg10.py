from framework.grundlage import level
level.lade(10,weiblich=False)
from framework.grundlage import *

# Ab hier darfst du programmieren:
for i in range(10):
    held.geh()
    if held.ist_auf_herz():
        held.nimm_herz()
        held.links()
for i in range(4):
    knappe.geh()
    if knappe.ist_auf_herz():
        knappe.nimm_herz()

# Dieser Befehl muss immer am Ende stehen
framework.starten()