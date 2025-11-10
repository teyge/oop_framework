from .knappe import Knappe

class Held(Knappe):
    def __init__(self, level, x, y, richt, weiblich=False):
        # student-held receives only the level
        super().__init__(level, x, y, richt)
        self.weiblich = weiblich
        #self.gold = 0
        self.typ = "Held"

    def setze_knappe(self, knappe):
        if knappe.typ == "Knappe":
            self.knappe = knappe

    def gib_knappe(self):
        return self.knappe
