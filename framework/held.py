# framework/held.py
import pygame
from .objekt import Objekt

class Held(Objekt):
    def __init__(self, framework, x=0, y=0, richtung="down",
                 sprite_pfad="sprites/held.png", name="Namenloser Held",
                 steuerung_aktiv=True,weiblich = False):
        if weiblich:
            sprite_pfad="sprites/held2.png"
        super().__init__(typ="Held", x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)
        self.framework = framework
        self.ist_held = True
        self.geheimer_code = None
        self.weiblich = weiblich
        self.knappen = []

        if steuerung_aktiv:
            self.aktiviere_steuerung()




    def aktiviere_steuerung(self):
        self.framework.taste_registrieren(pygame.K_LEFT,  lambda: self.links(0))
        self.framework.taste_registrieren(pygame.K_RIGHT, lambda: self.rechts(0))
        self.framework.taste_registrieren(pygame.K_UP,    lambda: self.geh(0))
        self.framework.taste_registrieren(pygame.K_DOWN,    lambda: self.zurueck(0))
        self.framework.taste_registrieren(pygame.K_RETURN,lambda: self.nehme_auf(0))
        self.framework.taste_registrieren(pygame.K_SPACE, lambda: self.attack(0))
        self.framework.taste_registrieren(pygame.K_c, lambda: self.lese_code(0))
        self.framework.taste_registrieren(pygame.K_v, lambda: self.code_eingeben(delay_ms=0))
        self.framework.taste_registrieren(pygame.K_f, lambda: self.bediene_tor(0))
        
    def gib_knappe(self):
        if len(self.knappen)>0:
            return self.knappen[0]
        
    def add_knappe(self,k):
        self.knappen.append(k)
        
    def attack(self, delay_ms=500):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        if self.tot or not self.framework:
            return

        import os, pygame
        from .utils import richtung_offset

        # aktuelle Blickrichtung merken
        alte_richtung = self.richtung
        basis = os.path.splitext(self.sprite_pfad)[0]

        # Animation: 3 Frames
        frames = [
            f"{basis}_att1.png",
            f"{basis}_att2.png",
            f"{basis}_att3.png",
        ]

        start = pygame.time.get_ticks()
        frame_delay = 100  # ms pro Frame
        for i, pfad in enumerate(frames):
            if os.path.exists(pfad):
                try:
                    self.bild = pygame.image.load(pfad).convert_alpha()
                    self._render_and_delay(frame_delay)
                except Exception as e:
                    print(f"[Held] Fehler beim Laden von {pfad}: {e}")

        # Nach Animation wieder ursprüngliches Richtungsbild laden
        self.richtung = alte_richtung
        self._update_sprite_richtung()

        # Angriff auf Monster prüfen (wie bisher)
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        monster = self.framework.spielfeld.finde_monster(tx, ty)
        if monster:
            # NICHT mehr entfernen:
            # self.framework.spielfeld.entferne_objekt(monster)

            monster.tot = True
            monster._update_sprite_richtung()
            try:
                base_m = monster.sprite_pfad.split(".png")[0]
                ko_m   = f"{base_m}_ko.png"
                if os.path.exists(ko_m):
                    monster.bild = pygame.image.load(ko_m).convert_alpha()
            except Exception as e:
                print("[Warnung] KO-Sprite Monster:", e)

            self._kills += 1


        # letzte Frame kurz sichtbar halten
        self._render_and_delay(delay_ms)
        
    def lese_code(self,delay_ms=500):
        self.lese_spruch(delay_ms)

        
    def lese_spruch(self,delay_ms=500):
        """Liest den Code vom Boden (falls dort ein Zettel liegt)."""
        if not self.framework:
            return None
        code_obj = self.framework.spielfeld.finde_code(self.x, self.y)
        if code_obj:
            self.geheimer_code = code_obj.gib_code()
            print(f"[Held] Spruch {self.geheimer_code} notiert.")
            if self.framework:
                self.framework.spielfeld.entferne_objekt(code_obj)
            return self.geheimer_code
        print("[Held] Kein Spruch hier.")
        self._render_and_delay(delay_ms)
        return None
    
    def spruch_lesen(self,delay_ms=500):
        self.lese_spruch(delay_ms)
    
    def bediene_tor(self,delay_ms=500):
        """Versucht, das Tor vor dem Helden zu öffnen oder zu schließen."""
        tor = self.framework.spielfeld.finde_tor_vor(self)
        if tor:
            if tor.offen:
                tor.schliessen()
            else:
                tor.oeffnen()
        else:
            print("[Held]: Kein Tor vor mir")
        self._render_and_delay(delay_ms)

    def spruch_sagen(self, code=None, delay_ms=500):
        self.code_eingeben(code,delay_ms)

    def code_eingeben(self, code=None,delay_ms=500):
        """Versucht, vor der Tür einen Code einzugeben."""
        if not self.framework:
            return
        if code is None and hasattr(self, "geheimer_code"):
            code = self.geheimer_code
        dx, dy = self.framework.spielfeld.level.texturen["w"].get_size()  # irrelevant
        dx, dy = 0, 0
        dx, dy = self.framework.spielfeld.level.texturen["w"].get_size()
        dx, dy = self.framework.spielfeld.level.texturen["w"].get_size()
        dx, dy = 0, 0
        # Korrekt:
        from .utils import richtung_offset
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        tuer = self.framework.spielfeld.finde_tuer(tx, ty)
        if tuer:
            if tuer.code_eingeben(code):
                print("[Held] " + self.geheimer_code + "!")
            else:
                if self.geheimer_code == None:
                    print("[Held] Ich habe keinen Spruch...")
                    self._ungueltige_aktion("Ungültige Aktion! Versuch es nochmal!")
                else:
                    self._ungueltige_aktion("Ungültige Aktion! Versuch es nochmal!")
        else:
            print("[Held] Keine Tür vor mir.")
            self._ungueltige_aktion("Ungültige Aktion! Versuch es nochmal!")
        self._render_and_delay(delay_ms)

    def attribute_als_text(self):
        if self.tot:
            return {
                "name": self.name, "x": self.x, "y": self.y,
                "ist_tot":"True"}
        if self.geheimer_code is None:
            return {
                "name": self.name, "x": self.x, "y": self.y,
                "richtung": self.transmute_richtung(self.richtung)
            }
        else:
            return {
                "name": self.name, "x": self.x, "y": self.y,
                "richtung": self.transmute_richtung(self.richtung), "Spruch":self.geheimer_code
            }
    """    
    def transmute_richtung(self,r):
        if r=="down":
            return "S"
        elif r=="up":
            return "N"
        elif r=="left":
            return "W"
        else:
            return "O"
    """
