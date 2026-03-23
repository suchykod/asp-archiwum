#!/usr/bin/env python3
import sys
from pathlib import Path

def clean_directory(root_dir: str):
    root = Path(root_dir).resolve()
    
    if not root.is_dir():
        print(f"❌ Folder nie istnieje: {root}")
        sys.exit(1)

    print(f"Rozpoczynam sprzątanie w: {root}\n")
    renamed_count = 0
    mac_junk_count = 0

    # 1. Przywracanie plików .renaming i .fixing do ich rozszerzeń bazowych
    for ext in ["*.renaming", "*.fixing"]:
        for p in root.rglob(ext):
            new_path = p.with_suffix('') # ucina ostatnie rozszerzenie (.renaming)
            p.rename(new_path)
            print(f"  ✓ Przywrócono: {new_path.name}")
            renamed_count += 1

    # 2. Usuwanie ukrytych plików systemowych macOS (zaczynających się od ._)
    for p in root.rglob("._*"):
        try:
            p.unlink()
            mac_junk_count += 1
        except Exception as e:
            print(f"  ⚠ Nie udało się usunąć {p.name}: {e}")

    print("\n━━━ PODSUMOWANIE ━━━")
    print(f"Naprawione pliki ze złymi rozszerzeniami: {renamed_count}")
    print(f"Usunięte śmieci systemowe macOS (._*): {mac_junk_count}")
    print("✅ Gotowe. Możesz teraz uruchomić główny skrypt.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    clean_directory(target)