# -*- coding: utf-8 -*-
"""
RUNNER: uruchamia WSZYSTKIE testy V3 jedna komenda i zbiera PASS/FAIL.

Odpala po kolei (kazdy w osobnym procesie python) caly zestaw testow:
  - 4 nazwane rdzenne:  regresja, testy_v2, benchmark_v2, regresja_znane_bledy
  - wszystkie dynamiczne: testy/test_*.py
Lista budowana automatycznie (dedup + sort) - nowy test_*.py wchodzi sam z siebie.

Semantyka wyniku:
  - PASS  gdy kod wyjscia procesu == 0
  - FAIL  gdy kod wyjscia != 0 (albo timeout / wyjatek uruchomienia)
  - regresja_znane_bledy: XFAIL to NIE FAIL - ten test zwraca 1 tylko przy REGRESJI,
    wiec zwykla regula exit==0 dziala tu bez wyjatku.

Uzycie:
  python testy\\wszystkie.py            # pelny zestaw (wolno: benchmark + silnik)
  python testy\\wszystkie.py --szybko   # pomija wolne testy uruchamiajace silnik
                                         # (benchmark_v2, test_sweep_54_4867, test_gr4)

Kod wyjscia: 0 gdy wszystkie URUCHOMIONE testy PASS, inaczej 1.
Pominiete (--szybko) NIE licza sie jako FAIL, ale sa wypisane GLOSNO.
"""
import io
import sys
import time
import subprocess
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent

# rdzenne testy bez prefiksu test_ - trzeba je dopisac recznie (reszta z glob test_*.py)
NAZWANE = ["regresja", "testy_v2", "benchmark_v2", "regresja_znane_bledy"]

# testy wolne (uruchamiaja silnik przez subprocess / benchmark 36 plikow x2) -> --szybko je pomija
SKIP_SZYBKO = {"benchmark_v2", "test_sweep_54_4867", "test_gr4"}

TIMEOUT_S = 1800  # 30 min - twardy limit na pojedynczy test, zeby runner nie wisial


def zbierz_testy():
    """Lista sciezek testow: nazwane rdzenne + wszystkie test_*.py, bez duplikatow, sort."""
    stems = set(NAZWANE)
    for f in HERE.glob("test_*.py"):
        stems.add(f.stem)
    sciezki = []
    for stem in sorted(stems):
        p = HERE / f"{stem}.py"
        if p.exists():
            sciezki.append(p)
        else:
            print(f"  UWAGA: brak pliku dla '{stem}' - pomijam (sprawdz nazwe w NAZWANE)")
    return sciezki


def uruchom(path):
    """Uruchamia jeden test w podprocesie. Zwraca (ok, sekundy, kod, wyjscie_tekst)."""
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=TIMEOUT_S,
        )
        dt = time.perf_counter() - t0
        wyjscie = (r.stdout or "") + (r.stderr or "")
        return r.returncode == 0, dt, r.returncode, wyjscie
    except subprocess.TimeoutExpired as e:
        dt = time.perf_counter() - t0
        czesc = ((e.stdout or "") + (e.stderr or "")) if isinstance(e.stdout, str) else ""
        return False, dt, -1, czesc + f"\n[TIMEOUT po {TIMEOUT_S}s]"
    except Exception as e:  # noqa: BLE001
        dt = time.perf_counter() - t0
        return False, dt, -2, f"[BLAD URUCHOMIENIA]: {e}"


def ogon(tekst, n=18):
    """Ostatnie n niepustych linii wyjscia - do raportu bledu."""
    linie = [ln for ln in (tekst or "").splitlines() if ln.strip()]
    return "\n".join(linie[-n:])


def main():
    szybko = "--szybko" in sys.argv[1:]
    testy = zbierz_testy()

    print("=" * 66)
    print("RUNNER TESTOW V3 - testy/wszystkie.py" + ("   [TRYB --szybko]" if szybko else ""))
    print("=" * 66)

    pominiete = []
    if szybko:
        pominiete = [p for p in testy if p.stem in SKIP_SZYBKO]
        testy = [p for p in testy if p.stem not in SKIP_SZYBKO]
        if pominiete:
            print("\n!!! POMINIETO (--szybko), NIE URUCHOMIONE - wolne testy silnika/benchmark:")
            for p in pominiete:
                print(f"    - {p.stem}")
            print("    (uruchom BEZ --szybko przed oddaniem zmiany - to warunek regresji)")

    print(f"\nDo uruchomienia: {len(testy)} testow\n")

    wyniki = []  # (stem, ok, sekundy, kod, wyjscie)
    for p in testy:
        print(f"  >> {p.stem} ...", flush=True)
        ok, dt, kod, wyjscie = uruchom(p)
        znak = "PASS" if ok else "FAIL"
        print(f"     {znak}  ({dt:.1f}s)")
        wyniki.append((p.stem, ok, dt, kod, wyjscie))

    # --- tabela ---
    szer = max((len(s) for s, *_ in wyniki), default=10)
    print("\n" + "=" * 66)
    print("TABELA WYNIKOW")
    print("-" * 66)
    print(f"  {'nazwa':<{szer}}  {'wynik':<6}  {'czas':>8}")
    print(f"  {'-' * szer}  {'-' * 6}  {'-' * 8}")
    for stem, ok, dt, kod, _ in wyniki:
        print(f"  {stem:<{szer}}  {'PASS' if ok else 'FAIL':<6}  {dt:>7.1f}s")
    for p in pominiete:
        print(f"  {p.stem:<{szer}}  {'POMIN':<6}  {'--':>8}  (--szybko)")
    print("-" * 66)

    n_pass = sum(1 for _, ok, *_ in wyniki if ok)
    n_uruch = len(wyniki)
    print(f"\nPODSUMOWANIE: {n_pass}/{n_uruch} PASS", end="")
    if pominiete:
        print(f"   (+{len(pominiete)} POMINIETO --szybko)", end="")
    print()

    # --- szczegoly bledow ---
    fails = [(s, kod, w) for s, ok, dt, kod, w in wyniki if not ok]
    if fails:
        print("\n" + "=" * 66)
        print("SZCZEGOLY BLEDOW (ostatnie linie wyjscia)")
        for stem, kod, wyjscie in fails:
            print("-" * 66)
            print(f"  FAIL: {stem}  (kod wyjscia {kod})")
            for ln in ogon(wyjscie).splitlines():
                print(f"    | {ln}")

    print("\n" + "=" * 66)
    if fails:
        print(f"=== WSZYSTKIE: FAIL ({len(fails)} test(ow) padlo) ===")
    else:
        print("=== WSZYSTKIE: PASS ===")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
