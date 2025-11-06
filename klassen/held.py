"""Demo-Implementierung einer Schüler-Klasse für 'Held' in klassen/held.py"""
class Held:
    def __init__(self, level, x, y, richt, weiblich=False):
        # student-held receives only the level
        self.level = level
        self.x = x
        self.y = y
        self.richtung = richt
        self.weiblich = weiblich
        self.gold = 0
        self.typ = "Held"

    def zeichne(self, screen, feldgroesse):
        return
