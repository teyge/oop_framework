import os
import pytest
from framework.spielfeld import Spielfeld


class DummyFW:
    pass


def _find_obj_by_typ(sp, typname):
    for o in sp.objekte:
        try:
            if getattr(o, 'typ', None) == typname:
                return o
        except Exception:
            continue
    return None


def test_privacy_enforced(tmp_path):
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    levelfile = os.path.join(repo, 'level', 'level_privacy_private.json')
    fw = DummyFW()
    sp = Spielfeld(levelfile, fw, auto_erzeuge_objekte=True)

    held = getattr(sp, 'held', None)
    assert held is not None

    # Accessing x,y,richtung from test code should raise AttributeError when privatized
    with pytest.raises(AttributeError):
        _ = held.x
    with pytest.raises(AttributeError):
        _ = held.y
    with pytest.raises(AttributeError):
        _ = held.richtung
    with pytest.raises(AttributeError):
        held.y = 5

    herz = _find_obj_by_typ(sp, 'Herz')
    assert herz is not None
    with pytest.raises(AttributeError):
        _ = herz.x
    with pytest.raises(AttributeError):
        herz.x = 1

    tuer = _find_obj_by_typ(sp, 'Tuer')
    assert tuer is not None
    # 'offen' is a property on Tuer; access and write should be blocked when private
    with pytest.raises(AttributeError):
        _ = tuer.offen
    with pytest.raises(AttributeError):
        tuer.offen = True


def test_privacy_not_enforced(tmp_path):
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    levelfile = os.path.join(repo, 'level', 'level_privacy_public.json')
    fw = DummyFW()
    sp = Spielfeld(levelfile, fw, auto_erzeuge_objekte=True)

    held = getattr(sp, 'held', None)
    assert held is not None

    # Attributes should be accessible and writable
    assert isinstance(held.x, int)
    held.y = held.y + 1
    assert isinstance(held.richtung, str)

    herz = _find_obj_by_typ(sp, 'Herz')
    assert herz is not None
    assert isinstance(herz.x, int)
    herz.x = herz.x + 1

    tuer = _find_obj_by_typ(sp, 'Tuer')
    assert tuer is not None
    # reading and writing 'offen' should work
    val = tuer.offen
    tuer.offen = not val
