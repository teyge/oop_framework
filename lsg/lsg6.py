from framework.grundlage import level
level.lade(6,weiblich=False)
from framework.grundlage import *

# Ab hier darfst du programmieren:
held.links()

knappe.links()
for i in range(2):
    for i in range(3):
        knappe.geh()
        knappe.nimm_herz()
    knappe.rechts()
    held.geh()
    held.geh()
    held.nimm_herz()

# Dieser Befehl muss immer am Ende stehen
framework.starten()