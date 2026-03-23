#!/usr/bin/env python3
"""
ASP Warszawa - Wydział Wzornictwa
Skrypt do archiwizacji dokumentacji semestralnej
Zgodny z INSTRUKCJĄ DOKUMENTACJI 2026

Użycie:
  python3 asp_archiwum.py                     # uruchom z folderu semestru
  python3 asp_archiwum.py /ścieżka/do/folderu # lub podaj ścieżkę jako argument
"""

import re
import sys
import shutil
from pathlib import Path

# ── Pillow ─────────────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageOps # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠  Pillow nie jest zainstalowane → Małe Archiwum NIE zostanie utworzone.")
    print("   Zainstaluj: pip install Pillow\n")

# ── Stałe ─────────────────────────────────────────────────────────────────────
IMAGE_EXTENSIONS     = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
CATEGORY_FOLDERS     = {"projektowe", "plastyczne", "inne"}
SMALL_ARCHIVE_LONG   = 1080   # dłuższy bok skalowany do tej wartości
JPEG_QUALITY         = 60     # ≈ Quality 7 w Photoshopie

WORKSHOP_CODES = {
    "P1","P2","P3","P4","PPPP","PKW","MS","JP","GN","DZ","PG","AF","BM","MK",
    "JK","PJ","MWP","MPB","BP","G",
    "M1","RZ1","RZ2","RZ3",
    "TM","KT","TP","E","KD","GA",
    "PU1","PU2","PU3","GM1","GM2","MAT1","MAT2","RM1","RM2",
}

# ── Parsowanie ─────────────────────────────────────────────────────────────────

def parse_root_name(root_name: str) -> dict:
    parts = root_name.split("_")
    if len(parts) < 3:
        print(f"⚠  Nazwa folderu '{root_name}' nie pasuje do wzoru NazwiskoI_RRRR_SEM.")
        return {"surname_initial": root_name, "year": "????", "semester": "?"}
    return {"surname_initial": parts[0], "year": parts[1], "semester": parts[2]}

def extract_workshop_code(folder_name: str, meta: dict) -> str:
    pattern = rf"^{re.escape(meta['surname_initial'])}_([A-Za-z0-9]+)_"
    m = re.match(pattern, folder_name)
    if m:
        code = m.group(1).upper()
        if code not in WORKSHOP_CODES:
            print(f"    ⚠  Kod '{code}' nieznany wg instrukcji – kontynuuję.")
        return code
    return folder_name.upper()

# ── Nazewnictwo ────────────────────────────────────────────────────────────────

def sanitize(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()

def correct_image_name(meta: dict, workshop_code: str, project_name: str, index: int) -> str:
    return (
        f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
        f"_{sanitize(project_name)}_M{index:02d}.jpg"
    )

def correct_inf_name(meta: dict, workshop_code: str, project_name: str) -> str:
    return (
        f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
        f"_{sanitize(project_name)}_INF.txt"
    )

def is_bad_name(filename: str, meta: dict) -> bool:
    return "__M" in filename and filename.startswith(meta["surname_initial"])

def is_inf_file(path: Path) -> bool:
    return path.suffix.lower() == ".txt" and "_INF" in path.name

# ── Struktura folderów ─────────────────────────────────────────────────────────

def has_image_files(directory: Path) -> bool:
    return any(
        f.is_file() and not f.name.startswith(".") and f.suffix.lower() in IMAGE_EXTENSIONS
        for f in directory.iterdir()
    )

def iter_projects(root: Path, meta: dict):
    for level1 in sorted(root.iterdir()):
        if not level1.is_dir() or level1.name.startswith("."):
            continue

        if level1.name.lower() in CATEGORY_FOLDERS:
            cat_label = level1.name
            for level2 in sorted(level1.iterdir()):
                if not level2.is_dir() or level2.name.startswith("."):
                    continue
                workshop_code = extract_workshop_code(level2.name, meta)

                if has_image_files(level2):
                    project_name = _short_project_name(level2.name, meta, workshop_code)
                    yield cat_label, workshop_code, level2, project_name
                else:
                    for level3 in sorted(level2.iterdir()):
                        if not level3.is_dir() or level3.name.startswith("."):
                            continue
                        yield cat_label, workshop_code, level3, level3.name
        else:
            cat_label     = "–"
            workshop_code = extract_workshop_code(level1.name, meta)
            if has_image_files(level1):
                project_name = _short_project_name(level1.name, meta, workshop_code)
                yield cat_label, workshop_code, level1, project_name
            else:
                for level2 in sorted(level1.iterdir()):
                    if not level2.is_dir() or level2.name.startswith("."):
                        continue
                    yield cat_label, workshop_code, level2, level2.name

def _short_project_name(folder_name: str, meta: dict, workshop_code: str) -> str:
    prefix = f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
    if folder_name.startswith(prefix):
        rest = folder_name[len(prefix):].lstrip("_")
        return rest if rest else workshop_code
    return folder_name

# ── Naprawa złych nazw ─────────────────────────────────────────────────────────

def repair_bad_names(root: Path, meta: dict) -> None:
    found_bad = False

    for cat_label, workshop_code, project_dir, project_name in iter_projects(root, meta):
        bad_images = sorted(
            [f for f in project_dir.iterdir()
             if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in IMAGE_EXTENSIONS
             and is_bad_name(f.name, meta)],
            key=lambda f: f.name
        )
        bad_txts = [
            f for f in project_dir.iterdir()
            if f.is_file() and not f.name.startswith(".") and f.suffix.lower() == ".txt"
            and is_bad_name(f.name, meta)
        ]

        if not bad_images and not bad_txts:
            continue

        if not found_bad:
            print("\n━━━  NAPRAWA BŁĘDNYCH NAZW  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            found_bad = True

        print(f"\n  [{cat_label} / {workshop_code}] {project_name}")

        tmp_paths = []
        for img in bad_images:
            tmp = img.with_name(img.name + ".fixing")
            img.rename(tmp)
            tmp_paths.append(tmp)

        for i, tmp in enumerate(tmp_paths, start=1):
            new_path = project_dir / correct_image_name(meta, workshop_code, project_name, i)
            tmp.rename(new_path)
            print(f"    ✓  {new_path.name}")

        for txt in bad_txts:
            new_path = project_dir / correct_inf_name(meta, workshop_code, project_name)
            if not new_path.exists():
                txt.rename(new_path)
                print(f"    ✓  {new_path.name}  (INF naprawiony)")
            else:
                txt.unlink()
                print(f"    ○  Stary INF usunięty (właściwy już istnieje)")

    if not found_bad:
        print("  ✓  Brak plików do naprawy.")

# ── Duże Archiwum ──────────────────────────────────────────────────────────────

def process_large_archive(root: Path, meta: dict) -> None:
    print("\n━━━  DUŻE ARCHIWUM  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for cat_label, workshop_code, project_dir, project_name in iter_projects(root, meta):
        print(f"\n  [{cat_label} / {workshop_code}] {project_name}")

        images = sorted(
            [f for f in project_dir.iterdir()
             if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in IMAGE_EXTENSIONS],
            key=lambda f: f.name
        )

        if not images:
            print("    –  Brak zdjęć do przetworzenia")
        else:
            tmp_paths = []
            for img in images:
                tmp = img.with_name(img.name + ".renaming")
                img.rename(tmp)
                tmp_paths.append(tmp)

            for i, tmp in enumerate(tmp_paths, start=1):
                new_path = project_dir / correct_image_name(meta, workshop_code, project_name, i)
                tmp.rename(new_path)
                print(f"    ✓  {new_path.name}")

        inf_path = project_dir / correct_inf_name(meta, workshop_code, project_name)
        if not inf_path.exists():
            _create_inf_template(inf_path, meta, workshop_code, project_name)
            print(f"    ✓  Utworzono: {inf_path.name}")
        else:
            print(f"    –  {inf_path.name}  (już istnieje)")

def _create_inf_template(path: Path, meta: dict, workshop_code: str, project_name: str) -> None:
    try:
        academic_year = f"{meta['year']}/{int(meta['year']) + 1}"
    except ValueError:
        academic_year = meta["year"]
    content = (
        f"TYTUŁ PRACY:        {project_name}\n"
        f"IMIĘ I NAZWISKO:    [uzupełnij]\n"
        f"NR ALBUMU:          [uzupełnij]\n"
        f"PRACOWNIA:          {workshop_code}  –  [pełna nazwa pracowni]\n"
        f"PROWADZĄCY:         [imię i nazwisko prowadzącego/prowadzącej]\n"
        f"ROK AKADEMICKI:     {academic_year}\n"
        f"ROK / SEMESTR:      {meta['semester']}\n"
        f"OPIS PROJEKTU:\n"
        f"  [Kilka zdań opisu: założenia, materiały, technologia, cel projektu itp.]\n"
    )
    path.write_text(content, encoding="utf-8")

# ── Małe Archiwum ──────────────────────────────────────────────────────────────

def compress_image(src: Path, dst: Path) -> None:
    with Image.open(src) as img:
        # Tuta dodana poprawka EXIF - przed jakimikolwiek konwersjami 
        # nakładamy stałą rotację ze znaczników aparatu
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
        print("\n⚠  Pillow niedostępne – pomijam tworzenie Małego Archiwum.")
        return

    small_root = root.parent / (root.name + "_E")

    if small_root.exists():
        print(f"\n⚠  Folder '{small_root.name}' już istnieje.")
        answer = input("   Nadpisać? [t/N]: ").strip().lower()
        if answer != "t":
            print("   Pomijam tworzenie Małego Archiwum.")
            return
        shutil.rmtree(small_root)

    print(f"\n━━━  MAŁE ARCHIWUM  →  {small_root.name}  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

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
                print(f"    ○  {file_path.name}  (pominięto – wstaw ręcznie klatki/slajdy w _E)")

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
    print(f"  Rozpoznano:  {meta['surname_initial']}  |  rok {meta['year']}  |  semestr {meta['semester']}")

    subdirs = [d for d in root.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not subdirs:
        print("❌  Brak podfolderów.")
        sys.exit(1)

    print("\n  Sprawdzam czy są pliki z błędnymi nazwami...")
    repair_bad_names(root, meta)

    process_large_archive(root, meta)
    create_small_archive(root, meta)

    print("\n✅  Gotowe! Nie zapomnij:")
    print("   1. Uzupełnić pliki _INF.txt w każdym projekcie")
    print("   2. Ręcznie wyciągnąć klatki/slajdy z filmów i prezentacji")
    print("      i wstawić je jako JPEG (dłuższy bok 1080px) do folderów w _E")
    print("   3. Dołączyć oświadczenie o autorstwie")
    print("   4. Wysłać maila na dokumentacja.wwp@asp.waw.pl po link do Google Drive\n")

if __name__ == "__main__":
    main()