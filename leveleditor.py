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
        # Tür/Schlüssel Farbauswahl (mehrfaches Drücken der Taste wechselt Farbe)
        self.door_colors = ["green", "violet", "blue", "golden", "red"]
        self.door_color_idx = 0
        self.selected_door_color = None
        self.key_colors = ["green", "violet", "blue", "golden", "red"]
        self.key_color_idx = 0
        self.selected_key_color = None
        # Villager gender selection (toggle with key '4')
        self.selected_villager_weiblich = False
        # Persisted per-tile settings (colors for doors/keys, villagers genders)
        self.colors = {}
        self.villagers = {}
        # Persisted quest settings per tile
        self.quests = {}

        # Extra level-wide settings (initial_gold, quest_max_kosten, quest_mode, quest_items_needed)
        self.level_settings = {}

        # Victory condition settings (editable via F3)
        # Stored under level_settings['victory'] as a dict. Backwards-compatible default
        # is to require collecting all hearts.
        self.level_settings.setdefault('victory', {"collect_hearts": True, "move_to": None, "classes_present": False})

        # Student-class loader flags (F2 toggles)
        # If True the exported level will indicate student classes should be used
        # If student_classes_in_subfolder is True, the editor will mark that
        # student classes are expected under the `klassen/` package instead of
        # the repo root `schueler.py`.
        self.use_student_module = False
        self.student_classes_in_subfolder = False

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
        # zusätzliche Sprites: farbige Türen und Schlüssel, weiblicher Villager
        for col in ("green", "violet", "blue", "golden", "red"):
            sprites[f"locked_door_{col}"] = self._load_sprite(f"sprites/locked_door_{col}.png")
            sprites[f"key_{col}"] = self._load_sprite(f"sprites/key_{col}.png")
        sprites["v_female"] = self._load_sprite("sprites/villager2.png")
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
            # Entferne ggf. gespeicherte Settings für diese Koordinate
            key = f"{gx},{gy}"
            self.level[gy][gx] = "w"
            self.colors.pop(key, None)
            self.villagers.pop(key, None)
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

        # Falls wir eine Tür, einen Schlüssel oder einen Villager setzen,
        # dann speichere die gewählte Farbe / das gewählte Geschlecht in den settings.
        key = f"{gx},{gy}"
        if code.lower() == "d":
            # Türfarbe: falls keine ausgewählt, entferne Eintrag (spawn benutzt default)
            if self.selected_door_color:
                self.colors[key] = self.selected_door_color
            else:
                self.colors.pop(key, None)

        elif code.lower() == "s":
            # Schlüsselfarbe: falls keine ausgewählt, benutze default 'green'
            color = self.selected_key_color or "green"
            self.colors[key] = color

        elif code.lower() == "v":
            # Villager gender
            self.villagers[key] = "female" if self.selected_villager_weiblich else "male"

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

                # Tile (unterstützt farbige Türen/Schlüssel und weibliche Villager)
                if code != "w":
                    low = code.lower()
                    key_coord = f"{x},{y}"
                    sprite = None
                    if low == "d":
                        col = self.colors.get(key_coord)
                        if col:
                            sprite = self.sprites.get(f"locked_door_{col}")
                        else:
                            sprite = self.sprites.get("d")
                    elif low == "s":
                        col = self.colors.get(key_coord) or "green"
                        sprite = self.sprites.get(f"key_{col}")
                    elif low == "v":
                        gender = self.villagers.get(key_coord)
                        if isinstance(gender, str) and gender.lower() in ("female", "weiblich", "w"):
                            sprite = self.sprites.get("v_female")
                        else:
                            sprite = self.sprites.get("v")
                    else:
                        sprite = self.sprites.get(low)

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

                # If a move-to victory target is configured, draw a red highlight around that tile
                try:
                    vic = self.level_settings.get('victory', {}) or {}
                    mv = vic.get('move_to') if isinstance(vic, dict) else None
                    if mv and isinstance(mv, dict) and mv.get('enabled'):
                        tx = int(mv.get('x', -999))
                        ty = int(mv.get('y', -999))
                        if tx == x and ty == y:
                            pygame.draw.rect(self.screen, (255, 0, 0), rect, 4)
                except Exception:
                    pass

    def _draw_panel(self):
        x0 = MARGIN + self.grid_w * self.tilesize + MARGIN
        y = MARGIN
        pygame.draw.rect(self.screen, (35, 35, 35), (x0 - MARGIN, 0, self.panel_w, self.win_h))

        self._text(self.big, "Level-Editor", (240, 240, 240), x0, y); y += 34
        self._text(self.font, f"Größe: {self.grid_w} x {self.grid_h}", (220, 220, 220), x0, y); y += 30

        # Aktuelles Tile
        self._text(self.font, "Aktuelles Tile:", (200, 200, 80), x0, y); y += 22
        # Sonderfälle: Tür mit Farbe, Schlüssel mit Farbe, weiblicher Villager
        sprite = None
        if self.selected_code == "d":
            if self.selected_door_color:
                sprite = self.sprites.get(f"locked_door_{self.selected_door_color}")
            else:
                sprite = self.sprites.get("d")
        elif self.selected_code == "s":
            kc = self.selected_key_color or "green"
            sprite = self.sprites.get(f"key_{kc}")
        elif self.selected_code == "v":
            if self.selected_villager_weiblich:
                sprite = self.sprites.get("v_female")
            else:
                sprite = self.sprites.get("v")
        if not sprite:
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

    def open_quest_dialog(self):
        """Öffnet einen kleinen Dialog, um am Mauszeiger einen Questgeber zu platzieren
        und die Quest-Parameter (modus, wuensche, anzahl) festzulegen.
        """
        # Mouse grid coord
        mx, my = pygame.mouse.get_pos()
        gx = (mx - MARGIN) // self.tilesize
        gy = (my - MARGIN) // self.tilesize
        if not (0 <= gx < self.grid_w and 0 <= gy < self.grid_h):
            return

        # Tkinter dialog
        root = tk.Tk(); root.title("Questgeber platzieren")
        frm = ttk.Frame(root, padding=10); frm.grid(row=0, column=0)

        ttk.Label(frm, text=f"Position: {gx},{gy}").grid(row=0, column=0, columnspan=2, sticky='w')
        ttk.Label(frm, text="Modus:").grid(row=1, column=0, sticky='w')
        modus_var = tk.StringVar(value='items')
        ttk.Radiobutton(frm, text='Items', variable=modus_var, value='items').grid(row=1, column=1, sticky='w')
        ttk.Radiobutton(frm, text='Rätsel', variable=modus_var, value='raetsel').grid(row=1, column=2, sticky='w')

        ttk.Label(frm, text="Wuensche (Komma-separiert, Namen):").grid(row=2, column=0, sticky='w')
        wishes_ent = ttk.Entry(frm, width=40)
        wishes_ent.grid(row=2, column=1, columnspan=2)

        ttk.Label(frm, text="Anzahl Items (optional):").grid(row=3, column=0, sticky='w')
        anz_ent = ttk.Entry(frm, width=10)
        anz_ent.grid(row=3, column=1, sticky='w')

        def ok():
            mode = modus_var.get()
            wishes = [w.strip() for w in wishes_ent.get().split(',') if w.strip()]
            anz = None
            try:
                anz = int(anz_ent.get())
            except Exception:
                anz = None
            key = f"{gx},{gy}"
            self.quests[key] = {"modus": mode}
            if wishes:
                self.quests[key]["wuensche"] = wishes
            if anz is not None:
                self.quests[key]["anzahl"] = anz
            # set tile to 'q'
            self.level[gy][gx] = 'q'
            root.destroy()

        def cancel():
            root.destroy()

        ttk.Button(frm, text="OK", command=ok).grid(row=4, column=1, pady=8)
        ttk.Button(frm, text="Abbrechen", command=cancel).grid(row=4, column=2, pady=8)
        root.mainloop()

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
    # Allgemeine Level-Einstellungen (F2)
    # -----------------------------
    def open_settings_dialog(self):
        """Öffnet einen Dialog zum Einstellen von Level-weiten Parametern:
        initial_gold, quest_max_kosten, quest_mode, quest_items_needed
        """
        root = tk.Tk(); root.title("Level-Einstellungen")
        frm = ttk.Frame(root, padding=10); frm.grid(row=0, column=0)

        ttk.Label(frm, text="Start-Gold:").grid(row=0, column=0, sticky='w')
        gold_var = tk.StringVar(value=str(self.level_settings.get('initial_gold', 0)))
        ttk.Entry(frm, textvariable=gold_var, width=12).grid(row=0, column=1, sticky='w')

        ttk.Label(frm, text="Quest-Modus:").grid(row=1, column=0, sticky='w')
        qm_var = tk.StringVar(value=str(self.level_settings.get('quest_mode', 'items')))
        ttk.Radiobutton(frm, text='items', variable=qm_var, value='items').grid(row=1, column=1, sticky='w')
        ttk.Radiobutton(frm, text='raetsel', variable=qm_var, value='raetsel').grid(row=1, column=2, sticky='w')

        ttk.Label(frm, text="Quest max Kosten:").grid(row=2, column=0, sticky='w')
        qmk_var = tk.StringVar(value=str(self.level_settings.get('quest_max_kosten', 0)))
        ttk.Entry(frm, textvariable=qmk_var, width=12).grid(row=2, column=1, sticky='w')

        ttk.Label(frm, text="Quest Items benötigt:").grid(row=3, column=0, sticky='w')
        qin_var = tk.StringVar(value=str(self.level_settings.get('quest_items_needed', 1)))
        ttk.Entry(frm, textvariable=qin_var, width=12).grid(row=3, column=1, sticky='w')

        # Schüler-Klassen Optionen
        ttk.Label(frm, text="Schüler-Klassen:", font=("Consolas", 10, "bold")).grid(row=10, column=0, sticky='w', pady=(8,0))
        use_student_var = tk.BooleanVar(value=bool(getattr(self, 'use_student_module', False)))
        subfolder_var = tk.BooleanVar(value=bool(getattr(self, 'student_classes_in_subfolder', False)))
        # Make the two options mutually exclusive: if one is checked the other is unchecked
        def on_use_changed():
            try:
                if use_student_var.get():
                    subfolder_var.set(False)
            except Exception:
                pass

        def on_subfolder_changed():
            try:
                if subfolder_var.get():
                    use_student_var.set(False)
            except Exception:
                pass

        # Ensure initial state is not contradictory
        try:
            if use_student_var.get() and subfolder_var.get():
                # prefer the explicit subfolder flag to be false in case both were set
                subfolder_var.set(False)
        except Exception:
            pass

        chk_use = ttk.Checkbutton(frm, text="Schülerklassen verwenden (schueler.py)", variable=use_student_var, command=on_use_changed)
        chk_use.grid(row=11, column=0, columnspan=2, sticky='w')
        chk_sub = ttk.Checkbutton(frm, text="Schülerklassen in Unterordner (klassen/)", variable=subfolder_var, command=on_subfolder_changed)
        chk_sub.grid(row=12, column=0, columnspan=2, sticky='w')

        def ok():
            try:
                self.level_settings['initial_gold'] = int(gold_var.get())
            except Exception:
                self.level_settings['initial_gold'] = 0
            self.level_settings['quest_mode'] = qm_var.get()
            try:
                self.level_settings['quest_max_kosten'] = int(qmk_var.get())
            except Exception:
                self.level_settings['quest_max_kosten'] = 0
            try:
                self.level_settings['quest_items_needed'] = int(qin_var.get())
            except Exception:
                self.level_settings['quest_items_needed'] = 1
            # Persist the student-class flags on the editor instance
            try:
                self.use_student_module = bool(use_student_var.get())
            except Exception:
                self.use_student_module = False
            try:
                self.student_classes_in_subfolder = bool(subfolder_var.get())
            except Exception:
                self.student_classes_in_subfolder = False
            root.destroy()

        def cancel():
            root.destroy()

        ttk.Button(frm, text='OK', command=ok).grid(row=4, column=1, pady=8)
        ttk.Button(frm, text='Abbrechen', command=cancel).grid(row=4, column=2, pady=8)
        root.mainloop()

    # -----------------------------
    # Victory conditions (F3)
    # -----------------------------
    def open_victory_dialog(self):
        """Dialog (F3) to configure multiple victory conditions.
        - Collect all hearts (boolean)
        - Move to coordinate (boolean + x,y)
        - Classes implemented (boolean)
        """
        # Prefill with existing values
        vic = self.level_settings.get('victory', {}) or {}
        collect_def = bool(vic.get('collect_hearts', True))
        move_def = vic.get('move_to') or {}
        move_enabled = bool(move_def.get('enabled', False)) if isinstance(move_def, dict) else False
        move_x = str(move_def.get('x', 0)) if isinstance(move_def, dict) else '0'
        move_y = str(move_def.get('y', 0)) if isinstance(move_def, dict) else '0'
        classes_def = bool(vic.get('classes_present', False))

        root = tk.Tk(); root.title("Siegbedingungen (F3)")
        frm = ttk.Frame(root, padding=10); frm.grid(row=0, column=0)

        ttk.Label(frm, text="Siegbedingungen:", font=("Consolas", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky='w')

        collect_var = tk.BooleanVar(value=collect_def)
        tk.Checkbutton(frm, text="Alle Herzen sammeln (Standard)", variable=collect_var).grid(row=1, column=0, columnspan=3, sticky='w', pady=(6,2))

        move_var = tk.BooleanVar(value=move_enabled)
        tk.Checkbutton(frm, text="Zum Zielfeld bewegen (x,y):", variable=move_var).grid(row=2, column=0, sticky='w')
        x_ent = ttk.Entry(frm, width=6)
        x_ent.insert(0, move_x)
        x_ent.grid(row=2, column=1, sticky='w')
        y_ent = ttk.Entry(frm, width=6)
        y_ent.insert(0, move_y)
        y_ent.grid(row=2, column=2, sticky='w')

        ttk.Label(frm, text="Tipp: Klicke das Level-Feld an und öffne F3, um Koordinaten vorzufüllen.").grid(row=3, column=0, columnspan=3, sticky='w', pady=(4,6))

        classes_var = tk.BooleanVar(value=classes_def)
        tk.Checkbutton(frm, text="Alle im Level verwendeten Klassen implementiert (Schülerklassen)", variable=classes_var).grid(row=4, column=0, columnspan=3, sticky='w', pady=(6,2))

        def ok():
            try:
                v = {}
                v['collect_hearts'] = bool(collect_var.get())
                if move_var.get():
                    try:
                        vx = int(x_ent.get())
                        vy = int(y_ent.get())
                        v['move_to'] = {'enabled': True, 'x': vx, 'y': vy}
                    except Exception:
                        v['move_to'] = {'enabled': False}
                else:
                    v['move_to'] = None
                v['classes_present'] = bool(classes_var.get())
                self.level_settings['victory'] = v
            except Exception:
                pass
            root.destroy()

        def cancel():
            root.destroy()

        ttk.Button(frm, text='OK', command=ok).grid(row=5, column=1, pady=8)
        ttk.Button(frm, text='Abbrechen', command=cancel).grid(row=5, column=2, pady=8)
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
            # settings may contain both per-type dicts (e.g. {"Held": {"public": true}})
            # and scalar keys (initial_gold, quest_mode...). Be defensive and only
            # extract privacy info from dict entries. Support both old 'privat' and
            # current 'public' keys.
            self.privacy_flags = {}
            try:
                for k, v in data["settings"].items():
                    if isinstance(v, dict):
                        if 'privat' in v:
                            self.privacy_flags[k] = bool(v.get('privat', False))
                        elif 'public' in v:
                            # privacy flag stored as public: True/False -> invert
                            self.privacy_flags[k] = not bool(v.get('public', True))
                        else:
                            # no privacy info in this dict
                            continue
            except Exception:
                # defensive fallback: empty dict
                self.privacy_flags = {}

            # Ensure expected keys exist
            for k in ["Held", "Knappe", "Monster", "Herz", "Tuer", "Code", "Villager"]:
                self.privacy_flags.setdefault(k, False)
        # Lade Orientierungen, falls vorhanden (Format: {"x,y": "up"})
        settings = data.get("settings", {})
        self.orientations = settings.get("orientations", {})
        # Lade gespeicherte Tür-/Schlüssel-Farben (falls vorhanden)
        self.colors = settings.get("colors", {}) or {}
        # Lade Villager-Geschlechter
        self.villagers = settings.get("villagers", {}) or {}
        # Lade Quest-Konfigurationen
        self.quests = settings.get("quests", {}) or {}
        # Lade zusätzliche Level-Einstellungen (z.B. initial_gold, quest_max_kosten,...)
        for k in ("initial_gold", "quest_max_kosten", "quest_mode", "quest_items_needed"):
            if k in settings:
                self.level_settings[k] = settings.get(k)

        # Load victory settings if present (backwards compatible: default to collect_hearts)
        try:
            vic = settings.get('victory')
            default_vic = {"collect_hearts": True, "move_to": None, "classes_present": False}
            # If level file contains an explicit victory dict, use it. Otherwise
            # overwrite any previous editor state with the default so that the
            # editor doesn't carry the last-loaded level's target into the new one.
            if isinstance(vic, dict):
                self.level_settings['victory'] = vic
            else:
                self.level_settings['victory'] = default_vic
        except Exception:
            self.level_settings['victory'] = {"collect_hearts": True, "move_to": None, "classes_present": False}

        # Lade Flags für Schülerklassen (falls vorhanden)
        try:
            self.use_student_module = bool(settings.get('use_student_module', False))
        except Exception:
            self.use_student_module = False
        try:
            self.student_classes_in_subfolder = bool(settings.get('student_classes_in_subfolder', False))
        except Exception:
            self.student_classes_in_subfolder = False

        # Ensure victory settings present (backwards compatibility)
        self.level_settings.setdefault('victory', {"collect_hearts": True, "move_to": None, "classes_present": False})

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
        # Farben für Türen/Schlüssel exportieren
        if self.colors:
            data["settings"].setdefault("colors", {})
            data["settings"]["colors"].update(self.colors)
        # Villager-Geschlechter exportieren
        if self.villagers:
            data["settings"].setdefault("villagers", {})
            data["settings"]["villagers"].update(self.villagers)
        # Quests exportieren
        if self.quests:
            data["settings"].setdefault("quests", {})
            data["settings"]["quests"].update(self.quests)
        # Zusätzliche Level-Einstellungen exportieren (falls gesetzt)
        if getattr(self, 'level_settings', None):
            for k, v in self.level_settings.items():
                # only export simple scalars
                try:
                    if v is None:
                        continue
                    data["settings"][k] = v
                except Exception:
                    continue
        # Export student-class flags so the framework can decide whether to load them
        try:
            data["settings"]["use_student_module"] = bool(getattr(self, 'use_student_module', False))
        except Exception:
            pass
        try:
            data["settings"]["student_classes_in_subfolder"] = bool(getattr(self, 'student_classes_in_subfolder', False))
        except Exception:
            pass
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
                    elif event.key == pygame.K_F2:
                        self.open_settings_dialog()
                    elif event.key == pygame.K_F3:
                        self.open_victory_dialog()
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
                    elif event.key == pygame.K_q:
                        # Quest konfigurieren / platzieren
                        self.open_quest_dialog()
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
        # Tür-Farbwahl (Taste '8' cycle) — inkl. Möglichkeit für 'normale' Tür (None)
        if key_str == "8":
            total = len(self.door_colors) + 1
            self.door_color_idx = (self.door_color_idx + 1) % total
            if self.door_color_idx == 0:
                self.selected_door_color = None
                print("[Info] Normale Tür ausgewählt (keine Farbe)")
            else:
                self.selected_door_color = self.door_colors[self.door_color_idx - 1]
                print(f"[Info] Türfarbe ausgewählt: {self.selected_door_color}")
            self.selected_code = TILES.get(key_str, ("d",))[0]
            return

        # Schlüssel-Farbwahl (Taste '0' cycle) -> inkl. 'keine Auswahl' -> wählt 's' als Tile
        if key_str == "0":
            total_k = len(self.key_colors) + 1
            self.key_color_idx = (self.key_color_idx + 1) % total_k
            if self.key_color_idx == 0:
                self.selected_key_color = None
                print("[Info] Schlüssel: keine Farbauswahl (Default green beim Spawn)")
            else:
                self.selected_key_color = self.key_colors[self.key_color_idx - 1]
                print(f"[Info] Schlüssel-Farbe ausgewählt: {self.selected_key_color}")
            self.selected_code = "s"
            return

        # Villager gender toggle (Taste '4')
        if key_str == "4":
            self.selected_villager_weiblich = not self.selected_villager_weiblich
            self.selected_code = "v"
            print(f"[Info] Villager weiblich={self.selected_villager_weiblich}")
            return

        # Taste '7' toggelt zwischen Code-Zettel ('c') und normaler Tür ('d')
        if key_str == "7":
            if self.selected_code == "c":
                self.selected_code = "d"
                self.selected_door_color = None
                print("[Info] Auswahl: Tür (normale Tür)")
            else:
                self.selected_code = "c"
                print("[Info] Auswahl: Code-Zettel ('c')")
            return

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
