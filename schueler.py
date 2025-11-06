"""Beispiel-Schueler-Modul im Projekt-Root.
Dieses Modul demonstriert eine minimal kompatible 'Held'-Klasse, die
vom Framework verwendet werden kann, wenn in Level-Settings
"import_pfad": "schueler" gesetzt ist.
"""

class Held:
    def __init__(self, level, x, y, richt, weiblich=False):
        # Student-implementierte Held-Klasse erhält nur die Level-Instanz (nicht das gesamte Framework)
        self.level = level
        self.x = x
        self.y = y
        self.richtung = richt
        self.weiblich = weiblich
        self.gold = 0
        self.typ = "Held"
"""
    def links(self):
        if self.richung=="down":
            self.richtung="right"

    def geh(self):
        if self.richtung == "right":
            self.x += 1
"""

    
from framework.grundlage import level
level.lade(30,weiblich=False)
from framework.grundlage import *

# Ab hier darfst du programmieren:

# Dieser Befehl muss immer am Ende stehen
framework.starten()