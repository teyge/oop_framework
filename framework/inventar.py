from typing import List, Iterator, Optional


class Inventar:
    """Ein kleines Inventarsystem zur Aufnahme von Gegenständen.

    Das Inventar speichert Gegenstandsobjekte in einer Liste. Wird ein
    Gegenstand mittels `hinzufuegen` eingefügt, bekommt das Objekt eine
    rückwärtsreferenz `_inventar`, so dass z. B. Schlüssel sich beim
    Benutzen selbst entfernen können.
    """

    def __init__(self):
        # interne Liste; wir bieten zusätzlich ein public attribute `items`
        # damit Aufrufer direkt auf die Liste zugreifen können, wenn gewünscht.
        self._items: List[object] = []
        self.items = self._items

    def hinzufuegen(self, item: object) -> None:
        """Fügt ein Item ans Ende des Inventars hinzu.

        Setzt optional eine Rückreferenz `item._inventar = self` wenn das
        Attribut nicht verhindert wird.
        """
        self._items.append(item)
        try:
            setattr(item, "_inventar", self)
        except Exception:
            # Falls das Item das Setzen nicht erlaubt, ignorieren
            pass

    def entfernen(self, item: object) -> bool:
        """Entfernt das Item aus dem Inventar (falls vorhanden).

        Gibt True zurück, wenn ein Item entfernt wurde, sonst False.
        """
        try:
            self._items.remove(item)
            try:
                # Aufräumen der Rückreferenz
                if getattr(item, "_inventar", None) is self:
                    delattr(item, "_inventar")
            except Exception:
                pass
            return True
        except ValueError:
            return False

    def anzahl(self) -> int:
        return len(self._items)

    def gib_item(self, index: int) -> Optional[object]:
        try:
            return self._items[index]
        except Exception:
            return None

    def items_vom_typ(self, typ: str) -> List[object]:
        """Gibt alle Items zurück, deren Attribut `typ` gleich dem übergebenen String ist.

        Falls ein Item kein Attribut `typ` besitzt, wird es ignoriert.
        """
        out = []
        for it in self._items:
            if hasattr(it, "typ") and getattr(it, "typ") == typ:
                out.append(it)
        return out

    # Kompatibler Alias wie gewünscht
    def suche_nach_typ(self, typ: str) -> List[object]:
        """Alias zu items_vom_typ(): liefert alle Items eines bestimmten Typs."""
        return self.items_vom_typ(typ)

    def __str__(self) -> str:
        """Gibt eine kurze Textliste der Item-Namen zurück."""
        try:
            names = [getattr(it, 'name', str(it)) for it in self._items]
            return ", ".join(names)
        except Exception:
            return f"Inventar({len(self._items)} items)"

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, i: int) -> object:
        return self._items[i]

    def __iter__(self) -> Iterator[object]:
        return iter(self._items)
