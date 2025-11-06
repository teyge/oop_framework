import pygame
from .objekt import Objekt
from .utils import lade_sprite

class Schluessel(Objekt):
    def __init__(self, x, y, color="green", sprite_pfad=None, name=None):
        # default name: Schlüssel
        if name is None:
            name = "Schlüssel"
        if sprite_pfad is None:
            sprite_pfad = f"sprites/key_{color}.png"
        super().__init__(typ="Schlüssel", x=x, y=y, richtung="down", sprite_pfad=sprite_pfad, name=name)
        # englisches Attribut 'color' und deutsches Alias 'farbe'
        self.color = color
        self.farbe = color

    def benutzen(self, ziel):
        """Versuche, diesen Schlüssel an einem Ziel (z.B. Tuer) zu benutzen."""
        if ziel is None:
            return False
        try:
            return ziel.schluessel_einsetzen(self)
        except Exception:
            return False

    def oeffne_tuer(self, tuer) -> bool:
        """Versuche die übergebene Tür mit diesem Schlüssel zu öffnen.
        Versucht zuerst, tuer.verwende_schluessel(self) aufzurufen; wenn nicht vorhanden,
        fällt es auf tuer.schluessel_einsetzen(self) zurück.
        """
        if tuer is None:
            return False
        try:
            if hasattr(tuer, 'verwende_schluessel'):
                return tuer.verwende_schluessel(self)
            return tuer.schluessel_einsetzen(self)
        except Exception:
            return False
