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
        # Use ASCII 'Schluessel' as canonical typ so rendering keymap matches
        super().__init__(typ="Schluessel", x=x, y=y, richtung="down", sprite_pfad=sprite_pfad, name=name)
        # english attribute 'color' and german alias 'farbe'
        self.color = color
        self.farbe = color

    def gib_farbe(self):
        return self.farbe
    
    def get_farbe(self):
        return self.farbe
    
    def set_farbe(self,farbe):
        if farbe in ["green","red","blue","golden","violet"]:
            self.farbe = farbe
            self.color = farbe
            # update the sprite path to match the new color and reload the image
            try:
                self.sprite_pfad = f"sprites/key_{farbe}.png"
                self.bild = lade_sprite(self.sprite_pfad)
            except Exception:
                # If loading fails, keep previous image but continue
                pass
            # apply direction-specific variant if available and show a short render
            self._update_sprite_richtung()
            self._render_and_delay(150)

        else:
            print("Ungültige Farbe: ", farbe)

    def benutzen(self, ziel):
        """Try to use this key on a target (e.g. a Tuer)."""
        if ziel is None:
            return False
        try:
            return ziel.schluessel_einsetzen(self)
        except Exception:
            return False

    def oeffne_tuer(self, tuer) -> bool:
        """Attempt to open the given door with this key.
        Calls tuer.verwende_schluessel(self) if present; otherwise falls back
        to tuer.schluessel_einsetzen(self).
        """
        if tuer is None:
            return False
        try:
            if hasattr(tuer, 'verwende_schluessel'):
                return tuer.verwende_schluessel(self)
            return tuer.schluessel_einsetzen(self)
        except Exception:
            return False
