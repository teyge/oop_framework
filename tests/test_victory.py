import os
from framework.spielfeld import Spielfeld


import os
from framework.spielfeld import Spielfeld


class DummyFW:
    pass


def test_move_to_victory():
    # Use the example level created in repo
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    levelfile = os.path.join(repo, 'level', 'level_victory_move.json')
    fw = DummyFW()
    sp = Spielfeld(levelfile, fw, auto_erzeuge_objekte=True)
    # ensure held exists
    assert getattr(sp, 'held', None) is not None, "Held must be spawned for move-to test"
    # move the held to target
    sp.held.x = 2
    sp.held.y = 0
    # ensure framework not blocking
    sp.framework._aktion_blockiert = False
    assert sp.check_victory() is True


def test_classes_present_negative():
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    levelfile = os.path.join(repo, 'level', 'level_victory_classes.json')
    fw = DummyFW()
    sp = Spielfeld(levelfile, fw, auto_erzeuge_objekte=True)
    # classes_present is required in this level, but no student classes exist -> should be False
    assert sp.check_victory() is False