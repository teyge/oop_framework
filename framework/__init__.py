# framework/__init__.py
from .inventar import Inventar
from .gegenstand import Gegenstand, Schluessel

__all__ = [
	"framework", "spielfeld", "level", "objekt", "held", "monster", "herz", "utils",
	"Inventar", "Gegenstand", "Schluessel"
]

# Namens- und Itemlisten für zufällige Generierung
VORNAMEN_M = ["Alrik", "Borin", "Cedric", "Doran", "Eirik"]
VORNAMEN_W = ["Hilda", "Jara", "Kira", "Lyra", "Mira"]
ITEMNAMEN = ["Apfel", "Trank", "Fackel", "Buch", "Amulett"]
