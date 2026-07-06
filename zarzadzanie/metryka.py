# -*- coding: utf-8 -*-
"""METRYKA ZAUFANIA (Etap 6) - glowna miara sukcesu V3, per zlecenie.

CLAUDE.md: "System jest dobry, gdy czlowiek sprawdza malo i szybko, a bledy na
laser = zero". Ten skrypt liczy z wynikow zlecenia (bez ezdxf - czyste CSV):
  - rozklad semaforow FINALNYCH (obnizenie AI ma pierwszenstwo, zasada 5),
  - ODSETEK POZYCJI DO PRZEGLADU = nie-zielone / wszystkie (🔴/🟡 obowiazkowo),
  - flagi AI (sprawdz_folder) + ile AI OBNIZYLO,
  - werdykty zebrane (nauka/etykiety) dla tego zlecenia: OK/BLAD wg kto (czlowiek/ai).
Dopisuje wiersz do testy/raporty/metryka_zaufania.csv (TREND - odsetek MA maleC).

Zrodla (kolejnosc): <zeinr>_podsumowanie.csv (raport.py) -> <zeinr>_ocena.csv (warianty)
-> nakladka sprawdz_folder (<zeinr>_sprawdzanie_ai.csv) + nauka/etykiety/etykiety.csv.

UWAGA (uczciwie): "czas sprawdzania/pozycje" i "bledy NA LASER" (uciekly do produkcji)
wymagaja danych, ktorych jeszcze nie zbieramy (stopery, feedback po wypaleniu) - tu
raportujemy bledy WYKRYTE w przegladzie (BLAD czlowiek), nie post-laserowe. Pole
czas_na_pozycje = puste do czasu instrumentacji przegladu.

Uzycie:
  python zarzadzanie\\metryka.py <folder_wynikow> [--etykiety <csv>] [--bez-trendu]

Po zmianie tutaj: python testy\\test_metryka.py (PASS).
"""
import csv
import io
import sys
from collections import Counter
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
ETYKIETY_DOMYSLNE = REPO / "nauka" / "etykiety" / "etykiety.csv"
TREND_CSV = REPO / "testy" / "raporty" / "metryka_zaufania.csv"
SEMAFORY = ("zielony", "zolty", "czerwony")


def _norm_sem(s):
    s = (s or "").strip().lower()
    if s.startswith("ziel"):
        return "zielony"
    if s.startswith(("zolt", "zólt", "żółt")):
        return "zolty"
    if s.startswith("czerw"):
        return "czerwony"
    return "czerwony"      # nieznany = traktuj jako do-decyzji (nie zawyzaj zaufania)


def _czytaj(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _semafory_bazowe(folder):
    """{posn: semafor} z podsumowania (raport.py) albo oceny (warianty). (zeinr, mapa)."""
    folder = Path(folder)
    pod = next(iter(sorted(folder.glob("*_podsumowanie.csv"))), None)
    oce = next(iter(sorted(folder.glob("*_ocena.csv"))), None)
    src = pod or oce
    if src is None:
        return None, {}
    zeinr = src.name.replace("_podsumowanie.csv", "").replace("_ocena.csv", "")
    mapa = {}
    for r in _czytaj(src):
        try:
            mapa[int(r["posn"])] = _norm_sem(r.get("semafor"))
        except (KeyError, ValueError):
            continue
    return zeinr, mapa


def _sprawdzanie_ai(folder):
    """{posn: wiersz} z <zeinr>_sprawdzanie_ai.csv (jesli sprawdzanie AI zrobione)."""
    out = {}
    for p in sorted(Path(folder).glob("*_sprawdzanie_ai.csv")):
        for r in _czytaj(p):
            try:
                out[int(r["posn"])] = r
            except (KeyError, ValueError):
                continue
    return out


def _werdykty_zlecenia(etykiety_csv, zeinr):
    """Werdykty z etykiet dla tego zlecenia (plik zawiera zeinr). Licznik wg (kto, werdykt)."""
    lic = Counter()
    p = Path(etykiety_csv)
    if not p.exists() or not zeinr:
        return lic
    for r in _czytaj(p):
        if zeinr in (r.get("plik") or ""):
            lic[(r.get("kto") or "?", (r.get("werdykt") or "").upper())] += 1
    return lic


def metryka_zlecenia(folder_wynikow, etykiety_csv=None):
    """Liczy metryke zaufania jednego zlecenia. Zwraca dict (albo None gdy brak danych)."""
    zeinr, bazowe = _semafory_bazowe(folder_wynikow)
    if not bazowe:
        return None
    ai = _sprawdzanie_ai(folder_wynikow)
    etykiety_csv = etykiety_csv or ETYKIETY_DOMYSLNE

    finalne = {}
    obnizone = 0
    flagi_ai = 0
    for posn, sem_baz in bazowe.items():
        row = ai.get(posn)
        sem = _norm_sem(row["semafor_ai"]) if row and row.get("semafor_ai") else sem_baz
        finalne[posn] = sem
        if row:
            if row.get("flaga", "").upper() == "TAK":
                flagi_ai += 1
            if row.get("semafor_ai") and _norm_sem(row["semafor_ai"]) != sem_baz:
                obnizone += 1

    rozklad = Counter(finalne.values())
    n = len(finalne)
    do_przegladu = rozklad["zolty"] + rozklad["czerwony"]
    werd = _werdykty_zlecenia(etykiety_csv, zeinr)
    n_blad_czl = werd[("czlowiek", "BLAD")]
    n_ok_czl = werd[("czlowiek", "OK")]

    return dict(
        data=date.today().isoformat(), zeinr=zeinr, n_pozycji=n,
        n_zielony=rozklad["zielony"], n_zolty=rozklad["zolty"],
        n_czerwony=rozklad["czerwony"],
        odsetek_przegladu_proc=round(100.0 * do_przegladu / n, 1) if n else 0.0,
        n_flag_ai=flagi_ai, n_obnizone_ai=obnizone,
        n_werdykt_ok_czl=n_ok_czl, n_blad_czl=n_blad_czl,
        czas_na_pozycje="",   # do instrumentacji przegladu (uczciwie: brak danych)
    )


POLA_TREND = ["data", "zeinr", "n_pozycji", "n_zielony", "n_zolty", "n_czerwony",
              "odsetek_przegladu_proc", "n_flag_ai", "n_obnizone_ai",
              "n_werdykt_ok_czl", "n_blad_czl", "czas_na_pozycje"]


def dopisz_trend(metryka, trend_csv=None):
    """Dopisuje/aktualizuje wiersz trendu (klucz: data+zeinr). Zwraca sciezke."""
    trend_csv = Path(trend_csv or TREND_CSV)
    trend_csv.parent.mkdir(parents=True, exist_ok=True)
    wiersze = []
    if trend_csv.exists():
        wiersze = [r for r in _czytaj(trend_csv)
                   if not (r.get("data") == metryka["data"]
                           and r.get("zeinr") == metryka["zeinr"])]
    wiersze.append({k: metryka.get(k, "") for k in POLA_TREND})
    wiersze.sort(key=lambda r: (r.get("zeinr", ""), r.get("data", "")))
    with open(trend_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=POLA_TREND, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(wiersze)
    return trend_csv


def drukuj(m):
    print(f"\n=== METRYKA ZAUFANIA {m['zeinr']} ({m['data']}) ===")
    print(f"  pozycji: {m['n_pozycji']}  |  🟢 {m['n_zielony']}  🟡 {m['n_zolty']}  "
          f"🔴 {m['n_czerwony']}")
    print(f"  ODSETEK DO PRZEGLADU: {m['odsetek_przegladu_proc']}%  "
          f"(cel: maleje w czasie)")
    print(f"  flagi AI: {m['n_flag_ai']}  |  AI obnizylo: {m['n_obnizone_ai']}")
    print(f"  werdykty czlowieka: OK={m['n_werdykt_ok_czl']}  BLAD={m['n_blad_czl']}  "
          f"(cel bledow na laser: 0)")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    folder = argv[0]
    etykiety = argv[argv.index("--etykiety") + 1] if "--etykiety" in argv else None
    m = metryka_zlecenia(folder, etykiety)
    if m is None:
        print(f"[METRYKA] brak podsumowania/oceny w {folder} (GLOSNO)")
        return 1
    drukuj(m)
    if "--bez-trendu" not in argv:
        t = dopisz_trend(m)
        print(f"\n  trend: {t}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
