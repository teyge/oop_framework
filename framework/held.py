"""framework.held

Clean, minimal Held + MetaHeld implementation for the framework.
Provides the APIs the framework and tests expect (e.g. nehm_auf_alle,
gold_gib, add_item) and a Meta wrapper that delegates to student objects.
"""

import pygame
from .objekt import Objekt
from .inventar import Inventar


class Held(Objekt):
    """Minimal, robust implementation used when no student Held is present."""

    def __init__(self, framework, x=0, y=0, richtung="down",
                 sprite_pfad="sprites/held.png", name="Namenloser Held",
                 steuerung_aktiv=True, weiblich=False):
        if weiblich:
            sprite_pfad = "sprites/held2.png"
        super().__init__(typ="Held", x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)
        self.framework = framework
        self.ist_held = True
        self.geheimer_code = None
        self.weiblich = weiblich
        self.knappen = []

        # initial gold (best-effort read from level settings)
        try:
            settings = getattr(self.framework, 'spielfeld', None).settings or {}
        except Exception:
            settings = {}
        held_settings = settings.get('Held', {}) if isinstance(settings, dict) else {}
        try:
            self.gold = int(held_settings.get('gold', settings.get('gold', 0) if isinstance(settings, dict) else 0) or 0)
        except Exception:
            self.gold = 0

        try:
            self.inventar = Inventar()
        except Exception:
            self.inventar = None

        if steuerung_aktiv:
            try:
                self.aktiviere_steuerung()
            except Exception:
                pass

    def aktiviere_steuerung(self):
        try:
            self.framework.taste_registrieren(pygame.K_LEFT,  lambda: self.links(0))
            self.framework.taste_registrieren(pygame.K_RIGHT, lambda: self.rechts(0))
            self.framework.taste_registrieren(pygame.K_UP,    lambda: self.geh(0))
            self.framework.taste_registrieren(pygame.K_DOWN,  lambda: self.zurueck(0))
            # Enter: pick up a single relevant object (heart, key or spruch)
            self.framework.taste_registrieren(pygame.K_RETURN, lambda: getattr(self, 'nehm_auf_einfach', getattr(self, 'nehm_auf_alle', lambda: None))())
            # Space: attack
            self.framework.taste_registrieren(pygame.K_SPACE, lambda: getattr(self, 'attack', lambda: None)())
            # C: only pick up a spruch/code on current tile
            self.framework.taste_registrieren(pygame.K_c, lambda: getattr(self, 'lese_spruch', lambda: None)())
            # F: try to open a Tor in front (open only)
            self.framework.taste_registrieren(pygame.K_f, lambda: getattr(self, 'oeffne_tor_vor', lambda: None)())
            # V: try to open a Tür in front: prefer spruch, else try keys
            self.framework.taste_registrieren(pygame.K_v, lambda: getattr(self, 'oeffne_tuer_vor', lambda: None)())
        except Exception:
            pass

    def gold_gib(self) -> int:
        return int(getattr(self, 'gold', 0) or 0)

    def add_item(self, item: object) -> None:
        if not hasattr(self, 'inventar') or self.inventar is None:
            try:
                self.inventar = Inventar()
            except Exception:
                self.inventar = None
        if self.inventar is None:
            return
        try:
            self.inventar.hinzufuegen(item)
        except Exception:
            try:
                if hasattr(self.inventar, '_items'):
                    self.inventar._items.append(item)
            except Exception:
                pass

    # ------------------ Knappen (Button page) ------------------
    def add_knappe(self, knappe_obj) -> None:
        """Adds a Knappe object to the hero's knappen list (idempotent).

        Spielfeld will call this when it spawns a Knappe; for student-held
        cases the held may be a MetaHeld which inherits this method.
        """
        #print("[DEBUG] Versuche Knappe hinzuzufügen zu Held!")
        try:
            if not hasattr(self, 'knappen') or self.knappen is None:
                self.knappen = []
            if knappe_obj not in self.knappen:
                self.knappen.append(knappe_obj)
        except Exception:
            pass

    def gib_knappe(self, index: int = 0):
        """Return the knappe at index (default first) or None if not present.

        This must not block when no knappe exists.
        """
        try:
            if not hasattr(self, 'knappen') or not self.knappen:
                #print("[DEBUG] Held hat keine Knappen Liste!")
                return None
            if index is None:
                #print("[DEBUG] Kein Index übergeben. Gebe ersten Knappen zurück!")
                index = 0
            if index < 0:
                #print("[DEBUG] Index < 0 wurde verwendet!")
                return None
            return self.knappen[index] if index < len(self.knappen) else None
        except Exception:
            print("Held hat keinen Knappen zum Rufen!")
            return None

    # ------------------ Code/Schloss Interaktion: Eingabe / Anwenden ------------------
    def code_eingeben(self, code=None, delay_ms=500):
        """Versucht, vor der Tür einen Code einzugeben.

        Wenn `code` None ist, wird `self.geheimer_code` verwendet. Wenn keine
        Tür vor dem Helden ist, wird die Aktion als ungültig behandelt (blockierend
        falls nicht via Tastatur aufgerufen).
        """
        if not self.framework:
            return False
        if code is None and hasattr(self, 'geheimer_code'):
            code = self.geheimer_code

        # find tile in front
        from .utils import richtung_offset
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        tuer = self.framework.spielfeld.finde_tuer(tx, ty)
        if not tuer:
            # according to spec: block when no door
            self._ungueltige_aktion("Keine Tür vor mir!")
            return False

        try:
            # prefer public API
            if hasattr(tuer, 'code_eingeben'):
                ok = tuer.code_eingeben(code)
            elif hasattr(tuer, '_eingeben'):
                ok = tuer._eingeben(code)
            else:
                ok = False
        except Exception:
            ok = False

        if not ok:
            # block if code incorrect
            self._ungueltige_aktion("Ungültiger Spruch / Code!")
            return False

        # success
        return True

    def spruch_anwenden(self, code=None, delay_ms=500):
        """Alias: versucht, den gespeicherten Spruch vor der Tür anzuwenden."""
        return self.code_eingeben(code=code, delay_ms=delay_ms)

    def spruch_sagen(self, code=None, delay_ms=500):
        return self.spruch_anwenden(code=code, delay_ms=delay_ms)



    def nehm_auf_alle(self):
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            return

        if not hasattr(self, 'inventar') or self.inventar is None:
            try:
                self.inventar = Inventar()
            except Exception:
                self.inventar = None

        objects_on_tile = [o for o in list(sp.objekte) if getattr(o, 'x', None) == self.x and getattr(o, 'y', None) == self.y and o is not self]
        for o in objects_on_tile:
            try:
                if hasattr(o, 'aufgenommen_von'):
                    try:
                        o.aufgenommen_von(self)
                        try:
                            sp.objekte.remove(o)
                        except Exception:
                            pass
                        continue
                    except Exception:
                        pass

                try:
                    if hasattr(o, 'gib_code'):
                        code = o.gib_code()
                        self.geheimer_code = code
                        try:
                            sp.objekte.remove(o)
                        except Exception:
                            pass
                        continue
                    if hasattr(o, '_code'):
                        self.geheimer_code = getattr(o, '_code')
                        try:
                            sp.objekte.remove(o)
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                try:
                    typ = getattr(o, 'typ', '') or getattr(o, 'name', '')
                    if typ and str(typ).lower() in ('herz', 'heart'):
                        try:
                            sp.objekte.remove(o)
                        except Exception:
                            pass
                        try:
                            from .config import HEART_GOLD
                            self.gold = int(getattr(self, 'gold', 0) or 0) + int(HEART_GOLD)
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                try:
                    color = getattr(o, 'farbe', None) or getattr(o, 'color', None) or getattr(o, 'key_color', None)
                    if (getattr(o, 'typ', '') and 'schluessel' in str(getattr(o, 'typ', '')).lower()) or color:
                        try:
                            from .gegenstand import Schluessel as ItemSchluessel
                        except Exception:
                            ItemSchluessel = None
                        if self.inventar is not None and ItemSchluessel is not None:
                            name = getattr(o, 'name', f"Schluessel_{color}")
                            try:
                                item = ItemSchluessel(name=name, wert=0, farbe=color)
                                self.inventar.hinzufuegen(item)
                            except Exception:
                                pass
                        try:
                            sp.objekte.remove(o)
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                try:
                    from .gegenstand import Gegenstand
                except Exception:
                    Gegenstand = None
                try:
                    if self.inventar is not None and Gegenstand is not None:
                        item_name = getattr(o, 'name', getattr(o, 'typ', 'Gegenstand'))
                        item = Gegenstand(name=item_name, wert=0)
                        try:
                            self.inventar.hinzufuegen(item)
                        except Exception:
                            try:
                                if hasattr(self.inventar, '_items'):
                                    self.inventar._items.append(item)
                            except Exception:
                                pass
                        try:
                            sp.objekte.remove(o)
                        except Exception:
                            pass
                        continue
                except Exception:
                    pass

                try:
                    if o in sp.objekte:
                        sp.objekte.remove(o)
                except Exception:
                    pass
            except Exception:
                continue

    def nehm_auf_einfach(self):
        """Pick up only heart, key or spruch on the current tile.

        If nothing is found, print a console message "Hier liegt nichts." and
        return False. Otherwise perform the pickup and return True.
        """
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            return False

        found = False
        # prefer heart
        try:
            herz = sp.finde_herz(self.x, self.y)
            if herz:
                try:
                    sp.entferne_objekt(herz)
                except Exception:
                    try:
                        sp.objekte.remove(herz)
                    except Exception:
                        pass
                try:
                    from .config import HEART_GOLD
                    self.gold = int(getattr(self, 'gold', 0) or 0) + int(HEART_GOLD)
                except Exception:
                    pass
                self._render_and_delay(150)
                return True
        except Exception:
            pass

        # then spruch/code
        try:
            code_obj = sp.finde_code(self.x, self.y)
            if code_obj:
                try:
                    if hasattr(code_obj, 'gib_code'):
                        self.geheimer_code = code_obj.gib_code()
                    else:
                        self.geheimer_code = getattr(code_obj, '_code', None)
                except Exception:
                    try:
                        self.geheimer_code = getattr(code_obj, '_code', None)
                    except Exception:
                        self.geheimer_code = None
                try:
                    sp.entferne_objekt(code_obj)
                except Exception:
                    try:
                        sp.objekte.remove(code_obj)
                    except Exception:
                        pass
                self._render_and_delay(150)
                return True
        except Exception:
            pass

        # then keys (Schluessel-like objects)
        try:
            for o in list(sp.objekte):
                try:
                    if (getattr(o, 'typ', '') and 'schluessel' in str(getattr(o, 'typ', '')).lower()) or getattr(o, 'farbe', None) or getattr(o, 'color', None) or getattr(o, 'key_color', None):
                        # create key item similar to nehm_auf_alle behaviour
                        try:
                            from .gegenstand import Schluessel as ItemSchluessel
                        except Exception:
                            ItemSchluessel = None
                        if getattr(self, 'inventar', None) is not None and ItemSchluessel is not None:
                            name = getattr(o, 'name', f"Schluessel_{getattr(o, 'farbe', getattr(o, 'color', getattr(o, 'key_color', 'unk')))}")
                            color = getattr(o, 'farbe', None) or getattr(o, 'color', None) or getattr(o, 'key_color', None)
                            try:
                                item = ItemSchluessel(name=name, wert=0, farbe=color)
                                self.inventar.hinzufuegen(item)
                            except Exception:
                                try:
                                    if hasattr(self.inventar, '_items'):
                                        self.inventar._items.append(item)
                                except Exception:
                                    pass
                        try:
                            sp.entferne_objekt(o)
                        except Exception:
                            try:
                                sp.objekte.remove(o)
                            except Exception:
                                pass
                        self._render_and_delay(150)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # nothing picked up
        try:
            print("Hier liegt nichts.")
        except Exception:
            pass
        return False

    def oeffne_tor_vor(self):
        """Toggle a Tor in front of the hero (open <-> close).

        Prints a console message if no Tor is present.
        """
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            print("Kein Tor vorhanden.")
            return False
        try:
            tor = sp.finde_tor_vor(self)
        except Exception:
            tor = None
        if not tor:
            print("Kein Tor vor mir!")
            return False
        try:
            # toggle
            if getattr(tor, 'offen', False):
                try:
                    tor.schliessen()
                except Exception:
                    pass
            else:
                try:
                    tor.oeffnen()
                except Exception:
                    pass
            self._render_and_delay(150)
            return True
        except Exception:
            print("Tor konnte nicht umgeschaltet werden.")
            return False

    def oeffne_tuer_vor(self):
        """Try to open a Tür in front using stored spruch first, otherwise try keys from inventar."""
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            print("Keine Tür vorhanden.")
            return False
        from .utils import richtung_offset
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        tuer = sp.finde_tuer(tx, ty)
        if not tuer:
            print("Keine Tür vor mir!")
            return False

        # try spruch/code first
        try:
            if getattr(self, 'geheimer_code', None) is not None:
                try:
                    ok = False
                    if hasattr(tuer, 'code_eingeben'):
                        ok = tuer.code_eingeben(self.geheimer_code)
                    elif hasattr(tuer, 'spruch_anwenden'):
                        ok = tuer.spruch_anwenden(self.geheimer_code)
                    if ok:
                        self._render_and_delay(150)
                        return True
                except Exception:
                    pass
        except Exception:
            pass

        # try keys from inventar
        try:
            inv = getattr(self, 'inventar', None)
            if inv is not None:
                for it in list(inv):
                    try:
                        ok = False
                        if hasattr(tuer, 'verwende_schluessel'):
                            ok = tuer.verwende_schluessel(it)
                        elif hasattr(tuer, 'schluessel_einsetzen'):
                            ok = tuer.schluessel_einsetzen(it)
                        if ok:
                            try:
                                inv.entfernen(it)
                            except Exception:
                                pass
                            self._render_and_delay(150)
                            return True
                    except Exception:
                        continue
        except Exception:
            pass

        # nothing worked
        if getattr(self, 'geheimer_code', None) is None:
            print("Ich habe keinen Spruch.")
        else:
            print("Kein passender Schlüssel und Spruch unwirksam.")
        return False

    def attack(self, delay_ms=500):
        # restore old behavior: do nothing if actions are blocked
        if self.framework and getattr(self.framework, "_aktion_blockiert", False):
            return
        if self.tot or not self.framework:
            return

        import os, pygame
        from .utils import richtung_offset

        # aktuelle Blickrichtung merken
        alte_richtung = self.richtung
        try:
            basis = os.path.splitext(self.sprite_pfad)[0]
        except Exception:
            basis = None

        # Animation: 3 Frames (att1..att3)
        frames = [
            f"{basis}_att1.png" if basis else None,
            f"{basis}_att2.png" if basis else None,
            f"{basis}_att3.png" if basis else None,
        ]

        start = pygame.time.get_ticks()
        frame_delay = 100  # ms per frame
        for pfad in frames:
            if not pfad:
                continue
            if os.path.exists(pfad):
                try:
                    self.bild = pygame.image.load(pfad).convert_alpha()
                    try:
                        self._render_and_delay(frame_delay)
                    except Exception:
                        pygame.time.delay(frame_delay)
                except Exception as e:
                    # don't break on missing frames
                    print(f"[Held] Fehler beim Laden von {pfad}: {e}")

        # Nach Animation wieder ursprüngliches Richtungsbild laden
        try:
            self.richtung = alte_richtung
            self._update_sprite_richtung()
        except Exception:
            pass

        # Angriff auf Monster prüfen
        dx, dy = richtung_offset(self.richtung)
        tx, ty = self.x + dx, self.y + dy
        monster = None
        try:
            monster = self.framework.spielfeld.finde_monster(tx, ty)
        except Exception:
            monster = None

        if monster:
            try:
                monster.tot = True
                monster._update_sprite_richtung()
                try:
                    base_m = monster.sprite_pfad.split(".png")[0]
                    ko_m = f"{base_m}_ko.png"
                    if os.path.exists(ko_m):
                        monster.bild = pygame.image.load(ko_m).convert_alpha()
                except Exception as e:
                    print("[Warnung] KO-Sprite Monster:", e)
                try:
                    self._kills = int(getattr(self, '_kills', 0)) + 1
                except Exception:
                    pass
            except Exception:
                pass

        # letzte Frame kurz sichtbar halten
        try:
            self._render_and_delay(delay_ms)
        except Exception:
            pygame.time.delay(delay_ms)

    # ------------------ Code / Spruch lesen ------------------
    def lese_spruch(self, delay_ms=500):
        """Read a code/spruch on the current tile and store it in the hero.

        Removes the code object from the Spielfeld and stores the code in
        `self.geheimer_code`. Returns the code string if found, otherwise None.
        """
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            return None
        try:
            code_obj = sp.finde_code(self.x, self.y)
        except Exception:
            code_obj = None
        if not code_obj:
            return None
        try:
            if hasattr(code_obj, 'gib_code'):
                code = code_obj.gib_code()
            else:
                code = getattr(code_obj, '_code', None)
            self.geheimer_code = code
        except Exception:
            try:
                self.geheimer_code = getattr(code_obj, '_code', None)
            except Exception:
                self.geheimer_code = None
        try:
            sp.entferne_objekt(code_obj)
        except Exception:
            pass
        return getattr(self, 'geheimer_code', None)

    # backward-compatible aliases
    def lese_code(self, delay_ms=500):
        return self.lese_spruch(delay_ms)

    def spruch_lesen(self, delay_ms=500):
        return self.lese_spruch(delay_ms)

    # ------------------ Tür / Tor bedienen ------------------
    def bediene_tor(self, delay_ms=500):
        """Toggle a Tor in front of the hero (open/close) if present.

        Returns True if a Tor was found and toggled, False otherwise.
        Does not raise or block.
        """
        sp = getattr(self.framework, 'spielfeld', None)
        if not sp:
            return False
        try:
            tor = sp.finde_tor_vor(self)
        except Exception:
            tor = None
        if not tor:
            return False
        try:
            if getattr(tor, 'offen', False):
                try:
                    tor.schliessen()
                except Exception:
                    pass
            else:
                try:
                    tor.oeffnen()
                except Exception:
                    pass
            return True
        except Exception:
            return False



class MetaHeld(Held):
    """Wrapper that keeps framework responsibilities and delegates the
    rest to a student-provided object.
    """

    def __init__(self, framework, student_obj, x=0, y=0, richtung='down', weiblich=False):
        super().__init__(framework, x, y, richtung, steuerung_aktiv=False, weiblich=weiblich)
        object.__setattr__(self, '_student', student_obj)
        try:
            setattr(student_obj, 'meta', self)
        except Exception:
            pass
        # Do NOT proactively set x/y/richtung on the student object here.
        # If the student explicitly provides these attributes, they remain.
        # The framework will not create attributes on the student to avoid
        # masking incomplete implementations.
        try:
            self.aktiviere_steuerung()
        except Exception:
            pass

    def aktiviere_steuerung(self):
        """Register controls that prefer student-provided methods when available.
        After calling a student method we sync student's x/y/richtung back to the MetaHeld.
        """
        try:
            stud = object.__getattribute__(self, '_student')
        except Exception:
            stud = None

        def call_student(method_name, *args):
            def _inner():
                try:
                    if stud is not None and hasattr(stud, method_name) and callable(getattr(stud, method_name)):
                        fn = getattr(stud, method_name)
                        try:
                            fn(*args)
                        except TypeError:
                            try:
                                fn()
                            except Exception:
                                pass
                    else:
                        # If the student object does not provide the requested
                        # movement methods, DO NOT fall back to the framework's
                        # implementation — that would allow bypassing the
                        # exercise. For movement-related methods, block the
                        # action and show a hint; for other actions (like
                        # pick-up/attack), falling back to framework behavior is
                        # acceptable to keep levels playable.
                        movement_methods = ('links', 'rechts', 'geh', 'zurueck')
                        if method_name in movement_methods:
                            try:
                                # Treat as invalid action when invoked programmatically
                                # (framework will block non-keyboard calls as appropriate).
                                self._ungueltige_aktion("Schülerklasse hat keine Bewegungsmethode")
                            except Exception:
                                pass
                        else:
                            m = getattr(self, method_name, None)
                            if callable(m):
                                try:
                                    m(*args)
                                except TypeError:
                                    try:
                                        m()
                                    except Exception:
                                        pass
                finally:
                    # sync position/direction from student -> meta if student updated them
                    try:
                        if stud is not None:
                            for a in ('x','y','richtung'):
                                if hasattr(stud, a):
                                    try:
                                        object.__setattr__(self, a, getattr(stud, a))
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                    # Ensure the MetaHeld's sprite reflects the (possibly new) direction
                    try:
                        # Only update directional sprite for MetaHeld (student-wrapped)
                        if hasattr(self, '_update_sprite_richtung'):
                            try:
                                self._update_sprite_richtung()
                            except Exception:
                                pass
                    except Exception:
                        pass
            return _inner

        try:
            # movement keys
            self.framework.taste_registrieren(pygame.K_LEFT,  call_student('links', 0))
            self.framework.taste_registrieren(pygame.K_RIGHT, call_student('rechts', 0))
            self.framework.taste_registrieren(pygame.K_UP,    call_student('geh', 0))
            self.framework.taste_registrieren(pygame.K_DOWN,  call_student('zurueck', 0))
            # Enter: pick up a single relevant object (heart, key or spruch)
            self.framework.taste_registrieren(pygame.K_RETURN, call_student('nehm_auf_einfach'))
            # Space: attack
            self.framework.taste_registrieren(pygame.K_SPACE, call_student('attack'))
            # C: only pick up a spruch/code on current tile
            self.framework.taste_registrieren(pygame.K_c, call_student('lese_spruch'))
            # F: try to open a Tor in front (open only)
            self.framework.taste_registrieren(pygame.K_f, call_student('oeffne_tor_vor'))
            # V: try to open a Tür in front: prefer spruch, else try keys
            self.framework.taste_registrieren(pygame.K_v, call_student('oeffne_tuer_vor'))
        except Exception:
            try:
                super().aktiviere_steuerung()
            except Exception:
                pass

    def __getattr__(self, name):
        stud = object.__getattribute__(self, '_student')
        if hasattr(stud, name):
            return getattr(stud, name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in ('x', 'y', 'richtung'):
            object.__setattr__(self, name, value)
            try:
                stud = object.__getattribute__(self, '_student')
                # Only propagate to the student object if the student already
                # defines this attribute; do not create new attributes on the
                # student object that weren't present before.
                if hasattr(stud, name):
                    try:
                        setattr(stud, name, value)
                    except Exception:
                        pass
            except Exception:
                pass
            return
        object.__setattr__(self, name, value)
        try:
            stud = object.__getattribute__(self, '_student')
            setattr(stud, name, value)
        except Exception:
            pass

    def update(self):
        """Framework-controlled update for MetaHeld.

        Ensure the student object stays in sync with the MetaHeld's authoritative
        position/direction values. Do NOT call any student-provided update() so
        the framework remains responsible for movement and rendering.
        """
        try:
            stud = object.__getattribute__(self, '_student')
        except Exception:
            stud = None
        if stud is None:
            return
        for a in ('x', 'y', 'richtung'):
            try:
                # propagate only to already-existing student attributes
                if hasattr(stud, a):
                    setattr(stud, a, getattr(self, a))
            except Exception:
                pass

    def zeichne(self, screen, feldgroesse):
        """Draw the MetaHeld. Prefer a student-provided zeichne(); otherwise
        use the framework sprite but rotate it according to direction so
        student direction changes immediately reflect visually.
        """
        try:
            stud = object.__getattribute__(self, '_student')
        except Exception:
            stud = None
        # If student provided a custom zeichne(), prefer it
        try:
            if stud is not None and hasattr(stud, 'zeichne') and callable(getattr(stud, 'zeichne')):
                try:
                    stud.zeichne(screen, feldgroesse)
                    return
                except Exception:
                    # fall through to framework drawing
                    pass
        except Exception:
            pass

        # Framework fallback: ensure directional sprite loaded if available
        try:
            try:
                self._update_sprite_richtung()
            except Exception:
                pass
            surf = getattr(self, 'bild', None)
            if surf is None:
                # nothing to draw
                return
            img = pygame.transform.scale(surf, (feldgroesse, feldgroesse))
            # Do not rotate the sprite at runtime; rely on per-direction
            # sprite files loaded by _update_sprite_richtung() instead.
            screen.blit(img, (int(self.x) * feldgroesse, int(self.y) * feldgroesse))
            return
        except Exception:
            return

