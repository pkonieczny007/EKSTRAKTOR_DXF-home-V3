# -*- coding: utf-8 -*-
"""
PRZEBIEG ZLECENIA (P0.1 audytu 2026-07-06) - JEDNA komenda spinajaca caly tor.

Powod (audyt sekcja 5 P0.1 + realny defekt SL40034116): warstwy POMIARU (sweep,
sprawdz_folder, metryka) istnieja w kodzie, ale nikt ich nie odpala na zleceniach
-> bledy uciekaja (4 zlecenia bez sladu nakladek/sweepa/metryki). Ten skrypt tylko
WYWOLUJE istniejace moduly (subprocess) w kolejnosci pipeline'u; NIC nie zmienia
w produkcja/. Zasada 7 ("zlecenie domyka sweep") przestaje byc deklaracja.

Kroki (kazdy logowany, kazdy = subprocess istniejacego modulu):
  (a) produkcja/orkiestrator.py       - ekstrakcja (default warianty; --parytet = sam W-B)
  (b) produkcja/raport.py --wykaz     - merge ocen/raportow + writeback do KOPII wykazu
  (c) sprawdzanie/ai/sprawdz_folder.py- nakladki wynik-na-zrodlo + flagi kompletnosci
  (d) produkcja/kontrola/sweep.py     - sweep kompletnosci region-vs-zrodlo (zasada 7)
  (e) sprawdzanie/czlowiek/przeglad.py- galeria przegladu    (pomijalne: --bez-galerii)
  (f) zarzadzanie/metryka.py          - metryka zaufania      (pomijalne: --bez-metryki)

GLOSNOSC (zasada 15): krok padl -> wyrazny blok w konsoli + KONTYNUACJA pozostalych
krokow + niezerowy exit na koncu. Podsumowanie = tabela rysunek x krok x status x
czas x artefakty. NIGDY cichy sukces przy padnietym kroku.

Uwaga o layoutach (dlaczego sweep jest "stagowany"): raport/sprawdz_folder/przeglad/
metryka pracuja na FLAT folderze jednego rysunku (biora pierwszy *_ocena.csv). sweep.py
wymaga natomiast layoutu <folder>/<zeinr>/<zeinr>_raport.csv + osobnego folderu rysunkow
(wyn_path = folder/zeinr/file). Przebieg NIE zmienia sweepa - buduje mu tymczasowy
staging (_sweep_<zeinr>/) z bboxow raportu + zwycieskich plikow produkcyjnych i podaje
zrodlo jako <zeinr>_1_conv.dxf. Dla FOLDERU rysunkow kazdy rysunek dostaje wlasny
podfolder wynikow (bo moduly ww. sa per-rysunek).

Uzycie:
  python produkcja\\przebieg.py <conv.dxf|folder_z_conv> <wykaz.xlsx> <folder_wynikow>
                                [--parytet] [--bez-galerii] [--bez-metryki]

Po zmianie tutaj: python testy\\test_przebieg.py (PASS).
"""
import csv
import io
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent            # produkcja/
REPO = HERE.parent                                # korzen repo

# moduly wywolywane (jedno zrodlo prawdy sciezek)
ORK = HERE / "orkiestrator.py"
RAP = HERE / "raport.py"
SPR = REPO / "sprawdzanie" / "ai" / "sprawdz_folder.py"
SWEEP = HERE / "kontrola" / "sweep.py"
PRZ = REPO / "sprawdzanie" / "czlowiek" / "przeglad.py"
MET = REPO / "zarzadzanie" / "metryka.py"
RAPORTY = REPO / "testy" / "raporty"

PY = sys.executable

# nazwy krokow (kolejnosc pipeline'u = kolejnosc listy w _plan_krokow)
K_ORK, K_RAP, K_SPR, K_SWEEP, K_PRZ, K_MET = (
    "orkiestrator", "raport", "sprawdz_folder", "sweep", "przeglad", "metryka")


# --------------------------------------------------------------- narzedzia pomocnicze
def _zeinr_z_conv(conv):
    """zeinr z nazwy pliku conv (strip _1_conv / _conv / _1) - jak w warianty.py."""
    s = Path(conv).stem
    for suf in ("_1_conv", "_conv", "_1"):
        if s.endswith(suf):
            return s[: -len(suf)]
    return s


def _read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _run_cmd(nazwa, cmd):
    """Domyslny runner kroku: subprocess w korzeniu repo, wyjscie STRUMIENIOWANE
    (dziecko drukuje na zywo - GLOSNO). Zwraca kod wyjscia. nazwa = tylko do stubu."""
    try:
        r = subprocess.run([str(c) for c in cmd], cwd=str(REPO))
        return r.returncode
    except Exception as e:                          # brak interpretera/pliku itp.
        print(f"[PRZEBIEG] !! nie udalo sie uruchomic '{nazwa}': {e} (GLOSNO)")
        return 99


# --------------------------------------------------------------- staging dla sweepa
def _bbox_raport(out_dir, zeinr):
    """Wiersze raportu silnika z bboxem zrodla (src_x1..). Preferuje parytet-root,
    potem warianty/wB, wA. [] gdy brak - sweep bez bboxow niemozliwy."""
    for cand in (out_dir / f"{zeinr}_raport.csv",
                 out_dir / "warianty" / "wB" / f"{zeinr}_raport.csv",
                 out_dir / "warianty" / "wA" / f"{zeinr}_raport.csv"):
        if cand.exists():
            try:
                rows = [r for r in _read_csv(cand) if r.get("src_x1")]
            except Exception as e:
                print(f"[PRZEBIEG] nie wczytano {cand.name} ({e}) (GLOSNO)")
                continue
            if rows:
                return rows
    return []


def _zwyciezcy(out_dir, zeinr):
    """{posn: plik_produkcyjny}. Wielowariant: ocena.csv (plik_produkcyjny);
    parytet: root raport (file). Zwyciezcy leza FLAT w out_dir."""
    win = {}
    oce = out_dir / f"{zeinr}_ocena.csv"
    if oce.exists():
        for r in _read_csv(oce):
            p = (r.get("plik_produkcyjny") or "").strip()
            if p and p != "-":
                try:
                    win[int(r["posn"])] = p
                except (KeyError, ValueError):
                    pass
        return win
    rap = out_dir / f"{zeinr}_raport.csv"
    if rap.exists():
        for r in _read_csv(rap):
            f = (r.get("file") or "").strip()
            if f:
                try:
                    win[int(r["posn"])] = f
                except (KeyError, ValueError):
                    pass
    return win


def _stage_sweep(out_dir, conv, zeinr):
    """Buduje layout wymagany przez sweep.py z FLAT folderu wynikow (nie ruszajac
    sweepa). Zwraca (cmd, powod). cmd=None + powod gdy staging niemozliwy (GLOSNO).

    stage_wyn/<zeinr>/<zeinr>_raport.csv (posn+bbox+file) + skopiowane zwycieskie DXF;
    stage_rys/<zeinr>_1_conv.dxf (zrodlo)."""
    bbox_rows = _bbox_raport(out_dir, zeinr)
    if not bbox_rows:
        return None, "brak raportu silnika z bboxem (src_x1) - sweep niemozliwy"
    if not Path(conv).exists():
        return None, f"brak zrodla {Path(conv).name} - sweep niemozliwy"

    win = _zwyciezcy(out_dir, zeinr)
    stage_wyn = out_dir / f"_sweep_{zeinr}"
    inner = stage_wyn / zeinr
    stage_rys = out_dir / f"_sweep_{zeinr}_rys"
    # czysty start (idempotencja) - stary staging nie moze zaklamac wyniku
    for d in (stage_wyn, stage_rys):
        shutil.rmtree(d, ignore_errors=True)
    inner.mkdir(parents=True, exist_ok=True)
    stage_rys.mkdir(parents=True, exist_ok=True)

    rows_out = []
    skopiowane = 0
    for r in bbox_rows:
        try:
            posn = int(r["posn"])
            bbox = {k: float(r[k]) for k in ("src_x1", "src_y1", "src_x2", "src_y2")}
        except (KeyError, ValueError):
            continue
        plik = win.get(posn, "")
        file_name = ""
        if plik and (out_dir / plik).exists():
            try:
                shutil.copy(out_dir / plik, inner / plik)
                file_name = plik
                skopiowane += 1
            except Exception as e:
                print(f"[PRZEBIEG] sweep-staging p{posn}: nie skopiowano {plik} ({e}) (GLOSNO)")
        rows_out.append(dict(posn=posn, file=file_name, **bbox))

    if not rows_out:
        return None, "raport bez wierszy z bboxem - sweep niemozliwy"

    with open(inner / f"{zeinr}_raport.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, delimiter=";",
                           fieldnames=["posn", "src_x1", "src_y1", "src_x2", "src_y2", "file"])
        w.writeheader()
        w.writerows(rows_out)

    try:
        shutil.copy(conv, stage_rys / f"{zeinr}_1_conv.dxf")
    except Exception as e:
        return None, f"nie skopiowano zrodla do staging ({e})"

    if skopiowane == 0:
        print(f"[PRZEBIEG] sweep {zeinr}: 0 zwycieskich DXF do sprawdzenia - sweep "
              f"oflaguje braki plikow (GLOSNO)")
    return [PY, str(SWEEP), str(stage_wyn), str(stage_rys)], ""


# --------------------------------------------------------------- artefakty (do tabeli)
def _istniejace(sciezki):
    out = []
    for p in sciezki:
        p = Path(p)
        if p.exists():
            out.append(p.name + ("/" if p.is_dir() else ""))
    return ", ".join(out) if out else "-"


def _artefakty(nazwa, out_dir, zeinr, wykaz):
    out_dir = Path(out_dir)
    if nazwa == K_ORK:
        n_dxf = len(list(out_dir.glob(f"{zeinr}_p*.dxf")))
        base = _istniejace([out_dir / f"{zeinr}_ocena.csv", out_dir / f"{zeinr}_raport.csv"])
        return f"{base}; {n_dxf} DXF" if n_dxf else base
    if nazwa == K_RAP:
        art = [out_dir / f"{zeinr}_podsumowanie.csv"]
        if wykaz:
            wp = Path(wykaz)
            art.append(wp.with_name(f"{wp.stem}_WYNIKI{wp.suffix}"))
        return _istniejace(art)
    if nazwa == K_SPR:
        return _istniejace([out_dir / f"{zeinr}_sprawdzanie_ai.csv",
                            out_dir / "sprawdzanie_ai"])
    if nazwa == K_SWEEP:
        # sweep pisze do testy/raporty/sweep_<name>.csv (name = _sweep_<zeinr>)
        return _istniejace([RAPORTY / f"sweep__sweep_{zeinr}.csv"])
    if nazwa == K_PRZ:
        return _istniejace([out_dir / "przeglad.html",
                            out_dir / f"{zeinr}_werdykty_do_wypelnienia.csv"])
    if nazwa == K_MET:
        return _istniejace([RAPORTY / "metryka_zaufania.csv"])
    return "-"


# --------------------------------------------------------------- plan i wykonanie
def _plan_krokow(conv, wykaz, out_dir, zeinr, parytet, bez_galerii, bez_metryki):
    """Lista (nazwa, cmd, pomin, powod_pomin). cmd == 'SWEEP' = sentinel (staging w
    czasie wykonania - po tym jak orkiestrator/raport zdazyly wyprodukowac dane)."""
    conv_parent = str(Path(conv).resolve().parent)
    cmd_ork = [PY, str(ORK), str(conv), str(wykaz), str(out_dir)]
    if parytet:
        cmd_ork.append("--parytet")
    return [
        (K_ORK, cmd_ork, False, ""),
        (K_RAP, [PY, str(RAP), str(out_dir), str(conv), "--wykaz", str(wykaz)], False, ""),
        (K_SPR, [PY, str(SPR), str(out_dir), str(conv)], False, ""),
        (K_SWEEP, "SWEEP", False, ""),
        (K_PRZ, [PY, str(PRZ), str(out_dir), "--rysunki", conv_parent],
         bez_galerii, "pominieto (--bez-galerii)"),
        (K_MET, [PY, str(MET), str(out_dir)], bez_metryki, "pominieto (--bez-metryki)"),
    ]


def przebieg_rysunku(conv, wykaz, out_dir, zeinr=None, parytet=False,
                     bez_galerii=False, bez_metryki=False, run_fn=None):
    """Uruchamia caly tor dla JEDNEGO rysunku. Zwraca liste rekordow krokow
    (dict: rysunek, krok, status, czas_s, artefakty, powod). run_fn wstrzykiwane
    (test podaje stub; domyslnie subprocess)."""
    run_fn = run_fn or _run_cmd
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    zeinr = zeinr or _zeinr_z_conv(conv)

    print("\n" + "=" * 70)
    print(f"PRZEBIEG: {zeinr}   conv={Path(conv).name}   -> {out_dir}")
    print("=" * 70)

    rekordy = []
    for nazwa, cmd, pomin, powod_pomin in _plan_krokow(
            conv, wykaz, out_dir, zeinr, parytet, bez_galerii, bez_metryki):
        if pomin:
            print(f"\n[{zeinr}/{nazwa}] POMINIETO - {powod_pomin}")
            rekordy.append(dict(rysunek=zeinr, krok=nazwa, status="POMIN",
                                czas_s=0.0, artefakty="-", powod=powod_pomin))
            continue

        # sentinel: sweep = zbuduj staging teraz (po orkiestratorze/raporcie)
        powod = ""
        if cmd == "SWEEP":
            cmd, powod = _stage_sweep(out_dir, conv, zeinr)
            if cmd is None:
                print(f"\n[{zeinr}/{nazwa}] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"[{zeinr}/{nazwa}] KROK POMINIETY (staging niemozliwy): {powod}")
                print(f"[{zeinr}/{nazwa}] sweep obowiazkowy (zasada 7) -> exit != 0 (GLOSNO)")
                print(f"[{zeinr}/{nazwa}] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                rekordy.append(dict(rysunek=zeinr, krok=nazwa, status="FAIL",
                                    czas_s=0.0, artefakty="-", powod=powod))
                continue

        print(f"\n[{zeinr}/{nazwa}] >> {' '.join(str(c) for c in cmd)}", flush=True)
        t0 = time.perf_counter()
        try:
            kod = run_fn(nazwa, cmd)
        except Exception as e:                      # runner nie moze wywrocic calego toru
            kod = 98
            print(f"[{zeinr}/{nazwa}] wyjatek runnera: {e} (GLOSNO)")
        dt = round(time.perf_counter() - t0, 1)

        if kod == 0:
            art = _artefakty(nazwa, out_dir, zeinr, wykaz)
            print(f"[{zeinr}/{nazwa}] OK ({dt}s)  artefakty: {art}")
            rekordy.append(dict(rysunek=zeinr, krok=nazwa, status="OK",
                                czas_s=dt, artefakty=art, powod=powod))
        else:
            art = _artefakty(nazwa, out_dir, zeinr, wykaz)
            print(f"\n[{zeinr}/{nazwa}] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"[{zeinr}/{nazwa}] KROK PADL (kod wyjscia {kod}) - KONTYNUUJE pozostale")
            print(f"[{zeinr}/{nazwa}] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            rekordy.append(dict(rysunek=zeinr, krok=nazwa, status="FAIL",
                                czas_s=dt, artefakty=art, powod=f"kod wyjscia {kod}"))
    return rekordy


def _zadania(zrodlo, folder_wynikow):
    """Lista (conv_path, out_dir, zeinr). Plik .dxf -> jedno zadanie (FLAT out).
    Folder -> petla po *_conv.dxf, kazdy do wlasnego podfolderu (moduly sa per-rysunek)."""
    zrodlo = Path(zrodlo)
    folder_wynikow = Path(folder_wynikow)
    if zrodlo.is_file():
        return [(zrodlo, folder_wynikow, _zeinr_z_conv(zrodlo))]
    if zrodlo.is_dir():
        convs = sorted(zrodlo.glob("*_conv.dxf"))
        if not convs:
            print(f"[PRZEBIEG] BRAK plikow *_conv.dxf w {zrodlo} (GLOSNO)")
            return []
        zad = []
        for c in convs:
            z = _zeinr_z_conv(c)
            zad.append((c, folder_wynikow / z, z))
        return zad
    print(f"[PRZEBIEG] zrodlo nie istnieje: {zrodlo} (GLOSNO)")
    return []


def przebieg(zrodlo, wykaz, folder_wynikow, parytet=False, bez_galerii=False,
             bez_metryki=False, run_fn=None):
    """Caly przebieg (1 rysunek albo folder). Zwraca (rekordy, kod_wyjscia).
    kod_wyjscia != 0 gdy jakikolwiek krok = FAIL (zasada 15)."""
    zadania = _zadania(zrodlo, folder_wynikow)
    if not zadania:
        return [], 2

    rekordy = []
    for conv, out_dir, zeinr in zadania:
        rekordy += przebieg_rysunku(conv, wykaz, out_dir, zeinr=zeinr, parytet=parytet,
                                    bez_galerii=bez_galerii, bez_metryki=bez_metryki,
                                    run_fn=run_fn)

    fail = _drukuj_podsumowanie(rekordy, len(zadania))
    return rekordy, (1 if fail else 0)


IKONA = {"OK": "OK  ", "FAIL": "FAIL", "POMIN": "POMIN"}


def _drukuj_podsumowanie(rekordy, n_rysunkow):
    """Tabela rysunek x krok x status x czas x artefakty. Zwraca True gdy jakis FAIL."""
    szer_r = max((len(r["rysunek"]) for r in rekordy), default=8)
    szer_k = max((len(r["krok"]) for r in rekordy), default=12)
    print("\n" + "=" * 70)
    print(f"PODSUMOWANIE PRZEBIEGU ({n_rysunkow} rysunek/-ow)")
    print("-" * 70)
    print(f"  {'rysunek':<{szer_r}}  {'krok':<{szer_k}}  {'status':<5}  {'czas':>6}  artefakty")
    print(f"  {'-'*szer_r}  {'-'*szer_k}  {'-'*5}  {'-'*6}  {'-'*9}")
    for r in rekordy:
        print(f"  {r['rysunek']:<{szer_r}}  {r['krok']:<{szer_k}}  "
              f"{r['status']:<5}  {r['czas_s']:>5}s  {r['artefakty']}")
    print("-" * 70)

    fails = [r for r in rekordy if r["status"] == "FAIL"]
    pomin = [r for r in rekordy if r["status"] == "POMIN"]
    ok = [r for r in rekordy if r["status"] == "OK"]
    print(f"\n  OK: {len(ok)}  |  FAIL: {len(fails)}  |  POMIN: {len(pomin)}")
    if fails:
        print("\n  !!! KROKI KTORE PADLY (GLOSNO, exit != 0):")
        for r in fails:
            print(f"    - {r['rysunek']}/{r['krok']}: {r['powod']}")
        print("\n=== PRZEBIEG: FAIL (niektore kroki padly - patrz wyzej) ===")
    else:
        print("\n=== PRZEBIEG: OK (wszystkie uruchomione kroki PASS) ===")
    return bool(fails)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if len(argv) < 3:
        print("Uzycie: python produkcja\\przebieg.py <conv.dxf|folder> <wykaz.xlsx> "
              "<folder_wynikow> [--parytet] [--bez-galerii] [--bez-metryki]")
        return 2

    zrodlo, wykaz, folder_wynikow = argv[0], argv[1], argv[2]
    parytet = "--parytet" in argv
    bez_galerii = "--bez-galerii" in argv
    bez_metryki = "--bez-metryki" in argv

    if not Path(wykaz).exists():
        print(f"[PRZEBIEG] wykaz nie istnieje: {wykaz} (GLOSNO)")
        return 2

    _, kod = przebieg(zrodlo, wykaz, folder_wynikow, parytet=parytet,
                      bez_galerii=bez_galerii, bez_metryki=bez_metryki)
    return kod


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
