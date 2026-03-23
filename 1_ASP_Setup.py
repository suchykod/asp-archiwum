#!/usr/bin/env python3
"""ASP Warszawa – Krok 1: Setup struktury folderów"""

import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pathlib import Path

# ── Paleta – biała z neonową zielenią jak w instrukcji ASP ────────────────────
BG          = "#ffffff"
BG_DARK     = "#111111"
GREEN       = "#00e676"        # neonowa zieleń z dokumentu
GREEN_DARK  = "#00b85c"
BORDER      = "#111111"
TEXT        = "#111111"
TEXT_INV    = "#ffffff"
TEXT_DIM    = "#666666"
TEXT_LOG    = "#111111"
BG_LOG      = "#f5f5f5"
BG_TAG      = GREEN

FONT_TITLE  = ("Helvetica Neue", 28, "bold") if sys.platform == "darwin" else ("Arial", 22, "bold")
FONT_STEP   = ("Helvetica Neue", 20, "bold") if sys.platform == "darwin" else ("Arial", 16, "bold")
FONT_UI     = ("Helvetica Neue", 13)         if sys.platform == "darwin" else ("Arial", 12)
FONT_MONO   = ("Menlo", 10)                  if sys.platform == "darwin" else ("Consolas", 10)
FONT_SUB    = ("Helvetica Neue", 11)         if sys.platform == "darwin" else ("Arial", 10)
FONT_LABEL  = ("Helvetica Neue", 10, "bold") if sys.platform == "darwin" else ("Arial", 9, "bold")

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

def short_project_name(folder_name, meta, workshop_code):
    prefix = f"{meta['surname_initial']}_{workshop_code}_{meta['year']}_{meta['semester']}"
    if folder_name.startswith(prefix):
        rest = folder_name[len(prefix):].lstrip("_")
        return rest if rest else workshop_code
    return folder_name

def create_inf_template(path, meta, workshop_code, project_name):
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

def run_setup(root, log):
    CATEGORIES = {"projektowe", "plastyczne", "inne"}
    SUBFOLDERS  = ["film", "plansze", "rendering", "szkicownik", "zdjecia"]
    meta = parse_root_name(root.name)
    log(f"Folder: {root.name}")
    log(f"Student: {meta['surname_initial']}  |  rok {meta['year']}  |  semestr {meta['semester']}\n")
    found_any = False
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir() or cat_dir.name.startswith("."):
            continue
        if cat_dir.name.lower() not in CATEGORIES:
            continue
        log(f"▸  {cat_dir.name}")
        found_any = True
        for workshop_dir in sorted(cat_dir.iterdir()):
            if not workshop_dir.is_dir() or workshop_dir.name.startswith("."):
                continue
            log(f"   ↳  {workshop_dir.name}")
            for sub in SUBFOLDERS:
                (workshop_dir / sub).mkdir(exist_ok=True)
            log(f"      ✓  {', '.join(SUBFOLDERS)}")
            w_code   = extract_workshop_code(workshop_dir.name, meta)
            proj     = short_project_name(workshop_dir.name, meta, w_code)
            inf_name = (f"{meta['surname_initial']}_{w_code}_{meta['year']}_"
                        f"{meta['semester']}_{proj}_INF.txt")
            inf_path = workshop_dir / inf_name
            if not inf_path.exists():
                create_inf_template(inf_path, meta, w_code, proj)
                log(f"      ✓  {inf_name}")
            else:
                log(f"      –  {inf_name}  (już istnieje)")
    if not found_any:
        log("✗  Nie znaleziono podfolderów Projektowe / Plastyczne / Inne.")
        log("   Upewnij się że wybrałeś właściwy folder główny.")
        return False
    log("\n✓  Gotowe! Możesz teraz wrzucać pliki do podfolderów.")
    log("   Następnie uzupełnij _INF.txt i uruchom  2_ASP_Archiwum.")
    return True

# ── GUI ────────────────────────────────────────────────────────────────────────

class SetupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASP Archiwum – Krok 1")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._selected_path = tk.StringVar(value="")
        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 720, 640
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Top bar – czarna belka z zielonym tagiem ──────────────────────────
        topbar = tk.Frame(self, bg=BG_DARK, height=56)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tag = tk.Label(topbar, text=" KROK 1 ", font=FONT_LABEL,
                       bg=GREEN, fg=BG_DARK, padx=6, pady=3)
        tag.pack(side="left", padx=20, pady=14)

        tk.Label(topbar, text="Archiwizacja projektów  ·  Wydział Wzornictwa ASP",
                 font=FONT_SUB, fg="#aaaaaa", bg=BG_DARK).pack(side="left", padx=4)

        # ── Główny tytuł ──────────────────────────────────────────────────────
        title_frame = tk.Frame(self, bg=BG, pady=0)
        title_frame.pack(fill="x")

        # Zielony pasek po lewej jak w dokumencie
        accent_bar = tk.Frame(title_frame, bg=GREEN, width=8)
        accent_bar.pack(side="left", fill="y")

        title_inner = tk.Frame(title_frame, bg=BG, padx=24, pady=20)
        title_inner.pack(side="left", fill="x", expand=True)

        tk.Label(title_inner, text="Setup struktury\nfolderów",
                 font=FONT_TITLE, fg=TEXT, bg=BG,
                 justify="left").pack(anchor="w")
        tk.Label(title_inner, text="Uruchom po ręcznym stworzeniu głównego folderu i podfolderów pracowni.",
                 font=FONT_SUB, fg=TEXT_DIM, bg=BG, justify="left").pack(anchor="w", pady=(4, 0))

        # ── Separator ─────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=2).pack(fill="x")

        # ── Sekcja: wybór folderu ─────────────────────────────────────────────
        section = tk.Frame(self, bg=BG, padx=32, pady=20)
        section.pack(fill="x")

        tk.Label(section, text="FOLDER GŁÓWNY ARCHIWUM",
                 font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(0, 6))

        pick_row = tk.Frame(section, bg=BG)
        pick_row.pack(fill="x")

        path_box = tk.Frame(pick_row, bg=BG, highlightbackground=BORDER,
                            highlightthickness=2)
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
            relief="flat", padx=18, pady=10, cursor="hand2",
            bd=0, command=self._pick_folder
        ).pack(side="left", padx=(8, 0))

        # ── Sekcja: instrukcja w zielonych ramkach jak w PDF ──────────────────
        tk.Frame(self, bg="#eeeeee", height=1).pack(fill="x", padx=32)

        steps_frame = tk.Frame(self, bg=BG, padx=32, pady=16)
        steps_frame.pack(fill="x")

        tk.Label(steps_frame, text="KOLEJNOŚĆ KROKÓW",
                 font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(0, 8))

        steps = [
            ("1", "Utwórz folder  NazwiskoI_RRRR_SEM  (np. SuchyW_2026_SM1)"),
            ("2", "W środku utwórz podfoldery:  Projektowe  /  Plastyczne  /  Inne"),
            ("3", "W każdej kategorii utwórz foldery pracowni  (np. SuchyW_JK_2026_SM1)"),
            ("4", "Wybierz folder główny (NazwiskoI_RRRR_SEM) powyżej i kliknij  Uruchom Setup"),
        ]
        for num, text in steps:
            row = tk.Frame(steps_frame, bg=BG, pady=3)
            row.pack(fill="x")
            tk.Label(row, text=f" {num} ", font=FONT_LABEL,
                     bg=GREEN, fg=BG_DARK, padx=6, pady=3).pack(side="left")
            tk.Label(row, text=f"  {text}", font=FONT_SUB,
                     fg=TEXT, bg=BG, anchor="w").pack(side="left")

        # ── Przycisk ──────────────────────────────────────────────────────────
        tk.Frame(self, bg="#eeeeee", height=1).pack(fill="x", padx=32)

        btn_frame = tk.Frame(self, bg=BG, padx=32, pady=16)
        btn_frame.pack(fill="x")

        self._run_btn = tk.Button(
            btn_frame, text="▶   Uruchom Setup",
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

        log_frame = tk.Frame(self, bg=BG, padx=32, pady=(4, 24))
        log_frame.pack(fill="both", expand=True)

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
        self._run_btn.config(state="disabled", text="⏳  Trwa setup…")
        def worker():
            try:
                run_setup(root, self._log)
            finally:
                self.after(0, lambda: self._run_btn.config(
                    state="normal", text="▶   Uruchom Setup"))
        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = SetupApp()
    app.mainloop()