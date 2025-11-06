from .objekt import Objekt

class Hindernis(Objekt):
    """Repräsentiert ein unbegehbares Hindernis (Baum, Berg, Mauer).

    Dieses Objekt bietet readonly-Getter für den Namen und eine Methode
    `ist_betretbar()` die immer False zurückliefert.
    """
    def __init__(self, x, y, name: str = "Hindernis", sprite_pfad: str = None):
        # name kann z.B. 'Baum', 'Berg', 'Busch' sein
        sprite = sprite_pfad or "sprites/obstacle.png"
        super().__init__(typ=name, x=x, y=y, richtung="down", sprite_pfad=sprite, name=name)

    def get_name(self) -> str:
        return getattr(self, 'name', None)

    def ist_betretbar(self) -> bool:
        # Hindernisse sind per Definition nicht betretbar
        return False
