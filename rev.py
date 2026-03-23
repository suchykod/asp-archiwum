#!/usr/bin/env python3
import sys
import re
import uuid
from pathlib import Path

# Mapa odwrotna: z kodu na nazwę folderu roboczego
SUFFIX_TO_FOLDER = {
    "M": "zdjecia",
    "P": "plansze",
    "R": "rendering",
    "F": "film",
    "S": "szkicownik"
}

# Regex wyłapujący pliki ze specyficznymi końcówkami ASP (np. _M01.jpg, _P12.pdf)
PATTERN = re.compile(r"_([MPRFS])\d{2,}\.([a-zA-Z0-9]+)$", re.IGNORECASE)

def main():
    base_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    
    # Inteligentne wykrywanie folderu głównego
    root = base_path
    if not any(d.name.lower() in {"projektowe", "plastyczne", "inne"} for d in base_path.iterdir() if d.is_dir()):
        possible_roots = [d for d in base_path.iterdir() if d.is_dir() and "_" in d.name and not d.name.endswith("_E")]
        if possible_roots:
            root = possible_roots[0]
            print(f"👉 Zmieniam folder roboczy na: {root.name}\n")
        else:
            print(f"❌ Nie znaleziono folderów Projektowe/Plastyczne/Inne w: {base_path}")
            sys.exit(1)

    print(f"⏪ ODKRĘCAM ZMIANY W: {root.name}\n")
    files_moved = 0

    # rglob("*.*") skanuje absolutnie wszystko wewnątrz głównego folderu
    for file_path in root.rglob("*.*"):
        if not file_path.is_file() or file_path.name.startswith("."):
            continue

        # Ignorujemy pliki tekstowe (_INF.txt)
        if file_path.suffix.lower() == ".txt":
            continue

        match = PATTERN.search(file_path.name)
        if match:
            suffix_letter = match.group(1).upper()
            ext = match.group(2).lower()
            
            target_folder_name = SUFFIX_TO_FOLDER.get(suffix_letter)
            if not target_folder_name:
                continue
            
            # Tworzymy podfolder roboczy dokładnie tam, gdzie aktualnie leży plik
            target_dir = file_path.parent / target_folder_name
            target_dir.mkdir(exist_ok=True)
            
            # Generujemy "losową" nazwę symulującą plik z aparatu (np. odzyskany_8f3a1b.jpg)
            random_hash = uuid.uuid4().hex[:6]
            new_name = f"odzyskany_{random_hash}.{ext}"
            new_path = target_dir / new_name
            
            # Przenosimy plik
            file_path.rename(new_path)
            files_moved += 1
            print(f"  ↩ Przeniesiono: {file_path.name}  ->  {target_folder_name}/{new_name}")

    if files_moved == 0:
        print("\n🤷‍♂ Nie znalazłem żadnych plików do odkręcenia (z końcówkami _M01, _P01 itd.).")
    else:
        print(f"\n✅ Gotowe! Odkręciłem zmiany dla {files_moved} plików. Siedzą bezpiecznie w roboczych szufladkach.")

if __name__ == "__main__":
    main()