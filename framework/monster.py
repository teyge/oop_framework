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


class Bogenschuetze(Monster):
    """Ranged attacker: fires a fast arrow (rendered as a brown line)
    along its facing direction. The arrow travels quickly to the first
    visible target (Held, Knappe, Monster) and only travels while the
    line-of-sight isn't blocked by non-passierbare objects (doors, hindernisse).
    """
    def __init__(self, x, y, richtung="down", sprite_pfad="sprites/archer.png", name="Bogenschütze"):
        super().__init__(x=x, y=y, richtung=richtung, sprite_pfad=sprite_pfad, name=name)
        # shorter attack duration for ranged animation
        self.angriff_dauer = 300

    def links(self):
        print("Der Bogenschütze ist zu konzentriert, um sich zu drehen.")

    def geh(self):
        print("Der Bogenschütze ist zu konzentriert, um sich zu bewegen.")

    def rechts(self):
        print("Der Bogenschütze ist zu konzentriert, um sich zu drehen.")

    def zurueck(self, delay_ms=500):
        print("Der Bogenschütze ist zu konzentriert, um sich zu bewegen.")

    def setze_richtung(self,r):
        print("Der Bogenschütze ist zu konzentriert, um sich zu drehen.")

    def setze_position(self,x,y):
        print("Der Bogenschütze ist zu konzentriert, um sich zu bewegen.")

    

    def update(self):
        # If dead or framework missing, nothing to do
        if self.tot or not self.framework:
            return

        jetzt = pygame.time.get_ticks()

        # If currently in attack animation window, wait until finished
        if self.angriff_start:
            if jetzt - self.angriff_start >= self.angriff_dauer:
                # restore normal sprite
                self.bild = self.bild_normal
                self.angriff_start = None
            return

        # Walk the line of sight in facing direction until blocked
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            return

        while 0 <= tx < sp.level.breite and 0 <= ty < sp.level.hoehe:
            # First, check for blocking terrain (trees, bushes, mountains)
            try:
                terrain = sp.terrain_art_an(tx, ty)
                if terrain and terrain != 'Weg':
                    # terrain blocks sight
                    break
            except Exception:
                pass

            # Check for an object at (tx,ty)
            try:
                o = sp.objekt_an(tx, ty)
            except Exception:
                o = None

            if o is not None and o is not self:
                # If object explicitly provides ist_passierbar and it's False => blocks sight
                try:
                    if hasattr(o, 'ist_passierbar'):
                        try:
                            if not bool(o.ist_passierbar()):
                                break
                        except Exception:
                            # if checking fails, conservatively treat as blocking
                            break
                except Exception:
                    pass

                # If the object is a valid victim (Held, Knappe, Monster), shoot
                try:
                    ttyp = (getattr(o, 'typ', '') or '').lower()
                except Exception:
                    ttyp = ''

                # don't target already KO'd victims
                try:
                    is_dead = bool(getattr(o, 'tot', False))
                except Exception:
                    is_dead = False
                if ttyp in ('held', 'knappe', 'monster') and not is_dead:
                    # Create projectile: determine pixel centers
                    try:
                        fw = self.framework
                        if not hasattr(fw, '_projectiles'):
                            fw._projectiles = []
                        # attacker center
                        start_px = (self.x * fw.feldgroesse + fw.feldgroesse // 2, self.y * fw.feldgroesse + fw.feldgroesse // 2)
                        end_px = (o.x * fw.feldgroesse + fw.feldgroesse // 2, o.y * fw.feldgroesse + fw.feldgroesse // 2)
                        proj = {
                            'start': start_px,
                            'end': end_px,
                            'start_time': jetzt,
                            'duration': 200,
                            'attacker': self,
                            'victim': o,
                        }
                        fw._projectiles.append(proj)
                    except Exception:
                        pass

                    # set attack visual on archer immediately (frames may be handled by angriff())
                    try:
                        base = os.path.splitext(self.sprite_pfad)[0]
                        att_pfad = f"{base}_att.png"
                        if os.path.exists(att_pfad):
                            try:
                                self.bild = pygame.image.load(att_pfad).convert_alpha()
                            except Exception:
                                pass
                    except Exception:
                        pass

                    # mark attack start to prevent immediate repeat
                    self.angriff_start = jetzt
                    return

            # step further along line
            tx += dx
            ty += dy
