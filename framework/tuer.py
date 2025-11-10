# framework/tuer.py
from .objekt import Objekt
from .utils import lade_sprite

class Tuer(Objekt):
    """Eine verschlossene Tür.
    Kann entweder per Code (Spruch) geöffnet werden oder per farbigem Schlüssel.
    Wenn color gesetzt ist, erwartet die Tür einen Schlüssel dieser Farbe (z.B. 'green','golden').
    """
    def __init__(self, x, y, code=None, color=None, sprite_pfad=None):
        # Wenn color gesetzt, nutze das farbige locked_door Sprite, sonst Standard
        if sprite_pfad is None:
            if color:
                sprite_pfad = f"sprites/locked_door_{color}.png"
            else:
                sprite_pfad = "sprites/tuer.png"
        # Use 'Tuer' as the canonical type name (ASCII) for consistency with level settings/tests
        # Present the human-readable name with Umlaut so code that checks for 'Tür' still works
        super().__init__("Tuer", x, y, "down", sprite_pfad, name="Tür")
        self._richtiger_code = code
        # Farbattribut: 'farbe' ist die neue, deutsch-benannte Eigenschaft.
        # Wir behalten 'key_color' als Alias für Abwärtskompatibilität.
        self.farbe = color
        self.key_color = color
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
    def schluessel_einsetzen(self, schluessel):
        """Versuche die Tür mit einem Schlüssel-Objekt zu öffnen.
        schluessel kann ein Objekt mit .color / .key_color Attribut sein.
        """
        # Behalte bestehendes Verhalten über eine neue zentrale Methode
        return self.verwende_schluessel(schluessel)

    def verwende_schluessel(self, key) -> bool:
        """
        Öffnet die Tür, wenn der übergebene Schlüssel die passende Farbe hat.
        key: Objekt mit Attributen 'farbe' (deutsch), 'color' oder 'key_color'.
        Wenn self.farbe is None, akzeptiere jeden Schlüssel (universell).
        Setzt self.offen = True und lädt das offene Sprite. Rückgabe True bei Erfolg.
        """
        if key is None:
            return False
        # Ermittle Schlüssel-Farbe (prüfe deutsch/englisch Alias)
        kfarbe = getattr(key, 'farbe', None)
        if kfarbe is None:
            kfarbe = getattr(key, 'color', None)
        if kfarbe is None:
            kfarbe = getattr(key, 'key_color', None)

        # Türfarbe (None = universell)
        tfarbe = getattr(self, 'farbe', None) or getattr(self, 'key_color', None)

        if tfarbe is None:
            # universelle Tür: jeder Schlüssel wirkt
            ok = True
        else:
            ok = (kfarbe == tfarbe)

        if ok:
            self.offen = True
            try:
                self.bild = lade_sprite("sprites/tuer_offen.png")
            except Exception:
                pass
            return True
        return False
        
    def ist_passierbar(self):
        # A door is passable when it is open. Return True when offen == True.
        return bool(self.offen)

    # ----------------
    # Getter API
    # ----------------
    def get_farbe(self):
        """Gibt die konfigurierte Farbe der Tür zurück (oder None wenn universell)."""
        # prefer the german attribute, fall back to english alias
        return getattr(self, 'farbe', None) or getattr(self, 'key_color', None)

    def get_offen(self) -> bool:
        """Gibt zurück, ob die Tür offen ist (True) oder geschlossen (False)."""
        return bool(getattr(self, 'offen', False))
    
    def update(self):
        # Sprite abhängig vom Zustand der Tür wechseln
        if getattr(self, "offen", False):
            self.bild = lade_sprite("sprites/tuer_offen.png")
        else:
            # falls farbige Tür, stelle sicher, dass das correct locked sprite geladen ist
            if getattr(self, "key_color", None):
                try:
                    self.bild = lade_sprite(f"sprites/locked_door_{self.key_color}.png")
                except Exception:
                    pass

        # das Sprite neu laden (wenn du das schon irgendwo zentral machst, diesen Teil ggf. dort einfügen)
        try:
            self._bild_surface = self._lade_sprite(self._bild)
        except Exception:
            pass


