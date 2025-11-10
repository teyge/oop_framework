from .objekt import Objekt
from .utils import lade_sprite
import os
from .objekt import Objekt
from .utils import lade_sprite
import os


class Hindernis(Objekt):
    """Repräsentiert ein unbegehbares Hindernis (Baum, Berg, Busch, ...).

    Wenn kein expliziter `sprite_pfad` übergeben wird, versuchen wir, ein
    passendes Sprite automatisch aus dem `sprites/`-Verzeichnis zu laden
    (z. B. 'Baum' -> 'sprites/baum.png'). Falls keine Datei vorhanden ist,
    fällt die Klasse auf das Standardplatzhalter-Sprite zurück.
    """

    def __init__(self, x, y, name: str = "Hindernis", sprite_pfad: str = None):
        # name kann z. B. 'Baum', 'Berg', 'Busch' sein
        chosen = None
        try:
            if sprite_pfad:
                chosen = sprite_pfad
            else:
                # normalize name to filename-friendly form
                n = (name or "hindernis").strip().lower()
                # replace common German umlauts and spaces
                n = n.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
                n = n.replace('ß', 'ss')
                n = n.replace(' ', '_')
                repo_root = os.path.dirname(os.path.dirname(__file__))
                cand = os.path.join(repo_root, 'sprites', f"{n}.png")
                if os.path.exists(cand):
                    chosen = cand
                else:
                    # try alternate filename
                    cand2 = os.path.join(repo_root, 'sprites', f"{n}_small.png")
                    if os.path.exists(cand2):
                        chosen = cand2
                    else:
                        chosen = None
        except Exception:
            chosen = None

        # Use lade_sprite to get a Surface (handles missing files and placeholder)
        try:
            if chosen:
                _ = lade_sprite(chosen)
        except Exception:
            pass

        pfad = chosen if chosen else sprite_pfad
        # typ should be the canonical class name so the Spielfeld logic can
        # recognize Hindernis objects regardless of their display name.
        super().__init__(typ="Hindernis", x=x, y=y, richtung="down", sprite_pfad=pfad, name=name)

    def get_name(self) -> str:
        return getattr(self, 'name', None)

    def ist_betretbar(self) -> bool:
        # Hindernisse sind per Definition nicht betretbar
        return False

    def ist_passierbar(self) -> bool:
        """Compatibility shim: return True if the tile/object is passable.

        The rest of the codebase expects an `ist_passierbar()` method that
        returns True for passable tiles. For Hindernis this is always False.
        """
        try:
            # Hindernis is not enterable => not passierbar
            return bool(self.ist_betretbar())
        except Exception:
            return False

