#!/usr/bin/env python3
"""ASP Warszawa – Krok 1: Setup struktury folderów"""

import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
from pathlib import Path

BG         = "#1a1a1a"
BG_CARD    = "#242424"
BG_INPUT   = "#2e2e2e"
ACCENT     = "#00c896"
ACCENT_DIM = "#008f6a"
TEXT       = "#f0f0f0"
TEXT_DIM   = "#888888"
TEXT_LOG   = "#d4d4d4"
FONT_UI    = ("Helvetica Neue", 13)
FONT_MONO  = ("Menlo", 11) if sys.platform == "darwin" else ("Consolas", 10)
FONT_TITLE = ("Helvetica Neue", 22, "bold")
FONT_SUB   = ("Helvetica Neue", 11)

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
        log(f"📂  {cat_dir.name}")
        found_any = True
        for workshop_dir in sorted(cat_dir.iterdir()):
            if not workshop_dir.is_dir() or workshop_dir.name.startswith("."):
                continue
            log(f"    ↳  {workshop_dir.name}")
            for sub in SUBFOLDERS:
                (workshop_dir / sub).mkdir(exist_ok=True)
            log(f"       ✓  podfoldery: {', '.join(SUBFOLDERS)}")
            w_code   = extract_workshop_code(workshop_dir.name, meta)
            proj     = short_project_name(workshop_dir.name, meta, w_code)
            inf_name = (f"{meta['surname_initial']}_{w_code}_{meta['year']}_"
                        f"{meta['semester']}_{proj}_INF.txt")
            inf_path = workshop_dir / inf_name
            if not inf_path.exists():
                create_inf_template(inf_path, meta, w_code, proj)
                log(f"       ✓  {inf_name}")
            else:
                log(f"       –  {inf_name}  (już istnieje)")
    if not found_any:
        log("❌  Nie znaleziono podfolderów Projektowe / Plastyczne / Inne.")
        log("    Upewnij się że wybrałeś właściwy folder główny.")
        return False
    log("\n✅  Gotowe! Możesz teraz wrzucać pliki do podfolderów.")
    log("    Następnie uzupełnij _INF.txt i uruchom  2_ASP_Archiwum.")
    return True

# ── GUI ────────────────────────────────────────────────────────────────────────

class SetupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASP Archiwum – Krok 1: Setup")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._selected_path = tk.StringVar(value="")
        self._build_ui()
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = 700, 600
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, pady=20)
        header.pack(fill="x", padx=32)
        tk.Label(header, text="ASP Warszawa", font=FONT_TITLE,
                 fg=ACCENT, bg=BG).pack(anchor="w")
        tk.Label(header, text="Krok 1 z 2  ·  Przygotowanie struktury folderów",
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
            bg=BG_INPUT, fg=TEXT, activebackground=BG_CARD, activeforeground=ACCENT,
            relief="flat", padx=16, cursor="hand2",
            command=self._pick_folder
        ).pack(side="left", padx=(8, 0))

        # ── Instrukcja ────────────────────────────────────────────────────────
        info = tk.Frame(self, bg=BG_CARD, padx=16, pady=12)
        info.pack(fill="x", padx=32)
        steps = [
            "1.  Utwórz folder  NazwiskoI_RRRR_SEM  (np. SuchyW_2026_SM1)",
            "2.  W środku utwórz podfoldery:  Projektowe  /  Plastyczne  /  Inne",
            "3.  W każdej kategorii utwórz foldery pracowni  (np. SuchyW_JK_2026_SM1)",
            "4.  Wybierz folder główny (NazwiskoI_RRRR_SEM) powyżej i kliknij  Uruchom Setup",
        ]
        for s in steps:
            tk.Label(info, text=s, font=FONT_SUB, fg=TEXT_DIM,
                     bg=BG_CARD, anchor="w").pack(anchor="w", pady=1)

        # ── Przycisk (nad logiem – zawsze widoczny) ───────────────────────────
        btn_frame = tk.Frame(self, bg=BG, pady=14)
        btn_frame.pack(fill="x", padx=32)
        self._run_btn = tk.Button(
            btn_frame, text="▶   Uruchom Setup",
            font=("Helvetica Neue", 14, "bold"),
            bg=ACCENT, fg=BG, activebackground=ACCENT_DIM, activeforeground=BG,
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
            insertbackground=ACCENT, state="disabled",
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