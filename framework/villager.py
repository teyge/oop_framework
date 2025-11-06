# framework/villager.py
import pygame
import random
from .objekt import Objekt
from .inventar import Inventar
from .gegenstand import Gegenstand


class Villager(Objekt):
    """Ein einfacher Dorfbewohner / Dorfbewohnerin.

    Minimalimplementierung: wählt Sprite basierend auf dem weiblich-Flag
    und bietet eine kleine Attributanzeige. Verwendet das Basisklasse-Verhalten
    für Bewegung und Zeichnen.
    """

    def __init__(self, framework, x=0, y=0, richtung="down",
                 sprite_pfad: str = None, name: str = "Nils",
                 steuerung_aktiv: bool = False, weiblich: bool = False):
        if weiblich:
            typ = "Dorfbewohnerin"
            sprite_pfad = sprite_pfad or "sprites/villager2.png"
        else:
            typ = "Dorfbewohner"
            sprite_pfad = sprite_pfad or "sprites/villager.png"

        # wenn kein Name mitgegeben wurde, wähle zufälligen
        if not name:
            name = random.choice(["Frieda", "Klaus", "Nina", "Otto", "Lena", "Karl"])

        # rufe Basisklassen-Konstruktor auf
        super().__init__(typ=typ, x=x, y=y, richtung=richtung,
                         sprite_pfad=sprite_pfad, name=name)
        # If this instance is a Questgeber subclass, that subclass may override typ; leave as is by default
        self.framework = framework
        self.steuerung_aktiv = steuerung_aktiv
        self.weiblich = weiblich
        self.ist_held = False
        # Inventar und Preisliste: preisliste speichert Preise keyed by id(item)
        self.inventar = Inventar()
        self.preisliste = {}  # { id(item): price }

        # Beim Erzeugen erhalten Villager 2-4 zufällige Gegenstände (mit Preisen)
        try:
            ITEM_NAMES = ["Ring", "Apple", "Sword", "Shield", "Potion", "Scroll", "Bread", "Gem", "Torch", "Amulet"]
            count = random.randint(2, 4)
            for _ in range(count):
                name_item = random.choice(ITEM_NAMES)
                wert = random.randint(5, 60)
                preis = random.randint(10, 100)
                try:
                    item = Gegenstand(name_item, wert)
                    self.biete_item_an(item, preis)
                except Exception:
                    # ignore item creation errors
                    pass
        except Exception:
            pass


    def attribute_als_text(self):
        return {
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "richtung": self.richtung,
            "weiblich": self.weiblich,
            "items": len(self.inventar),
        }

    # ----------------
    # Handel
    # ----------------
    def biete_item_an(self, item, preis: int):
        """Bietet ein Item zum Verkauf an: legt es ins Villager-Inventar
        und registriert den Preis. Liefert die Position (index) zurück."""
        try:
            self.inventar.hinzufuegen(item)
            idx = len(self.inventar) - 1
            self.preisliste[id(item)] = int(preis)
            return idx
        except Exception:
            return None

    def verkaufe_item(self, *args) -> bool:
        """Verkauft ein Item an den Held.

        Unterstützte Signaturen:
        - verkaufe_item(held, index)
        - verkaufe_item(index, held)

        Diese flexible API bewahrt Abwärtskompatibilität mit bestehendem
        Code (der `held, index` übergibt), ermöglicht aber auch die
        alternative Reihenfolge `index, held` wie gewünscht.
        """
        try:
            if len(args) != 2:
                return False
            a, b = args[0], args[1]
            # Erkenne welches Argument der Held ist (hat gold_gib)
            if hasattr(a, 'gold_gib'):
                held = a
                index = b
            elif hasattr(b, 'gold_gib'):
                held = b
                index = a
            else:
                # Fallback: assume (held, index)
                held = a
                index = b

            # normalize index to int
            try:
                index = int(index)
            except Exception:
                return False

            item = self.inventar.gib_item(index)
            if item is None:
                return False
            price = self.preisliste.get(id(item))
            if price is None:
                return False

            # Held muss gold_gib/gold_setzen oder kaufe haben
            if not hasattr(held, 'gold_gib'):
                return False
            if held.gold_gib() < price:
                return False

            # Transfer: bezahle und übertrage Item
            # prefer using provided api if present
            if hasattr(held, 'kaufe'):
                # kaufe() expects (item, price) and will add to inventar
                ok = False
                try:
                    ok = held.kaufe(item, price)
                except Exception:
                    ok = False
                if not ok:
                    return False
                # remove from villager
                try:
                    self.inventar.entfernen(item)
                except Exception:
                    pass
                try:
                    del self.preisliste[id(item)]
                except Exception:
                    pass
                return True
            else:
                # fallback: manual transfer
                try:
                    held.gold_setzen(held.gold_gib() - price)
                except Exception:
                    # if can't set gold, abort
                    return False
                try:
                    self.inventar.entfernen(item)
                except Exception:
                    pass
                try:
                    del self.preisliste[id(item)]
                except Exception:
                    pass
                try:
                    held.inventar.hinzufuegen(item)
                except Exception:
                    pass
                return True
        except Exception:
            return False

    # ----------------
    # Getter-API
    # ----------------
    def get_name(self) -> str:
        """Gibt den Anzeigenamen des Villagers zurück."""
        return getattr(self, 'name', None)

    def get_offers(self):
        """Gibt alle angebotenen Items zusammen mit Preisen zurück.

        Rückgabe: Liste von Dicts mit Schlüsseln: index, item, name, price
        """
        out = []
        try:
            for idx, it in enumerate(self.inventar):
                price = self.preisliste.get(id(it))
                out.append({
                    'index': idx,
                    'item': it,
                    'name': getattr(it, 'name', None),
                    'price': price
                })
        except Exception:
            pass
        return out


class Questgeber(Villager):
    """Ein spezieller Villager, der Quests vergibt: entweder verlangt er Items
    oder stellt ein kleines Rätsel.
    """

    def __init__(self, framework, x=0, y=0, richtung="down", modus: str = "items",
                 wuensche=None, anzahl_items: int = None, **kwargs):
        # wuensche: list of item names
        super().__init__(framework, x=x, y=y, richtung=richtung, **kwargs)
        self.modus = modus if modus in ("items", "raetsel") else "items"
        self.wuensche = list(wuensche) if wuensche else []

        # Wenn im 'items'-Modus und keine Wünsche vorgegeben sind, generiere eine Wunschliste
        try:
            if self.modus == 'items' and not self.wuensche:
                ITEM_NAMES = ["Ring", "Apple", "Sword", "Shield", "Potion", "Scroll", "Bread", "Gem", "Torch", "Amulet"]
                wish_count = max(1, min(3, int(anzahl_items) if anzahl_items else 1))
                self.wuensche = random.sample(ITEM_NAMES, wish_count)
        except Exception:
            pass
        # Anzahl Items kann aus Level-Settings kommen (quest_items_needed)
        settings = {}
        try:
            settings = getattr(self.framework, 'spielfeld', None).settings or {}
        except Exception:
            settings = {}
        if anzahl_items is None:
            self.anzahl_items = int(settings.get('quest_items_needed', 0) or 0)
        else:
            self.anzahl_items = int(anzahl_items)

        # Rätsel-Cache (letzte Frage/Antwort)
        self._letzte_raetsel = None
        # expliziter Typ für Erkennung
        try:
            self.typ = "Questgeber"
        except Exception:
            pass
        # Wenn Modus 'raetsel' und kein Rätsel vorhanden, generiere eines
        try:
            if self.modus == 'raetsel' and (self._letzte_raetsel is None):
                # raetsel_geben setzt self._letzte_raetsel
                self._vorgegebene_frage = self.raetsel_geben()
        except Exception:
            pass

    # ----------------
    # Getter / Setter API for Questgeber
    # ----------------
    def get_wuensche(self):
        """Gibt eine Kopie der Wunschliste (Namen der Items) zurück."""
        try:
            return list(self.wuensche)
        except Exception:
            return []

    def set_modus(self, modus: str) -> None:
        """Setzt den Modus des Questgebers. Erlaubt nur 'items' oder 'raetsel'.

        Bei ungültigem Modus wird eine ValueError ausgelöst.
        """
        if modus not in ("items", "raetsel"):
            raise ValueError(f"Ungültiger Modus für Questgeber: {modus}")
        try:
            self.modus = modus
        except Exception as e:
            print(f"[Questgeber] Fehler beim Setzen des Modus: {e}")

    def pruefe_abgabe(self, held) -> bool:
        """Prüft, ob `held` alle gewünschten Items besitzt. Entfernt diese
        aus dem Held-Inventar bei Erfolg und ruft `weiche_aus()` auf.
        """
        if self.modus != "items":
            return False
        if not hasattr(held, 'inventar'):
            return False
        inv = held.inventar
        # find matching items by name for all wishes
        matches = []
        for w in self.wuensche:
            found = None
            for it in inv:
                try:
                    if getattr(it, 'name', None) == w:
                        found = it
                        break
                except Exception:
                    continue
            if found is None:
                return False
            matches.append(found)

        # All found -> remove them
        for it in matches:
            try:
                inv.entfernen(it)
            except Exception:
                pass

        # Erfolgreiche Abgabe
        try:
            self.weiche_aus()
        except Exception:
            pass
        return True

    def weiche_aus(self) -> None:
        """Bewegt den Questgeber einen Schritt nach rechts, falls möglich."""
        try:
            self.setze_position(self.x + 1, self.y)
            # kleines visuelles Feedback
            try:
                self._render_and_delay(120)
            except Exception:
                pass
        except Exception:
            # setze_position kann False zurückgeben oder Exceptions werfen
            try:
                # alternativ: fallback prüfen mit spielfeld
                sp = getattr(self.framework, 'spielfeld', None)
                if sp and sp.kann_betreten(self, self.x + 1, self.y):
                    self.x += 1
            except Exception:
                pass

    def raetsel_geben(self) -> str:
        """Generiert ein einfaches arithmetisches Rätsel wie '7*4=' und speichert die Lösung."""
        a = random.randint(2, 12)
        b = random.randint(2, 12)
        op = random.choice(['+', '-', '*'])
        frage = f"{a}{op}{b}="
        if op == '+':
            loes = a + b
        elif op == '-':
            loes = a - b
        else:
            loes = a * b
        self._letzte_raetsel = loes
        return frage

    def raetsel_loesn(self, antwort: str) -> bool:
        """Prüft Antwort; bei Erfolg `weiche_aus()` und gibt True zurück."""
        try:
            if self._letzte_raetsel is None:
                return False
            ok = int(str(antwort).strip()) == int(self._letzte_raetsel)
            if ok:
                try:
                    self.weiche_aus()
                except Exception:
                    pass
                self._letzte_raetsel = None
                return True
            return False
        except Exception:
            return False

