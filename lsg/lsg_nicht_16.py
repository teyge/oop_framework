from framework.grundlage import level
level.lade(16)
from framework.grundlage import *

# Ab hier darfst du programmieren:
held.links()
knappe.links()
while held.verbleibende_herzen()>0:
    knappe.geh()
    if knappe.was_ist_rechts() == "Baum":
        if held.was_ist_links() == "Baum":
            held.geh()
            held.nimm_herz()
        else:
            held.geh()
            held.links()
            held.geh()
            held.nimm_herz()
            held.rechts()
    else:
        if held.was_ist_rechts() == "Baum":
            held.geh()
        else:
            held.rechts()
            held.geh()
            held.links()
            held.geh()
    


# Dieser Befehl muss immer am Ende stehen
framework.starten()