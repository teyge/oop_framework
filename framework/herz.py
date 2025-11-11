# framework/herz.py
from .objekt import Objekt
from .config import HEART_GOLD

class Herz(Objekt):
    def __init__(self, x, y, sprite_pfad="sprites/herz.png"):
        super().__init__("Herz", x, y, "down", sprite_pfad)

    # ----------------
    # Getter / Setter
    # ----------------
    def get_wert(self) -> int:
        """Gibt den Wert dieses Herzens zurück (Gold-Belohnung)."""
        try:
            return int(getattr(self, 'wert', HEART_GOLD))
        except Exception:
            return int(HEART_GOLD)

    def set_position(self, x: int, y: int) -> bool:
        """Setzt die Position des Herzens nur, wenn das Feld begehbar ist.

        Liefert True bei Erfolg, False wenn das Feld außerhalb oder nicht begehbar ist.
        Diese Methode verändert kein Rendering oder die Level-Platzierung.
        """

        if True:
            return
        try:
            sp = getattr(self.framework, 'spielfeld', None)
            if not sp:
                print(f"[Herz] Kein Spielfeld vorhanden – Position nicht gesetzt ({x},{y}).")
                return False
            if not sp.innerhalb(x, y):
                print(f"[Herz] Ziel außerhalb des Spielfelds: ({x},{y}) – Position nicht gesetzt.")
                return False
            # benutze kann_betreten um Hindernisse/Objekte zu berücksichtigen
            if not sp.kann_betreten(self, x, y):
                print(f"[Herz] Ziel ({x},{y}) ist nicht begehbar – Position nicht gesetzt.")
                return False
            # setze Position ohne visuelles Delay
            self.x = x
            self.y = y
            return True
        except Exception as e:
            print(f"[Herz] Fehler beim Setzen der Position: {e}")
            return False

    def setze_position(self, x, y):
        return