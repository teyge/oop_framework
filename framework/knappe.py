# framework/held.py
import pygame
from .objekt import Objekt

class Knappe(Objekt):
    def __init__(self, framework, x=0, y=0, richtung="down",
                 sprite_pfad="sprites/knappe.png", name="Nils",
                 steuerung_aktiv=False):
        super().__init__(typ="Knappe", x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)
        self.framework = framework
        self.ist_held = True
        self.geheimer_code = None

        if steuerung_aktiv:
            self.aktiviere_steuerung()




    def aktiviere_steuerung(self):
        self.framework.taste_registrieren(pygame.K_a,  lambda: self.links(0))
        self.framework.taste_registrieren(pygame.K_d, lambda: self.rechts(0))
        self.framework.taste_registrieren(pygame.K_w,    lambda: self.geh(0))
        self.framework.taste_registrieren(pygame.K_s,lambda: self.zurueck(0))
        """
        self.framework.taste_registrieren(pygame.K_SPACE, lambda: self.attack(0))
        self.framework.taste_registrieren(pygame.K_c, lambda: self.lese_code(0))
        self.framework.taste_registrieren(pygame.K_v, lambda: self.code_eingeben(0))
        self.framework.taste_registrieren(pygame.K_f, lambda: self.bediene_tor())


        """
    def lese_code(self,delay_ms=500):
        self.lese_spruch(delay_ms)
        
    def spruch_sagen(self, code=None, delay_ms=500):
        self.code_eingeben(code,delay_ms)
        
    def spruch_lesen(self, delay_ms=500):
        self.lese_spruch(delay_ms)
        
    def lese_spruch(self,delay_ms=500):
        """Liest den Code vom Boden (falls dort ein Zettel liegt)."""
        if not self.framework:
            return None
        code_obj = self.framework.spielfeld.finde_code(self.x, self.y)
        if code_obj:
            self.geheimer_code = code_obj.gib_code()
            print(f"[Knappe] Spruch {self.geheimer_code} notiert.")
            if self.framework:
                self.framework.spielfeld.entferne_objekt(code_obj)
            return self.geheimer_code
        print("[Knappe] Kein Spruch hier.")
        self._render_and_delay(delay_ms)
        return None
    
    def bediene_tor(self,delay_ms=500):
        """Versucht, das Tor vor dem Helden zu öffnen oder zu schließen."""
        tor = self.framework.spielfeld.finde_tor_vor(self)
        if tor:
            if tor.offen:
                tor.schliessen()
            else:
                tor.oeffnen()
        else:
            return None
        self._render_and_delay(delay_ms)


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
            if tuer._eingeben(code):
                print("[Knappe] " + self.geheimer_code + "!")
            else:
                if self.geheimer_code == None:
                    print("[Knappe] Ich habe keinen Spruch...")
                    self._ungueltige_aktion("Ungültige Aktion! Versuch es nochmal!")
                else:
                    self._ungueltige_aktion("Ungültige Aktion! Versuch es nochmal!")
        else:
            print("[Knappe] Keine Tür vor mir.")
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
        
    def transmute_richtung(self,r):
        if r=="down":
            return "S"
        elif r=="up":
            return "N"
        elif r=="left":
            return "W"
        else:
            return "O"