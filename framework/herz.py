# framework/herz.py
from .objekt import Objekt

class Herz(Objekt):
    def __init__(self, x, y, sprite_pfad="sprites/herz.png"):
        super().__init__("Herz", x, y, "down", sprite_pfad)
