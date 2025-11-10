"""Beispiel-Schueler-Modul im Projekt-Root.
Dieses Modul demonstriert eine minimal kompatible 'Held'-Klasse, die
vom Framework verwendet werden kann, wenn in Level-Settings
"import_pfad": "schueler" gesetzt ist.
"""

class Held:
    def __init__(self, level, x, y, richt, weiblich=False):
        # Student-implementierte Held-Klasse erhält nur die Level-Instanz
        # (nicht das gesamte Framework). This minimal example fills the
        # attributes the framework expects so it can be detected/used.
        self.level = level
        self.x = x
        self.y = y
        self.richtung = richt
        self.weiblich = weiblich
        # self.gold = 0
        self.typ = "Held"
        self.name = "Namenloser Held"

    # Beispiel-Methoden (kommentiert) - Schüler können diese anpassen
    # def links(self):
    #     if self.richtung == "down":
    #         self.richtung = "right"

    # def geh(self):
    #     if self.richtung == "right":
    #         self.x += 1


from framework.grundlage import level
level.lade(29, weiblich=False)
from framework.grundlage import *

key_color = ""


x = 1
while key_color != "golden":
    key = level.gib_objekt_bei(x,3)
    key_color = key.gib_farbe()
    x+=1

tuer = held.gib_objekt_vor_dir()
tuer.verwende_schluessel(key)
held.geh()
held.geh()
held.nimm_herz()


"""
from framework.hindernis import Hindernis
from framework.tor import Tor
from framework.monster import Bogenschuetze
"""

# Ab hier darfst du programmieren:
#level.objekt_hinzufuegen(Hindernis(4,2,"Baum"))
# Dieser Befehl muss immer am Ende stehen
framework.starten()
