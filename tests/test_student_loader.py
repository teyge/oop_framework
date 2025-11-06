import sys, os, json
# ensure project root is on sys.path when tests are run as scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from framework.spielfeld import Spielfeld
from framework.held import MetaHeld


def _write_level(path, import_pfad):
    lvl = {
        'tiles': ["www", "wPw", "www"],
        'settings': {'import_pfad': import_pfad}
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(lvl, f, ensure_ascii=False, indent=2)


class DummyFW:
    def __init__(self):
        # minimal attributes used by Held/Spielfeld
        self.weiblich = False
        self.spielfeld = None
        self._keyregs = {}

    def taste_registrieren(self, key, callback):
        try:
            self._keyregs[key] = callback
        except Exception:
            pass


def test_student_root_import():
    path = 'tests/tmp_level_student_root.json'
    _write_level(path, 'schueler')
    fw = DummyFW()
    sp = Spielfeld(path, fw, feldgroesse=16)
    # student-provided Held should be wrapped by MetaHeld (framework wrapper)
    if not isinstance(sp.held, MetaHeld):
        print('STUDENT-ROOT IMPORT FAILED: Held not wrapped by MetaHeld', type(sp.held))
        raise SystemExit(1)
    # student instance should be accessible and receive the Level
    stud = getattr(sp.held, '_student', None)
    if stud is None or getattr(stud, 'level', None) is not sp.level:
        print('STUDENT-ROOT IMPORT FAILED: student instance missing or wrong level')
        raise SystemExit(1)
    print('STUDENT-ROOT IMPORT OK')


def test_student_klassen_import():
    path = 'tests/tmp_level_student_klassen.json'
    _write_level(path, 'held')
    fw = DummyFW()
    sp = Spielfeld(path, fw, feldgroesse=16)
    if not isinstance(sp.held, MetaHeld):
        print('STUDENT-KLASSEN IMPORT FAILED: Held not wrapped by MetaHeld', type(sp.held))
        raise SystemExit(1)
    stud = getattr(sp.held, '_student', None)
    if stud is None or getattr(stud, 'level', None) is not sp.level:
        print('STUDENT-KLASSEN IMPORT FAILED: student instance missing or wrong level')
        raise SystemExit(1)
    print('STUDENT-KLASSEN IMPORT OK')


if __name__ == '__main__':
    test_student_root_import()
    test_student_klassen_import()
    print('ALL STUDENT IMPORT TESTS OK')
