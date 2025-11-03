# framework/code.py
import random
from .objekt import Objekt
import pygame

class Code(Objekt):
    """Ein Zettel auf dem Boden, der einen geheimen Code enthält."""
    def __init__(self, x, y, sprite_pfad="sprites/code.png",c=""):
        super().__init__("Spruch", x, y, "down", sprite_pfad)
        # zufälliger Code (4-stellig)
        if c != "":
            self._code = c
        else:
            self._code = self.random_zaubertwort()
        #self._code = str(random.randint(1000, 9999))
        self.gesammelt = False

    def gib_code(self):
        """Gibt den Code zurück (für fortgeschrittene Schüleraufgaben)."""
        return self._code
    
    def gib_spruch(self):
        return self._code
    
    def zeichne(self, screen, feldgroesse):
        img = pygame.transform.scale(self.bild,(0.7*feldgroesse, 0.7*feldgroesse))
        screen.blit(img, (self.x * feldgroesse, self.y * feldgroesse))
        
    def random_zauberwort(self):
        zauberwoerter = [
            "Alohomora", "Ignis", "Fulgura", "Lumos", "Nox",
            "Aqua", "Ventus", "Terra", "Glacius", "Silencio",
            "Accio", "Protego", "Obliviate", "Impervius"
        ]

        # Wähle zufälligen Spruch
        spruch = random.choice(zauberwoerter) + " " + random.choice(zauberwoerter)
        return spruch
    
    def spruch_ausgeben(self):
        print("Der Spruch ist " + self._code +"!")
