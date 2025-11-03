from framework.grundlage import level
level.lade(104,weiblich=True)
from framework.grundlage import *

# Ab hier darfst du programmieren:


knappe = held.gib_knappe()
knappe.geh()
monster = knappe.gib_objekt_vor_dir()

t = monster.gib_objekt_vor_dir().gib_spruch()

monster.rechts()
monster.angriff()
door = held.gib_objekt_vor_dir()

door.spruch_anwenden(t)
held.geh()
held.geh()
held.geh()
held.nimm_herz()




# Dieser Befehl muss immer am Ende stehen
framework.starten()