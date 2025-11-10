import sys
import os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from framework.spielfeld import Spielfeld


class DummyFramework:
    def __init__(self):
        self.weiblich = False


if __name__ == '__main__':
    d = DummyFramework()
    s = Spielfeld('level/level30.json', d, auto_erzeuge_objekte=True)
    print('held exists:', bool(getattr(s, 'held', None)))
    print('held repr:', getattr(s, 'held', None))
    print('object count:', len(s.objekte))
    print('object types:', [getattr(o, 'typ', None) or o.__class__.__name__ for o in s.objekte])
