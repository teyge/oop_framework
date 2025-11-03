# framework/spielfeld.py
import pygame
from .level import Level
from .utils import richtung_offset
from .tuer import Tuer
from .code import Code
from .tor import Tor
from .knappe import Knappe
from random import randint
import random

class Spielfeld:
    def __init__(self, levelfile, framework, feldgroesse=64, auto_erzeuge_objekte=True):
        self.framework = framework
        self.feldgroesse = feldgroesse
        self.level = Level(levelfile)
        self.settings = self.level.settings
        self.objekte = []
        self.held = None
        self.knappe = None
        #self.zufallscode = str(randint(1000,9999))
        self.zufallscode = self.random_zauberwort()
        self.orc_names = []
        if auto_erzeuge_objekte:
            self._spawn_aus_level()
            
    def random_zauberwort(self):
        zauberwoerter = [
            "Alohomora", "Ignis", "Fulgura", "Lumos", "Nox",
            "Aqua", "Ventus", "Terra", "Glacius", "Silencio",
            "Accio", "Protego", "Obliviate", "Impervius"
        ]

        # Wähle zufälligen Spruch
        spruch = random.choice(zauberwoerter) + " " + random.choice(zauberwoerter)
        return spruch 
        

    def _spawn_aus_level(self):
        from .held import Held
        from .herz import Herz
        from .monster import Monster
        from .tor import Tor
        for typ, x, y,sichtbar in self.level.iter_entity_spawns():
            if typ == "p":
                self.held = Held(self.framework, x, y, "down",weiblich=self.framework.weiblich)
                self.objekte.append(self.held)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, self.held.typ.lower(), self.held)
            elif typ == "h":
                obj = Herz(x,y)
                cfg = self.settings.get(obj.typ, {})
                self.objekte.append(obj)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, obj.typ.lower(), obj)
            elif typ == "x":
                n = self.generate_orc_name()
                while n in self.orc_names:
                    n = self.generate_orc_name()
                self.orc_names.append(n)
                m = Monster(x,y,name=n)
                m.framework = self.framework
                self.objekte.append(m)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, m.typ.lower(), m)
            elif typ == "c":
                from .code import Code
                code = Code(x, y,c=self.zufallscode)
                code.framework = self.framework
                self.objekte.append(code)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, code.typ.lower(), code)

            elif typ == "d":
                from .tuer import Tuer
                tuer = Tuer(x, y, code=self.zufallscode)  # z. B. Standardcode
                tuer.framework = self.framework
                self.objekte.append(tuer)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "tuer", tuer)
            elif typ == "g":
                tor = Tor(x, y, offen=False)
                tor.framework = self.framework
                self.objekte.append(tor)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "tor", tor)
            elif typ == "k":
                self.knappe = Knappe(self.framework, x, y, "down",name=self.generate_knappe_name())
                self.objekte.append(self.knappe)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "knappe", self.knappe)
        """
        if not self.held:
            from .held import Held
            print("[Warnung] Kein Held im Level – Dummy bei (0,0).")
            self.held = Held(self.framework, 0, 0, "down")
            self.objekte.append(self.held)
        """
            
        print(f"Level geladen: {len(self.objekte)} Objekte gespawnt.")
        for o in self.objekte:
            #print(f" - {o.name} an ({o.x}, {o.y})")
            cfg = self.settings.get(o.typ, {})

            if cfg.get("public") is False:
                o.set_privatmodus(True)
            if o.typ == "Knappe":
                self.held.add_knappe(o)
            


    # --- Zeichnen ---
    def zeichne(self, screen):
        # Sortierte Zeichnung: zuerst Boden / Hindernisse, dann Items, dann Lebewesen
        zeichenreihenfolge = ["Berg", "Baum", "Busch", "Spruch", "Herz", "Tür", "Tor","Monster", "Held","Knappe"]
        self.level.zeichne(screen, self.feldgroesse)
        for typ in zeichenreihenfolge:
            #for o in [obj for obj in self.objekte if not obj.tot and obj.typ == typ]:
            for o in [obj for obj in self.objekte if obj.typ == typ]:
                o.zeichne(screen, self.feldgroesse)


        """
        for o in self.objekte:
            if not o.tot:
                o.zeichne(screen, self.feldgroesse)
                """
    
    def _privatisiere(self, obj):
        print("Privatisiere",obj.typ)
        class Proxy:
            def __init__(self, original):
                super().__setattr__("_original", original)

            def __getattribute__(self, name):
                if name == "_original":
                    return super().__getattribute__(name)
                # Zugriff blockieren, wenn "privates" Attribut
                if name.startswith("_"):
                    raise AttributeError(f"Privates Attribut '{name}' – Zugriff nicht erlaubt")
                original = super().__getattribute__("_original")
                return getattr(original, name)

            def __setattr__(self, name, value):
                if name == "_original":
                    super().__setattr__(name, value)
                elif name.startswith("_"):
                    raise AttributeError(f"Privates Attribut '{name}' – Zugriff nicht erlaubt")
                else:
                    setattr(self._original, name, value)

            def __dir__(self):
                # damit dir() oder Autovervollständigung nur "öffentliche" Namen zeigt
                return [n for n in dir(self._original) if not n.startswith("_")]

            def __repr__(self):
                return f"<Proxy({repr(self._original)})>"

        return Proxy(obj)


    
    def generate_orc_name(self):
        prefixes = ["Gor", "Thr", "Mok", "Grim", "Rag", "Dur", "Zug", "Kra", "Lok", "Ur", "Gar", "Vor"]
        middles = ["'", "a", "o", "u", "ra", "ok", "ug", "ar", "th", "ruk", ""]
        suffixes = ["lok", "grim", "thar", "gash", "rok", "dush", "mok", "zug", "rak", "grom", "nash"]

        name = random.choice(prefixes) + random.choice(middles) + random.choice(suffixes)
        return name.capitalize()
    
    def generate_knappe_name(self):
        names = ["Page Skywalker","Jon Snowflake","Sir Lancelame","Rick Rollins",
                 "Ben of the Rings","Tony Stork","Bucky Stables","Frodolin Beutelfuss","Jamie Lameister","Gerold of Trivia",
                 "Arthur Denton","Samwise the Slacker","Obi-Wan Knappobi","Barry Slow","Knight Fury","Grogulette",
                 "Sir Bean of Gondor","Thorin Eichensohn","Legoless","Knappernick",
                 "Knapptain Iglo","Ritterschorsch","Helm Mut","Sigi von Schwertlingen","Klaus der Kleingehauene","Egon Eisenfaust","Ben Knied","Rainer Zufallsson","Dietmar Degenhart","Uwe von Ungefähr","Hartmut Helmrich","Bodo Beinhart","Kai der Kurze","Knapphart Stahl","Tobi Taschenmesser","Fridolin Fehlschlag","Gernot Gnadenlos","Ralf Rüstungslos","Gustav Gürtelschwert","Kuno Knickbein"]
        return random.choice(names).capitalize()

    # --- Kollisionen / Logik ---
    def innerhalb(self, x, y):
        return 0 <= x < self.level.breite and 0 <= y < self.level.hoehe

    def terrain_art_an(self, x, y):
        if not self.innerhalb(x, y): return None
        return {"w":"Weg", "m":"Berg", "b":"Busch", "t":"Baum"}.get(self.level.tiles[y][x])

    def kann_betreten(self, obj, x, y):
        """Prüft, ob ein Feld betreten werden darf."""
        # Grenzen prüfen
        if y < 0 or y >= len(self.level.tiles) or x < 0 or x >= len(self.level.tiles[y]):
            return False

        # Feste Hindernisse im Level
        tile = self.level.tiles[y][x]
        if tile in ("b", "t", "m"):  # Berge, Bäume, Monster etc.
            return False

        # Alle Objekte am Ziel prüfen
        for o in self.objekte:
            if o.tot:
                return True
            if (o.x, o.y) == (x, y) and o != self:
                if o.name == "Tür":
                    # Tür ist nur passierbar, wenn offen
                    if hasattr(o, "offen") and not o.offen:
                        return False
                elif o.typ in ("Monster", "Code", "Herz", "Knappe", "Held"):
                    # Monster sind unpassierbar (außer besiegt)
                    if o.typ in ("Monster","Knappe"):
                        return False
                    # Code oder Herz: darf man betreten (man steht drauf)
                    continue
                elif o.typ == "Tor":
                    if o.ist_passierbar():
                        return False
        return True


    def ist_frontal_zu_monster(self, held, monster):
        # Monster schaut in monster.richtung – frontal wenn Held aus dieser Richtung hineinläuft
        mdx, mdy = richtung_offset(monster.richtung)
        hdx, hdy = held.x - monster.x, held.y - monster.y
        return (hdx, hdy) == (mdx, mdy)

    # --- Objekt-Suchen ---
    def finde_herz(self, x, y):
        for o in self.objekte:
            if o.name == "Herz" and (o.x, o.y) == (x, y):
                return o
        return None
    
    def finde_tor_vor(self, held):
        dx, dy = richtung_offset(held.richtung)
        ziel_x, ziel_y = held.x + dx, held.y + dy
        for obj in self.objekte:
            if isinstance(obj, Tor) and obj.x == ziel_x and obj.y == ziel_y:
                return obj
        return None


    def finde_monster(self, x, y):
        for o in self.objekte:
            if o.typ == "Monster" and (o.x, o.y) == (x, y):
                return o
        return None

    def objekt_an(self, x, y):
        for o in self.objekte:
            if (o.x, o.y) == (x, y):
                return o
        return None
    
    def finde_tuer(self, x, y):
        for o in self.objekte:
            if o.name == "Tür" and (o.x, o.y) == (x, y):
                return o
        return None

    def finde_code(self, x, y):
        for o in self.objekte:
            if o.name == "Spruch" and (o.x, o.y) == (x, y):
                return o
        return None


    def objekt_art_an(self, x, y):
        o = self.objekt_an(x, y)
        return o.name if o else None

    def entferne_objekt(self, obj):
        if obj in self.objekte:
            self.objekte.remove(obj)

    def gibt_noch_herzen(self):
        return any(o.name == "Herz" for o in self.objekte)
    
    def anzahl_herzen(self):
        c = 0
        for o in self.objekte:
            if o.name == "Herz":
                c+=1
        return c
