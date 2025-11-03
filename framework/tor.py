import pygame
from .objekt import Objekt
from .utils import lade_sprite

class Tor(Objekt):
    """Ein Tor, das geöffnet und geschlossen werden kann."""

    def __init__(self, x, y, offen=False):
        sprite = "sprites/tor_offen.png" if offen else "sprites/tor_zu.png"
        super().__init__("Tor", x, y, "down", sprite)
        self.offen = offen

    def oeffnen(self):
        if not self.offen:
            self.offen = True
            self.bild = lade_sprite("sprites/tor_offen.png")

    def schliessen(self):
        if self.offen:
            self.offen = False
            self.bild = lade_sprite("sprites/tor_zu.png")

    def ist_passierbar(self):
        return not self.offen
    
    #def _lade_sprite(self):
        
