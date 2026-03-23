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

# ── Paleta – jak instrukcja ASP: biała + neonowa zieleń ──────────────────────
BG          = "#ffffff"
BG_DARK     = "#111111"
GREEN       = "#00e676"
GREEN_DARK  = "#00b85c"
BORDER      = "#111111"
TEXT        = "#111111"
TEXT_INV    = "#ffffff"
TEXT_DIM    = "#666666"
TEXT_LOG    = "#111111"
BG_LOG      = "#f5f5f5"

FONT_TITLE  = ("Helvetica Neue", 28, "bold") if sys.platform == "darwin" else ("Arial", 22, "bold")
FONT_UI     = ("Helvetica Neue", 13)         if sys.platform == "darwin" else ("Arial", 12)
FONT_MONO   = ("Menlo", 10)                  if sys.platform == "darwin" else ("Consolas", 10)
FONT_SUB    = ("Helvetica Neue", 11)         if sys.platform == "darwin" else ("Arial", 10)
FONT_LABEL  = ("Helvetica Neue", 10, "bold") if sys.platform == "darwin" else ("Arial", 9, "bold")

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
    log("━━  DUŻE ARCHIWUM  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
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
                log(f"    ✗  Usunięto pusty folder: {folder_name}/")
            except OSError:
                log(f"    ⚠  Folder '{folder_name}/' nie jest pusty.")

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
        return
    small_root = root.parent / (root.name + "_E")
    if small_root.exists():
        shutil.rmtree(small_root)
    log(f"\n━━  MAŁE ARCHIWUM  →  {small_root.name}  ━━━━━━━━━━━━━━━━━━━━━━━━")
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
                    log(f"    ✗  {file_path.name}  – błąd: {e}")
            elif file_path.suffix.lower() == ".txt":
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dst)
                log(f"    –  {file_path.name}  (INF skopiowany)")
            else:
                log(f"    ○  {file_path.name}  (pominięto – dodaj klatki/slajdy ręcznie)")
    log(f"\n  ✓  Małe Archiwum gotowe: {small_root.name}")

def run_archive(root, log):
    if root.name.endswith("_E"):
        log("✗  To jest folder Małego Archiwum. Wybierz Duże Archiwum (bez _E).")
        return
    meta = parse_root_name(root.name)
    log(f"Folder: {root.name}")
    log(f"Student: {meta['surname_initial']}  |  rok {meta['year']}  |  semestr {meta['semester']}\n")
    process_large_archive(root, meta, log)
    create_small_archive(root, meta, log)
    log("\n✓  Gotowe! Nie zapomnij:")
    log("   1. Sprawdzić i uzupełnić pliki _INF.txt")
    log("   2. Ręcznie dodać klatki z filmów / slajdy z prezentacji do _E")
    log("   3. Dołączyć oświadczenie o autorstwie")
    log("   4. Wysłać maila na dokumentacja.wwp@asp.waw.pl po link do Drive")

# ── GUI ────────────────────────────────────────────────────────────────────────

class ArchiveApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASP Archiwum – Krok 2")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._selected_path = tk.StringVar(value="")
        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 720, 680
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Top bar ───────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=BG_DARK, height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(topbar, text=" KROK 2 ", font=FONT_LABEL,
                 bg=GREEN, fg=BG_DARK, padx=6, pady=3).pack(side="left", padx=20, pady=14)
        tk.Label(topbar, text="Archiwizacja projektów  ·  Wydział Wzornictwa ASP",
                 font=FONT_SUB, fg="#aaaaaa", bg=BG_DARK).pack(side="left", padx=4)

        # ── Pillow status w topbarze ───────────────────────────────────────────
        pil_text  = "● Pillow OK" if PIL_AVAILABLE else "● Pillow BRAK  →  pip install Pillow"
        pil_color = GREEN if PIL_AVAILABLE else "#ff5252"
        tk.Label(topbar, text=pil_text, font=FONT_LABEL,
                 fg=pil_color, bg=BG_DARK).pack(side="right", padx=20)

        # ── Tytuł z zielonym paskiem ──────────────────────────────────────────
        title_frame = tk.Frame(self, bg=BG)
        title_frame.pack(fill="x")

        tk.Frame(title_frame, bg=GREEN, width=8).pack(side="left", fill="y")

        title_inner = tk.Frame(title_frame, bg=BG, padx=24, pady=20)
        title_inner.pack(side="left", fill="x", expand=True)

        tk.Label(title_inner, text="Archiwizacja\ni kompresja",
                 font=FONT_TITLE, fg=TEXT, bg=BG,
                 justify="left").pack(anchor="w")
        tk.Label(title_inner,
                 text="Uruchom po uzupełnieniu _INF.txt i wrzuceniu plików do podfolderów.",
                 font=FONT_SUB, fg=TEXT_DIM, bg=BG, justify="left").pack(anchor="w", pady=(4, 0))

        tk.Frame(self, bg=BORDER, height=2).pack(fill="x")

        # ── Wybór folderu ─────────────────────────────────────────────────────
        section = tk.Frame(self, bg=BG, padx=32, pady=20)
        section.pack(fill="x")

        tk.Label(section, text="FOLDER GŁÓWNY ARCHIWUM",
                 font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(0, 6))

        pick_row = tk.Frame(section, bg=BG)
        pick_row.pack(fill="x")

        path_box = tk.Frame(pick_row, bg=BG, highlightbackground=BORDER, highlightthickness=2)
        path_box.pack(side="left", fill="x", expand=True)

        self._path_label = tk.Label(
            path_box, textvariable=self._selected_path,
            font=FONT_MONO, fg=TEXT_DIM, bg=BG,
            anchor="w", padx=12, pady=10
        )
        self._path_label.pack(fill="x")

        tk.Button(
            pick_row, text="Wybierz…",
            font=FONT_UI, bg=BG_DARK, fg=TEXT_INV,
            activebackground="#333333", activeforeground=TEXT_INV,
            relief="flat", padx=18, pady=10, cursor="hand2", bd=0,
            command=self._pick_folder
        ).pack(side="left", padx=(8, 0))

        # ── Checklist ─────────────────────────────────────────────────────────
        tk.Frame(self, bg="#eeeeee", height=1).pack(fill="x", padx=32)

        checks_frame = tk.Frame(self, bg=BG, padx=32, pady=14)
        checks_frame.pack(fill="x")

        tk.Label(checks_frame, text="PRZED URUCHOMIENIEM",
                 font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(0, 6))

        checks = [
            "✓   Uruchomiłeś/aś  1_ASP_Setup  i uzupełniłeś/aś pliki _INF.txt",
            "✓   Pliki są w podfolderach:  zdjecia / plansze / film / rendering / szkicownik",
            "✓   Folder główny NIE kończy się na  _E",
        ]
        for c in checks:
            row = tk.Frame(checks_frame, bg=BG, pady=2)
            row.pack(fill="x")
            tk.Label(row, text=" ✓ ", font=FONT_LABEL,
                     bg=GREEN, fg=BG_DARK, padx=4, pady=2).pack(side="left")
            tk.Label(row, text=f"  {c[4:]}", font=FONT_SUB,
                     fg=TEXT, bg=BG).pack(side="left")

        # ── Przycisk ──────────────────────────────────────────────────────────
        tk.Frame(self, bg="#eeeeee", height=1).pack(fill="x", padx=32)

        btn_frame = tk.Frame(self, bg=BG, padx=32, pady=16)
        btn_frame.pack(fill="x")

        self._run_btn = tk.Button(
            btn_frame, text="▶   Uruchom Archiwizację",
            font=("Helvetica Neue", 14, "bold") if sys.platform == "darwin" else ("Arial", 12, "bold"),
            bg=GREEN, fg=BG_DARK,
            activebackground=GREEN_DARK, activeforeground=BG_DARK,
            relief="flat", padx=28, pady=12, cursor="hand2", bd=0,
            command=self._run
        )
        self._run_btn.pack(side="right")

        # ── Log ───────────────────────────────────────────────────────────────
        tk.Label(self, text="LOG", font=FONT_LABEL, fg=TEXT_DIM,
                 bg=BG).pack(anchor="w", padx=32)

        # POPRAWKA: Usunięto pady stąd, a dodano je poniżej do pack()
        log_frame = tk.Frame(self, bg=BG, padx=32)
        log_frame.pack(fill="both", expand=True, pady=(4, 24))

        self._log_box = scrolledtext.ScrolledText(
            log_frame, font=FONT_MONO, bg=BG_LOG, fg=TEXT_LOG,
            relief="flat", padx=12, pady=10,
            insertbackground=GREEN, state="disabled",
            wrap="word",
            highlightbackground=BORDER, highlightthickness=1
        )
        self._log_box.pack(fill="both", expand=True)

        # ── Stopka ────────────────────────────────────────────────────────────
        tk.Label(
            self, 
            text="autor: Wiktor Suchy", 
            font=FONT_SUB, 
            fg=TEXT_DIM, 
            bg=BG
        ).place(relx=1.0, rely=1.0, anchor="se", x=-16, y=-8)

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
            self._log("✗  Wybrany folder nie istnieje.")
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