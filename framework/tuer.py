# framework/tuer.py
from .objekt import Objekt
from .utils import lade_sprite

class Tuer(Objekt):
    """Eine verschlossene Tür, die nur mit dem richtigen Code geöffnet werden kann."""
    def __init__(self, x, y, code, sprite_pfad="sprites/tuer.png"):
        super().__init__("Tür", x, y, "down", sprite_pfad)
        self._richtiger_code = code
        self.offen = False

    def code_eingeben(self, code):
        """Öffnet die Tür, wenn der Code stimmt."""
        if str(code) == str(self._richtiger_code):
            if self.offen:
                print("[Tür] War bereits offen")
                return True
            #print("[Tür] Richtiger Code – Tür öffnet sich.")
            self.offen = True
            self.bild = lade_sprite("sprites/tuer_offen.png")
            """
            if self.framework:
                self.framework.spielfeld.entferne_objekt(self)
            return True
            """
            self.bild = lade_sprite("sprites/tuer_offen.png")
            return True
        else:
            if code != None:
                print("[Tür] Falscher Spruch!")
            return False
        
    def spruch_anwenden(self,code):
        self.code_eingeben(code)
        
    def ist_passierbar(self):
        return not self.offen
    
    def update(self):
        # Sprite abhängig vom Zustand der Tür wechseln
        if getattr(self, "offen", True):
            self.bild = lade_sprite("sprites/tuer_offen.png")

        # das Sprite neu laden (wenn du das schon irgendwo zentral machst, diesen Teil ggf. dort einfügen)
        self._bild_surface = self._lade_sprite(self._bild)


