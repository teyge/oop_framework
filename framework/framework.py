# framework/framework.py
import pygame
import tkinter as tk
from tkinter import filedialog
from .spielfeld import Spielfeld

class Framework:
    def __init__(self, levelnummer=1, feldgroesse=64, auto_erzeuge_objekte=True, w = False, splash=False):
        print("(c) 2025 Johannes Harz\nFachkonferenz Informatik\nCusanus Gymnasium St. Wendel")
        pygame.init()
        self.feldgroesse = feldgroesse
        self._tasten = {}
        self._running = True
        self._sieg = False
        self._hinweis = None        # zeigt Text bei ungültiger Aktion
        self._aktion_blockiert = False  # verhindert Queue-Updates aus Schülercode
        self._aus_tastatur = False
        self.weiblich = w
        self.info_scroll = 0  # Scroll-Offset für Infotext




                # Dummy-Fenster (für convert_alpha) + später richtige Größe
        # --- Fensterposition dynamisch setzen (rechte Hälfte, oberes Drittel) ---
        import os
        import tkinter as tk

        # Bildschirmgröße über Tkinter ermitteln
        root = tk.Tk()
        root.withdraw()
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        root.destroy()

        # Fenstergröße (Dummy für Splash + Initialisierung)
        win_w, win_h = 800, 600

        # Position: rechte Hälfte, oberes Drittel
        x = screen_w - win_w - 50              # 50 px Abstand vom rechten Rand
        y = int(screen_h / 3 - win_h / 3)      # oberes Drittel zentriert
        if y < 0:
            y = 0

        os.environ['SDL_VIDEO_WINDOW_POS'] = f"{x},{y}"

        # Erstes Dummy-Fenster für Splash etc.
        self.screen = pygame.display.set_mode((win_w, win_h))

        
        # --- Splash-Screen (1 Sekunde, mit Aspect-Ratio) ---
        if splash:
            try:
                splash = pygame.image.load("sprites/splash.png").convert_alpha()
                img_w, img_h = splash.get_size()
                win_w, win_h = self.screen.get_size()

                # Maßstab berechnen (maximale Breite oder Höhe ausnutzen)
                scale = min(win_w / img_w, win_h / img_h)
                new_size = (int(img_w * scale), int(img_h * scale))
                splash_scaled = pygame.transform.smoothscale(splash, new_size)

                # Zentriert zeichnen
                x = (win_w - new_size[0]) // 2
                y = (win_h - new_size[1]) // 2
                self.screen.fill((0, 0, 0))
                self.screen.blit(splash_scaled, (x, y))
                pygame.display.flip()
                pygame.time.wait(1000)
            except Exception as e:
                print("[Splash] konnte nicht angezeigt werden:", e)
            # --- Ende Splash-Screen ---


        
        self.levelfile = f"level/level{levelnummer}.json"
        self.spielfeld = Spielfeld(self.levelfile, self, feldgroesse, auto_erzeuge_objekte)
        breite = self.spielfeld.level.breite * feldgroesse + 280
        hoehe  = self.spielfeld.level.hoehe  * feldgroesse
        self.screen = pygame.display.set_mode((breite, hoehe))
        pygame.display.set_caption("OOP-Framework")

        self.font = pygame.font.SysFont("consolas", 18)
        self.big  = pygame.font.SysFont("consolas", 32, bold=True)

        # Standard-Tasten
        self.taste_registrieren(pygame.K_ESCAPE, self.beenden)
        self.taste_registrieren(pygame.K_o, self.level_oeffnen)

        # sofort einmal zeichnen
        self._render_frame()
        pygame.time.wait(500)

    # --- Tastatur ---
    def taste_registrieren(self, key, fn): self._tasten[key] = fn
    
    def objekt_hinzufuegen(self, obj):
        """Fügt ein Objekt dem Spielfeld hinzu und verknüpft es mit dem Framework."""
        obj.framework = self
        self.spielfeld.objekte.append(obj)
        self._render_frame()
        if obj.typ == "Knappe":
            self.spielfeld.knappe = obj
        
    def gib_objekt_an(self, x, y):
        """Gibt das Objekt an Position (x, y) zurück oder None."""
        return self.spielfeld.objekt_an(x, y)



    # --- Render-Hilfen ---
    def _zeichne_info(self):
        y = 8 - self.info_scroll  # Scroll-Offset berücksichtigen

        panel_x = self.spielfeld.level.breite * self.feldgroesse + 8
        #y = 8
        # Ensure the Held is always shown first with basic attributes
        try:
            sp = getattr(self, 'spielfeld', None)
        except Exception:
            sp = None

        if sp:
            held = getattr(sp, 'held', None)
            if held:
                try:
                    # use requested default name if not set
                    name = getattr(held, 'name', None) or 'namenloser held'
                    hdr = self.font.render(f"Name={name}", True, (255,255,255))
                    self.screen.blit(hdr, (panel_x, y)); y += 20
                except Exception:
                    pass
                try:
                    # one value per line (like Monster inspector)
                    x = getattr(held, 'x', 0)
                    yv = getattr(held, 'y', 0)
                    richt = getattr(held, 'richtung', '?')
                    # map directions for display only
                    dm = {'up': 'N', 'down': 'S', 'left': 'W', 'right': 'O', 'N': 'N', 'S': 'S', 'W': 'W', 'O': 'O'}
                    rdisp = dm.get(str(richt), str(richt))
                    x_txt = self.font.render(f"x={x}", True, (200,200,200))
                    self.screen.blit(x_txt, (panel_x, y)); y += 20
                    y_txt = self.font.render(f"y={yv}", True, (200,200,200))
                    self.screen.blit(y_txt, (panel_x, y)); y += 20
                    r_txt = self.font.render(f"richtung={rdisp}", True, (200,200,200))
                    self.screen.blit(r_txt, (panel_x, y)); y += 20
                except Exception:
                    pass
                y += 4

        for o in self.spielfeld.objekte:
            # Defensive inspection: attribute_als_text may raise for student-provided
            # objects (missing attributes or unexpected behavior). We want to ensure
            # the Held is always shown (if present) and that errors are surfaced
            # with a helpful message listing missing attributes.
            try:
                try:
                    items = o.attribute_als_text()
                except Exception as ex_attr:
                    # Determine object identity
                    try:
                        typ_name = getattr(o, 'typ', None) or o.__class__.__name__
                    except Exception:
                        typ_name = o.__class__.__name__

                    # Ensure header is drawn for the object
                    try:
                        hdr_txt = f"{getattr(o, 'name', typ_name)} ({typ_name})"
                        hdr = self.font.render(hdr_txt, True, (255,255,255))
                        self.screen.blit(hdr, (panel_x, y)); y += 20
                    except Exception:
                        pass

                    # Determine a set of likely-required attributes to report
                    required = ['x', 'y', 'richtung', 'typ', 'name']
                    missing = []
                    for a in required:
                        try:
                            if not hasattr(o, a):
                                missing.append(a)
                        except Exception:
                            missing.append(a)

                    # If no missing attributes were detected, include the exception text
                    msg = None
                    if missing:
                        msg = f"Fehler in der Schülerklasse {typ_name}: Fehlende Attribute: {', '.join(missing)}"
                    else:
                        msg = f"Fehler beim Lesen der Schülerklasse {typ_name}: {ex_attr}"

                    try:
                        err = self.font.render(msg, True, (255, 100, 100))
                        self.screen.blit(err, (panel_x, y)); y += 20
                    except Exception:
                        pass
                    # Space after each object
                    y += 10
                    # continue to next object
                    continue

                # Normal path: render each attribute line. Convert 'richtung' to N/O/W/S for display.
                for k, v in items.items():
                    try:
                        val = v
                        if isinstance(k, str) and 'richt' in k.lower():
                            dm = {'up': 'N', 'down': 'S', 'left': 'W', 'right': 'O', 'N': 'N', 'S': 'S', 'W': 'W', 'O': 'O'}
                            val = dm.get(str(v), str(v))
                        txt = f"{k}: {val}"
                        while self.font.size(txt)[0] > (self.screen.get_width() - panel_x - 20):
                            txt = txt[:-1]
                        txt = self.font.render(f"{k}: {val}", True, (240,240,240))
                        self.screen.blit(txt, (panel_x, y)); y += 20
                    except Exception:
                        continue
                y += 10
            except Exception:
                # Very defensive: if anything else goes wrong, show a minimal line
                try:
                    typ_name = getattr(o, 'typ', None) or o.__class__.__name__
                    msg = f"Fehler beim Anzeigen von {typ_name}"
                    err = self.font.render(msg, True, (255, 100, 100))
                    self.screen.blit(err, (panel_x, y)); y += 20
                except Exception:
                    pass
                y += 10
        """        
        if self._sieg:
            msg = self.font.render("Alle Herzen gesammelt!", True, (255, 230, 80))
            self.screen.blit(msg, (panel_x, y+10))"""

        # ... in framework/framework.py, in _zeichne_info() ...
        if self._hinweis:
            panel_x = self.spielfeld.level.breite * self.feldgroesse + 8
            max_w   = self.screen.get_width() - panel_x - 20
            line_h  = self.font.get_linesize()

            # einfache Wortumbruch-Logik
            words = self._hinweis.split()
            lines, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if self.font.size(test)[0] <= max_w:
                    cur = test
                else:
                    if cur: lines.append(cur)
                    # falls einzelnes Wort länger als max_w ist -> harte Teilung
                    while self.font.size(w)[0] > max_w and len(w) > 1:
                        # finde maximale Teil-Länge
                        lo, hi = 1, len(w)
                        while lo < hi:
                            mid = (lo + hi) // 2 + 1
                            if self.font.size(w[:mid])[0] <= max_w: lo = mid
                            else: hi = mid - 1
                        lines.append(w[:lo])
                        w = w[lo:]
                    cur = w
            if cur: lines.append(cur)

            # oben im Panel zeichnen (immer sichtbar)
            y0 = y
            for i, line in enumerate(lines):
                msg = self.font.render(line, True, (255, 100, 100))
                self.screen.blit(msg, (panel_x, y0 + i * line_h))
        panel_w = self.screen.get_width() - panel_x - 8
        anzeige_h = self.screen.get_height() - 16
        pygame.draw.rect(self.screen, (80,80,80), (panel_x + panel_w - 10, 8, 6, anzeige_h))







    def _render_frame(self):
        self.screen.fill((0, 0, 0))

        # Nur lebende Objekte updaten
        for o in self.spielfeld.objekte:
            if not getattr(o, "tot", False):
                try:
                    o.update()
                except Exception as e:
                    pass
                    #print("[Update-Fehler]", e)

        # Jetzt alle zeichnen (auch tote!)
        self.spielfeld.zeichne(self.screen)
        self._zeichne_info()
        self._zeichne_sieg_overlay()

        pygame.display.flip()


    # --- Public API ---
    def sieg(self): self._sieg = True
    def beenden(self): self._running = False

    def level_oeffnen(self):
        """
        root = tk.Tk(); root.withdraw()
        pfad = filedialog.askopenfilename(filetypes=[("JSON Level","*.json")], title="Level öffnen")
        root.destroy()
        if pfad:
            self.spielfeld = Spielfeld(pfad, self, self.feldgroesse, True)
            breite = self.spielfeld.level.breite * self.feldgroesse + 280
            hoehe  = self.spielfeld.level.hoehe  * self.feldgroesse
            self.screen = pygame.display.set_mode((breite, hoehe))
            self._sieg = False
            self._render_frame()
            self._hinweis = None
            self._aktion_blockiert = False
        """
        
        self.spielfeld = Spielfeld(self.levelfile, self, self.feldgroesse, True)
        breite = self.spielfeld.level.breite * self.feldgroesse + 280
        hoehe  = self.spielfeld.level.hoehe  * self.feldgroesse
        self.screen = pygame.display.set_mode((breite, hoehe))
        self._sieg = False
        self._render_frame()
        self._hinweis = None
        self._aktion_blockiert = False

            
    def stoppe_programm(self, meldung="Ungültige Aktion"):
        """Bricht die Schüleraktions-Queue ab, aber Framework läuft weiter."""
        self._hinweis = meldung
        self._aktion_blockiert = True
        print(f"[Framework] {meldung}")  # optional für Debug
        
    def _zeichne_sieg_overlay(self):
        """Dunkelt den Spielfeldbereich ab und zeigt 'Level geschafft'."""
        if not self._sieg or self._aktion_blockiert:
            return  # keine Anzeige, wenn Sieg noch nicht aktiv oder blockiert wurde

        # Spielfeld-Bereich berechnen (ohne rechtes Panel)
        spielfeld_breite = self.spielfeld.level.breite * self.feldgroesse
        spielfeld_hoehe  = self.spielfeld.level.hoehe  * self.feldgroesse

        overlay = pygame.Surface((spielfeld_breite, spielfeld_hoehe), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))  # halbtransparentes Schwarz
        self.screen.blit(overlay, (0, 0))

        # Text mittig anzeigen
        text = self.big.render("Level geschafft!", True, (255, 230, 80))
        text_rect = text.get_rect(center=(spielfeld_breite // 2, spielfeld_hoehe // 2))
        self.screen.blit(text, text_rect)



    def starten(self):
        import os, sys, time
        clock = pygame.time.Clock()

        # Test-Modus: sofort nach Sieg/Timeout den Prozess beenden (damit ein externes Runner-Skript weiter macht)
        TEST_MODE = os.getenv("OOP_TEST", "") == "1"
        TEST_TIMEOUT_MS = int(os.getenv("OOP_TEST_TIMEOUT_MS", "8000"))

        start_time = time.time()

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    # --- neu: Enter (Return) nimmt alle Gegenstände auf der aktuellen Heldposition auf ---
                    try:
                        if event.key == pygame.K_RETURN:
                            try:
                                sp = getattr(self, "spielfeld", None)
                                held = getattr(sp, "held", None) if sp else None
                                # Prefer a more specific single-item pickup if available
                                if held:
                                    if hasattr(held, "nehm_auf_einfach"):
                                        try:
                                            held.nehm_auf_einfach()
                                        except Exception:
                                            pass
                                    elif hasattr(held, "nehm_auf_alle"):
                                        try:
                                            held.nehm_auf_alle()
                                        except Exception:
                                            pass
                                    elif hasattr(held, "nehme_auf_alle"):
                                        try:
                                            held.nehme_auf_alle()
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                            # continue to allow other handlers to run too
                    except Exception:
                        pass

                    # bestehende Tasten-Registrierung aufrufen (wie bisher)
                    fn = self._tasten.get(event.key)
                    if fn:
                        try:
                            self._aus_tastatur = True
                            fn()
                        except Exception as e:
                            print("Fehler in Tastenaktion:", e)
                        finally:
                            self._aus_tastatur = False
                elif event.type == pygame.MOUSEWHEEL:
                    self.info_scroll += event.y * 20
                    if self.info_scroll < 0:
                        self.info_scroll = 0
            # Sieg erkennen (kombinierte Bedingungen)
            try:
                if not self._aktion_blockiert and getattr(self, 'spielfeld', None) and self.spielfeld.check_victory():
                    self.sieg()
            except Exception:
                # fallback to legacy hearts-only check
                if not self._aktion_blockiert and not self.spielfeld.gibt_noch_herzen():
                    self.sieg()

            # Wenn im Testmodus: beende Prozess bei Sieg oder bei Timeout
            if TEST_MODE:
                # Erfolg: sofort exit(0)
                if self._sieg and not self._aktion_blockiert:
                    print("[TEST] Level erfolgreich beendet.")
                    pygame.quit()
                    sys.exit(0)

                # Timeout
                elapsed_ms = int((time.time() - start_time) * 1000)
                if elapsed_ms > TEST_TIMEOUT_MS:
                    print(f"[TEST] Timeout ({TEST_TIMEOUT_MS}ms): Noch Herzen vorhanden oder blockiert.")
                    pygame.quit()
                    sys.exit(2)

            # --- Render: Objekt-Inspektor (rechte Seite) erweitern um Inventaranzeige ---
            try:
                # existierender inspector-render-code befindet sich irgendwo in _render_frame oder hier;
                # füge das Inventar-Rendering direkt an der Stelle ein, an der held/knappe/monster angezeigt werden.
                # defensive search for inspector surface / font
                screen = getattr(self, "_screen", None) or pygame.display.get_surface()
                if screen:
                    font = pygame.font.SysFont(None, 20)
                    x0 = screen.get_width() - 200  # rechter Bereich
                    y0 = 20
                    line_h = 20

                    sp = getattr(self, "spielfeld", None)
                    if sp:
                        # Reihenfolge: Held, Knappe, dann Monster(s)
                        entities = []
                        if getattr(sp, "held", None):
                            entities.append(sp.held)
                        if getattr(sp, "knappe", None):
                            entities.append(sp.knappe)
                        # append monsters
                        for o in sp.objekte:
                            try:
                                typ = getattr(o, "typ", "") or getattr(o, "name", "")
                                if typ and "monster" in str(typ).lower():
                                    entities.append(o)
                            except Exception:
                                continue

                        # Zeichne Basisinfos + Inventar
                        for ent in entities:
                            try:
                                # header: Name (Typ)
                                name = getattr(ent, "name", getattr(ent, "typ", ent.__class__.__name__))
                                hdr = font.render(f"{name} ({getattr(ent,'typ', '')})", True, (255,255,255))
                                screen.blit(hdr, (x0, y0))
                                y0 += line_h
                                # position + richtung (one per line, direction displayed as N/O/W/S)
                                try:
                                    ex = getattr(ent, 'x', 0)
                                    ey = getattr(ent, 'y', 0)
                                    er = getattr(ent, 'richtung', '?')
                                    dm = {'up': 'N', 'down': 'S', 'left': 'W', 'right': 'O', 'N': 'N', 'S': 'S', 'W': 'W', 'O': 'O'}
                                    rdisp = dm.get(str(er), str(er))
                                    sx = font.render(f"x={ex}", True, (200,200,200))
                                    screen.blit(sx, (x0, y0)); y0 += line_h
                                    sy = font.render(f"y={ey}", True, (200,200,200))
                                    screen.blit(sy, (x0, y0)); y0 += line_h
                                    sr = font.render(f"richtung={rdisp}", True, (200,200,200))
                                    screen.blit(sr, (x0, y0)); y0 += line_h
                                except Exception:
                                    try:
                                        xyt = font.render(f"x={getattr(ent,'x',0)} y={getattr(ent,'y',0)} dir={getattr(ent,'richtung','?')}", True, (200,200,200))
                                        screen.blit(xyt, (x0, y0)); y0 += line_h
                                    except Exception:
                                        y0 += line_h

                                # Spells / gesammelte Sprueche: falls vorhanden als Text (bestehendes Verhalten)
                                spells = getattr(ent, "spruch", None) or getattr(ent, "zauberspruch", None) or getattr(ent, "_spruch", None)
                                if spells:
                                    srf = font.render(f"Spruch: {spells}", True, (180,220,180))
                                    screen.blit(srf, (x0, y0))
                                    y0 += line_h

                                # Inventar: falls vorhanden, zeichne sehr kleine Icons für Schlüssel (einmal pro Farbe)
                                inv = getattr(ent, "inventar", None)
                                if inv is not None:
                                    # collect unique key colors and generic item names
                                    keys_seen = {}
                                    item_x = x0
                                    item_y = y0
                                    icon_size = 16  # very small
                                    spacing = icon_size + 4
                                    # draw small label
                                    lbl = font.render("Inventar:", True, (220,220,160))
                                    screen.blit(lbl, (item_x, item_y))
                                    item_y += line_h
                                    # draw icons in a row
                                    ix = 0
                                    for it in inv:
                                        try:
                                            # if it's a key item (has attribute 'farbe' or class name Schluessel)
                                            color = getattr(it, "farbe", None) or getattr(it, "color", None)
                                            if color:
                                                if color in keys_seen:
                                                    continue
                                                keys_seen[color] = True
                                                # try to load sprite path or construct key sprite filename
                                                surf = None
                                                try:
                                                    # if item has 'bild' surface use it
                                                    if hasattr(it, "bild") and getattr(it, "bild", None) is not None:
                                                        surf = it.bild
                                                    else:
                                                        # try to locate sprite on disk
                                                        import os, pygame as _pg
                                                        cand = os.path.join("sprites", f"key_{color}.png")
                                                        if os.path.exists(cand):
                                                            surf = _pg.image.load(cand).convert_alpha()
                                                except Exception:
                                                    surf = None
                                                # if we have a surface, scale and blit
                                                if surf:
                                                    try:
                                                        surf_small = pygame.transform.smoothscale(surf, (icon_size, icon_size))
                                                        screen.blit(surf_small, (x0 + ix * spacing, item_y))
                                                    except Exception:
                                                        # fallback draw small rect
                                                        pygame.draw.rect(screen, (200,200,0), (x0 + ix * spacing, item_y, icon_size, icon_size))
                                                else:
                                                    pygame.draw.rect(screen, (200,200,0), (x0 + ix * spacing, item_y, icon_size, icon_size))
                                                ix += 1
                                            else:
                                                # non-key item: draw short name
                                                nm = getattr(it, "name", str(it))
                                                s = font.render(nm, True, (200,200,200))
                                                screen.blit(s, (x0 + ix * spacing, item_y))
                                                ix += 1
                                            # keep row compact
                                            if ix >= 10:
                                                # move to next row
                                                ix = 0
                                                item_y += icon_size + 6
                                        except Exception:
                                            continue
                                    # advance y0 after inventory rendering
                                    y0 = item_y + icon_size + 6
                            except Exception:
                                continue
            except Exception:
                pass

            self._render_frame()
            clock.tick(60)

