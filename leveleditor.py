# leveleditor.py
import os
import json
import pygame
import tkinter as tk
from tkinter import filedialog, ttk

# -----------------------------
# Konfiguration
# -----------------------------
TILESIZE = 64
MARGIN = 8
MIN_W, MIN_H = 2, 2

# -----------------------------
# Basis-Tiles
# -----------------------------
TILES = {
    "1": ("w", "sprites/gras.png"),        # Weg/Gras
    "2": ("t", "sprites/baum.png"),        # zyklisch: Baum/Berg/Busch (Taste 2)
    "3": ("h", "sprites/herz.png"),        # Herz
    "4": ("v", "sprites/villager.png"),    # Dorfbewohner
    "5": ("x", "sprites/monster.png"),     # Monster
    "6": ("p", "sprites/held.png"),        # Held/Knappe: Taste 6 toggelt 'p' <-> 'k'
    "7": ("c", "sprites/code.png"),        # Code-Zettel
    "8": ("d", "sprites/tuer.png"),        # Tür
    "9": ("g", "sprites/tor_zu.png"),      # Tor (geschlossen)
}

# -----------------------------
# Zyklische Gruppen
# -----------------------------
TILE_GROUPS = {
    # Mehrfach '2' drücken -> t (Baum) -> m (Berg) -> b (Busch) -> t ...
    "2": [
        ("t", "sprites/baum.png"),
        ("m", "sprites/berg.png"),
        ("b", "sprites/busch.png"),
    ],
}

FALLBACK_COLORS = {
    "w": (50, 160, 50),
    "t": (34, 100, 34),
    "m": (120, 120, 120),
    "b": (20, 120, 20),
    "h": (220, 60, 60),
    "x": (60, 60, 220),
    "p": (220, 200, 60),
    "k": (200, 200, 220),
    "v": (150, 120, 60),
    "c": (220, 180, 60),
    "d": (150, 90, 40),
    "g": (150, 100, 40),
    "G": (180, 130, 60),
}


class LevelEditor:
    def __init__(self, start_w=4, start_h=4, tilesize=TILESIZE):
        pygame.init()
        pygame.display.set_caption("Level-Editor")

        # Zeit & Fonts
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 18)
        self.big = pygame.font.SysFont("consolas", 22, bold=True)
        self.small = pygame.font.SysFont("consolas", 14)

        # Grid
        self.tilesize = tilesize
        self.grid_w = max(MIN_W, start_w)
        self.grid_h = max(MIN_H, start_h)
        self.level = [["w" for _ in range(self.grid_w)] for _ in range(self.grid_h)]

        # Auswahl
        self.selected_key = "1"
        self.selected_code = TILES[self.selected_key][0]
        self.tile_cycle_idx = {k: 0 for k in TILE_GROUPS}
        self._toggle_held_knappe = True  # True: 'p' (Held), False: 'k' (Knappe)

        # Sprites
        self.sprites = self._load_all_sprites()

        # Fenster
        self._recalc_window()
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))

        # Schnellspeichern
        self.quick_mode = False
        self.quick_digits = ""

        # Privatisierungs-Flags (F1-Menü)
        self.privacy_flags = {
            "Held": False, "Knappe": False, "Monster": False,
            "Herz": False, "Tuer": False, "Code": False, "Villager": False
        }
        # Orientierungen pro Koordinate als dict "x,y" -> "up|right|down|left"
        self.orientations = {}

    # -----------------------------
    # Sprites
    # -----------------------------
    def _load_all_sprites(self):
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.display.get_surface():
            pygame.display.set_mode((1, 1))

        sprites = {}
        for key, (code, path) in TILES.items():
            sprites[code] = self._load_sprite(path)

        # Knappe & evtl. weitere
        sprites["k"] = self._load_sprite("sprites/knappe.png")

        # Gruppen-Sprites
        for key, group in TILE_GROUPS.items():
            for code, path in group:
                sprites[code] = self._load_sprite(path)
        return sprites

    def _load_sprite(self, path):
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (self.tilesize, self.tilesize))
        except Exception as e:
            print(f"[Warnung] Sprite fehlgeschlagen {path}: {e}")
        # Fallback
        surf = pygame.Surface((self.tilesize, self.tilesize), pygame.SRCALPHA)
        surf.fill((200, 0, 0, 60))
        return surf

    # -----------------------------
    # Fenster/Panel
    # -----------------------------
    def _recalc_window(self):
        self.panel_w = 380
        self.win_w = self.grid_w * self.tilesize + self.panel_w + 2 * MARGIN
        self.win_h = max(self.grid_h * self.tilesize + 2 * MARGIN, 620)

    # -----------------------------
    # Tiles setzen
    # -----------------------------
    def set_tile_at_mouse(self, code, right_click=False):
        mx, my = pygame.mouse.get_pos()
        gx = (mx - MARGIN) // self.tilesize
        gy = (my - MARGIN) // self.tilesize
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return

        if right_click:
            self.level[gy][gx] = "w"
            return

        aktueller_code = self.level[gy][gx]

        # Sichtbarkeit toggeln, wenn gleicher Typ (Großbuchstabe = sichtbar markiert)
        if aktueller_code.lower() == code.lower():
            if aktueller_code.isupper():
                self.level[gy][gx] = aktueller_code.lower()
            else:
                # Nur eine sichtbare Markierung je Typ
                for y in range(self.grid_h):
                    for x in range(self.grid_w):
                        if self.level[y][x].lower() == code.lower():
                            self.level[y][x] = self.level[y][x].lower()
                self.level[gy][gx] = code.upper()
            return

        # Max. ein Held und max. ein Knappe
        if code.lower() in ("p", "k"):
            for row in self.level:
                for c in row:
                    if c.lower() == code.lower():
                        print(f"[Hinweis] Es darf nur einen '{code.lower()}' geben!")
                        return

        self.level[gy][gx] = code

    # -----------------------------
    # Rendering
    # -----------------------------
    def draw(self):
        self.screen.fill((15, 15, 15))
        self._draw_grid()
        self._draw_panel()
        pygame.display.flip()

    def _draw_grid(self):
        for y in range(self.grid_h):
            for x in range(self.grid_w):
                gx, gy = MARGIN + x * self.tilesize, MARGIN + y * self.tilesize
                rect = pygame.Rect(gx, gy, self.tilesize, self.tilesize)
                code = self.level[y][x]

                # Basisgras
                self.screen.blit(self.sprites.get("w"), (gx, gy))

                # Tile
                if code != "w":
                    sprite = self.sprites.get(code.lower())
                    if sprite:
                        self.screen.blit(sprite, (gx, gy))
                    else:
                        pygame.draw.rect(self.screen, FALLBACK_COLORS.get(code.lower(), (80, 80, 80)), rect)

                # Sichtbarkeitsrahmen
                if code.isupper():
                    pygame.draw.rect(self.screen, (255, 0, 0), rect, 3)

                # Raster
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
                # Richtungsindikator (kleiner Pfeil) falls Orientierung gesetzt oder Tile drehbar
                key = f"{x},{y}"
                dir = self.orientations.get(key, None)
                if dir:
                    # einfache Pfeil- / Richtungsanzeige: Linie vom Zentrum nach dir
                    cx, cy = gx + self.tilesize // 2, gy + self.tilesize // 2
                    off = self.tilesize // 3
                    vecs = {"up": (0, -off), "right": (off, 0), "down": (0, off), "left": (-off, 0)}
                    dx, dy = vecs.get(dir, (0, off))
                    pygame.draw.line(self.screen, (255, 240, 0), (cx, cy), (cx + dx, cy + dy), 3)
                    # Pfeilspitze
                    pygame.draw.circle(self.screen, (255, 240, 0), (cx + dx, cy + dy), 4)

    def _draw_panel(self):
        x0 = MARGIN + self.grid_w * self.tilesize + MARGIN
        y = MARGIN
        pygame.draw.rect(self.screen, (35, 35, 35), (x0 - MARGIN, 0, self.panel_w, self.win_h))

        self._text(self.big, "Level-Editor", (240, 240, 240), x0, y); y += 34
        self._text(self.font, f"Größe: {self.grid_w} x {self.grid_h}", (220, 220, 220), x0, y); y += 30

        # Aktuelles Tile
        self._text(self.font, "Aktuelles Tile:", (200, 200, 80), x0, y); y += 22
        sprite = self.sprites.get(self.selected_code)
        if sprite:
            preview = pygame.transform.smoothscale(sprite, (48, 48))
            self.screen.blit(preview, (x0, y))
        y += 60

        # Tile-Tabelle
        self._text(self.font, "Tiles:", (200, 200, 80), x0, y); y += 25
        for key, (code, path) in TILES.items():
            if key == "2":
                txt = f"[2]  →  't'/'m'/'b' (zyklisch)"
            elif key == "6":
                txt = f"[6]  →  'p'/'k' (toggle Held/Knappe)"
            else:
                txt = f"[{key}]  →  '{code}'"
            self._text(self.small, txt, (230, 230, 230), x0 + 10, y)
            y += 20
        y += 15

        # Privatisierung (Bonuspanel)
        self._text(self.font, "Privatisierung:", (200, 200, 80), x0, y); y += 25
        for k, v in self.privacy_flags.items():
            color = (180, 60, 60) if v else (100, 180, 100)
            self._text(self.small, f"{k}: {'privat' if v else 'öffentlich'}", color, x0, y)
            y += 18

    def _text(self, font, text, color, x, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, (x, y))

    # -----------------------------
    # Privatisierung (F1)
    # -----------------------------
    def open_privacy_menu(self):
        root = tk.Tk()
        root.title("Privatisierung pro Klasse")

        frame = ttk.Frame(root, padding=10)
        frame.grid(row=0, column=0)

        ttk.Label(frame, text="Privatisierung pro Klasse:", font=("Consolas", 12, "bold")).grid(row=0, column=0, sticky="w")

        vars_by_class = {}
        for i, (klasse, val) in enumerate(self.privacy_flags.items(), start=1):
            var = tk.BooleanVar(value=val)
            chk = ttk.Checkbutton(frame, text=klasse, variable=var)
            chk.grid(row=i, column=0, sticky="w")
            vars_by_class[klasse] = var

        def speichern():
            for klasse, var in vars_by_class.items():
                self.privacy_flags[klasse] = var.get()
            root.destroy()

        ttk.Button(frame, text="OK", command=speichern).grid(row=len(vars_by_class) + 1, column=0, pady=10)
        root.mainloop()

    # -----------------------------
    # JSON I/O
    # -----------------------------
    def from_json(self, data):
        if "tiles" not in data:
            raise ValueError("JSON enthält kein Feld 'tiles'.")
        tiles = data["tiles"]
        self.grid_h = len(tiles)
        self.grid_w = max(len(r) for r in tiles)
        self.level = [list(r.ljust(self.grid_w, "w")) for r in tiles]

        # Settings optional (Abwärtskompatibilität)
        if "settings" in data:
            self.privacy_flags = {k: v.get("privat", False) for k, v in data["settings"].items()}
            # Fehlende Klassen auf False ergänzen
            for k in list(self.privacy_flags.keys()):
                self.privacy_flags.setdefault(k, False)
            for k in ["Held", "Knappe", "Monster", "Herz", "Tuer", "Code", "Villager"]:
                self.privacy_flags.setdefault(k, False)
        # Lade Orientierungen, falls vorhanden (Format: {"x,y": "up"})
        self.orientations = data.get("settings", {}).get("orientations", {})

        self._recalc_window()
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))

    def to_json(self):
        data = {"tiles": ["".join(row) for row in self.level]}
        # Immer Settings schreiben, auch wenn alle False sind
        data["settings"] = {k: {"public": not v} for k, v in self.privacy_flags.items()}
        # Orientierungen exportieren (falls gesetzt)
        if self.orientations:
            data["settings"].setdefault("orientations", {})
            data["settings"]["orientations"].update(self.orientations)
        return data


    def lade_dialog(self):
        root = tk.Tk(); root.withdraw()
        pfad = filedialog.askopenfilename(filetypes=[("JSON Level", "*.json")])
        root.destroy()
        if not pfad:
            return
        with open(pfad, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.from_json(data)
        print(f"[OK] Level geladen: {pfad}")

    def speichere_json(self, pfad):
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=2)
        print(f"[OK] Level gespeichert: {pfad}")

    def speicher_dialog(self):
        root = tk.Tk(); root.withdraw()
        pfad = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Level", "*.json")])
        root.destroy()
        if pfad:
            self.speichere_json(pfad)

    # -----------------------------
    # Event-Loop
    # -----------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.set_tile_at_mouse(self.selected_code)
                    elif event.button == 3:
                        self.set_tile_at_mouse(self.selected_code, right_click=True)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_F1:
                        self.open_privacy_menu()
                    elif event.key == pygame.K_s:
                        self.speicher_dialog()
                    elif event.key == pygame.K_o:
                        self.lade_dialog()
                    elif event.key == pygame.K_RIGHT:
                        self.resize(+1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.resize(0, +1)
                    elif event.key == pygame.K_LEFT:
                        self.resize(-1, 0)
                    elif event.key == pygame.K_UP:
                        self.resize(0, -1)
                    elif pygame.K_0 <= event.key <= pygame.K_9:
                        self.handle_digit(chr(event.key))
                elif event.type == pygame.MOUSEWHEEL:
                    # Mausrad drehen => Orientierung ändern (Vorsicht: event.y positive = up)
                    self.rotate_orientation_at_mouse(event.y)
            self.draw()
            self.clock.tick(60)
        pygame.quit()

    # -----------------------------
    # Tastenauswertung
    # -----------------------------
    def handle_digit(self, key_str: str):
        # Zyklische Gruppe (Taste '2')
        if key_str in TILE_GROUPS:
            idx = (self.tile_cycle_idx[key_str] + 1) % len(TILE_GROUPS[key_str])
            self.tile_cycle_idx[key_str] = idx
            code, path = TILE_GROUPS[key_str][idx]
            if code not in self.sprites:
                self.sprites[code] = self._load_sprite(path)
            self.selected_code = code
            return

        # Held/Knappe Toggle (Taste '6')
        if key_str == "6":
            self._toggle_held_knappe = not self._toggle_held_knappe
            self.selected_code = "p" if self._toggle_held_knappe else "k"
            print("[Info] Auswahl:", "Held ('p')" if self._toggle_held_knappe else "Knappe ('k')")
            return

        # Standardtiles
        if key_str in TILES:
            self.selected_code = TILES[key_str][0]

    # -----------------------------
    # Mausrad / Orientierungen
    # -----------------------------
    def rotate_orientation_at_mouse(self, delta):
        """Delta int: positive = wheel up, negative = wheel down. Zyklisch: up->right->down->left."""
        mx, my = pygame.mouse.get_pos()
        gx = (mx - MARGIN) // self.tilesize
        gy = (my - MARGIN) // self.tilesize
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return
        code = self.level[gy][gx]
        # Nur für entitätstypen (veränderbar) reagieren; erweitert bei Bedarf
        if code.lower() not in ("p", "k", "x", "d", "g", "v"):
            return
        key = f"{gx},{gy}"
        dirs = ["up", "right", "down", "left"]
        cur = self.orientations.get(key, "down")
        idx = dirs.index(cur) if cur in dirs else 2
        idx = (idx + (1 if delta > 0 else -1)) % 4
        self.orientations[key] = dirs[idx]

    # -----------------------------
    # Resize
    # -----------------------------
    def resize(self, dx, dy):
        if dx != 0:
            if dx > 0:
                for row in self.level:
                    row.extend(["w"] * dx)
                self.grid_w += dx
            elif self.grid_w + dx >= MIN_W:
                for row in self.level:
                    for _ in range(-dx):
                        row.pop()
                self.grid_w += dx

        if dy != 0:
            if dy > 0:
                for _ in range(dy):
                    self.level.append(["w"] * self.grid_w)
                self.grid_h += dy
            elif self.grid_h + dy >= MIN_H:
                for _ in range(-dy):
                    self.level.pop()
                self.grid_h += dy

        self._recalc_window()
        self.screen = pygame.display.set_mode((self.win_w, self.win_h))


if __name__ == "__main__":
    LevelEditor().run()
