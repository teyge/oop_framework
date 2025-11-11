"""
Create a release ZIP containing selected project parts.

Usage:
  - Run interactively: python scripts/make_framework_version_zip.py
    -> it will prompt for a version number
  - Or pass version on command line: python scripts/make_framework_version_zip.py 6

Produces: framework_version_<ver>.zip in the current working directory.
Includes:
 - framework/ folder, but excludes any __pycache__ directories and their contents
 - sprites/ folder completely
 - leveleditor.py and schueler.py
 - from level/ only files matching ^level\d+\.json$

"""

import os
import sys
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_DIR = ROOT / "framework"
LEVEL_DIR = ROOT / "level"
SPRITES_DIR = ROOT / "sprites"
LEVELEDITOR = ROOT / "leveleditor.py"
SCHUELER = ROOT / "schueler.py"

LEVEL_FILE_RE = re.compile(r"^level\d+\.json$")


def gather_framework_files(root_dir: Path):
    """Yield (filepath, arcname) for framework folder excluding __pycache__ dirs."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Remove any __pycache__ dirs from traversal
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for fname in filenames:
            # skip .pyc or other compiled files
            if fname.endswith('.pyc'):
                continue
            fpath = Path(dirpath) / fname
            arcname = fpath.relative_to(ROOT)
            yield fpath, str(arcname).replace('\\', '/')


def gather_sprites(root_dir: Path):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for fname in filenames:
            fpath = Path(dirpath) / fname
            arcname = fpath.relative_to(ROOT)
            yield fpath, str(arcname).replace('\\', '/')


def gather_levels(level_dir: Path):
    if not level_dir.exists():
        return
    for item in sorted(level_dir.iterdir()):
        if item.is_file() and LEVEL_FILE_RE.match(item.name):
            arcname = item.relative_to(ROOT)
            yield item, str(arcname).replace('\\', '/')


def add_file_to_zip(zf: zipfile.ZipFile, filepath: Path, arcname: str):
    zf.write(filepath, arcname)
    print(f"Added: {arcname}")


def main(argv):
    if len(argv) >= 2:
        version = argv[1]
    else:
        version = input("Versionsnummer (z.B. 6): ").strip()

    if not version:
        print("Keine Versionsnummer angegeben. Abbruch.")
        return 2

    zipname = f"framework_version_{version}.zip"
    zip_path = Path.cwd() / zipname
    if zip_path.exists():
        ans = input(f"{zipname} existiert bereits. Überschreiben? [j/N]: ").strip().lower()
        if ans not in ('j', 'y'):
            print("Abgebrochen.")
            return 1

    print(f"Erstelle {zip_path} ...")

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        # framework folder (walk, exclude __pycache__)
        if FRAMEWORK_DIR.exists():
            for fpath, arc in gather_framework_files(FRAMEWORK_DIR):
                add_file_to_zip(zf, fpath, arc)
        else:
            print("Warnung: framework/ Verzeichnis nicht gefunden.")

        # sprites folder (full)
        if SPRITES_DIR.exists():
            for fpath, arc in gather_sprites(SPRITES_DIR):
                add_file_to_zip(zf, fpath, arc)
        else:
            print("Warnung: sprites/ Verzeichnis nicht gefunden.")

        # leveleditor.py and schueler.py
        if LEVELEDITOR.exists():
            add_file_to_zip(zf, LEVELEDITOR, str(LEVELEDITOR.relative_to(ROOT)).replace('\\', '/'))
        else:
            print("Warnung: leveleditor.py nicht gefunden.")

        if SCHUELER.exists():
            add_file_to_zip(zf, SCHUELER, str(SCHUELER.relative_to(ROOT)).replace('\\', '/'))
        else:
            print("Warnung: schueler.py nicht gefunden.")

        # level JSON files matching level<digits>.json
        for fpath, arc in gather_levels(LEVEL_DIR):
            add_file_to_zip(zf, fpath, arc)

    print(f"Fertig: {zip_path}")
    return 0


if __name__ == '__main__':
    rc = main(sys.argv)
    sys.exit(rc)
