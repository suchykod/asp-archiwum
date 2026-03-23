#!/usr/bin/env python3
"""
ASP Warszawa - Wydział Wzornictwa
Skrypt do archiwizacji dokumentacji semestralnej
Zgodny z INSTRUKCJĄ DOKUMENTACJI 2026
"""

import re
import sys
import shutil
from pathlib import Path

try:
    from PIL import Image, ImageOps # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠  Pillow nie jest zainstalowane → Małe Archiwum NIE zostanie utworzone.")

# ── Stałe ─────────────────────────────────────────────────────────────────────
IMAGE_EXTENSIONS     = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
SMALL_ARCHIVE_LONG   = 1080
JPEG_QUALITY         = 60
CATEGORY_FOLDERS     = {"projektowe", "plastyczne", "inne"}

# Mapa podfolderów na odpowiednie przyrostki z instrukcji ASP
SUFFIX_MAP = {
    "zdjecia": "M",     # zdjęcia modelu, obrazy, rysunki
    "plansze": "P",     # plansze (często PDF lub JPG)
    "rendering": "R",   # rendering
    "film": "F",        # prezentacja, film, animacja (mp4, avi)
    "szkicownik": "S"   # szkicownik
}

WORKSHOP_CODES = {
    "P1","P2","P3","P4","PPPP","PKW","MS","JP","GN","DZ","PG","AF","BM","MK",
    "JK","PJ","MWP","MPB","BP","G","M1","RZ1","RZ2","RZ3",
    "TM","KT","TP","E","KD","GA","PU1","PU2","PU3","GM1","GM2","MAT1","MAT2","RM1","RM2",
}

# ── Parsowanie ─────────────────────────────────────────────────────────────────
def parse_root_name(root_name: str) -> dict:
    parts = root_name.split("_")
    if len(parts) < 3:
        return {"surname_initial": root_name, "year": "????", "semester": "?"}
    return {"surname_initial": parts[0], "year": parts[1], "semester": parts[2]}

def extract_workshop_code(folder_name: str, meta: dict) -> str:
    pattern = rf"^{re.escape(meta['surname_initial'])}_([A-Za-z0-9]+)_"
    m = re.match(pattern, folder_name)
    return m.group(1).upper() if m else folder_name.upper()

def sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()

def get_next_index(directory: Path, suffix: str) -> int:
    """Szuka najwyższego numeru pliku np. _M04.jpg i zwraca 5, aby unikać nadpisywania."""
    pattern = re.compile(rf"_{suffix}(\d+)\.[a-zA-Z0-9]+$")
    max_idx = 0
    for f in directory.iterdir():
        if f.is_file() and not f.name.startswith("."):
            m = pattern.search(f.name)
            if m:
                max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1

# ── Struktura folderów ─────────────────────────────────────────────────────────
def iter_projects(root: Path, meta: dict):
    """
    Znajduje foldery pracowni (które w Twojej strukturze stanowią też projekty).
    """
    for level1 in sorted(root.iterdir()):
        if not level1.is_dir() or level1.name.startswith("."):
            continue

        if level1.name.lower() in CATEGORY_FOLDERS:
            cat_label = level1.name
            for level2 in sorted(level1.iterdir()):
                if not level2.is_dir() or level2.name.startswith("."):
                    continue
                workshop_code = extract_workshop_code(level2.name, meta)
                
                prefix = f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
                project_name = level2.name[len(prefix):].lstrip("_")
                project_name = project_name if project_name else workshop_code

                yield cat_label, workshop_code, level2, project_name

# ── Duże Archiwum ──────────────────────────────────────────────────────────────
def process_large_archive(root: Path, meta: dict) -> None:
    print("\n━━━  DUŻE ARCHIWUM (Wciąganie z folderów roboczych)  ━━━━━━")

    for cat_label, workshop_code, project_dir, project_name in iter_projects(root, meta):
        print(f"\n  [{cat_label} / {workshop_code}] {project_name}")
        
        # 1. Wyciąganie plików z roboczych folderów (zdjecia, plansze, itp.)
        for folder_name, suffix_code in SUFFIX_MAP.items():
            sub_dir = project_dir / folder_name
            if not sub_dir.is_dir():
                continue

            # Pobierz wszystkie sensowne pliki z podfolderu
            files = sorted([f for f in sub_dir.iterdir() if f.is_file() and not f.name.startswith(".")])
            
            for file_path in files:
                # Nie ruszamy plików tekstowych z folderów roboczych (gdyby tam trafiły)
                if file_path.suffix.lower() == ".txt":
                    continue
                
                # Zdobądź kolejny wolny numerek dla danego kodu (np. M01, P02)
                idx = get_next_index(project_dir, suffix_code)
                new_name = f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}_{sanitize(project_name)}_{suffix_code}{idx:02d}{file_path.suffix.lower()}"
                
                # Przenieś piętro wyżej i zmień nazwę
                file_path.rename(project_dir / new_name)
                print(f"    ✓ {folder_name}/...  →  {new_name}")

            # Usuń folder roboczy, jeśli jest pusty (kasujemy najpierw ewentualne ukryte pliki .DS_Store)
            try:
                for hidden in sub_dir.rglob(".*"):
                    hidden.unlink()
                sub_dir.rmdir()
            except OSError:
                print(f"    ⚠ Nie usunięto '{folder_name}' - zawiera nierozpoznane pliki.")

# ── Małe Archiwum ──────────────────────────────────────────────────────────────
def compress_image(src: Path, dst: Path) -> None:
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        w, h = img.size
        long_side = max(w, h)
        if long_side > SMALL_ARCHIVE_LONG:
            scale = SMALL_ARCHIVE_LONG / long_side
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst, format="JPEG", quality=JPEG_QUALITY, optimize=True)

def create_small_archive(root: Path, meta: dict) -> None:
    if not PIL_AVAILABLE:
        return

    small_root = root.parent / (root.name + "_E")
    if small_root.exists():
        shutil.rmtree(small_root)

    print(f"\n━━━  MAŁE ARCHIWUM  →  {small_root.name}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Wymuś bazową strukturę
    for cat in ["Projektowe", "Plastyczne", "Inne"]:
        (small_root / cat).mkdir(parents=True, exist_ok=True)

    for cat_label, workshop_code, project_dir, project_name in iter_projects(root, meta):
        print(f"\n  [{cat_label} / {workshop_code}] {project_name}")

        for file_path in sorted(project_dir.iterdir()):
            if not file_path.is_file() or file_path.name.startswith("."):
                continue

            rel = file_path.relative_to(root)
            dst = small_root / rel

            if file_path.suffix.lower() in IMAGE_EXTENSIONS:
                dst_jpg = dst.with_suffix(".jpg")
                try:
                    compress_image(file_path, dst_jpg)
                    orig_kb  = file_path.stat().st_size // 1024
                    small_kb = dst_jpg.stat().st_size  // 1024
                    print(f"    ✓  {file_path.name}  ({orig_kb} KB → {small_kb} KB)")
                except Exception as e:
                    print(f"    ❌  {file_path.name}  – błąd: {e}")

            elif file_path.suffix.lower() == ".txt":
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dst)
                print(f"    –  {file_path.name}  (skopiowano INF)")

            else:
                # Np. Filmy .mp4, pdfy, z których student musi wyciagnac klatki recznie
                print(f"    ○  {file_path.name}  (pominięto – wstaw ręcznie klatki/slajdy JPG z tym kodem w _E)")

    print(f"\n  ✅  Małe Archiwum gotowe: {small_root}")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()

    if not root.is_dir():
        print(f"❌  Folder nie istnieje: {root}")
        sys.exit(1)

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ASP Warszawa – Archiwizacja dokumentacji semestralnej  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  Folder roboczy: {root}")

    if root.name.endswith("_E"):
        print("❌  To jest folder Małego Archiwum (_E). Uruchom z Dużego Archiwum.")
        sys.exit(1)

    meta = parse_root_name(root.name)
    process_large_archive(root, meta)
    create_small_archive(root, meta)

    print("\n✅  Gotowe! Nie zapomnij:")
    print("   1. Uzupełnić pliki _INF.txt w każdym projekcie")
    print("   2. Wyciągnąć klatki/slajdy z przeniesionych filmów i PDFów")
    print("      i wstawić je jako JPEG do małego archiwum (_E).")
    print("   3. Dołączyć oświadczenie o autorstwie")

if __name__ == "__main__":
    main()