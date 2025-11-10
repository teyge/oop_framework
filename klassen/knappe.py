"""Demo-Implementierung einer Schüler-Klasse für 'Held' in klassen/held.py"""
class Knappe:
    def __init__(self, level, x, y, richt):
        # student-held receives only the level
        self.level = level
        self.x = x
        self.y = y
        self.richtung = richt
        self.typ = "Knappe"
        self.name = "Namenloser Knappe"
        self.spruch = ""
        #self.inventar = Inventar() TODO (nicht von agent implementieren lassen!)

    def ist_passierbar(self):
        return False

    def geh(self):
        if self.richtung == "right":
            self.x += 1
        elif self.richtung == "left":
            self.x -= 1
        elif self.richtung == "up":
            self.y -= 1
        elif self.richtung == "down":
            self.y += 1

    def links(self):
        if self.richtung == "down":
            self.richtung = "right"
        elif self.richtung == "right":
            self.richtung = "up"
        elif self.richtung == "up":
            self.richtung = "left"
        elif self.richtung == "left":
            self.richtung = "down"

    def rechts(self):
        if self.richtung == "down":
            self.richtung = "left"
        elif self.richtung == "left":
            self.richtung = "up"
        elif self.richtung == "up":
            self.richtung = "right"
        elif self.richtung == "right":
            self.richtung = "down"

    def zurueck(self):
        if self.richtung == "right":
            self.x -= 1
        elif self.richtung == "left":
            self.x += 1
        elif self.richtung == "up":
            self.y += 1
        elif self.richtung == "down":
            self.y -= 1

    def setze_richtung(self, richt):
        if richt == "up" or richt == "N" or richt == "Norden" or richt == "oben":
            self.richtung = "up"
        elif richt == "down" or richt == "S" or richt == "Sueden" or richt == "unten":
            self.richtung = "down"
        elif richt == "left" or richt == "W" or richt == "Westen" or richt == "links":
            self.richtung = "left"
        elif richt == "right" or richt == "O" or richt == "Osten" or richt == "rechts":
            self.richtung = "right"

    

    # Die folgende Methode wird später die ursprüngliche Basis-Methode ersetzen und dabei das level verwenden
    # Analog für zurueck
    """def geh(self):
        max_right = self.level.gib_breite() - 1
        max_down = self.level.gib_hoehe() - 1
        if self.richtung == "right" and self.x < max_right:
            self.x += 1
        elif self.richtung == "left" and self.x > 0:
            self.x -= 1
        elif self.richtung == "up" and self.y > 0:
            self.y -= 1
        elif self.richtung == "down" and self.y < max_down:
            self.y += 1
    """
    def gib_objekt_vor_dir(self):
        if self.richtung == "right":
            return self.level.gib_objekt_an(self.x + 1, self.y)
        elif self.richtung == "left":
            return self.level.gib_objekt_an(self.x - 1, self.y)
        elif self.richtung == "up":
            return self.level.gib_objekt_an(self.x, self.y - 1)
        elif self.richtung == "down":
            return self.level.gib_objekt_an(self.x, self.y + 1)

    def ist_auf_herz(self):
        obj = self.level.gib_objekt_bei(self.x,self.y)
        if obj == None:
            return False
        if obj.typ == "Herz":
            return True

    def nimm_herz(self):
        obj = self.gib_objekt_vor_dir()
        if obj == None:
            return False
        if obj.typ == "Herz":
            self.level.entferne_objekt(obj)
            return True
        
    def verbleibende_herzen(self):
        return self.level.gib_anzahl_herzen()
    
    def herzen_vor_mir(self):
        if self.richtung == "up":
            dx = 0
            dy = -1
        elif self.richtung == "down":
            dx = 0
            dy = 1
        elif self.richtung == "left":
            dx = -1
            dy = 0
        elif self.richtung == "right":
            dx = 1
            dy = 0

        px = self.x + dx
        py = self.y + dy
        current = self.level.gib_objekt_bei(px,py)
        amount = 0
        while current != None and current.ist_passierbar():
            if current.typ == "Herz":
                amount += 1
            px += dx
            py += dy
            current = self.level.gib_objekt_bei(px,py)

        return amount
    
    def was_ist_vorn(self):
        obj = self.gib_objekt_vor_dir()
        if obj == None:
            return "None"
        else:
            return obj.typ
        
    def was_ist_links(self):
        self.links()
        obj = self.gib_objekt_vor_dir()
        self.rechts()
        if obj == None:
            return "None"
        else:
            return obj.typ
        
    def was_ist_rechts(self):
        self.rechts()
        obj = self.gib_objekt_vor_dir()
        self.links()
        if obj == None:
            return "None"
        else:
            return obj.typ

    def spruch_sagen(self):
        obj = self.gib_objekt_vor_dir()
        if obj == None:
            return False
        if obj.typ != "Tuer":
            return False
        if self.spruch == "":
            return False
        obj.spruch_anwenden(self.spruch)
        return True
    
    def sage_spruch(self):
        self.spruch_sagen()
    
    def spruch_lesen(self):
        obj = self.level.gib_objekt_bei(self.x, self.y)
        if obj == None:
            return False
        if obj.typ != "Spruch":
            return False
        self.spruch = obj.gib_spruch()

    # TODOS (Agent: Diese nicht implementieren)
    # def schluessel_nehmen() und def schluessel_verwenden
