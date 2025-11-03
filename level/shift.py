import os
import shutil
import sys

def shift_levels(folder: str, start: int, end: int, shift: int):
    """Verschiebt fortlaufend benannte Leveldateien (levelX.json)
    im Bereich [start, end] um eine bestimmte Anzahl."""

    files = []
    for f in os.listdir(folder):
        if f.startswith("level") and f.endswith(".json"):
            try:
                num = int(f[5:-5])
                files.append((num, f))
            except ValueError:
                pass

    if not files:
        print("⚠️ Keine Leveldateien gefunden.")
        return

    # Nur betroffene Level
    files = sorted([(n, f) for n, f in files if start <= n <= end], reverse=True)
    if not files:
        print(f"⚠️ Keine Level im Bereich {start}–{end} gefunden.")
        return

    # Prüfen, ob Kollisionen auftreten würden
    existing_numbers = {n for n, _ in files}
    all_numbers = {int(f[5:-5]) for f in os.listdir(folder)
                   if f.startswith("level") and f.endswith(".json") and f[5:-5].isdigit()}

    for num, _ in files:
        new_num = num + shift
        if new_num in all_numbers and new_num not in existing_numbers:
            print(f"❌ FEHLER: Kollision – level{new_num}.json existiert bereits.")
            sys.exit(1)
        if new_num < 0:
            print(f"❌ FEHLER: Ungültige Zielnummer ({new_num}) für level{num}.json")
            sys.exit(1)

    # Verschieben (rückwärts, um Überschreibungen zu vermeiden)
    print(f"🔄 Verschiebe Level {start}–{end} um {shift} ...")
    for num, fname in files:
        new_num = num + shift
        new_name = f"level{new_num}.json"
        old_path = os.path.join(folder, fname)
        new_path = os.path.join(folder, new_name)
        print(f"  {fname} → {new_name}")
        shutil.move(old_path, new_path)

    print("✅ Verschieben abgeschlossen.")


if __name__ == "__main__":
    folder = input("📁 Ordnerpfad (Enter = aktueller Ordner): ").strip() or "."
    start = int(input("🔢 Ab welchem Level soll verschoben werden? ").strip())
    end = int(input("🔢 Bis zu welchem Level soll verschoben werden? ").strip())
    shift = int(input("↕️ Um wie viele Level verschieben (z. B. +1 oder -2)? ").strip())
    shift_levels(folder, start, end, shift)
