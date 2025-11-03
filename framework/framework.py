# framework/framework.py
import pygame, tkinter as tk
from tkinter import filedialog
from .spielfeld import Spielfeld

class Framework:
    def __init__(self, levelnummer=1, feldgroesse=64, auto_erzeuge_objekte=True, w = False, splash=False):
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
        for o in self.spielfeld.objekte:
            for k, v in o.attribute_als_text().items():
                txt = f"{k}: {v}"
                
                while self.font.size(txt)[0] > (self.screen.get_width() - panel_x - 20):
                    txt = txt[:-1]
                txt = self.font.render(f"{k}: {v}", True, (240,240,240))
                self.screen.blit(txt, (panel_x, y)); y += 20
                
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
        clock = pygame.time.Clock()
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    fn = self._tasten.get(event.key)
                    if fn:
                        try:
                            self._aus_tastatur = True
                            fn()  # Tastatur bleibt aktiv, auch wenn blockiert
                            #self._hinweis = None
                        except Exception as e:
                            print("Fehler in Tastenaktion:", e)
                        finally:
                            self._aus_tastatur = False     # <-- Rücksetzen
                            
                elif event.type == pygame.MOUSEWHEEL:
                    self.info_scroll += event.y * 20  # Schrittweite anpassen (z. B. 20 px)
                    if self.info_scroll < 0:
                        self.info_scroll = 0



            # Schüler-Aktionen blockieren: nichts „Automatisches“ mehr ausführen.
            # (Bei deiner Baseline gibt es keine Autoupdates – das ist okay.
            #  Wichtig ist nur: Rendering und Tastatur laufen weiter.)
            # 🧩 Nach Beendigung der Schülerbefehle prüfen, ob Level gewonnen wurde
            if not self._aktion_blockiert and not self.spielfeld.gibt_noch_herzen():
                self.sieg()

            self._render_frame()
            clock.tick(60)

        pygame.quit()

