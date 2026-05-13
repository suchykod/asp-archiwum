#!/usr/bin/env python3
"""ASP Warszawa – Krok 1: Setup struktury folderów (Wizard + Projekty)"""

import csv
import re
import sys
import threading
from datetime import date
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

SCROLL_UNIT = 1
# Smaller divisors give finer-grained scrolling (more responsive)
SCROLL_DIV_WIN = 50
SCROLL_DIV_MAC = 2

# ── Dane kierunków ────────────────────────────────────────────────────────────
KIERUNKI = {
    "PPP": "Projektowanie produktu, przestrzeni, przekazu",
    "PU":  "Projektowanie ubioru i jego konteksty",
    "PIB": "Projektowanie i badania (mgr)",
}

# ── Map short codes → full CSV values ────────────────────────────────────────
KIERUNEK_MAP = {
    "PPP": "Projektowanie produktu, przestrzeni, przekazu (I stopnia)",
    "PU":  "Projektowanie ubioru i jego konteksty (I stopnia)",
    "PIB": "Projektowanie i badania (II stopnia)",
}

SEMESTRY = {
    "PPP": ["1", "2", "3", "4", "5", "6", "7", "L"],
    "PU":  ["1", "2", "3", "4", "5", "6", "L"],
    "PIB": ["SM1", "SM2", "SM3", "M"],
}
KATEGORIE_ORDER = ["Projektowe", "Plastyczne", "Inne"]
SUBFOLDERS = ["film_prezentacja_animacja", "plansze", "rendering", "szkicownik", "zdjecia"]
PROJECT_TAGS = [
    "Moda", "Ekologia", "Jedzenie", "Transport", "Miasto", "Komunikacja Wizualna",
    "Aplikacja mobilna", "Strona www", "Identyfikacja wizualna", "Dla osób z niepełnosprawnościami",
    "Ruch", "Wzrok", "Słuch", "Zabawa", "Dla dzieci", "Gra", "Aktywizacja", "Mebel",
    "Urządzenie domowe", "Wspólnotowość", "Natura", "Technologia", "Viral", "Człowiek",
    "Rodzina", "Choroba", "Mobilność", "Sport", "Pomoc", "Przewodnik", "Książka",
    "Broszura", "Dziedzictwo", "Historia", "Tradycja", "Kultura", "Międzypokoleniowe",
    "Stół", "Siedzisko", "Biurko", "Miejsce pracy", "Organizacja pracy", "Oświetlenie",
    "Pomoc medyczna", "Pomoc edukacyjna", "Pomoc domowa", "Seniorzy", "Poród",
    "Posiłek", "Obowiązki",
]

CSV_FILENAME = "Pracownie_ASP_v3.csv"

# ── Pomocnicze ────────────────────────────────────────────────────────────────

def resource_path(filename: str) -> Path:
    base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    candidate = base_dir / filename
    if candidate.exists():
        return candidate

    candidate = Path(__file__).resolve().parent / filename
    if candidate.exists():
        return candidate

    return Path.cwd() / filename

def load_csv(csv_path: Path) -> list[dict]:
    rows = []
    if not csv_path.exists():
        return rows
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "semestr" in row: 
                row["semestr"] = str(row["semestr"]).strip()
            if "kierunek" in row: 
                row["kierunek"] = str(row["kierunek"]).strip()
            if "kategoria" in row:
                # TO ROZWIĄZUJE PROBLEM: CSV miało "projektowe", GUI szukało "Projektowe"
                row["kategoria"] = str(row["kategoria"]).strip().capitalize()
            rows.append(row)
    return rows

def get_pracownie(db: list[dict], kierunek: str, semestr: str) -> list[dict]:
    full_kierunek = KIERUNEK_MAP.get(kierunek, kierunek)
    gui_s = semestr.strip().upper()

    return [
        r
        for r in db
        if str(r.get("kierunek", "")).strip() == full_kierunek
        and str(r.get("semestr", "")).strip().upper() == gui_s
    ]

def sanitize_filename(name: str) -> str:
    """Usuwa niedozwolone znaki z nazw folderów."""
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()

def get_academic_year_end(today: date | None = None) -> int:
    """Zwraca rok zakończenia roku akademickiego dla podanej daty."""
    d = today or date.today()
    # Rok akademicki trwa od 1 października do 30 września.
    return d.year + 1 if d.month >= 10 else d.year

# ── Tworzenie plików i folderów ───────────────────────────────────────────────

def create_inf_template(path: Path, meta: dict, workshop_code: str,
                        nazwa: str, prowadzacy: str, title: str,
                        tags: list[str]) -> None:
    try:
        end_year = int(meta["year"])
        academic_year = f"{end_year - 1}/{end_year}"
    except ValueError:
        academic_year = meta["year"]

    display_title = title if title else "[uzupełnij – nazwa projektu]"
    display_tags = ", ".join(tags) if tags else "[brak]"
    content = (
        f"TYTUŁ PRACY:        {display_title}\n"
        f"TAGI:               {display_tags}\n"
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
    """Tworzy strukturę, uwzględniając podfoldery dla wielu projektów i 'stopklatki' w filmie."""
    si   = meta["surname_initial"]
    year = meta["year"]
    sem  = meta["semester"]

    root = parent_dir / f"{si}_{year}_{sem}"
    root.mkdir(parents=True, exist_ok=True)
    log(f"✓  Folder główny: {root.name}\n")

    by_cat: dict[str, list] = {k: [] for k in KATEGORIE_ORDER}
    for p in selected:
        cat = p["kategoria"]
        if cat in by_cat:
            by_cat[cat].append(p)

    def _create_subfolders_and_inf(base_dir, code, nazwa, prow, title, tags):
        for sub in SUBFOLDERS:
            sub_path = base_dir / sub
            sub_path.mkdir(exist_ok=True)
            if sub == "film_prezentacja_animacja":
                (sub_path / "stopklatki").mkdir(exist_ok=True)
        inf_name = f"{si}_{code}_{year}_{sem}_INF.txt"
        create_inf_template(base_dir / inf_name, meta, code, nazwa, prow, title, tags)

    for cat in KATEGORIE_ORDER:
        pracownie = by_cat.get(cat, [])
        if not pracownie:
            continue
        cat_dir = root / cat
        cat_dir.mkdir(exist_ok=True)
        log(f"▸  {cat}/")

        for p in pracownie:
            code    = p["kod_pracowni"]
            nazwa   = p["nazwa_przedmiotu"]
            prow    = p["prowadzacy"]
            w_dir   = cat_dir / f"{si}_{code}_{year}_{sem}"
            w_dir.mkdir(exist_ok=True)

            projects = projects_dict.get(code, [])
            titles = [p["title"] for p in projects if p["title"].strip()]

            if len(titles) <= 1:
                # Brak lub jeden projekt - wrzucamy wszystko bezpośrednio do folderu pracowni
                project = projects[0] if projects else {"title": "", "tags": []}
                _create_subfolders_and_inf(w_dir, code, nazwa, prow, project["title"], project["tags"])
                log(f"   ↳  {w_dir.name}/  ✓  INF.txt wygenerowany")
            else:
                # Wiele projektów - robimy podfoldery
                log(f"   ↳  {w_dir.name}/  (Złożone z {len(titles)} projektów)")
                for idx, project in enumerate(projects):
                    title = project["title"]
                    tags = project["tags"]
                    safe_title = sanitize_filename(title) or f"Projekt_{idx+1}"
                    p_dir = w_dir / safe_title
                    p_dir.mkdir(exist_ok=True)
                    _create_subfolders_and_inf(p_dir, code, nazwa, prow, title, tags)
                    log(f"      ↳  {safe_title}/  ✓  INF.txt")

    log(f"\n✓  Struktura gotowa w: {root}")
    log("   Pamiętaj o wrzuceniu klatek do /film_prezentacja_animacja/stopklatki.")
    log("   Uzupełnij OPIS PROJEKTU w plikach _INF.txt i uruchom Krok 2.")

# ── GUI – główne okno ─────────────────────────────────────────────────────────

class SetupWizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Archiwiktor setup")
        self.configure(bg=BG)
        self.resizable(True, True)

        self._db = load_csv(resource_path(CSV_FILENAME))
        if not self._db:
            self._db = load_csv(Path.cwd() / CSV_FILENAME)

        self._kierunek_var  = tk.StringVar(value="PPP")
        self._semestr_var   = tk.StringVar(value="1")
        self._name_var      = tk.StringVar()
        self._surname_var   = tk.StringVar()
        self._album_var     = tk.StringVar()
        self._location_var  = tk.StringVar()

        self._check_vars: dict[str, tk.BooleanVar] = {}
        self._wheel_accum = 0.0

        self._build_ui()
        self._build_semestr_buttons()
        self._center()
        self._bring_to_front()
        self._refresh_pracownie()

    def _center(self):
        self.update_idletasks()
        w, h = 780, 780
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _bring_to_front(self):
        """Próbuje pokazać okno na wierzchu przy starcie aplikacji."""
        self.deiconify()
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))

    def _build_ui(self):
        topbar = tk.Frame(self, bg=BG, height=48)
        topbar.pack(fill="x")
        topbar.grid_propagate(False)
        topbar.columnconfigure(0, weight=1)
        topbar.columnconfigure(1, weight=1)
        topbar.columnconfigure(2, weight=1)

        tk.Label(topbar, text=" ", font=FONT_LABEL, bg=GREEN, fg=BG_DARK, padx=6, pady=3).grid(
            row=0, column=0, sticky="w", padx=20, pady=12
        )
        tk.Label(topbar, text="Archiwiktor setup  ·  Wydział Wzornictwa ASP", font=FONT_SUB, fg=TEXT_DIM, bg=BG).grid(
            row=0, column=1
        )
        tk.Label(topbar, text="Autor: Wiktor Suchy", font=FONT_SUB, fg=TEXT_DIM, bg=BG).grid(
            row=0, column=2, sticky="e", padx=20
        )
        tk.Frame(self, bg=GREEN, height=3).pack(fill="x")

        title_frame = tk.Frame(self, bg=BG)
        title_frame.pack(fill="x")
        tk.Frame(title_frame, bg=GREEN, width=8).pack(side="left", fill="y")
        ti = tk.Frame(title_frame, bg=BG, padx=24, pady=16)
        ti.pack(side="left", fill="x", expand=True)
        tk.Label(ti, text=" Archiwiktor setup  ·  KROK 1", font=FONT_TITLE, fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(ti, text="Wypełnij formularz – skrypt automatycznie stworzy całą strukturę archiwum.", font=FONT_SUB, fg=TEXT_DIM, bg=BG).pack(anchor="w", pady=(2, 0))

        tk.Frame(self, bg=BORDER, height=2).pack(fill="x")

        # System Scrolla
        self._canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._content = tk.Frame(self._canvas, bg=BG)
        self._content_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")

        def _on_configure(e):
            self._canvas.configure(scrollregion=self._canvas.bbox("all"))
            self._canvas.itemconfig(self._content_window, width=self._canvas.winfo_width())

        self._content.bind("<Configure>", _on_configure)
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._content_window, width=e.width))

        # Mouse wheel binding dla wszystkich platform
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

        self._build_form(self._content)

    def _on_mousewheel(self, event):
        """Obsługa scrolla dla Windows/macOS/Linux."""
        units = self._get_scroll_units(event)
        if units:
            self._canvas.yview_scroll(units, "units")

    def _get_scroll_units(self, event) -> int:
        num = getattr(event, "num", None)
        if num == 4:
            return -SCROLL_UNIT
        if num == 5:
            return SCROLL_UNIT

        delta = getattr(event, "delta", 0)
        if not delta:
            return 0
        # Normalize direction: positive delta typically means scroll up on some platforms
        # Accumulate small deltas to allow smooth trackpad scrolling on all platforms.
        self._wheel_accum += -delta
        if IS_MAC:
            div = SCROLL_DIV_MAC
        else:
            div = SCROLL_DIV_WIN

        units = int(self._wheel_accum / div)
        if units != 0:
            self._wheel_accum -= units * div
            return units * SCROLL_UNIT

        return 0

    def _sep(self, parent):
        tk.Frame(parent, bg="#eeeeee", height=1).pack(fill="x", padx=32, pady=4)

    def _section_label(self, parent, text):
        tk.Label(parent, text=text, font=FONT_LABEL, fg=TEXT_DIM, bg=BG).pack(anchor="w", padx=32, pady=(14, 4))

    def _build_form(self, parent):
        self._section_label(parent, "1  DANE OSOBOWE")
        grid = tk.Frame(parent, bg=BG, padx=32)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1); grid.columnconfigure(3, weight=1)

        fields = [
            ("Imię:", self._name_var, 0, 0),
            ("Nazwisko:", self._surname_var, 0, 2),
            ("Nr albumu:", self._album_var, 1, 0),
        ]
        for label, var, row, col in fields:
            tk.Label(grid, text=label, font=FONT_SUB, fg=TEXT, bg=BG).grid(row=row, column=col, sticky="w", pady=3, padx=(0, 8))
            tk.Entry(grid, textvariable=var, font=FONT_UI, bg=BG_INPUT, fg=TEXT, insertbackground=TEXT, relief="flat", highlightbackground=BORDER, highlightcolor=GREEN, highlightthickness=1).grid(row=row, column=col+1, sticky="ew", padx=(0, 16), pady=3, ipady=6)

        self._sep(parent)

        self._section_label(parent, "2  KIERUNEK I SEMESTR")
        ks_frame = tk.Frame(parent, bg=BG, padx=32); ks_frame.pack(fill="x")
        tk.Label(ks_frame, text="Kierunek:", font=FONT_SUB, fg=TEXT, bg=BG).pack(anchor="w")
        for code, name in KIERUNKI.items():
            r = tk.Frame(ks_frame, bg=BG); r.pack(anchor="w", pady=2)
            tk.Radiobutton(r, variable=self._kierunek_var, value=code, command=self._on_kierunek_change, bg=BG, activebackground=BG, selectcolor=GREEN, fg=TEXT, font=FONT_UI, relief="flat", bd=0).pack(side="left")
            tk.Label(r, text=f"{code}  –  {name}", font=FONT_SUB, fg=TEXT, bg=BG).pack(side="left")

        tk.Label(ks_frame, text="Semestr:", font=FONT_SUB, fg=TEXT, bg=BG).pack(anchor="w", pady=(8, 0))
        self._sem_frame = tk.Frame(ks_frame, bg=BG); self._sem_frame.pack(anchor="w", pady=4)

        end_year = get_academic_year_end()
        tk.Label(
            ks_frame,
            text=f"Rok akademicki (auto): {end_year - 1}/{end_year}",
            font=FONT_SUB,
            fg=TEXT_DIM,
            bg=BG,
        ).pack(anchor="w", pady=(6, 0))

        self._sep(parent)

        self._section_label(parent, "3  WYBIERZ PRACOWNIE W KTÓRYCH UCZESTNICZYSZ")
        self._prac_outer = tk.Frame(parent, bg=BG, padx=32); self._prac_outer.pack(fill="x")
        self._no_data_label = tk.Label(self._prac_outer, text="⚠  Brak pliku Pracownie_ASP_v3.csv", font=FONT_SUB, fg="#cc4400", bg=BG)
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
            tk.Radiobutton(self._sem_frame, text=s, variable=self._semestr_var, value=s, command=self._refresh_pracownie, bg=BG, activebackground=BG, selectcolor=GREEN, fg=TEXT, font=FONT_UI, relief="flat", bd=0).pack(side="left", padx=4)

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
        if not rows: return

        current_kierunek = self._kierunek_var.get()
        current_semestr = self._semestr_var.get()

        by_cat = {}
        for r in rows: by_cat.setdefault(r["kategoria"], []).append(r)

        for cat in KATEGORIE_ORDER:
            if cat not in by_cat: continue
            cat_row = tk.Frame(self._prac_frame, bg=BG, pady=2); cat_row.pack(fill="x")
            tk.Label(cat_row, text=f" {cat.upper()} ", font=FONT_LABEL, bg=GREEN, fg=BG_DARK, padx=6).pack(side="left", pady=2)

            for p in by_cat[cat]:
                key = p["kod_pracowni"]
                var = tk.BooleanVar(value=False)
                self._check_vars[key] = var
                row = tk.Frame(self._prac_frame, bg=BG); row.pack(fill="x", padx=8, pady=1)
                tk.Checkbutton(row, variable=var, bg=BG, activebackground=BG, selectcolor=GREEN, relief="flat", bd=0).pack(side="left")
                tk.Label(row, text=f" {key} ", font=FONT_LABEL, bg="#eeeeee", fg=TEXT, padx=4).pack(side="left", padx=(2, 8), pady=1)
                label_text = p["nazwa_przedmiotu"]
                if current_kierunek == "PPP" and current_semestr == "L" and label_text == "dyplom licencjacki":
                    label_text = f'{label_text} ({p["prowadzacy"]})'
                elif current_kierunek == "PIB" and current_semestr == "SM3" and label_text == "pracownia dyplomowa":
                    label_text = f'{label_text} ({p["prowadzacy"]})'
                elif current_kierunek == "PIB" and current_semestr == "M" and label_text == "dyplom magisterski":
                    label_text = f'{label_text} ({p["prowadzacy"]})'
                tk.Label(row, text=label_text, font=FONT_SUB, fg=TEXT, bg=BG).pack(side="left")

    def _pick_location(self):
        path = filedialog.askdirectory(title="Wybierz folder gdzie zapisać archiwum")
        if path: self._location_var.set(path)

    def _log(self, msg):
        self._log_box.config(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _show_projects_dialog(self, selected_workshops: list[dict]) -> dict:
        title_placeholder = "Tytuł Twojego projektu"

        dialog = tk.Toplevel(self)
        dialog.title("Tytuły i tagi projektów")
        dialog.configure(bg=BG)
        dialog.transient(self)
        dialog.grab_set()

        w, h = 980, 760
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        dialog.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Label(dialog, text="Podaj tytuły realizowanych projektów", font=FONT_TITLE, bg=BG, fg=TEXT).pack(pady=(20, 5))
        tk.Label(
            dialog,
            text="Po wpisaniu tytułu wybierz tagi z listy. Możesz też dodać własne tagi dla konkretnego projektu.",
            font=FONT_SUB,
            bg=BG,
            fg=TEXT_DIM,
        ).pack(pady=(0, 15))

        canvas = tk.Canvas(dialog, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="top", fill="both", expand=True)
        canvas.configure(yscrollcommand=scroll.set)

        frame = tk.Frame(canvas, bg=BG, padx=20)
        win_id = canvas.create_window((0, 0), window=frame, anchor="nw")

        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        def _on_dlg_mousewheel(e):
            units = self._get_scroll_units(e)
            if units:
                canvas.yview_scroll(units, "units")

        dialog.bind("<MouseWheel>", _on_dlg_mousewheel)
        dialog.bind("<Button-4>", _on_dlg_mousewheel)
        dialog.bind("<Button-5>", _on_dlg_mousewheel)

        def _set_placeholder(entry: tk.Entry, var: tk.StringVar):
            if not var.get().strip():
                var.set(title_placeholder)
                entry.config(fg=TEXT_DIM)

        def _bind_placeholder(entry: tk.Entry, var: tk.StringVar):
            def on_focus_in(_):
                entry.config(highlightbackground=GREEN)
                if var.get().strip() == title_placeholder:
                    var.set("")
                    entry.config(fg=TEXT)

            def on_focus_out(_):
                entry.config(highlightbackground=BORDER)
                _set_placeholder(entry, var)

            _set_placeholder(entry, var)
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

        projects_vars: dict[str, list[dict]] = {}

        for p in selected_workshops:
            code = p["kod_pracowni"]
            p_vars = [
                {
                    "title_var": tk.StringVar(),
                    "tag_vars": {},
                    "custom_tag_var": tk.StringVar(),
                    "custom_tags": [],
                }
            ]
            projects_vars[code] = p_vars

            sec = tk.Frame(frame, bg=BG)
            sec.pack(fill="x", pady=(10, 5))
            tk.Label(sec, text=f"[{code}] {p['nazwa_przedmiotu']}", font=FONT_LABEL, bg=BG).pack(anchor="w")
            tk.Label(
                sec,
                text=f"Pracownia: {code}  |  Prowadzący: {p['prowadzacy']}",
                font=FONT_SMALL,
                fg=TEXT_DIM,
                bg=BG,
            ).pack(anchor="w", pady=(0, 2))

            entries_frame = tk.Frame(sec, bg=BG)
            entries_frame.pack(fill="x", padx=10)

            def build_tag_picker(tag_frame: tk.Frame, project_state: dict):
                for child in tag_frame.winfo_children():
                    child.destroy()

                header_row = tk.Frame(tag_frame, bg=BG)
                header_row.pack(fill="x", pady=(4, 2))

                tk.Label(header_row, text="Tagi:", font=FONT_SMALL, bg=BG).pack(side="left")

                tags_panel = tk.Frame(tag_frame, bg=BG)
                tags_visible = tk.BooleanVar(value=project_state.get("tags_expanded", False))

                def toggle_tags():
                    if tags_visible.get():
                        tags_panel.pack_forget()
                        tags_toggle.config(text="▸ Pokaż tagi")
                        tags_visible.set(False)
                        project_state["tags_expanded"] = False
                    else:
                        tags_panel.pack(fill="x", pady=(2, 4))
                        tags_toggle.config(text="▾ Ukryj tagi")
                        tags_visible.set(True)
                        project_state["tags_expanded"] = True

                tags_toggle = tk.Button(
                    header_row,
                    text="▸ Pokaż tagi",
                    font=FONT_SMALL,
                    bg="#eeeeee",
                    relief="flat",
                    bd=0,
                    padx=10,
                    pady=6,
                    command=toggle_tags,
                )
                tags_toggle.pack(side="right")

                tags_grid = tk.Frame(tags_panel, bg=BG)
                tags_grid.pack(fill="x", pady=(0, 4))
                tags_grid.columnconfigure(0, weight=1)
                tags_grid.columnconfigure(1, weight=1)
                tags_grid.columnconfigure(2, weight=1)

                project_state.setdefault("tag_vars", {})
                for idx, tag_name in enumerate(PROJECT_TAGS):
                    if tag_name not in project_state["tag_vars"]:
                        project_state["tag_vars"][tag_name] = tk.BooleanVar(value=False)
                    col = idx % 3
                    row = idx // 3
                    cell = tk.Frame(tags_grid, bg=BG)
                    cell.grid(row=row, column=col, sticky="w", padx=(0, 12), pady=1)
                    tk.Checkbutton(
                        cell,
                        text=tag_name,
                        variable=project_state["tag_vars"][tag_name],
                        bg=BG,
                        activebackground=BG,
                        fg=TEXT,
                        activeforeground=TEXT,
                        selectcolor=GREEN,
                        relief="flat",
                        bd=0,
                        anchor="w",
                    ).pack(anchor="w")

                custom_start = len(PROJECT_TAGS)
                for offset, tag_name in enumerate(project_state["custom_tags"]):
                    if tag_name not in project_state["tag_vars"]:
                        project_state["tag_vars"][tag_name] = tk.BooleanVar(value=True)
                    else:
                        project_state["tag_vars"][tag_name].set(True)
                    idx = custom_start + offset
                    col = idx % 3
                    row = idx // 3
                    cell = tk.Frame(tags_grid, bg=BG)
                    cell.grid(row=row, column=col, sticky="w", padx=(0, 12), pady=1)
                    tk.Checkbutton(
                        cell,
                        text=tag_name,
                        variable=project_state["tag_vars"][tag_name],
                        bg=BG,
                        activebackground=BG,
                        fg=TEXT,
                        activeforeground=TEXT,
                        selectcolor=GREEN,
                        relief="flat",
                        bd=0,
                        anchor="w",
                    ).pack(anchor="w")

                custom_row = tk.Frame(tags_panel, bg=BG)
                custom_row.pack(fill="x", pady=(4, 0))
                custom_entry = tk.Entry(
                    custom_row,
                    textvariable=project_state["custom_tag_var"],
                    font=FONT_SMALL,
                    bg=BG_INPUT,
                    fg=TEXT,
                    insertbackground=TEXT,
                    highlightbackground=BORDER,
                    highlightcolor=GREEN,
                    highlightthickness=1,
                    relief="flat",
                )
                custom_entry.pack(side="left", fill="x", expand=True)

                custom_tags_label = tk.Label(
                    tags_panel,
                    text="",
                    font=FONT_SMALL,
                    fg=TEXT_DIM,
                    bg=BG,
                    wraplength=860,
                    justify="left",
                )
                custom_tags_label.pack(anchor="w", pady=(3, 0))

                def add_custom_tag():
                    raw_tag = project_state["custom_tag_var"].get().strip()
                    if not raw_tag:
                        return
                    if raw_tag in project_state["custom_tags"] or raw_tag in PROJECT_TAGS:
                        project_state["custom_tag_var"].set("")
                        return
                    project_state["custom_tags"].append(raw_tag)
                    project_state["tag_vars"][raw_tag] = tk.BooleanVar(value=True)
                    project_state["custom_tag_var"].set("")
                    build_tag_picker(tag_frame, project_state)

                custom_entry.bind("<Return>", lambda _event: add_custom_tag())
                tk.Button(
                    custom_row,
                    text="+ Dodaj tag",
                    font=FONT_SMALL,
                    bg="#eeeeee",
                    relief="flat",
                    bd=0,
                    padx=10,
                    pady=5,
                    command=add_custom_tag,
                ).pack(side="left", padx=(8, 0))

                tk.Label(
                    tags_panel,
                    text="Własne tagi zostaną dopisane do pliku INF obok tagów z listy.",
                    font=FONT_SMALL,
                    fg=TEXT_DIM,
                    bg=BG,
                    wraplength=860,
                    justify="left",
                ).pack(anchor="w", pady=(3, 0))

                if tags_visible.get():
                    tags_panel.pack(fill="x", pady=(2, 4))

            def build_entries(e_frame=entries_frame, vs=p_vars, workshop_code=code):
                for child in e_frame.winfo_children():
                    child.destroy()
                for i, project_state in enumerate(vs):
                    r = tk.Frame(e_frame, bg=BG)
                    r.pack(fill="x", pady=2)
                    tk.Label(r, text=f"Projekt {i+1}:", font=FONT_SMALL, bg=BG, width=10, anchor="w").pack(side="left")
                    entry = tk.Entry(
                        r,
                        textvariable=project_state["title_var"],
                        font=FONT_UI,
                        bg=BG_INPUT,
                        fg=TEXT,
                        insertbackground=TEXT,
                        highlightbackground=BORDER,
                        highlightcolor=GREEN,
                        highlightthickness=1,
                        relief="flat",
                    )
                    entry.pack(side="left", fill="x", expand=True)
                    _bind_placeholder(entry, project_state["title_var"])

                    tag_frame = tk.Frame(e_frame, bg=BG, padx=20, pady=4)
                    tag_frame.pack(fill="x", pady=(0, 4))
                    build_tag_picker(tag_frame, project_state)

                tk.Button(
                    e_frame,
                    text=f"+ Dodaj kolejny projekt dla {workshop_code}",
                    font=FONT_SMALL,
                    bg="#eeeeee",
                    relief="flat",
                    bd=0,
                    command=lambda: add_var(e_frame, vs),
                    padx=10,
                    pady=6,
                ).pack(anchor="w", pady=(6, 2), ipady=2)

            def add_var(e_frame, vs):
                vs.append(
                    {
                        "title_var": tk.StringVar(),
                        "tag_vars": {},
                        "custom_tag_var": tk.StringVar(),
                        "custom_tags": [],
                    }
                )
                build_entries(e_frame, vs)

            build_entries()

        result = {}
        cancelled = True

        def on_submit():
            nonlocal cancelled
            cancelled = False
            for code, vs in projects_vars.items():
                result[code] = []
                for project_state in vs:
                    title = project_state["title_var"].get().strip()
                    if not title or title == title_placeholder:
                        continue
                    selected_tags = [
                        tag_name
                        for tag_name, tag_var in project_state["tag_vars"].items()
                        if tag_var.get()
                    ]
                    for custom_tag in project_state["custom_tags"]:
                        if custom_tag not in selected_tags:
                            selected_tags.append(custom_tag)
                    result[code].append({"title": title, "tags": selected_tags})
            dialog.destroy()

        btn_f = tk.Frame(dialog, bg=BG, pady=15)
        btn_f.pack(fill="x")
        tk.Button(btn_f, text="Zatwierdź i Utwórz", font=("Helvetica Neue", 12, "bold") if IS_MAC else ("Arial", 11, "bold"), bg=GREEN, fg=BG_DARK, relief="flat", padx=20, pady=10, command=on_submit).pack()

        self.wait_window(dialog)
        return None if cancelled else result

    def _run(self):
        if not all([self._name_var.get(), self._surname_var.get(), self._album_var.get(), self._location_var.get()]):
            messagebox.showwarning("Brak danych", "Wypełnij wszystkie pola tekstowe i wybierz lokalizację.")
            return
        
        selected_codes = [k for k, v in self._check_vars.items() if v.get()]
        if not selected_codes:
            messagebox.showwarning("Brak pracowni", "Zaznacz co najmniej jedną pracownię.")
            return

        selected_workshops = [r for r in get_pracownie(self._db, self._kierunek_var.get(), self._semestr_var.get()) if r["kod_pracowni"] in selected_codes]
        
        projects_dict = self._show_projects_dialog(selected_workshops)
        if projects_dict is None:
            return

        self._log_box.config(state="normal"); self._log_box.delete("1.0", "end"); self._log_box.config(state="disabled")
        self._run_btn.config(state="disabled", text="⏳  Tworzę strukturę…")

        first_name = self._name_var.get().strip()
        surname = self._surname_var.get().strip()

        meta = {
            "surname_initial": f"{surname}{first_name[0].upper()}",
            "year": str(get_academic_year_end()),
            "semester": self._semestr_var.get(),
            "full_name": f"{first_name} {surname}",
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