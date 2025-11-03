# framework/objekt.py
import pygame
from .utils import richtung_offset,richtung_offset2, lade_sprite, RICHTUNGEN
import os
import inspect
import sys


class Objekt:
    def __init__(self, typ, x=0, y=0, richtung="down", sprite_pfad=None, name=None):
        self._privatmodus = False
        self.typ = typ                    # "Held", "Monster", "Herz", ...
        self.name = name or typ           # Anzeigename, z. B. "Harribert"
        self.x = x
        self.y = y
        self.richtung = richtung
        self.sprite_pfad = sprite_pfad
        self.bild = lade_sprite(sprite_pfad)
        self.framework = None
        self.tot = False
        self._herzen = 0
        self._kills = 0
        
        self._update_sprite_richtung()
        
    def set_privatmodus(self, aktiv: bool):
        print("Setze private mode bei",self.typ)
        self._privatmodus = aktiv
        
    def setze_richtung(self,r):
        if r not in ["up","down","left","right"]:
            if r not in ["N","S","O","W"]:
                print("Ungültige Richtungsangabe!")
            else:
                print(self.transmute_richtung(r))
                self.richtung = self.transmute_richtung(r)
        else:
            self.richtung = r
        self._update_sprite_richtung()
            
    def setze_position(self, x, y):
        """Setzt die Position nur, wenn (x,y) im Spielfeld liegt,
        das Terrain dort 'Weg' ist und kein anderes Objekt dort steht."""
        sp = getattr(self, "framework", None)
        sp = getattr(sp, "spielfeld", None) if sp else None
        if not sp:
            print("[Warnung] Kein Spielfeld vorhanden – setze_position() abgebrochen.")
            return False

        # 1) Grenzen prüfen
        if not sp.innerhalb(x, y):
            print(f"[{self.typ}] Position außerhalb des Spielfelds: ({x},{y})")
            return False

        # 2) Terrain muss 'Weg' sein
        if sp.terrain_art_an(x, y) != "Weg":
            print(f"[{self.typ}] Feld ({x},{y}) ist kein begehbarer Weg.")
            return False

        # 3) Feld muss leer sein (kein anderes Objekt)
        occupant = sp.objekt_an(x, y)
        if occupant is not None and occupant is not self:
            print(f"[{self.typ}] Position ({x},{y}) ist bereits belegt ({occupant.typ}).")
            return False

        # 4) Setzen + kurzer sichtbarer Refresh
        self.x, self.y = x, y
        self._render_and_delay(150)
        print(f"[{self.typ}] wurde nach ({x},{y}) gesetzt.")
        return True


        
    

    def __getattribute__(self, name):
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        # Framework-interner Zugriff bleibt erlaubt
        caller = sys._getframe(1).f_code.co_filename
        if "framework" in caller.replace("\\", "/"):
            return object.__getattribute__(self, name)

        if object.__getattribute__(self, "_privatmodus") and name in ("x", "y", "r", "richtung"):
            raise AttributeError(f"Attribut '{name}' ist privat – Zugriff nicht erlaubt")

        return object.__getattribute__(self, name)


    def __setattr__(self, name, value):
        # interne Variablen dürfen immer gesetzt werden
        if name.startswith("_"):
            return object.__setattr__(self, name, value)
        

        caller = sys._getframe(1).f_code.co_filename
        if "framework" in caller.replace("\\", "/"):
            return object.__setattr__(self, name, value)

        if object.__getattribute__(self, "_privatmodus") and name in ("x", "y", "r", "richtung"):
            raise AttributeError(f"Attribut '{name}' ist privat – Schreiben nicht erlaubt")

        object.__setattr__(self, name, value)


 
     
    """
    def __getattribute__(self, name):
        # Zugriff auf private Attribute verbieten, wenn der Modus aktiv ist
        if name in ("x", "y", "richtung", "leben", "herzen") and object.__getattribute__(self, "_privatmodus"):
            raise AttributeError(f"Attribut '{name}' ist privat – Zugriff nicht erlaubt")
        return object.__getattribute__(self, name)
            
        def verbleibende_herzen(self):
            return self.framework.spielfeld.anzahl_herzen()
    """
        
    def getX(self):
        return self.x
    
    def verbleibende_herzen(self):
            return self.framework.spielfeld.anzahl_herzen()

        
    def _ungueltige_aktion(self, meldung="Ungültige Aktion"):
        if self.framework:
            # Nur blockieren, wenn nicht über Tastatur ausgelöst
            if not getattr(self.framework, "_aus_tastatur", False):
                self.framework.stoppe_programm(meldung)
            else:
                # Tastatur: nur Hinweis ausgeben, aber weiterlaufen
                self.framework._hinweis = meldung



    # ---- sichtbare Verzögerung, inklusive Render ----
    def _render_and_delay(self, ms=0):
        if not self.framework:  # falls außerhalb genutzt
            if ms > 0: pygame.time.wait(ms)
            return
        self.framework._render_frame()
        if ms > 0:
            # aktiv warten, Events pumpen, damit Fenster responsiv bleibt
            start = pygame.time.get_ticks()
            while pygame.time.get_ticks() - start < ms:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); raise SystemExit
                self.framework._render_frame()
                pygame.time.delay(16)  # ~60 FPS

    # ---- Aktionen (Baseline: direkt ausführen + sichtbar machen) ----
    def geh(self, delay_ms=500):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return

        """Bewegt das Objekt ein Feld in Blickrichtung, prüft Hindernisse und Monster."""
        if self.tot or not self.framework:
            return

        dx, dy = richtung_offset(self.richtung)
        nx, ny = self.x + dx, self.y + dy

        # 1️⃣ Prüfe, ob das Ziel betretbar ist
        if not self.framework.spielfeld.kann_betreten(self, nx, ny):
            mon = self.framework.spielfeld.finde_monster(nx, ny)
            if mon and self.typ == "Held" and self.framework.spielfeld.ist_frontal_zu_monster(self, mon):
                # Held läuft in Monster hinein → stirbt
                self.tot = True
                self._update_sprite_richtung()
                self._render_and_delay(100)

                return
            # Ungültige Bewegung (z. B. Wand, Baum, Tür)
            if not self.framework._aus_tastatur:
                self._ungueltige_aktion("Ungültige Aktion. Versuch es nochmal!")
            print("["+self.typ+"] Dahin kann ich nicht gehen!")
            return

        # 2️⃣ Bewegung ist gültig → Koordinaten übernehmen
        self.x, self.y = nx, ny
        self._render_and_delay(delay_ms)
        
    def zurueck(self, delay_ms=500):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return

        """Bewegt das Objekt ein Feld in Blickrichtung, prüft Hindernisse und Monster."""
        if self.tot or not self.framework:
            return

        dx, dy = richtung_offset2(self.richtung)
        nx, ny = self.x + dx, self.y + dy

        # 1️⃣ Prüfe, ob das Ziel betretbar ist
        if not self.framework.spielfeld.kann_betreten(self, nx, ny):
            mon = self.framework.spielfeld.finde_monster(nx, ny)
            if mon and self.typ == "Held" and self.framework.spielfeld.ist_frontal_zu_monster(self, mon):
                if mon and self.typ == "Held" and self.framework.spielfeld.ist_frontal_zu_monster(self, mon):
                    self.tot = True
                    self._update_sprite_richtung()  # 🔧 KO-Grafik laden
                    self._render_and_delay(delay_ms)
                    return

            # Ungültige Bewegung (z. B. Wand, Baum, Tür)
            if not self.framework._aus_tastatur:
                self._ungueltige_aktion("Ungültige Aktion. Versuch es nochmal!")
            print("["+self.typ+"] Dahin kann ich nicht gehen!")
            return

        # 2️⃣ Bewegung ist gültig → Koordinaten übernehmen
        self.x, self.y = nx, ny
        self._render_and_delay(delay_ms)


    def links(self, delay_ms=500):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        if self.tot: return
        idx = (RICHTUNGEN.index(self.richtung) - 1) % 4
        self.richtung = RICHTUNGEN[idx]
        self._update_sprite_richtung()
        self._render_and_delay(delay_ms)

    def rechts(self, delay_ms=500):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        if self.tot: return
        idx = (RICHTUNGEN.index(self.richtung) + 1) % 4
        self.richtung = RICHTUNGEN[idx]
        self._update_sprite_richtung()
        self._render_and_delay(delay_ms)
        
        
    def nimm_herz(self,delay_ms=500):
        self.nehme_auf(delay_ms)

    def nehme_auf(self, delay_ms=500):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        if self.typ not in ["Held","Knappe"]:
            self._ungueltige_aktion("Dieses Objekt darf keine Herzen nehmen!")
            return
        if self.tot or not self.framework: return
        herz = self.framework.spielfeld.finde_herz(self.x, self.y)
        if herz:
            self.framework.spielfeld.entferne_objekt(herz)
            self._herzen += 1
            self._render_and_delay(delay_ms)
            """
            if not self.framework.spielfeld.gibt_noch_herzen() and not self.framework._aktion_blockiert:
                self.framework.sieg()"""

        else:
            if not self.framework._aus_tastatur:
                self._ungueltige_aktion("Ungültige Aktion! Versuch es nochmal!")
            print("["+self.typ+"] Hier liegt kein Herz!")
            return

    def attack(self, delay_ms=500):
        """Nur Held darf angreifen – alle anderen ignorieren."""
        if self.typ != "Held":
            self._ungueltige_aktion("Dieses Objekt kann nicht angreifen!")
            return

    
#    def _zeige_angriff_sprite(self):
#        """Wechselt temporär zum Angriffssprite, falls vorhanden."""
#        t = self.sprite_pfad.copy()
#        base = self.sprite_pfad.split(".png")[0]
#        att_pfad = f"{base}_att.png"
#        try:
#            self.bild = pygame.image.load(att_pfad).convert_alpha()
#            self._render_and_delay(150)
#            return t
#        except FileNotFoundError:
#            pass  # kein Angriffssprite vorhanden
    


    # ---- Wahrnehmung / Infos (für Schüler) ----
    def was_ist_vorn(self):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        return self.framework.spielfeld.objekt_art_an(tx, ty) or \
               self.framework.spielfeld.terrain_art_an(tx, ty)
    
    def was_ist_links(self):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        i = RICHTUNGEN.index(self.richtung)
        links_richtung = RICHTUNGEN[(i - 1) % 4]
        dx, dy = richtung_offset(links_richtung)
        tx, ty = self.x + dx, self.y + dy
        return self.framework.spielfeld.objekt_art_an(tx, ty) or \
               self.framework.spielfeld.terrain_art_an(tx, ty)
    
    def was_ist_rechts(self):
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        i = RICHTUNGEN.index(self.richtung)
        rechts_richtung = RICHTUNGEN[(i + 1) % 4]
        dx, dy = richtung_offset(rechts_richtung)
        tx, ty = self.x + dx, self.y + dy
        return self.framework.spielfeld.objekt_art_an(tx, ty) or \
               self.framework.spielfeld.terrain_art_an(tx, ty)

    def gib_objekt_vor_dir(self):
        """Gibt das erste Objekt auf dem Feld vor diesem Objekt zurück (oder None).
        Verwendet immer self.richtung und self.framework.spielfeld."""
        sp = getattr(self, "framework", None)
        sp = getattr(sp, "spielfeld", None) if sp else None
        if not sp:
            return None
        richt = getattr(self, "richtung", "down")
        dx, dy = richtung_offset(richt)
        tx, ty = getattr(self, "x", 0) + dx, getattr(self, "y", 0) + dy
        return sp.objekt_an(tx, ty)

    def ist_auf_herz(self):
        """
        if self.typ not in ["Held","Knappe"]:
            self._ungueltige_aktion("Dieses Objekt darf das nicht!")
            return
        """
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        return bool(self.framework.spielfeld.finde_herz(self.x, self.y))
    
    def herzen_vor_mir(self):
        """Zählt, wie viele Herzen in Sichtlinie liegen – einschließlich des Felds, auf dem das Objekt steht.
        Stoppt bei Hindernis oder Monster. Das eigene Objekt blockiert nicht."""
        sp = getattr(self, "framework", None)
        sp = getattr(sp, "spielfeld", None) if sp else None
        if not sp:
            print("[Warnung] Kein Spielfeld vorhanden – herzen_vor_mir() abgebrochen.")
            return 0

        dx, dy = richtung_offset(self.richtung)
        x, y = self.x, self.y  # beginne beim aktuellen Feld
        count = 0

        # Solange innerhalb des Spielfelds
        while sp.innerhalb(x, y):
            terrain = sp.terrain_art_an(x, y)
            if terrain != "Weg":
                break  # Hindernis (Baum, Mauer, etc.)

            # Zähle Herz, auch wenn es auf demselben Feld wie das Objekt liegt
            herz = sp.finde_herz(x, y)
            if herz:
                count += 1

            obj = sp.objekt_an(x, y)
            if obj:
                # Das eigene Objekt soll die Sichtlinie nicht blockieren
                if obj is self:
                    pass
                elif obj.typ.lower() == "monster":
                    break  # Sichtlinie blockiert
                elif obj.typ.lower() == "herz":
                    # Herz wurde bereits über finde_herz gezählt
                    pass
                else:
                    break  # anderes Objekt blockiert

            # Ein Feld weiter in Blickrichtung
            x += dx
            y += dy

        return count


    # ---- Zeichnen + Attributanzeige ----
    def zeichne(self, screen, feldgroesse):
        img = pygame.transform.scale(self.bild, (feldgroesse, feldgroesse))
        screen.blit(img, (self.x * feldgroesse, self.y * feldgroesse))

    def attribute_als_text(self):
        return {}
        """
        return {
            "name": self.name, "x": self.x, "y": self.y,
            "richtung": self.richtung
        }
        """
    
    def _update_sprite_richtung(self):
        """Lädt automatisch das passende Richtungs-Sprite, falls vorhanden."""
        if not self.sprite_pfad:
            return
        if self.tot:
            basis = os.path.splitext(self.sprite_pfad)[0]
            ko_pfad = f"{basis}_ko.png"
            if os.path.exists(ko_pfad):
                self.bild = pygame.image.load(ko_pfad).convert_alpha()
                self.bild.set_alpha(220)
            else:
                # Fallback: rotes Rechteck, falls kein KO-Sprite existiert
                self.bild = pygame.Surface((64, 64), pygame.SRCALPHA)
                self.bild.fill((180, 0, 0, 180))
            return


        basis = os.path.splitext(self.sprite_pfad)[0]
        pfad_gerichtet = f"{basis}_{self.richtung}.png"
        if os.path.exists(pfad_gerichtet):
            self.bild = lade_sprite(pfad_gerichtet)
            
    def transmute_richtung(self,r):
        if r=="down":
            return "S"
        elif r=="up":
            return "N"
        elif r=="left":
            return "W"
        elif r=="right":
            return "O"
        elif r=="N":
            return "up"
        elif r=="O":
            return "right"
        elif r=="W":
            return "left"
        elif r=="S":
            return "down"

