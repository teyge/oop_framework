from .utils import richtung_offset
from .objekt import Objekt

class Monster(Objekt):
    def __init__(self, x, y, richtung="down", sprite_pfad="sprites/monster.png", name="Orc"):
        super().__init__(typ="Monster", x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)

    def update(self):
        if self.tot or not self.framework:
            return
        
        dx, dy = richtung_offset(self.richtung)
        ziel_x, ziel_y = self.x + dx, self.y + dy
        
        held = self.framework.spielfeld.held

        if held and not held.tot and (held.x, held.y) == (ziel_x, ziel_y):
            held.tot = True
            self.framework._hinweis = f"{held.name} wurde von {self.name} überrascht!"
            self.framework._aktion_blockiert = True
            return
        
        try:
            knappe = self.framework.spielfeld.knappe
            if knappe and not knappe.tot and (knappe.x, knappe.y) == (ziel_x, ziel_y):
                knappe.tot = True
                self.framework._hinweis = f"{knappe.name} wurde von {self.name} überrascht!"
                self.framework._aktion_blockiert = True
                return
        
        except:
            pass
        

        #super().update()
        
    def attribute_als_text(self):
        return {
            "name": self.name, "x": self.x, "y": self.y
        }
