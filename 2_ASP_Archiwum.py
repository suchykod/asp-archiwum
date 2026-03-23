#!/usr/bin/env python3
"""ASP Warszawa – Krok 2: Archiwizacja"""

import re
import sys
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pathlib import Path

try:
    from PIL import Image, ImageOps # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

BG          = "#1a1a1a"
BG_CARD     = "#242424"
BG_INPUT    = "#2e2e2e"
ACCENT      = "#00c896"
ACCENT2     = "#5b8cff"
ACCENT2_DIM = "#3a6bdd"
TEXT        = "#f0f0f0"
TEXT_DIM    = "#888888"
TEXT_LOG    = "#d4d4d4"
FONT_UI     = ("Helvetica Neue", 13)
FONT_MONO   = ("Menlo", 11) if sys.platform == "darwin" else ("Consolas", 10)
FONT_TITLE  = ("Helvetica Neue", 22, "bold")
FONT_SUB    = ("Helvetica Neue", 11)

IMAGE_EXTENSIONS   = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
CATEGORY_FOLDERS   = {"projektowe", "plastyczne", "inne"}
SMALL_ARCHIVE_LONG = 1080
JPEG_QUALITY       = 60
SUFFIX_MAP = {
    "zdjecia": "M", "plansze": "P", "rendering": "R",
    "film": "F", "szkicownik": "S",
}

# ── Logika ─────────────────────────────────────────────────────────────────────

def parse_root_name(root_name):
    parts = root_name.split("_")
    if len(parts) < 3:
        return {"surname_initial": root_name, "year": "????", "semester": "?"}
    return {"surname_initial": parts[0], "year": parts[1], "semester": parts[2]}

def extract_workshop_code(folder_name, meta):
    pattern = rf"^{re.escape(meta['surname_initial'])}_([A-Za-z0-9]+)_"
    m = re.match(pattern, folder_name)
    return m.group(1).upper() if m else folder_name.upper()

def sanitize(name):
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()

def get_next_index(directory, suffix):
    pattern = re.compile(rf"_{suffix}(\d+)\.[a-zA-Z0-9]+$")
    max_idx = 0
    for f in directory.iterdir():
        if f.is_file():
            m = pattern.search(f.name)
            if m:
                max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1

def iter_projects(root, meta):
    for level1 in sorted(root.iterdir()):
        if not level1.is_dir() or level1.name.startswith("."):
            continue
        if level1.name.lower() not in CATEGORY_FOLDERS:
            continue
        for level2 in sorted(level1.iterdir()):
            if not level2.is_dir() or level2.name.startswith("."):
                continue
            workshop_code = extract_workshop_code(level2.name, meta)
            prefix = f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
            rest = level2.name[len(prefix):].lstrip("_")
            yield level1.name, workshop_code, level2, (rest if rest else workshop_code)

def process_large_archive(root, meta, log):
    log("━━━  DUŻE ARCHIWUM  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    for cat_label, workshop_code, project_dir, project_name in iter_projects(root, meta):
        log(f"\n  [{cat_label} / {workshop_code}] {project_name}")
        for folder_name, suffix_code in SUFFIX_MAP.items():
            sub_dir = project_dir / folder_name
            if not sub_dir.is_dir():
                continue
            files = sorted([f for f in sub_dir.iterdir()
                            if f.is_file() and not f.name.startswith(".")])
            for file_path in files:
                if file_path.suffix.lower() == ".txt":
                    continue
                idx = get_next_index(project_dir, suffix_code)
                new_name = (
                    f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
                    f"_{sanitize(project_name)}_{suffix_code}{idx:02d}{file_path.suffix.lower()}"
                )
                file_path.rename(project_dir / new_name)
                log(f"    ✓  {folder_name}/{file_path.name}  →  {new_name}")
            try:
                for hidden in sub_dir.rglob(".*"):
                    hidden.unlink()
                sub_dir.rmdir()
                log(f"    🗑  Usunięto pusty folder: {folder_name}/")
            except OSError:
                log(f"    ⚠  Folder '{folder_name}/' nie jest pusty – sprawdź ręcznie.")

def compress_image(src, dst):
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        w, h = img.size
        long_side = max(w, h)
        if long_side > SMALL_ARCHIVE_LONG:
            scale = SMALL_ARCHIVE_LONG / long_side
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        img.save(dst, format="JPEG", quality=JPEG_QUALITY, optimize=True)

def create_small_archive(root, meta, log):
    if not PIL_AVAILABLE:
        log("\n⚠  Pillow niedostępne – pomijam Małe Archiwum.")
        log("   Zainstaluj:  pip install Pillow")
        return
    small_root = root.parent / (root.name + "_E")
    if small_root.exists():
        shutil.rmtree(small_root)
    log(f"\n━━━  MAŁE ARCHIWUM  →  {small_root.name}  ━━━━━━━━━━━━━━━━━━━━━━━━")
    for cat in ["Projektowe", "Plastyczne", "Inne"]:
        (small_root / cat).mkdir(parents=True, exist_ok=True)
    for cat_label, workshop_code, project_dir, project_name in iter_projects(root, meta):
        log(f"\n  [{cat_label} / {workshop_code}] {project_name}")
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
                    log(f"    ✓  {file_path.name}  ({orig_kb} KB → {small_kb} KB)")
                except Exception as e:
                    log(f"    ❌  {file_path.name}  – błąd: {e}")
            elif file_path.suffix.lower() == ".txt":
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dst)
                log(f"    –  {file_path.name}  (INF skopiowany)")
            else:
                log(f"    ○  {file_path.name}  (pominięto – dodaj klatki/slajdy ręcznie do _E)")
    log(f"\n  ✅  Małe Archiwum gotowe: {small_root.name}")

def run_archive(root, log):
    if root.name.endswith("_E"):
        log("❌  To jest folder Małego Archiwum. Wybierz Duże Archiwum (bez _E).")
        return
    meta = parse_root_name(root.name)
    log(f"Folder: {root.name}")
    log(f"Student: {meta['surname_initial']}  |  rok {meta['year']}  |  semestr {meta['semester']}\n")
    process_large_archive(root, meta, log)
    create_small_archive(root, meta, log)
    log("\n✅  Gotowe! Nie zapomnij:")
    log("   1. Sprawdzić i uzupełnić pliki _INF.txt")
    log("   2. Ręcznie dodać klatki/slajdy z filmów i prezentacji do _E")
    log("   3. Dołączyć oświadczenie o autorstwie")
    log("   4. Wysłać maila na dokumentacja.wwp@asp.waw.pl po link do Google Drive")

# ── GUI ────────────────────────────────────────────────────────────────────────

class ArchiveApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASP Archiwum – Krok 2: Archiwizacja")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._selected_path = tk.StringVar(value="")
        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 700, 620
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, pady=20)
        header.pack(fill="x", padx=32)
        tk.Label(header, text="ASP Warszawa", font=FONT_TITLE,
                 fg=ACCENT2, bg=BG).pack(anchor="w")
        tk.Label(header, text="Krok 2 z 2  ·  Archiwizacja i kompresja",
                 font=FONT_SUB, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=BG_INPUT, height=1).pack(fill="x", padx=32)

        # ── Wybór folderu ─────────────────────────────────────────────────────
        pick_frame = tk.Frame(self, bg=BG, pady=16)
        pick_frame.pack(fill="x", padx=32)
        tk.Label(pick_frame, text="Folder główny archiwum (np. SuchyW_2026_SM1):",
                 font=FONT_UI, fg=TEXT, bg=BG).pack(anchor="w")
        row = tk.Frame(pick_frame, bg=BG, pady=6)
        row.pack(fill="x")
        self._path_label = tk.Label(
            row, textvariable=self._selected_path,
            font=FONT_MONO, fg=TEXT_DIM, bg=BG_INPUT,
            anchor="w", padx=12, pady=8, relief="flat"
        )
        self._path_label.pack(side="left", fill="x", expand=True, ipady=2)
        tk.Button(
            row, text="Wybierz…", font=FONT_UI,
            bg=BG_INPUT, fg=TEXT, activebackground=BG_CARD, activeforeground=ACCENT2,
            relief="flat", padx=16, cursor="hand2",
            command=self._pick_folder
        ).pack(side="left", padx=(8, 0))

        # ── Checklist ─────────────────────────────────────────────────────────
        info = tk.Frame(self, bg=BG_CARD, padx=16, pady=12)
        info.pack(fill="x", padx=32)
        tk.Label(info, text="Przed uruchomieniem upewnij się że:",
                 font=("Helvetica Neue", 11, "bold"), fg=TEXT, bg=BG_CARD).pack(anchor="w", pady=(0, 4))
        checks = [
            "✓  Uruchomiłeś/aś już  1_ASP_Setup  i uzupełniłeś/aś pliki _INF.txt",
            "✓  Pliki są w podfolderach (zdjecia / plansze / film / rendering / szkicownik)",
            "✓  Folder główny NIE ma na końcu  _E",
        ]
        for c in checks:
            tk.Label(info, text=c, font=FONT_SUB, fg=TEXT_DIM,
                     bg=BG_CARD, anchor="w").pack(anchor="w", pady=1)

        # ── Pillow status ──────────────────────────────────────────────────────
        pil_color = ACCENT if PIL_AVAILABLE else "#e05555"
        pil_text  = "● Pillow zainstalowane" if PIL_AVAILABLE else "● Pillow NIE jest zainstalowane  →  pip install Pillow"
        tk.Label(self, text=pil_text, font=FONT_SUB, fg=pil_color,
                 bg=BG).pack(anchor="w", padx=32, pady=(10, 0))

        # ── Przycisk (nad logiem – zawsze widoczny) ───────────────────────────
        btn_frame = tk.Frame(self, bg=BG, pady=14)
        btn_frame.pack(fill="x", padx=32)
        self._run_btn = tk.Button(
            btn_frame, text="▶   Uruchom Archiwizację",
            font=("Helvetica Neue", 14, "bold"),
            bg=ACCENT2, fg=BG, activebackground=ACCENT2_DIM, activeforeground=BG,
            relief="flat", padx=24, pady=10, cursor="hand2",
            command=self._run
        )
        self._run_btn.pack(side="right")

        # ── Log (na dole, rozciąga się) ───────────────────────────────────────
        tk.Label(self, text="Log:", font=FONT_SUB, fg=TEXT_DIM,
                 bg=BG).pack(anchor="w", padx=32)
        self._log_box = scrolledtext.ScrolledText(
            self, font=FONT_MONO, bg=BG_CARD, fg=TEXT_LOG,
            relief="flat", padx=12, pady=10,
            insertbackground=ACCENT2, state="disabled",
            wrap="word"
        )
        self._log_box.pack(fill="both", expand=True, padx=32, pady=(4, 20))

    def _pick_folder(self):
        path = filedialog.askdirectory(title="Wybierz folder główny archiwum")
        if path:
            self._selected_path.set(path)
            self._path_label.config(fg=TEXT)

    def _log(self, msg):
        self._log_box.config(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")

    def _run(self):
        path_str = self._selected_path.get()
        if not path_str:
            self._log("⚠  Najpierw wybierz folder.")
            return
        root = Path(path_str)
        if not root.is_dir():
            self._log("❌  Wybrany folder nie istnieje.")
            return
        self._clear_log()
        self._run_btn.config(state="disabled", text="⏳  Trwa archiwizacja…")
        def worker():
            try:
                run_archive(root, self._log)
            finally:
                self.after(0, lambda: self._run_btn.config(
                    state="normal", text="▶   Uruchom Archiwizację"))
        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = ArchiveApp()
    app.mainloop()