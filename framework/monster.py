import os, pygame
from .utils import richtung_offset
from .objekt import Objekt

class Monster(Objekt):
    def __init__(self, x, y, richtung="down", sprite_pfad="sprites/monster.png", name="Orc"):
        super().__init__(typ="Monster", x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)
        self.angriff_start = None
        self.angriff_dauer = 500  # ms
        self.bild_normal = self.bild

    def update(self):
        # Wenn tot → Sprite dauerhaft KO lassen, keine Logik mehr
        if self.tot or not self.framework:
            return

        jetzt = pygame.time.get_ticks()

        # Wenn gerade Angriff läuft
        if self.angriff_start:
            if jetzt - self.angriff_start >= self.angriff_dauer:
                # Angriff vorbei → Sprite zurücksetzen
                self.bild = self.bild_normal
                self.angriff_start = None
            return

        dx, dy = richtung_offset(self.richtung)
        ziel_x, ziel_y = self.x + dx, self.y + dy
        held = getattr(self.framework.spielfeld, "held", None)
        knappe = getattr(self.framework.spielfeld, "knappe", None)

        def starte_angriff(opfer):
            base = self.sprite_pfad.split(".png")[0]
            att_pfad = f"{base}_att.png"
            if os.path.exists(att_pfad):
                try:
                    self.bild = pygame.image.load(att_pfad).convert_alpha()
                except:
                    pass
            self.angriff_start = jetzt  # Zeit merken
            self.bild_normal = pygame.image.load(self.sprite_pfad).convert_alpha()
            opfer.tot = True
            opfer._update_sprite_richtung()
            # KO-Sprite für das Opfer laden
            try:
                base = opfer.sprite_pfad.split(".png")[0]
                ko_pfad = f"{base}_ko.png"
                if os.path.exists(ko_pfad):
                    opfer.bild = pygame.image.load(ko_pfad).convert_alpha()
            except Exception as e:
                print("[Warnung] KO-Sprite Opfer:", e)


            self.framework._hinweis = f"{opfer.name} wurde von {self.name} überrascht!"
            self.framework._aktion_blockiert = True

        if held and not held.tot and (held.x, held.y) == (ziel_x, ziel_y):
            starte_angriff(held)
            return

        if knappe and not knappe.tot and (knappe.x, knappe.y) == (ziel_x, ziel_y):
            starte_angriff(knappe)
            return


        
    def attribute_als_text(self):
        return {
            "name": self.name, "x": self.x, "y": self.y
        }
