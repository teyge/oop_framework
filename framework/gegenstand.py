from typing import Any


class Gegenstand:
    """Basisklasse für Inventar-Gegenstände.

    Attribute:
    - name: Anzeige- bzw. interner Name
    - wert: numerischer Wert (z. B. zum Handeln)
    - typ: string-Kategorie (z. B. 'Gegenstand')
    """

    def __init__(self, name: str, wert: int, typ: str = "Gegenstand"):
        self.name = name
        self.wert = int(wert)
        self.typ = typ

    def beschreibung(self) -> str:
        return f"{self.name} ({self.typ}) — Wert: {self.wert}"

    def __repr__(self) -> str:
        return f"Gegenstand(name={self.name!r}, typ={self.typ!r}, wert={self.wert})"

    # ----------------
    # Getter-Methoden
    # ----------------
    def get_name(self) -> str:
        """Gibt den Namen des Gegenstandes zurück."""
        return getattr(self, 'name', None)

    def get_wert(self) -> int:
        """Gibt den numerischen Wert des Gegenstandes zurück."""
        try:
            return int(getattr(self, 'wert', 0) or 0)
        except Exception:
            return 0

    def get_typ(self) -> str:
        """Gibt den Typ/Kategorie des Gegenstandes zurück."""
        return getattr(self, 'typ', None)


class Schluessel(Gegenstand):
    """Ein einfacher Schlüssel-Gegenstand, der Türen öffnen kann.

    Der Schlüssel besitzt eine `farbe` (z. B. 'green', 'red'). Beim
    Aufruf von `oeffne_tuer(tuer)` versucht er, die Tür zu öffnen. Falls die
    Tür geöffnet wird und der Schlüssel in einem Inventar liegt (Attribut
    `_inventar` gesetzt), entfernt sich der Schlüssel selbst aus dem Inventar.
    """

    def __init__(self, name: str, wert: int, farbe: str):
        super().__init__(name=name, wert=wert, typ="Schlüssel")
        self.farbe = farbe

    def oeffne_tuer(self, tuer: Any) -> bool:
        """Versucht die Tür zu öffnen. Gibt True zurück, wenn geöffnet.

        Entfernt den Schlüssel aus dem zugehörigen Inventar (falls vorhanden).
        """
        if tuer is None:
            return False
        try:
            # Tür soll die Methode `schluessel_einsetzen` implementieren
            erfolg = False
            if hasattr(tuer, "schluessel_einsetzen"):
                erfolg = tuer.schluessel_einsetzen(self)
            else:
                # Fallback: prüfe direkt die Farbe auf dem Türobjekt
                tcol = getattr(tuer, "key_color", None) or getattr(tuer, "keycolor", None)
                if tcol and tcol == self.farbe:
                    # markiere offen, falls möglich
                    if hasattr(tuer, "offen"):
                        setattr(tuer, "offen", True)
                    erfolg = True

            if erfolg:
                inv = getattr(self, "_inventar", None)
                if inv is not None:
                    try:
                        inv.entfernen(self)
                    except Exception:
                        pass
                return True
            return False
        except Exception:
            return False

    # ----------------
    # Schlüssel-spezifische Getter
    # ----------------
    def get_farbe(self) -> str:
        """Gibt die Farbe des Schlüssels zurück (z. B. 'green')."""
        return getattr(self, 'farbe', None)
