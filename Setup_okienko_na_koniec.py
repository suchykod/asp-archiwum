#!/usr/bin/env python3
"""ASP Warszawa – Krok 1: Setup struktury (Wariant B - Popup)"""

import csv
import re
import sys
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from pathlib import Path

# ── Paleta ────────────────────────────────────────────────────────────────────
BG         = "#ffffff"
BG_DARK    = "#111111"
GREEN      = "#00e676"
GREEN_DARK = "#00b85c"
BORDER     = "#111111"
TEXT       = "#111111"
TEXT_INV   = "#ffffff"
TEXT_DIM   = "#666666"
BG_LOG     = "#f5f5f5"
BG_INPUT   = "#f9f9f9"

IS_MAC     = sys.platform == "darwin"
FONT_TITLE = ("Helvetica Neue", 24, "bold") if IS_MAC else ("Arial", 18, "bold")
FONT_UI    = ("Helvetica Neue", 13)         if IS_MAC else ("Arial", 12)
FONT_MONO  = ("Menlo", 10)                  if IS_MAC else ("Consolas", 10)
FONT_SUB   = ("Helvetica Neue", 11)         if IS_MAC else ("Arial", 10)
FONT_LABEL = ("Helvetica Neue", 10, "bold") if IS_MAC else ("Arial", 9, "bold")
FONT_SMALL = ("Helvetica Neue", 9)          if IS_MAC else ("Arial", 8)

KIERUNKI = {
    "PPP": "Projektowanie produktu, przestrzeni, przekazu",
    "PU":  "Projektowanie ubioru i jego konteksty",
    "PIB": "Projektowanie i badania (mgr)",
}
SEMESTRY = {
    "PPP": ["1", "2", "3", "4", "5", "6", "L"],
    "PU":  ["1", "2", "3", "4", "5", "6", "L"],
    "PIB": ["SM1", "SM2", "SM3", "M"],
}
KATEGORIE_ORDER = ["Projektowe", "Plastyczne", "Inne"]
SUBFOLDERS = ["film", "plansze", "rendering", "szkicownik", "zdjecia"]

def load_csv(csv_path: Path) -> list[dict]:
    rows = []
    if not csv_path.exists(): return rows
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader: rows.append(row)
    return rows

def get_pracownie(db: list[dict], kierunek: str, semestr: str) -> list[dict]:
    return [r for r in db if r["kierunek"] == kierunek and r["semestr"] == semestr]

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()

def create_inf_template(path: Path, meta: dict, workshop_code: str,
                        nazwa: str, prowadzacy: str, title: str) -> None:
    try:
        year_int = int(meta["year"])
        academic_year = f"{year_int}/{year_int + 1}"
    except ValueError:
        academic_year = meta["year"]

    display_title = title if title else "[uzupełnij – nazwa projektu]"
    content = (
        f"TYTUŁ PRACY:        {display_title}\n"
        f"IMIĘ I NAZWISKO:    {meta['full_name']}\n"
        f"NR ALBUMU:          {meta['album']}\n"
        f"PRACOWNIA:          {workshop_code}  –  {nazwa}\n"
        f"PROWADZĄCY:         {prowadzacy}\n"
        f"ROK AKADEMICKI:     {academic_year}\n"
        f"ROK / SEMESTR:      {meta['semester']}\n"
        f"OPIS PROJEKTU:\n"
        f"  [Kilka zdań opisu: założenia, materiały, technologia, cel projektu itp.]\n"
    )
    path.write_text(content, encoding="utf-8")

def build_structure(root_dir: Path, parent_dir: Path, meta: dict,
                    selected: list[dict], projects_dict: dict, log) -> None:
    si   = meta["surname_initial"]
    year = meta["year"]
    sem  = meta["semester"]

    root = parent_dir / f"{si}_{year}_{sem}"
    root.mkdir(parents=True, exist_ok=True)
    log(f"✓  Folder główny: {root.name}\n")

    by_cat = {k: [] for k in KATEGORIE_ORDER}
    for p in selected:
        cat = p["kategoria"]
        if cat in by_cat: by_cat[cat].append(p)

    def _create_folders(base_dir, code, nazwa, prow, title):
        for sub in SUBFOLDERS:
            sub_path = base_dir / sub
            sub_path.mkdir(exist_ok=True)
            if sub == "film":
                (sub_path / "stopklatki").mkdir(exist_ok=True)
        inf_name = f"{si}_{code}_{year}_{sem}_INF.txt"
        create_inf_template(base_dir / inf_name, meta, code, nazwa, prow, title)

    for cat in KATEGORIE_ORDER:
        pracownie = by_cat.get(cat, [])
        if not pracownie: continue
        cat_dir = root / cat
        cat_dir.mkdir(exist_ok=True)
        log(f"▸  {cat}/")

        for p in pracownie:
            code  = p["kod_pracowni"]
            nazwa = p["nazwa_przedmiotu"]
            prow  = p["prowadzacy"]
            w_dir = cat_dir / f"{si}_{code}_{year}_{sem}"
            w_dir.mkdir(exist_ok=True)

            titles = [t.strip() for t in projects_dict.get(code, []) if t.strip()]

            if len(titles) <= 1:
                title = titles[0] if titles else ""
                _create_folders(w_dir, code, nazwa, prow, title)
                log(f"   ↳  {w_dir.name}/  ✓  INF.txt")
            else:
                log(f"   ↳  {w_dir.name}/  (Wiele projektów)")
                for idx, title in enumerate(titles):
                    safe_title = sanitize_filename(title) or f"Projekt_{idx+1}"
                    p_dir = w_dir / safe_title
                    p_dir.mkdir(exist_ok=True)
                    _create_folders(p_dir, code, nazwa, prow, title)
                    log(f"      ↳  {safe_title}/  ✓  INF.txt")

    log(f"\n✓  Struktura gotowa w: {root}")
    log("   Dodaj zrzuty do /film/stopklatki, uzupełnij OPIS PROJEKTU w plikach _INF.txt")

class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ASP Archiwum – Krok 1 (Wariant B)")
        self.configure(bg=BG)
        self.resizable(True, True)

        script_dir = Path(sys.argv[0]).resolve().parent
        self._db = load_csv(script_dir / "asp_pracownie.csv")
        if not self._db: self._db = load_csv(Path.cwd() / "asp_pracownie.csv")

        self._kierunek_var  = tk.StringVar(value="PPP")
        self._semestr_var   = tk.StringVar(value="1")
        self._surname_var   = tk.StringVar()
        self._initial_var   = tk.StringVar()
        self._fullname_var  = tk.StringVar()
        self._album_var     = tk.StringVar()
        self._year_var      = tk.StringVar(value="2026")
        self._location_var  = tk.StringVar()

        self._check_vars = {} 
        self._build_ui()
        self._center()
        self._refresh_pracownie()

    def _center(self):
        self.update_idletasks()
        w, h = 820, 780
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        topbar = tk.Frame(self, bg=BG_DARK, height=48)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)
        tk.Label(topbar, text=" KROK 1 ", font=FONT_LABEL, bg=GREEN, fg=BG_DARK, padx=6, pady=3).pack(side="left", padx=20, pady=12)
        tk.Label(topbar, text="Archiwizacja projektów  ·  Wariant z Popupem", font=FONT_SUB, fg="#aaaaaa", bg=BG_DARK).pack(side="left", padx=4)

        title_frame = tk.Frame(self, bg=BG)
        title_frame.pack(fill="x")
        tk.Frame(title_frame, bg=GREEN, width=8).pack(side="left", fill="y")
        ti = tk.Frame(title_frame, bg=BG, padx=24, pady=16)
        ti.pack(side="left", fill="x", expand=True)
        tk.Label(ti, text="Setup struktury folderów", font=FONT_TITLE, fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(ti, text="Wypełnij formularz – skrypt automatycznie stworzy całą strukturę archiwum.", font=FONT_SUB, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=BORDER, height=2).pack(fill="x")

        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self._content = tk.Frame(canvas, bg=BG)
        self._content_window = canvas.create_window((0, 0), window=self._content, anchor="nw")

        def _on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(self._content_window, width=canvas.winfo_width())

        self._content.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self._content_window, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._build_form(self._content)

    def _sep(self, parent): tk.Frame(parent, bg="#eeeeee", height=1).pack(fill="x", padx=32, pady=4)
    def _section_label(self, parent, text): tk.Label(parent, text=text, font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", padx=32, pady=(14, 4))

    def _build_form(self, parent):
        self._section_label(parent, "1  DANE OSOBOWE")
        grid = tk.Frame(parent, bg=BG, padx=32)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        for label, var, row, col in [("Nazwisko:", self._surname_var, 0, 0), ("Inicjał (np. W):", self._initial_var, 0, 2),
                                     ("Imię i nazwisko:", self._fullname_var, 1, 0), ("Nr albumu:", self._album_var, 1, 2)]:
            tk.Label(grid, text=label, font=FONT_SUB, fg=TEXT, bg=BG).grid(row=row, column=col, sticky="w", pady=3, padx=(0, 8))
            tk.Entry(grid, textvariable=var, font=FONT_UI, bg=BG_INPUT, fg=TEXT, relief="flat", highlightbackground=BORDER, highlightthickness=1).grid(row=row, column=col+1, sticky="ew", padx=(0, 16), pady=3, ipady=6)

        self._sep(parent)

        self._section_label(parent, "2  KIERUNEK I SEMESTR")
        ks_frame = tk.Frame(parent, bg=BG, padx=32); ks_frame.pack(fill="x")
        tk.Label(ks_frame, text="Kierunek:", font=FONT_SUB, fg=TEXT, bg=BG).pack(anchor="w")
        for code, name in KIERUNKI.items():
            r = tk.Frame(ks_frame, bg=BG); r.pack(anchor="w", pady=2)
            tk.Radiobutton(r, variable=self._kierunek_var, value=code, command=self._on_kierunek_change, bg=BG, activebackground=BG, selectcolor=GREEN, relief="flat", bd=0).pack(side="left")
            tk.Label(r, text=f"{code}  –  {name}", font=FONT_SUB, bg=BG).pack(side="left")

        tk.Label(ks_frame, text="Semestr:", font=FONT_SUB, fg=TEXT, bg=BG).pack(anchor="w", pady=(8, 0))
        self._sem_frame = tk.Frame(ks_frame, bg=BG); self._sem_frame.pack(anchor="w", pady=4)
        
        yr_row = tk.Frame(ks_frame, bg=BG); yr_row.pack(anchor="w", pady=(6, 0))
        tk.Label(yr_row, text="Rok (np. 2026):", font=FONT_SUB, bg=BG).pack(side="left", padx=(0, 8))
        tk.Entry(yr_row, textvariable=self._year_var, font=FONT_UI, bg=BG_INPUT, width=8, relief="flat", highlightbackground=BORDER, highlightthickness=1).pack(side="left", ipady=5)

        self._sep(parent)

        self._section_label(parent, "3  WYBIERZ PRACOWNIE W KTÓRYCH UCZESTNICZYSZ")
        self._prac_outer = tk.Frame(parent, bg=BG, padx=32); self._prac_outer.pack(fill="x")
        self._no_data_label = tk.Label(self._prac_outer, text="⚠  Brak pliku asp_pracownie.csv", font=FONT_SUB, fg="#cc4400", bg=BG)
        self._prac_frame = tk.Frame(self._prac_outer, bg=BG); self._prac_frame.pack(fill="x")

        self._sep(parent)

        self._section_label(parent, "4  GDZIE ZAPISAĆ ARCHIWUM")
        loc_frame = tk.Frame(parent, bg=BG, padx=32); loc_frame.pack(fill="x", pady=(0, 4))
        loc_row = tk.Frame(loc_frame, bg=BG); loc_row.pack(fill="x")
        path_box = tk.Frame(loc_row, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        path_box.pack(side="left", fill="x", expand=True)
        tk.Label(path_box, textvariable=self._location_var, font=FONT_MONO, fg=TEXT_DIM, bg=BG_INPUT, anchor="w", padx=10, pady=8).pack(fill="x")
        tk.Button(loc_row, text="Wybierz…", font=FONT_UI, bg="#eeeeee", fg=TEXT, activebackground="#dddddd", relief="flat", padx=16, pady=8, cursor="hand2", bd=0, command=self._pick_location).pack(side="left", padx=(8, 0))

        self._sep(parent)

        btn_frame = tk.Frame(parent, bg=BG, padx=32, pady=12); btn_frame.pack(fill="x")
        self._run_btn = tk.Button(btn_frame, text="▶   Utwórz strukturę archiwum", font=("Helvetica Neue", 14, "bold") if IS_MAC else ("Arial", 12, "bold"), bg=GREEN, fg=BG_DARK, relief="flat", padx=28, pady=12, cursor="hand2", bd=0, command=self._run)
        self._run_btn.pack(side="right")

        tk.Label(parent, text="LOG", font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", padx=32, pady=(8, 0))
        log_frame = tk.Frame(parent, bg=BG, padx=32); log_frame.pack(fill="x", pady=(4, 24))
        self._log_box = scrolledtext.ScrolledText(log_frame, font=FONT_MONO, bg=BG_LOG, fg=TEXT, relief="flat", padx=12, pady=8, height=10, state="disabled", wrap="word", highlightbackground=BORDER, highlightthickness=1)
        self._log_box.pack(fill="x")

    def _build_semestr_buttons(self):
        for w in self._sem_frame.winfo_children(): w.destroy()
        sems = SEMESTRY.get(self._kierunek_var.get(), [])
        if self._semestr_var.get() not in sems: self._semestr_var.set(sems[0] if sems else "")
        for s in sems:
            tk.Radiobutton(self._sem_frame, text=s, variable=self._semestr_var, value=s, command=self._refresh_pracownie, bg=BG, activebackground=BG, selectcolor=GREEN, relief="flat", bd=0).pack(side="left", padx=4)

    def _on_kierunek_change(self):
        self._build_semestr_buttons()
        self._refresh_pracownie()

    def _refresh_pracownie(self):
        if not self._prac_frame.winfo_exists(): return
        for w in self._prac_frame.winfo_children(): w.destroy()
        self._check_vars.clear()

        if not self._db:
            self._no_data_label.pack(anchor="w"); return
        self._no_data_label.pack_forget()

        rows = get_pracownie(self._db, self._kierunek_var.get(), self._semestr_var.get())
        if not rows:
            tk.Label(self._prac_frame, text="Brak danych dla tej kombinacji.", font=FONT_SUB, fg=TEXT_DIM, bg=BG).pack(anchor="w")
            return

        by_cat = {}
        for r in rows: by_cat.setdefault(r["kategoria"], []).append(r)

        for cat in KATEGORIE_ORDER:
            if cat not in by_cat: continue
            cat_row = tk.Frame(self._prac_frame, bg=BG, pady=2)
            cat_row.pack(fill="x")
            tk.Label(cat_row, text=f" {cat.upper()} ", font=FONT_LABEL, bg=GREEN, fg=BG_DARK, padx=6).pack(side="left", pady=4)
            for p in by_cat[cat]:
                key = p["kod_pracowni"]
                var = tk.BooleanVar(value=False)
                self._check_vars[key] = var

                row = tk.Frame(self._prac_frame, bg=BG)
                row.pack(fill="x", padx=8, pady=1)
                tk.Checkbutton(row, variable=var, bg=BG, activebackground=BG, selectcolor=GREEN, relief="flat", bd=0).pack(side="left")
                tk.Label(row, text=f" {key} ", font=FONT_LABEL, bg="#eeeeee", fg=TEXT, padx=4).pack(side="left", padx=(2, 8), pady=1)
                tk.Label(row, text=p["nazwa_przedmiotu"], font=FONT_SUB, fg=TEXT, bg=BG).pack(side="left")
                tk.Label(row, text=f"  {p['prowadzacy'].split('/')[0].strip()}", font=FONT_SMALL, fg=TEXT_DIM, bg=BG).pack(side="left")

    def _pick_location(self):
        path = filedialog.askdirectory(title="Wybierz folder gdzie zapisać archiwum")
        if path: self._location_var.set(path)

    def _log(self, msg):
        self._log_box.config(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _show_projects_dialog(self, selected_workshops: list[dict]) -> dict:
        dialog = tk.Toplevel(self)
        dialog.title("Tytuły projektów")
        dialog.configure(bg=BG)
        dialog.transient(self)
        dialog.grab_set()

        w, h = 600, 500
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        dialog.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Label(dialog, text="Podaj tytuły realizowanych projektów", font=FONT_TITLE, bg=BG, fg=TEXT).pack(pady=(20, 5))
        tk.Label(dialog, text="Jeśli w ramach przedmiotu było kilka projektów, kliknij '+ Dodaj kolejny'", font=FONT_SUB, bg=BG, fg=TEXT_DIM).pack(pady=(0, 15))

        canvas = tk.Canvas(dialog, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="top", fill="both", expand=True)
        canvas.configure(yscrollcommand=scroll.set)

        frame = tk.Frame(canvas, bg=BG, padx=20)
        win_id = canvas.create_window((0, 0), window=frame, anchor="nw")
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        projects_vars = {} # code -> [StringVar]

        for p in selected_workshops:
            code = p["kod_pracowni"]
            p_vars = [tk.StringVar()]
            projects_vars[code] = p_vars

            sec = tk.Frame(frame, bg=BG)
            sec.pack(fill="x", pady=(10, 5))
            tk.Label(sec, text=f"[{code}] {p['nazwa_przedmiotu']}", font=FONT_LABEL, bg=BG).pack(anchor="w")

            entries_frame = tk.Frame(sec, bg=BG)
            entries_frame.pack(fill="x", padx=10)

            def build_entries(e_frame=entries_frame, vs=p_vars):
                for child in e_frame.winfo_children(): child.destroy()
                for i, v in enumerate(vs):
                    r = tk.Frame(e_frame, bg=BG)
                    r.pack(fill="x", pady=2)
                    tk.Label(r, text=f"Projekt {i+1}:", font=FONT_SMALL, bg=BG, width=10, anchor="w").pack(side="left")
                    tk.Entry(r, textvariable=v, font=FONT_UI, bg=BG_INPUT, highlightbackground=BORDER, highlightthickness=1, relief="flat").pack(side="left", fill="x", expand=True)
                
                tk.Button(e_frame, text="+ Dodaj kolejny", font=FONT_SMALL, bg="#eeeeee", relief="flat", bd=0, command=lambda: add_var(e_frame, vs)).pack(anchor="w", pady=4)

            def add_var(e_frame, vs):
                vs.append(tk.StringVar())
                build_entries(e_frame, vs)

            build_entries()

        result = {}
        cancelled = True

        def on_submit():
            nonlocal cancelled
            cancelled = False
            for code, vs in projects_vars.items():
                result[code] = [v.get() for v in vs if v.get().strip()]
            dialog.destroy()

        btn_f = tk.Frame(dialog, bg=BG, pady=15)
        btn_f.pack(fill="x")
        tk.Button(btn_f, text="Zatwierdź i Utwórz", font=FONT_UI, bg=GREEN, fg=BG_DARK, relief="flat", padx=20, pady=10, command=on_submit).pack()

        self.wait_window(dialog)
        return None if cancelled else result

    def _run(self):
        if not all([self._surname_var.get(), self._initial_var.get(), self._fullname_var.get(), self._album_var.get(), self._year_var.get(), self._location_var.get()]):
            messagebox.showwarning("Brak danych", "Wypełnij wszystkie pola tekstowe i wybierz lokalizację.")
            return
        
        selected_codes = [k for k, v in self._check_vars.items() if v.get()]
        if not selected_codes:
            messagebox.showwarning("Brak pracowni", "Zaznacz co najmniej jedną pracownię.")
            return

        selected_workshops = [r for r in get_pracownie(self._db, self._kierunek_var.get(), self._semestr_var.get()) if r["kod_pracowni"] in selected_codes]
        
        # Otwieramy popup
        projects_dict = self._show_projects_dialog(selected_workshops)
        if projects_dict is None:
            return # Użytkownik zamknął okienko

        self._log_box.config(state="normal"); self._log_box.delete("1.0", "end"); self._log_box.config(state="disabled")
        self._run_btn.config(state="disabled", text="⏳  Tworzę strukturę…")

        meta = {
            "surname_initial": f"{self._surname_var.get().strip()}{self._initial_var.get().strip().upper()}",
            "year": self._year_var.get().strip(),
            "semester": self._semestr_var.get(),
            "full_name": self._fullname_var.get().strip(),
            "album": self._album_var.get().strip(),
        }

        def worker():
            try:
                build_structure(None, Path(self._location_var.get()), meta, selected_workshops, projects_dict, self._log)
            finally:
                self.after(0, lambda: self._run_btn.config(state="normal", text="▶   Utwórz strukturę archiwum"))

        threading.Thread(target=worker, daemon=True).start()

if __name__ == "__main__":
    app = SetupWizard()
    app.mainloop()