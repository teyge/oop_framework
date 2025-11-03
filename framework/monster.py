import os
import pygame
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
            # Merke das richtungsabhängige Normalbild (falls vorhanden) damit die Richtung nicht verloren geht
            try:
                gerichtetes = f"{base}_{self.richtung}.png"
                if os.path.exists(gerichtetes):
                    self.bild_normal = pygame.image.load(gerichtetes).convert_alpha()
                else:
                    self.bild_normal = pygame.image.load(self.sprite_pfad).convert_alpha()
            except Exception:
                # fallback: belasse das aktuelle self.bild als normal
                try:
                    self.bild_normal = self.bild
                except Exception:
                    self.bild_normal = None
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
    def angriff(self, opfer=None, delay_ms=500):
        """Führt den Angriff aus: Animation wie beim Helden, Opfer (falls vorhanden) wird KO gesetzt.
        Wenn opfer None ist, wird das Feld vor dem Monster geprüft (wie beim Helden)."""
        if self.tot or not self.framework:
            return

        # Bestimme Opfer falls nicht übergeben
        if opfer is None:
            dx, dy = richtung_offset(self.richtung)
            tx, ty = self.x + dx, self.y + dy
            sp = getattr(self.framework, "spielfeld", None)
            if sp:
                opfer = sp.objekt_an(tx, ty)

        jetzt = pygame.time.get_ticks()

        # Merke aktuellen Zustand, damit wir nach dem Angriff exakt wiederherstellen
        prev_richtung = getattr(self, "richtung", None)
        prev_bild_normal = getattr(self, "bild_normal", None)
        prev_bild = getattr(self, "bild", None)
        print(prev_bild,prev_bild_normal,prev_richtung)

        # Angriffssprite (wie beim Held). Versuche richtungsabhängige Frames, sonst generische.
        base = os.path.splitext(self.sprite_pfad)[0]
        dir_used = prev_richtung or getattr(self, "richtung", "down")
        dir_trio = [f"{base}_{dir_used}_att.png"]
        gen_trio = [f"{base}_att.png"]

        frames = []
        if any(os.path.exists(p) for p in dir_trio):
            frames = [p for p in dir_trio if os.path.exists(p)]
        elif any(os.path.exists(p) for p in gen_trio):
            frames = [p for p in gen_trio if os.path.exists(p)]

        frame_delay = 100  # ms pro Frame
        if frames:
            for pfad in frames:
                try:
                    self.bild = pygame.image.load(pfad).convert_alpha()
                    try:
                        self._render_and_delay(frame_delay)
                    except Exception:
                        pygame.time.delay(frame_delay)
                except Exception:
                    continue

        # markiere Angriff gestartet (verhindert sofortiges Nachangreifen in update)
        self.angriff_start = jetzt

        # Stelle sicher: Richtung beibehalten und lade richtungsabhängiges Normalbild (falls vorhanden)
        try:
            if prev_richtung is not None:
                self.richtung = prev_richtung
        except Exception:
            pass

        if prev_bild_normal is None:
            try:
                gerichtetes = f"{base}_{self.richtung}.png"
                if os.path.exists(gerichtetes):
                    self.bild_normal = pygame.image.load(gerichtetes).convert_alpha()
                else:
                    self.bild_normal = pygame.image.load(self.sprite_pfad).convert_alpha()
            except Exception:
                self.bild_normal = prev_bild

        # Wenn ein Opfer vorhanden ist -> KO setzen und KO-Sprite laden wie beim Held
        if opfer is not None:
            try:
                opfer.tot = True
                try:
                    opfer._update_sprite_richtung()
                except Exception:
                    pass
            except Exception:
                pass

            try:
                base_opf = os.path.splitext(opfer.sprite_pfad)[0]
                ko_pfad = f"{base_opf}_ko.png"
                if os.path.exists(ko_pfad):
                    opfer.bild = pygame.image.load(ko_pfad).convert_alpha()
            except Exception:
                pass

        # Hinweise / Aktionsblock setzen — nur blockieren, wenn Opfer Held oder Knappe ist
        try:
            victim_typ = (getattr(opfer, "typ", "") or "").lower() if opfer is not None else ""
            if opfer is not None:
                self.framework._hinweis = f"{opfer.name} wurde von {self.name} überrascht!"
            else:
                self.framework._hinweis = f"{self.name} schwingt die Keule ins Leere."
            if victim_typ in ("held", "knappe"):
                self.framework._aktion_blockiert = True
        except Exception:
            pass

        # kurze Pause nach Angriff (sichtbar lassen)
        try:
            self._render_and_delay(delay_ms)
        except Exception:
            pygame.time.delay(delay_ms)

        # Restore von bilder-Backup falls vorhanden
        try:
            if prev_bild_normal is not None:
                self.bild_normal = prev_bild_normal
            elif prev_bild is not None:
                self.bild = prev_bild
        except Exception:
            pass
        self._update_sprite_richtung()
