# framework/villager.py
import pygame
from .objekt import Objekt

class Villager(Objekt):
    def __init__(self, framework, x=0, y=0, richtung="down",
                 sprite_pfad="sprites/villager.png", name="Nils",
                 steuerung_aktiv=False,weiblich = False):
        if weiblich:
            t = "Dorfbewohnerin"
            sprite_pfad="sprites/villager2.png"
        else:
            t = "Dorfbewohner"
        super().__init__(typ=t, x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)
        self.framework = framework
        self.ist_held = False
        
        
        
    def 
        
    def transmute_richtung(self,r):
        if r=="down":
            return "S"
        elif r=="up":
            return "N"
        elif r=="left":
            return "W"
        else:
            return "O"
