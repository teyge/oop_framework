# framework/level.py
import json, os, pygame
from .utils import lade_sprite

TILE_SPRITES = {
    "w": "sprites/gras.png",
    "m": "sprites/berg.png",
    "b": "sprites/busch.png",
    "t": "sprites/baum.png",
    "h": "sprites/herz.png",
    "c": "sprites/code.png",
    "d": "sprites/tuer.png"
}

class Level:
    def __init__(self, dateipfad):
        if not os.path.exists(dateipfad):
            raise FileNotFoundError(dateipfad)
        with open(dateipfad, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "tiles" not in data or not isinstance(data["tiles"], list):
            raise ValueError("Leveldatei muss 'tiles' (Liste von Strings) enthalten.")
        self.tiles = [list(row) for row in data["tiles"]]
        self.hoehe = len(self.tiles)
        self.breite = len(self.tiles[0]) if self.hoehe else 0
        self.settings = data.get("settings", {})


        # Texturen laden
        self.texturen = {code: lade_sprite(pfad) for code, pfad in TILE_SPRITES.items()}

    def zeichne(self, screen, feldgroesse):
        # Hintergrundfläche (optional, hält Artefakte fern)
        screen.fill((20, 120, 20))
        for y, zeile in enumerate(self.tiles):
            for x, code in enumerate(zeile):
                # Immer Gras als Basis zeichnen
                gras = self.texturen.get("w")
                if gras:
                    img = pygame.transform.scale(gras, (feldgroesse, feldgroesse))
                    screen.blit(img, (x * feldgroesse, y * feldgroesse))
                # Hindernisse oben drauf
                if code in ("m","b","t","g"):
                    tex = self.texturen.get(code)
                    if tex:
                        img = pygame.transform.scale(tex, (feldgroesse, feldgroesse))
                        screen.blit(img, (x * feldgroesse, y * feldgroesse))

    def iter_entity_spawns(self):
        for y, zeile in enumerate(self.tiles):
            for x, code in enumerate(zeile):
                if code.lower() in ("p", "h", "x", "c", "d","g","k"):
                    # Unter Entities soll Gras liegen
                    self.tiles[y][x] = "w"
                    # bestimme Typ und Sichtbarkeit (Großbuchstabe = direkt verfügbar)
                    typ = code.lower()
                    sichtbar = code.isupper()
                    yield typ, x, y, sichtbar

