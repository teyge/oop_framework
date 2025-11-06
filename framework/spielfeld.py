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
import importlib
import traceback
import os
import ast
import types

class Spielfeld:
    def __init__(self, levelfile, framework, feldgroesse=64, auto_erzeuge_objekte=True):
        self.framework = framework
        # keep the original level file path for heuristics (e.g. level number)
        self.levelfile = levelfile
        # ensure framework has a reference back to this spielfeld (main program normally sets this)
        try:
            setattr(self.framework, 'spielfeld', self)
        except Exception:
            pass
        self.feldgroesse = feldgroesse
        self.level = Level(levelfile)
        self.settings = self.level.settings
        # Compute the set of canonical classes required by this level BEFORE
        # any spawning runs (iter_entity_spawns mutates level.tiles). This
        # preserves the original spawn information for victory checks.
        try:
            self._required_spawn_classes = self._compute_required_classes()
        except Exception:
            self._required_spawn_classes = set()
        # Victory settings (may contain dict with keys: collect_hearts, move_to, classes_present)
        try:
            self.victory_settings = self.settings.get('victory', {}) if isinstance(self.settings, dict) else {}
        except Exception:
            self.victory_settings = {}
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
        from .code import Code
        from .tuer import Tuer
        from .gegenstand import Gegenstand
        from .schluessel import Schluessel

        # Orientierungen evtl. in self.settings["orientations"] als {"x,y":"up"}
        orients = self.settings.get("orientations", {}) if isinstance(self.settings, dict) else {}
        # Tür-/Schlüssel-Farben in self.settings["colors"] (z.B. {"3,4":"golden"})
        colors = self.settings.get("colors", {}) if isinstance(self.settings, dict) else {}
        # Villager gender in self.settings["villagers"] as {"x,y": "female"/"male"}
        villagers = self.settings.get("villagers", {}) if isinstance(self.settings, dict) else {}
        # Quests in settings: self.settings["quests"]["x,y"] -> {"modus":"items"/"raetsel", "wuensche":[...], "anzahl":int}
        quests = self.settings.get("quests", {}) if isinstance(self.settings, dict) else {}

        # Level-wide quest/gold settings
        try:
            initial_gold = int(self.settings.get('initial_gold', 0) or 0)
        except Exception:
            initial_gold = 0
        try:
            quest_max_kosten = int(self.settings.get('quest_max_kosten', 0) or 0)
        except Exception:
            quest_max_kosten = 0
        quest_mode = self.settings.get('quest_mode', None)
        try:
            quest_items_needed = int(self.settings.get('quest_items_needed', 0) or 0)
        except Exception:
            quest_items_needed = 0

        # Detect whether the level requests student classes; we'll treat each
        # entity spawn independently: if a student class for that entity is
        # missing, we skip spawning that entity. The hero (Held) will be drawn
        # if its student class exists.
        try:
            student_mode_enabled = bool(self.settings.get('import_pfad') or self.settings.get('use_student_module') or self.settings.get('student_classes_in_subfolder'))
        except Exception:
            student_mode_enabled = False

        # If quest_mode == 'items', prepare desired item names and prices
        ITEM_NAMES = ["Ring", "Apple", "Sword", "Shield", "Potion", "Scroll", "Bread", "Gem", "Torch", "Amulet"]
        desired_items = []
        desired_prices = {}
        if isinstance(quest_mode, str) and quest_mode.lower() == 'items':
            needed = max(1, min(len(ITEM_NAMES), quest_items_needed or 1))
            # If quest_max_kosten is set but too small for the requested number of items,
            # reduce the number of needed items so minimal total cost (10 per item) fits.
            min_price = 10
            if quest_max_kosten and quest_max_kosten <= (min_price * needed):
                needed = max(1, quest_max_kosten // min_price)
            # choose unique item names
            try:
                desired_items = random.sample(ITEM_NAMES, needed)
            except Exception:
                # fallback
                desired_items = ITEM_NAMES[:needed]

            # assign prices such that sum <= quest_max_kosten (if quest_max_kosten > 0)
            # minimal price per item = 10
            min_price = 10
            max_price = 80
            if quest_max_kosten and quest_max_kosten > min_price * needed:
                remaining_budget = quest_max_kosten - (min_price * needed)
                # distribute remaining_budget among items up to (max_price - min_price)
                adds = [0] * needed
                for i in range(needed):
                    if remaining_budget <= 0:
                        break
                    add = min(remaining_budget, random.randint(0, max_price - min_price))
                    adds[i] = add
                    remaining_budget -= add
                for i, name in enumerate(desired_items):
                    desired_prices[name] = min_price + adds[i]
            else:
                # fallback small prices
                for name in desired_items:
                    desired_prices[name] = min_price

        # collect villagers created so we can inject desired items afterwards
        spawned_villagers = []

        for typ, x, y, sichtbar in self.level.iter_entity_spawns():
            t = typ.lower() if isinstance(typ, str) else typ
            # Lese Richtung (default "down")
            richt = orients.get(f"{x},{y}", "down")

            if t == "p":
                # try instantiating student-provided Held (student classes receive the Level),
                # wrap with MetaHeld so framework features (rendering, controls) remain available.
                FrameworkHeld = Held
                cls = self._get_entity_class("Held", FrameworkHeld)
                # Determine whether the level requested student classes
                student_mode_enabled = bool(self.settings.get('import_pfad') or self.settings.get('use_student_module') or self.settings.get('student_classes_in_subfolder'))
                if cls is None and student_mode_enabled:
                    # Student mode requested but no student Held class found -> do not spawn a hero
                    print("Hinweis: Level verlangt Schülerklassen, aber keine Held-Klasse gefunden; Held wird nicht gespawnt.")
                    self.held = None
                    # do not append to objekte
                    continue
                if cls is not FrameworkHeld and cls is not None:
                    student_inst = None
                    try:
                        # prefer signature (level, x, y, richt, weiblich=...)
                        student_inst = cls(self.level, x, y, richt, weiblich=getattr(self.framework, "weiblich", False))
                    except TypeError:
                        try:
                            student_inst = cls(self.level, x, y, richt)
                        except Exception:
                            student_inst = None
                    except Exception:
                        student_inst = None

                    if student_inst is not None:
                        try:
                            from .held import MetaHeld
                            self.held = MetaHeld(self.framework, student_inst, x, y, richt, weiblich=getattr(self.framework, "weiblich", False))
                        except Exception:
                            # fallback to internal Held
                            try:
                                self.held = FrameworkHeld(self.framework, x, y, richt, weiblich=getattr(self.framework, "weiblich", False))
                            except Exception:
                                raise
                    else:
                        # couldn't instantiate student class -> fallback
                        try:
                            self.held = FrameworkHeld(self.framework, x, y, richt, weiblich=getattr(self.framework, "weiblich", False))
                        except Exception:
                            raise
                else:
                    try:
                        self.held = FrameworkHeld(self.framework, x, y, richt, weiblich=getattr(self.framework, "weiblich", False))
                    except Exception:
                        raise

                self.objekte.append(self.held)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, self.held.typ.lower(), self.held)

            elif t == "h":
                cls = self._get_entity_class("Herz", Herz)
                if student_mode_enabled and cls is None:
                    # level explicitly requests student classes but none provided for Herz
                    continue
                try:
                    obj = cls(x, y)
                except Exception:
                    obj = Herz(x, y)
                obj.framework = self.framework
                cfg = self.settings.get(obj.typ, {})
                self.objekte.append(obj)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, obj.typ.lower(), obj)

            elif t == "x":
                n = self.generate_orc_name()
                while n in self.orc_names:
                    n = self.generate_orc_name()
                self.orc_names.append(n)
                cls = self._get_entity_class("Monster", Monster)
                if student_mode_enabled and cls is None:
                    continue
                try:
                    m = cls(x, y, name=n)
                except Exception:
                    m = Monster(x, y, name=n)
                m.framework = self.framework
                # setze Richtung falls unterstützt
                try:
                    m.richtung = richt
                except Exception:
                    pass
                self.objekte.append(m)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, m.typ.lower(), m)

            elif t == "c":
                cls = self._get_entity_class("Code", Code)
                if student_mode_enabled and cls is None:
                    continue
                try:
                    code = cls(x, y, c=self.zufallscode)
                except Exception:
                    code = Code(x, y, c=self.zufallscode)
                code.framework = self.framework
                self.objekte.append(code)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "zettel", code)

            elif t == "d":
                # prüfe, ob für diese Position eine Farbe konfiguriert ist
                color = colors.get(f"{x},{y}")
                # Wenn color gesetzt, erstelle farbige, schlüssel-verschlossene Tür
                cls = self._get_entity_class("Tuer", Tuer)
                if student_mode_enabled and cls is None:
                    continue
                try:
                    if color:
                        tuer = cls(x, y, code=None, color=color)
                    else:
                        tuer = cls(x, y, code=self.zufallscode)
                except Exception:
                    if color:
                        tuer = Tuer(x, y, code=None, color=color)
                    else:
                        tuer = Tuer(x, y, code=self.zufallscode)
                tuer.framework = self.framework
                self.objekte.append(tuer)
                # setze Richtung falls das Tür-Objekt diese Eigenschaft nutzt
                try:
                    tuer.richtung = richt
                except Exception:
                    pass
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "tuer", tuer)

            elif t == "s":
                # Schlüssel-Spawn: Farbe aus settings oder default 'green'
                color = colors.get(f"{x},{y}", "green")
                cls = self._get_entity_class("Schluessel", Schluessel)
                if student_mode_enabled and cls is None:
                    continue
                try:
                    sch = cls(x, y, color=color)
                except Exception:
                    sch = Schluessel(x, y, color=color)
                sch.framework = self.framework
                self.objekte.append(sch)
                if sichtbar:
                    import framework.grundlage as grundlage
                    # früher wurde 'zettel'/'tuer' etc. genutzt; hier verwenden wir 'schluessel' singular
                    setattr(grundlage, "schluessel", sch)

            elif t == "v":
                # Villager (Dorfbewohner) – gender kann in settings konfiguriert sein
                key = f"{x},{y}"
                weiblich_flag = False
                val = villagers.get(key)
                if isinstance(val, str) and val.lower() in ("female", "weiblich", "w"):
                    weiblich_flag = True
                try:
                    from .villager import Villager
                    cls = self._get_entity_class("Villager", Villager)
                    if student_mode_enabled and cls is None:
                        continue
                    try:
                        vill = cls(self.framework, x, y, richtung=richt, weiblich=weiblich_flag)
                    except Exception:
                        vill = Villager(self.framework, x, y, richtung=richt, weiblich=weiblich_flag)
                    vill.framework = self.framework
                    self.objekte.append(vill)
                    # If quest mode==items, populate villager with random offers (2-5 items, 10-80 Gold)
                    if isinstance(quest_mode, str) and quest_mode.lower() == 'items':
                        offer_count = random.randint(2, 5)
                        for _ in range(offer_count):
                            item_name = random.choice(ITEM_NAMES)
                            price = random.randint(10, 80)
                            try:
                                item = Gegenstand(item_name, price)
                                vill.biete_item_an(item, price)
                            except Exception:
                                pass
                    spawned_villagers.append(vill)
                    if sichtbar:
                        import framework.grundlage as grundlage
                        setattr(grundlage, "villager", vill)
                except Exception:
                    pass

            elif t == "q":
                # Questgeber spawn
                key = f"{x},{y}"
                qcfg = quests.get(key, {})
                modus = qcfg.get("modus", "items")
                wuensche = qcfg.get("wuensche", [])
                anzahl = qcfg.get("anzahl", None)
                # weiblich flag may be in villagers settings
                weiblich_flag = False
                val = villagers.get(key)
                if isinstance(val, str) and val.lower() in ("female", "weiblich", "w"):
                    weiblich_flag = True
                try:
                    from .villager import Questgeber
                    # If global quest_mode is 'raetsel' and no explicit puzzle provided in qcfg,
                    # generate a simple arithmetic puzzle here and attach it to the Questgeber.
                    initial_raetsel = None
                    if isinstance(quest_mode, str) and quest_mode.lower() == 'raetsel':
                        # generate a question 'a op b=' where a,b in 1..9 and op in +,-,*,/
                        ops = ['+', '-', '*', '/']
                        attempt = 0
                        while attempt < 50:
                            a = random.randint(1, 9)
                            b = random.randint(1, 9)
                            op = random.choice(ops)
                            if op == '/':
                                if b == 0:
                                    attempt += 1
                                    continue
                                if a % b != 0:
                                    attempt += 1
                                    continue
                                sol = a // b
                            elif op == '+':
                                sol = a + b
                            elif op == '-':
                                sol = a - b
                            else:
                                sol = a * b
                            initial_raetsel = (f"{a}{op}{b}=", sol)
                            break
                    cls = self._get_entity_class("Questgeber", Questgeber)
                    if student_mode_enabled and cls is None:
                        continue
                    try:
                        quest = cls(self.framework, x, y, richtung=richt, modus=modus, wuensche=wuensche, anzahl_items=anzahl, weiblich=weiblich_flag)
                    except Exception:
                        quest = Questgeber(self.framework, x, y, richtung=richt, modus=modus, wuensche=wuensche, anzahl_items=anzahl, weiblich=weiblich_flag)
                    # attach generated puzzle if present
                    if initial_raetsel is not None:
                        try:
                            quest._vorgegebene_frage = initial_raetsel[0]
                            quest._letzte_raetsel = int(initial_raetsel[1])
                        except Exception:
                            pass
                    quest.framework = self.framework
                    # set explicit type for drawing/lookup
                    try:
                        quest.typ = "Questgeber"
                    except Exception:
                        pass
                    self.objekte.append(quest)
                    if sichtbar:
                        import framework.grundlage as grundlage
                        setattr(grundlage, "questgeber", quest)
                except Exception:
                    pass

            elif t == "g":
                cls = self._get_entity_class("Tor", Tor)
                if student_mode_enabled and cls is None:
                    continue
                try:
                    tor = cls(x, y, offen=False)
                except Exception:
                    tor = Tor(x, y, offen=False)
                tor.framework = self.framework
                self.objekte.append(tor)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "tor", tor)

            elif t == "k":
                cls = self._get_entity_class("Knappe", Knappe)
                if student_mode_enabled and cls is None:
                    continue
                try:
                    self.knappe = cls(self.framework, x, y, richt, name=self.generate_knappe_name())
                except Exception:
                    self.knappe = Knappe(self.framework, x, y, richt, name=self.generate_knappe_name())
                self.objekte.append(self.knappe)
                if sichtbar:
                    import framework.grundlage as grundlage
                    setattr(grundlage, "knappe", self.knappe)
                # If a hero was already spawned, attach this Knappe to the hero immediately.
                try:
                    if getattr(self, 'held', None) is not None:
                        # Ensure the held has a knappen list
                        if not hasattr(self.held, 'knappen'):
                            try:
                                setattr(self.held, 'knappen', [])
                            except Exception:
                                pass
                        try:
                            self.held.add_knappe(self.knappe)
                        except Exception:
                            pass
                except Exception:
                    pass

        print(f"Level geladen: {len(self.objekte)} Objekte gespawnt.")
        # After spawning, set initial hero gold and, if in item-quest mode, distribute desired items to villagers
        try:
            if hasattr(self, 'held') and self.held is not None:
                self.held.gold = initial_gold
        except Exception:
            pass

        # --- Apply privacy settings per-object immediately after spawn ---
        try:
            # Provide a best-effort pass that enforces per-type 'public'/'privat' settings
            for o in list(self.objekte):
                try:
                    typ_name = getattr(o, 'typ', None)
                except Exception:
                    try:
                        typ_name = o.__class__.__name__
                    except Exception:
                        typ_name = None
                cfg = {}
                try:
                    if isinstance(self.settings, dict) and typ_name:
                        cfg = self.settings.get(typ_name, {}) or {}
                except Exception:
                    cfg = {}

                is_private = False
                try:
                    if 'public' in cfg:
                        is_private = (cfg.get('public') is False)
                    elif 'privat' in cfg:
                        is_private = bool(cfg.get('privat'))
                except Exception:
                    is_private = False

                if not is_private:
                    continue

                # If object exposes set_privatmodus, call it; otherwise replace with proxy
                try:
                    if hasattr(o, 'set_privatmodus'):
                        try:
                            o.set_privatmodus(True)
                        except Exception:
                            pass
                    else:
                        proxy = self._privatisiere(o)
                        try:
                            idx = self.objekte.index(o)
                            self.objekte[idx] = proxy
                        except ValueError:
                            pass
                        try:
                            if getattr(self, 'held', None) is o:
                                self.held = proxy
                        except Exception:
                            pass
                        try:
                            if getattr(self, 'knappe', None) is o:
                                self.knappe = proxy
                        except Exception:
                            pass
                        try:
                            import framework.grundlage as grundlage
                            for name in ('held','knappe','zettel','tuer','schluessel','villager','tor'):
                                try:
                                    if getattr(grundlage, name, None) is o:
                                        setattr(grundlage, name, proxy)
                                except Exception:
                                    pass
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass

    # --- Student-class override helpers ---
    def _get_entity_class(self, canonical_name: str, framework_cls):
        """Try to load a student-provided class according to level settings.

        Behavior:
        - If no student flags are present (nor explicit 'import_pfad'), return the framework class.
        - If 'import_pfad' is provided (string), try to import that module and return the mapped class
          if present. If module/class not found, return None to indicate "no student class".
        - If 'use_student_module' is True, use the editor flags to attempt to find student classes:
            * if 'student_classes_in_subfolder' is False: prefer repo-root 'schueler' module first,
              then fall back to 'klassen.<canonical_lower>' if present.
            * if 'student_classes_in_subfolder' is True: prefer 'klassen.<canonical_lower>' first.
          If a student class is found, return it. If not found, return None.

        Returning None signals the caller that student classes were enabled but none found; callers
        can decide whether to fall back to framework classes (we will for most entities) or to
        omit the entity (special-case: Held when student mode is on should not fall back).
        """
        try:
            settings = self.settings or {}

            # If an explicit import path is provided, prefer it (backwards-compatible)
            import_pfad = None
            try:
                import_pfad = settings.get('import_pfad')
            except Exception:
                import_pfad = None

            use_student_flag = bool(settings.get('use_student_module', False))
            subfolder_flag = bool(settings.get('student_classes_in_subfolder', False))

            # If nothing requests student classes (neither explicit import path nor
            # the student flags), return the framework class.
            if not import_pfad and not (use_student_flag or subfolder_flag):
                return framework_cls

            # Helper: import module with caching per module name
            if not hasattr(self, '_student_module_cache'):
                self._student_module_cache = {}

            def try_import(candidates, required_class_name=None):
                """Try to load candidate modules, but only return a module that
                actually contains the required_class_name (if provided). This
                prevents returning an earlier module (e.g. `schueler`) that was
                loaded but does not define the requested class while a later
                candidate (e.g. `klassen.held`) does.
                """
                for cand in candidates:
                    if cand in self._student_module_cache:
                        mod = self._student_module_cache.get(cand)
                        # if we have a cached module but a required class name is
                        # given, ensure the module actually defines it
                        if mod and required_class_name:
                            if getattr(mod, required_class_name, None) is None:
                                # cached module doesn't have the class -> continue
                                continue
                        return mod
                    # If candidate corresponds to a file in the repo, prefer a
                    # safe loader that executes only imports, class and function
                    # definitions to avoid running top-level student scripts.
                    try:
                        # helper to safely load only definitions from a file
                        def _safe_load_from_path(path, mod_name=None):
                            try:
                                src = open(path, 'r', encoding='utf-8').read()
                                tree = ast.parse(src, path)
                                new_nodes = []
                                for node in tree.body:
                                    # keep function and class defs, and simple assignments
                                    # but avoid executing imports that pull in framework internals
                                    # (e.g. `from framework.grundlage import *`) which would
                                    # expose framework classes into the student module namespace.
                                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                                        new_nodes.append(node)
                                    elif isinstance(node, ast.Import):
                                        # keep only imports that don't import from the 'framework' package
                                        keep = True
                                        for alias in node.names:
                                            if alias.name.startswith('framework'):
                                                keep = False
                                                break
                                        if keep:
                                            new_nodes.append(node)
                                    elif isinstance(node, ast.ImportFrom):
                                        # skip wildcard imports and any imports from our framework package
                                        modname = getattr(node, 'module', '') or ''
                                        if modname.startswith('framework'):
                                            continue
                                        # skip `from ... import *` which may pollute namespace
                                        if any(alias.name == '*' for alias in node.names):
                                            continue
                                        new_nodes.append(node)
                                    elif isinstance(node, ast.Assign):
                                        # avoid assignments that call functions at top-level
                                        val = getattr(node, 'value', None)
                                        if not isinstance(val, ast.Call):
                                            new_nodes.append(node)
                                    elif isinstance(node, ast.AnnAssign):
                                        val = getattr(node, 'value', None)
                                        if val is None or not isinstance(val, ast.Call):
                                            new_nodes.append(node)

                                new_mod = ast.Module(body=new_nodes, type_ignores=[])
                                ast.fix_missing_locations(new_mod)
                                module = types.ModuleType(mod_name or os.path.splitext(os.path.basename(path))[0])
                                module.__file__ = path
                                # execute only the trimmed AST
                                code_obj = compile(new_mod, path, 'exec')
                                exec(code_obj, module.__dict__)
                                return module
                            except Exception:
                                return None

                        # If cand refers to a dotted package (like klassen.x), try normal import first
                        if '.' in cand:
                            try:
                                mod = importlib.import_module(cand)
                                self._student_module_cache[cand] = mod
                                if required_class_name is None or getattr(mod, required_class_name, None) is not None:
                                    return mod
                                # module loaded but doesn't define the required class -> try next candidate
                                continue
                            except Exception:
                                self._student_module_cache[cand] = None
                                continue

                        # Resolve plain module name to possible file paths
                        repo_root = os.path.dirname(os.path.dirname(__file__))
                        fp_root = os.path.join(repo_root, f"{cand}.py")
                        fp_klassen = os.path.join(repo_root, 'klassen', f"{cand}.py")

                        if os.path.exists(fp_root):
                            mod = _safe_load_from_path(fp_root, mod_name=cand)
                            self._student_module_cache[cand] = mod
                            if mod and (required_class_name is None or getattr(mod, required_class_name, None) is not None):
                                return mod
                            else:
                                continue
                        if os.path.exists(fp_klassen):
                            mod = _safe_load_from_path(fp_klassen, mod_name=f"klassen.{cand}")
                            self._student_module_cache[cand] = mod
                            if mod and (required_class_name is None or getattr(mod, required_class_name, None) is not None):
                                return mod
                            else:
                                continue

                        # fallback: try normal import
                        try:
                            mod = importlib.import_module(cand)
                            self._student_module_cache[cand] = mod
                            if required_class_name is None or getattr(mod, required_class_name, None) is not None:
                                return mod
                            continue
                        except Exception:
                            self._student_module_cache[cand] = None
                            continue
                    except Exception:
                        self._student_module_cache[cand] = None
                        continue
                return None

            repo_root = os.path.dirname(os.path.dirname(__file__))

            # Build candidate modules depending on provided settings
            candidates = []
            if import_pfad:
                # import_pfad may be a dotted module path or a simple module name
                if isinstance(import_pfad, str) and '.' in import_pfad:
                    candidates.append(import_pfad)
                else:
                    # check repo-root file
                    rp = os.path.join(repo_root, f"{import_pfad}.py")
                    if os.path.exists(rp):
                        candidates.append(import_pfad)
                    kp = os.path.join(repo_root, 'klassen', f"{import_pfad}.py")
                    if os.path.exists(kp):
                        candidates.append(f"klassen.{import_pfad}")
                    # fallback names
                    candidates.append(import_pfad)
                    candidates.append(f"klassen.{import_pfad}")
            else:
                # use_student_flag is True
                cname = canonical_name.lower()
                spath = os.path.join(repo_root, 'schueler.py')
                kpath = os.path.join(repo_root, 'klassen', f"{cname}.py")

                # If the editor/lavel indicates student classes are in the subfolder,
                # prefer `klassen/<cname>.py`. If that file exists, try it only; if it
                # doesn't exist but `schueler.py` is present, try `schueler` instead.
                # Symmetrically, if the subfolder flag is False and `schueler.py`
                # exists, try `schueler` only and do NOT silently fall back to
                # `klassen/<cname>.py`. This enforces the level/editor preference and
                # avoids surprising fallbacks when the student intentionally provided
                # a root `schueler.py` without the requested class.
                if subfolder_flag:
                    if os.path.exists(kpath):
                        candidates.append(f"klassen.{cname}")
                    elif os.path.exists(spath):
                        candidates.append('schueler')
                    else:
                        # neither file exists: try both names (import fallback)
                        candidates.extend([f"klassen.{cname}", 'schueler'])
                else:
                    if os.path.exists(spath):
                        candidates.append('schueler')
                    elif os.path.exists(kpath):
                        candidates.append(f"klassen.{cname}")
                    else:
                        candidates.extend(['schueler', f"klassen.{cname}"])

            # Ask try_import to return the first module that defines the
            # requested student class (if present). If none of the candidates
            # define the class, try_import will return None.
            mod = try_import(candidates, required_class_name=canonical_name)
            if not mod:
                # No student module found
                return None

            # Determine class name (allow mapping)
            class_map = settings.get('student_class_map', {}) or {}
            student_cls_name = class_map.get(canonical_name, canonical_name)
            cls = getattr(mod, student_cls_name, None)
            if cls is None:
                return None
            return cls
        except Exception:
            return None

    def _student_has_class(self, canonical_name: str) -> bool:
        """Check (by filesystem/AST) whether a student-provided class with the
        given canonical name exists either in `schueler.py` or in `klassen/<name>.py`.
        This avoids importing/running student top-level code and provides a
        reliable presence test for tile-drawing logic.
        """
        try:
            repo_root = os.path.dirname(os.path.dirname(__file__))
            cname = canonical_name
            # 1) explicit import_pfad may point to a module name
            import_pfad = None
            try:
                import_pfad = (self.settings or {}).get('import_pfad')
            except Exception:
                import_pfad = None

            def _file_has_class(path, cls_name):
                try:
                    if not os.path.exists(path):
                        return False
                    src = open(path, 'r', encoding='utf-8').read()
                    tree = ast.parse(src, path)
                    # helper: check whether the class __init__ sets required attributes
                    def _class_has_required_attrs(class_node, required):
                        found = set()
                        for item in class_node.body:
                            # look for assignments like self.x = ...
                            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                                for stmt in ast.walk(item):
                                    # self.x = ...
                                    if isinstance(stmt, ast.Assign):
                                        for t in stmt.targets:
                                            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == 'self':
                                                found.add(t.attr)
                                    # setattr(self, 'x', ...)
                                    if isinstance(stmt, ast.Call) and isinstance(stmt.func, ast.Name) and stmt.func.id == 'setattr':
                                        args = stmt.args
                                        if len(args) >= 2:
                                            if isinstance(args[0], ast.Name) and args[0].id == 'self':
                                                # second arg may be a constant/string
                                                a1 = args[1]
                                                if isinstance(a1, ast.Constant) and isinstance(a1.value, str):
                                                    found.add(a1.value)
                                                elif isinstance(a1, ast.Str):
                                                    found.add(a1.s)
                        return set(required).issubset(found)

                    for node in tree.body:
                        if isinstance(node, ast.ClassDef) and node.name == cls_name:
                            # For Held classes require that __init__ assigns a minimal set
                            if cls_name == 'Held':
                                required = ['level', 'x', 'y', 'richtung', 'weiblich', 'typ']
                                try:
                                    if _class_has_required_attrs(node, required):
                                        return True
                                    else:
                                        return False
                                except Exception:
                                    return False
                            return True
                    return False
                except Exception:
                    return False

            # If import_pfad points to a specific file/module, check it first
            if import_pfad:
                # dotted module
                if isinstance(import_pfad, str) and '.' in import_pfad:
                    # try to resolve file via importlib
                    try:
                        spec = importlib.util.find_spec(import_pfad)
                        if spec and spec.origin:
                            return _file_has_class(spec.origin, cname)
                    except Exception:
                        pass
                else:
                    # check repo-root file and klassen/<import_pfad>.py
                    rp = os.path.join(repo_root, f"{import_pfad}.py")
                    if _file_has_class(rp, cname):
                        return True
                    kp = os.path.join(repo_root, 'klassen', f"{import_pfad}.py")
                    if _file_has_class(kp, cname):
                        return True

            # Align presence-check with the editor/level preference flags:
            # If student_classes_in_subfolder is requested, prefer/check
            # klassen/<name>.py first and only fall back to schueler.py if the
            # file does not exist. If the subfolder flag is False and
            # schueler.py exists, check only schueler.py and do not treat a
            # class found in klassen/* as satisfying the requirement.
            lower = canonical_name.lower()
            kp = os.path.join(repo_root, 'klassen', f"{lower}.py")
            sp = os.path.join(repo_root, 'schueler.py')

            subfolder_flag = bool((self.settings or {}).get('student_classes_in_subfolder', False))

            if subfolder_flag:
                # prefer klassen; if it exists, require it to have the class
                if os.path.exists(kp):
                    return _file_has_class(kp, canonical_name)
                # klassen file doesn't exist; if schueler exists, check it
                if os.path.exists(sp):
                    return _file_has_class(sp, canonical_name)
                # neither file exists -> false
                return False

            else:
                # prefer schueler; if schueler.py exists, require it to have the class
                if os.path.exists(sp):
                    return _file_has_class(sp, canonical_name)
                # schueler not present; if klassen file exists, check it
                if os.path.exists(kp):
                    return _file_has_class(kp, canonical_name)
                return False

        except Exception:
            return False

    def _compute_required_classes(self):
        """Return set of canonical class names required by the level based on
        the original tile data. This reads `self.level.tiles` without
        mutating it (we only examine, not yield/alter), so callers can use
        the result after spawning has occurred.
        """
        try:
            mapping = { 'p': 'Held', 'h': 'Herz', 'x': 'Monster', 'c': 'Code', 'd': 'Tuer', 's': 'Schluessel', 'v': 'Villager', 'k': 'Knappe', 'g': 'Tor', 'q': 'Questgeber' }
            needed = set()
            for y, zeile in enumerate(self.level.tiles):
                for x, code in enumerate(zeile):
                    if not isinstance(code, str):
                        continue
                    key = code.lower()
                    cn = mapping.get(key)
                    if cn:
                        needed.add(cn)
            return needed
        except Exception:
            return set()

        # Ensure desired items are available among villagers (inject if missing)
        if desired_items and spawned_villagers:
            for name in desired_items:
                # if no villager offers this yet, inject into a random villager
                offered = False
                for v in spawned_villagers:
                    # search v.preisliste for item names
                    try:
                        for it in v.inventar:
                            if getattr(it, 'name', None) == name:
                                offered = True
                                break
                        if offered:
                            break
                    except Exception:
                        continue
                if not offered:
                    # choose a random villager and add the desired item with decided price
                    target = random.choice(spawned_villagers)
                    price = desired_prices.get(name, random.randint(10, 80))
                    try:
                        target.biete_item_an(Gegenstand(name, price), price)
                    except Exception:
                        pass
        # Ensure we have a reference to the spawned Held (some code-paths may set it earlier,
        # but in case it wasn't set due to ordering, try to find it among spawned objects).
        if getattr(self, 'held', None) is None:
            for obj in self.objekte:
                try:
                    if getattr(obj, 'typ', None) == 'Held':
                        self.held = obj
                        break
                except Exception:
                    continue

        for o in self.objekte:
            # Determine object type name defensively (student objects may raise on attribute access)
            try:
                typ_name = getattr(o, 'typ', None)
            except Exception:
                try:
                    typ_name = o.__class__.__name__
                except Exception:
                    typ_name = None

            # Safely read settings for this type
            cfg = {}
            try:
                if isinstance(self.settings, dict) and typ_name:
                    cfg = self.settings.get(typ_name, {}) or {}
            except Exception:
                cfg = {}

            # Only call set_privatmodus if the flag is explicitly False (legacy keys handled above).
            # If the object does not implement set_privatmodus, fall back to creating a Proxy wrapper
            # that blocks critical attributes. This enforces privacy regardless of the object's API.
            try:
                # Consider both old ('privat') and new ('public') setting names.
                is_private = False
                try:
                    if 'public' in cfg:
                        is_private = (cfg.get('public') is False)
                    elif 'privat' in cfg:
                        is_private = bool(cfg.get('privat'))
                    else:
                        is_private = False
                except Exception:
                    is_private = False
                if is_private:
                    try:
                        if hasattr(o, 'set_privatmodus'):
                            try:
                                o.set_privatmodus(True)
                            except Exception:
                                pass
                        else:
                            # replace object in the list with a proxy wrapper
                            proxy = self._privatisiere(o)
                            try:
                                idx = self.objekte.index(o)
                                self.objekte[idx] = proxy
                            except ValueError:
                                pass
                            # update references to held/knappe if necessary
                            try:
                                if getattr(self, 'held', None) is o:
                                    self.held = proxy
                            except Exception:
                                pass
                            try:
                                if getattr(self, 'knappe', None) is o:
                                    self.knappe = proxy
                            except Exception:
                                pass
                            # also try to update names in framework.grundlage if present
                            try:
                                import framework.grundlage as grundlage
                                for name in ('held','knappe','zettel','tuer','schluessel','villager','tor'):
                                    try:
                                        if getattr(grundlage, name, None) is o:
                                            setattr(grundlage, name, proxy)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass

            # Attach Knappe to hero if possible. Use defensive attribute access to avoid triggering
            # student-provided __getattribute__ implementations unexpectedly.
            try:
                is_knappe = False
                try:
                    is_knappe = (typ_name == "Knappe")
                except Exception:
                    is_knappe = False

                if is_knappe:
                    if getattr(self, 'held', None) is None:
                        # no hero to attach to; leave for the post-spawn scan or hero-to-knappe attach
                        continue
                    # ensure held has knappen list
                    try:
                        if not hasattr(self.held, 'knappen'):
                            try:
                                setattr(self.held, 'knappen', [])
                            except Exception:
                                pass
                        try:
                            self.held.add_knappe(o)
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
            


    # --- Zeichnen ---
    def zeichne(self, screen):
        # If rendering was explicitly disabled (student classes requested but missing),
        # show a small overlay and skip normal drawing.
        try:
            if getattr(self, '_render_disabled', False):
                try:
                    screen.fill((0, 0, 0))
                except Exception:
                    pass
                if getattr(self, 'framework', None) and getattr(self.framework, 'font', None):
                    try:
                        msg = "Level deaktiviert: Schülerklassen fehlen"
                        txt = self.framework.font.render(msg, True, (255, 80, 80))
                        screen.blit(txt, (8, 8))
                    except Exception:
                        pass
                return
        except Exception:
            pass
        # Sortierte Zeichnung: zuerst Boden / Hindernisse, dann Items, dann Lebewesen
        # Use canonical type names (matching Objekt.typ) so objects are drawn.
        zeichenreihenfolge = ["Berg", "Baum", "Busch", "Spruch", "Herz", "Tuer", "Tor", "Schluessel",
                              "Monster", "Held", "Knappe", "Dorfbewohner", "Dorfbewohnerin"]

        # Determine whether student mode requests are active and whether a student
        # Hindernis class exists. If the level requests student classes but the
        # Hindernis class is missing, don't draw obstacle tiles (m,b,t).
        try:
            student_mode_enabled = bool(self.settings.get('import_pfad') or self.settings.get('use_student_module') or self.settings.get('student_classes_in_subfolder'))
        except Exception:
            student_mode_enabled = False
        hide_obstacles = False
        try:
            if student_mode_enabled:
                # Use AST-based presence check which handles both schueler.py and klassen/*.py
                if not self._student_has_class('Hindernis'):
                    hide_obstacles = True
        except Exception:
            hide_obstacles = False

        # Draw tiles with optional obstacle hiding
        try:
            # Draw grass and optionally obstacle overlays
            for y, zeile in enumerate(self.level.tiles):
                for x, code in enumerate(zeile):
                    # Always draw grass base
                    gras = self.level.texturen.get('w')
                    if gras:
                        img = pygame.transform.scale(gras, (self.feldgroesse, self.feldgroesse))
                        screen.blit(img, (x * self.feldgroesse, y * self.feldgroesse))
                    # Draw obstacle textures unless hidden
                    if code in ('m','b','t','g'):
                        if hide_obstacles and code in ('m','b','t'):
                            continue
                        tex = self.level.texturen.get(code)
                        if tex:
                            img = pygame.transform.scale(tex, (self.feldgroesse, self.feldgroesse))
                            screen.blit(img, (x * self.feldgroesse, y * self.feldgroesse))
        except Exception:
            # fallback to level's drawing if something goes wrong
            try:
                self.level.zeichne(screen, self.feldgroesse)
            except Exception:
                pass
        for typ in zeichenreihenfolge:
            #for o in [obj for obj in self.objekte if not obj.tot and obj.typ == typ]:
            for o in [obj for obj in self.objekte if obj.typ == typ]:
                o.zeichne(screen, self.feldgroesse)

        # Draw move-to victory target if configured
        try:
            vic = (self.settings or {}).get('victory', {}) or {}
            mv = vic.get('move_to') if isinstance(vic, dict) else None
            if mv and isinstance(mv, dict) and mv.get('enabled'):
                tx = int(mv.get('x', -999))
                ty = int(mv.get('y', -999))
                if 0 <= tx < self.level.breite and 0 <= ty < self.level.hoehe:
                    rect = pygame.Rect(tx * self.feldgroesse, ty * self.feldgroesse, self.feldgroesse, self.feldgroesse)
                    try:
                        highlight = pygame.Surface((self.feldgroesse, self.feldgroesse), pygame.SRCALPHA)
                        highlight.fill((255, 0, 0, 48))
                        screen.blit(highlight, rect.topleft)
                        pygame.draw.rect(screen, (255, 0, 0), rect, max(2, self.feldgroesse // 16))
                    except Exception:
                        # best-effort only
                        pygame.draw.rect(screen, (255, 0, 0), rect, 4)
        except Exception:
            pass


        """
        for o in self.objekte:
            if not o.tot:
                o.zeichne(screen, self.feldgroesse)
                """
    
    def _privatisiere(self, obj):
    # perform privatization without noisy debug prints
        blocked_attrs = {"x", "y", "r", "richtung"}
        class Proxy:
            def __init__(self, original):
                super().__setattr__("_original", original)

            def __getattribute__(self, name):
                if name == "_original":
                    return super().__getattribute__(name)
                original = super().__getattribute__("_original")
                # If attribute is private by naming convention, block
                if name.startswith("_"):
                    raise AttributeError(f"Privates Attribut '{name}' – Zugriff nicht erlaubt")
                # Block specific movement/critical attributes
                try:
                    typ = getattr(original, 'typ', None)
                except Exception:
                    typ = None
                if name in blocked_attrs:
                    raise AttributeError(f"Attribut '{name}' ist privat – Zugriff nicht erlaubt")
                if typ == 'Tuer' and name == 'offen':
                    raise AttributeError(f"Attribut '{name}' ist privat – Zugriff nicht erlaubt")
                return getattr(original, name)

            def __setattr__(self, name, value):
                if name == "_original":
                    super().__setattr__(name, value)
                    return
                original = super().__getattribute__("_original")
                if name.startswith("_"):
                    raise AttributeError(f"Privates Attribut '{name}' – Zugriff nicht erlaubt")
                try:
                    typ = getattr(original, 'typ', None)
                except Exception:
                    typ = None
                if name in blocked_attrs:
                    raise AttributeError(f"Attribut '{name}' ist privat – Schreiben nicht erlaubt")
                if typ == 'Tuer' and name == 'offen':
                    raise AttributeError(f"Attribut '{name}' ist privat – Schreiben nicht erlaubt")
                setattr(original, name, value)

            def __dir__(self):
                return [n for n in dir(super().__getattribute__("_original")) if not n.startswith("_")]

            def __repr__(self):
                try:
                    orig = super().__getattribute__("_original")
                    return "<Proxy({})>".format(repr(orig))
                except Exception:
                    return "<Proxy(unknown)>"

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

    def gib_objekte(self):
        """Gibt alle Objekte im Spielfeld zurück (shallow copy).

        Rückgabe ist eine Kopie der internen Liste, damit Aufrufer die Liste
        nicht versehentlich verändern. Dies steuert nur den logischen Zugriff
        auf Objekte; keine Darstellung oder Platzierungs-Logik wird verändert.
        """
        try:
            return list(self.objekte)
        except Exception:
            return []

    def check_victory(self) -> bool:
        """Evaluate configured victory conditions (AND semantics).

        Supported conditions (in self.settings['victory']):
        - collect_hearts: bool (default True) -> satisfied when no hearts remain
        - move_to: {'enabled':True, 'x':int, 'y':int} -> satisfied when Held is at (x,y)
        - classes_present: bool -> satisfied when all canonical classes used in level have student definitions

        If no victory dict exists, default behaviour is collect_hearts True (backwards-compatible).
        """
        try:
            vic = (self.settings or {}).get('victory')
            if not isinstance(vic, dict):
                # default: collect hearts
                return not self.gibt_noch_herzen()

            # collect_hearts
            if vic.get('collect_hearts', True):
                if self.gibt_noch_herzen():
                    return False

            # move_to
            mv = vic.get('move_to')
            if isinstance(mv, dict) and mv.get('enabled'):
                try:
                    held = getattr(self, 'held', None)
                    if not held:
                        return False
                    tx = int(mv.get('x', -999))
                    ty = int(mv.get('y', -999))
                    # framework may block actions; require not blocked
                    blocked = getattr(self.framework, '_aktion_blockiert', False) if getattr(self, 'framework', None) else False
                    if blocked:
                        return False
                    if getattr(held, 'x', None) != tx or getattr(held, 'y', None) != ty:
                        return False
                except Exception:
                    return False

            # classes_present
            if vic.get('classes_present', False):
                # map spawn codes to canonical names. Prefer the precomputed
                # required set (computed before spawning), otherwise fall back
                # to iter_entity_spawns (best-effort).
                mapping = { 'p': 'Held', 'h': 'Herz', 'x': 'Monster', 'c': 'Code', 'd': 'Tuer', 's': 'Schluessel', 'v': 'Villager', 'k': 'Knappe', 'g': 'Tor', 'q': 'Questgeber' }
                needed = getattr(self, '_required_spawn_classes', None)
                if not needed:
                    needed = set()
                    for typ, x, y, sichtbar in self.level.iter_entity_spawns():
                        cname = mapping.get(typ)
                        if cname:
                            needed.add(cname)
                # For each needed canonical class, require that a student class file exists
                for cname in needed:
                    try:
                        if not self._student_has_class(cname):
                            return False
                    except Exception:
                        return False

            # all enabled conditions satisfied
            return True
        except Exception:
            # on error, fail-safe to False to avoid false victories
            return False

    def set_objekt(self, x: int, y: int, obj) -> bool:
        """Platziert `obj` logisch auf Position (x,y) falls das Terrain begehbar ist.

        Regeln:
        - Die Koordinaten müssen innerhalb des Spielfelds liegen.
        - Das Terrain an (x,y) muss begehbar sein (z.B. 'Weg').
        - Wenn bereits ein anderes Objekt auf dem Feld steht, wird das Placement
          abgelehnt (kein Überschreiben).
        - Bei Erfolg werden `obj.x` und `obj.y` gesetzt; das Objekt wird der
          internen Objektliste hinzugefügt, falls es dort noch nicht existiert.

        Diese Methode verändert ausschließlich die logische Platzierung; sie
        führt kein Rendering, Delay oder sonstige UI-Operationen aus.
        """
        try:
            # 1) Grenzen prüfen
            if not self.innerhalb(x, y):
                return False

            # 2) Terrain prüfen (nur 'Weg' gilt als begehbar)
            if self.terrain_art_an(x, y) != "Weg":
                return False

            # 3) Prüfe, ob Feld bereits belegt ist (mit anderem Objekt)
            occupant = self.objekt_an(x, y)
            if occupant is not None and occupant is not obj:
                return False

            # 4) Setze Position und füge Objekt der Liste hinzu, falls nötig
            try:
                obj.x = int(x)
                obj.y = int(y)
            except Exception:
                # fallback: set attributes directly
                try:
                    setattr(obj, 'x', x)
                    setattr(obj, 'y', y)
                except Exception:
                    return False

            if obj not in self.objekte:
                self.objekte.append(obj)

            # Falls möglich, setze framework-Referenz auf dem Objekt
            try:
                obj.framework = self.framework
            except Exception:
                pass

            return True
        except Exception:
            return False

    def gibt_noch_herzen(self):
        return any(o.name == "Herz" for o in self.objekte)
    
    def anzahl_herzen(self):
        c = 0
        for o in self.objekte:
            if o.name == "Herz":
                c+=1
        return c

    def check_victory(self) -> bool:
        """Evaluate configured victory conditions.

        The configured conditions are combined with logical AND: all enabled
        conditions must be satisfied for the level to be considered won.

        Supported keys in self.victory_settings:
        - collect_hearts: bool (default True)
        - move_to: dict or None: {'enabled': True, 'x': int, 'y': int}
        - classes_present: bool (default False)
        """
        try:
            vs = self.victory_settings or {}
            # By default, if no config present, require collecting hearts (backwards compatible)
            collect_req = True if 'collect_hearts' not in vs else bool(vs.get('collect_hearts', True))

            # 1) collect_hearts
            if collect_req:
                if self.gibt_noch_herzen():
                    return False

            # 2) move_to coordinate
            mv = vs.get('move_to') if isinstance(vs, dict) else None
            if mv and isinstance(mv, dict) and mv.get('enabled'):
                try:
                    tx = int(mv.get('x', -999))
                    ty = int(mv.get('y', -999))
                except Exception:
                    return False
                # require a hero and that the framework is not blocking actions
                try:
                    held = getattr(self, 'held', None)
                    if held is None:
                        return False
                    hx = int(getattr(held, 'x', None))
                    hy = int(getattr(held, 'y', None))
                    if hx != tx or hy != ty:
                        return False
                    # also ensure framework not blocking student actions
                    if getattr(self.framework, '_aktion_blockiert', False):
                        return False
                except Exception:
                    return False

            # 3) classes_present: require that all canonical classes used in the level
            # (by entity spawn) are present in student files (AST check)
            if bool(vs.get('classes_present', False)):
                try:
                    # build canonical set
                    mapping = {
                        'p': 'Held', 'k': 'Knappe', 'x': 'Monster', 'h': 'Herz',
                        'd': 'Tuer', 'c': 'Code', 'v': 'Villager', 'g': 'Tor',
                        's': 'Schluessel', 'q': 'Questgeber'
                    }
                    # Prefer the precomputed required classes (computed before
                    # _spawn_aus_level runs and mutates tiles). Fall back to
                    # scanning iter_entity_spawns only when the precomputed set
                    # is not available.
                    needed = getattr(self, '_required_spawn_classes', None)
                    if not needed:
                        needed = set()
                        for typ, x, y, sichtbar in self.level.iter_entity_spawns():
                            if not isinstance(typ, str):
                                continue
                            key = typ.lower()
                            cn = mapping.get(key)
                            if cn:
                                needed.add(cn)
                    # for each needed canonical name, require _student_has_class True
                    for cn in needed:
                        if not self._student_has_class(cn):
                            return False
                except Exception:
                    return False

            # all enabled conditions satisfied
            return True
        except Exception:
            return False
