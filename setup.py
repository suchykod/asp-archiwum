#!/usr/bin/env python3
import sys
import re
from pathlib import Path

def parse_root_name(root_name: str) -> dict:
    parts = root_name.split("_")
    if len(parts) < 3:
        return {"surname_initial": root_name, "year": "????", "semester": "?"}
    return {"surname_initial": parts[0], "year": parts[1], "semester": parts[2]}

def extract_workshop_code(folder_name: str, meta: dict) -> str:
    pattern = rf"^{re.escape(meta['surname_initial'])}_([A-Za-z0-9]+)_"
    m = re.match(pattern, folder_name)
    return m.group(1).upper() if m else folder_name.upper()

def _short_project_name(folder_name: str, meta: dict, workshop_code: str) -> str:
    prefix = f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
    if folder_name.startswith(prefix):
        rest = folder_name[len(prefix):].lstrip("_")
        return rest if rest else workshop_code
    return folder_name

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

def main():
    base_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    
    # Automatyczne wykrywanie, czy skrypt odpalono jeden poziom za wysoko (np. w "sem1 copy 2")
    root = base_path
    if not any(d.name.lower() in {"projektowe", "plastyczne", "inne"} for d in base_path.iterdir() if d.is_dir()):
        # Szukamy folderu z Dużym Archiwum (np. SuchyW_2026_SM1) w środku
        possible_roots = [d for d in base_path.iterdir() if d.is_dir() and "_" in d.name and not d.name.endswith("_E")]
        if possible_roots:
            root = possible_roots[0]
            print(f"👉 Wykryto, że jesteś poziom wyżej. Zmieniam folder roboczy na: {root.name}\n")
        else:
            print(f"❌ Nie znaleziono głównych folderów (Projektowe / Plastyczne / Inne) w: {base_path}")
            sys.exit(1)

    print(f"Tworzę podfoldery robocze w GŁÓWNYM ARCHIWUM: {root.name}\n")
    meta = parse_root_name(root.name)
    
    categories = {"projektowe", "plastyczne", "inne"}
    found_any = False

    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue

        if cat_dir.name.lower() in categories:
            print(f"📂 Znaleziono kategorię: {cat_dir.name}")
            found_any = True
            
            for workshop_dir in sorted(cat_dir.iterdir()):
                if not workshop_dir.is_dir() or workshop_dir.name.startswith("."):
                    continue

                print(f"  ↳ Pracownia: {workshop_dir.name}")
                
                # Tworzenie podfolderów
                for sub in ["film", "plansze", "rendering", "szkicownik", "zdjecia"]:
                    (workshop_dir / sub).mkdir(exist_ok=True)
                
                print("    ✓ utworzono podfoldery: film, plansze, rendering, szkicownik, zdjecia")

                # Generowanie pliku INF
                w_code = extract_workshop_code(workshop_dir.name, meta)
                proj_name = _short_project_name(workshop_dir.name, meta, w_code)
                
                inf_name = f"{meta['surname_initial']}_{w_code}_{meta['year']}_{meta['semester']}_{proj_name}_INF.txt"
                inf_path = workshop_dir / inf_name
                
                if not inf_path.exists():
                    _create_inf_template(inf_path, meta, w_code, proj_name)
                    print(f"    ✓ wygenerowano plik {inf_name}")
                else:
                    print(f"    – plik {inf_name} już istnieje")

    if not found_any:
        print("\n❌ Skrypt nie znalazł żadnej głównej kategorii (Projektowe/Plastyczne/Inne).")
    else:
        print("\n✅ Gotowe! Możesz teraz wrzucać pliki do odpowiednich podfolderów roboczych.")

if __name__ == "__main__":
    main()