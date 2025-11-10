# grundlage.py
from framework.framework import Framework
from .code import Code
from .held import Held
from .knappe import Knappe

# Platzhalter für globale Variablen, die beim Level-Laden gefüllt werden


class LevelManager:
    """Verwaltet den Ladevorgang der Level und stellt den Helden bereit."""
    def __init__(self):
        self.framework = None
        self.held = None

    def lade(self, nummer: int, weiblich = False,splash = False):
        global held,framework
        """Lädt das angegebene Level und initialisiert das Framework."""
        import sys

        self.framework = Framework(levelnummer=nummer, auto_erzeuge_objekte=True,w = weiblich,splash=splash)
        self.held = self.framework.spielfeld.held
        held = self.held
        framework = self.framework

        # Hinweis und Status zurücksetzen
        self.framework._hinweis = None
        self.framework._aktion_blockiert = False
        
    def gib_objekt_bei(self,x,y):
        return framework.gib_objekt_an(x,y)

    def objekt_hinzufuegen(self, obj):
        """Convenience: forward to the active framework instance so students
        can call `level.objekt_hinzufuegen(obj)` directly from their code.
        """
        try:
            fw = getattr(self, 'framework', None)
            if fw is None:
                # fallback to module-level framework if available
                try:
                    from framework import grundlage as _g
                    fw = getattr(_g, 'framework', None)
                except Exception:
                    fw = None
            if fw is None:
                raise AttributeError('Kein Framework vorhanden')
            return fw.objekt_hinzufuegen(obj)
        except Exception:
            # Bubble up the AttributeError to make student errors visible
            raise
        
 
"""
def __getattr__(name):
    if name == "held":
        return level.framework.spielfeld.held
    if name == "framework":
        return level.framework
    raise AttributeError(name)
"""




# Globale Instanz
global held, framework
level = LevelManager()
held = None
framework = None
tuer = None
code = None
monster = None


# Optional: Direkter Start bei eigenständigem Aufruf (z. B. Test)
"""
if __name__ == "__main__":
    level.lade(1)
    framework.starten()
"""
