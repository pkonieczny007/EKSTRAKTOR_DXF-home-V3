# -*- coding: utf-8 -*-
"""Test gwintu (REDESIGN 2026-07-08): DOMYSLNIE zachowany+ZOLTY, transformacja NA ZADANIE.

Golden: testy/golden/gwint_hb450/wzorzec/SL10582645_p5.dxf - realny wynik 1:1 z 8x gwint
M12 (Hardox HB450). Plan operatora (2026-07-08 REDESIGN):
  - DOMYSLNIE (kazdy material): gwint ZOSTAJE (okrag+luk), oznaczony ZOLTO (kolor 2),
    status pozycji min. 🟡 (jak fazowanie) - oznacz_gwinty();
  - NA ZADANIE (flaga --transformuj-gwint): luk USUN, okrag POWIEKSZ wg KLASY materialu
    (trudnoscieralne M12->10.6 / zwykle M12->10.2), CZERWONY - zastosuj_do_pliku();
  - nieznana wartosc w tablicy -> gwint zostaje + ZOLTY (kotwica operatora).

Scenariusze (wszystkie na KOPII pliku - golden nietkniety):
  1. DEFAULT oznacz_gwinty      -> 8 arcs+8 circ ZOSTAJA, wszystkie ZOLTE (kolor 2), status zolty
  2. transform trudnoscieralne  -> 8 lukow out, 8 okregow czerwonych r=5.3 (o10.6)
  3. transform zwykle (S355)    -> 8 lukow out, 8 okregow czerwonych r=5.1 (o10.2)  [NOWE]
  4. transform HB450 + null     -> gwint zostaje ZOLTY (M12 bez wartosci)
  5. INTEGRACJA raport.scal: bez flagi -> ZOLTE; --transformuj-gwint HB450 -> CZERWONE

Uzycie:  python testy\\test_gwint_hardox_transformacja.py     (exit 0 = PASS)
"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent
GOLDEN = HERE / "golden" / "gwint_hb450" / "wzorzec" / "SL10582645_p5.dxf"
sys.path.insert(0, str(ROOT / "produkcja" / "kontrola"))
import gwint as gw          # noqa: E402

# tablice dwuklasowe (format wczytaj_tablice): rozne srednice per klasa
TAB_PELNA = {"trudnoscieralne": {"M12": 10.6}, "zwykle": {"M12": 10.2}}
TAB_NULL = {"trudnoscieralne": {"M12": None}, "zwykle": {"M12": None}}

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _stan(path):
    m = ezdxf.readfile(str(path)).modelspace()
    arcs = [e for e in m if e.dxftype() == "ARC"]
    circ = [e for e in m if e.dxftype() == "CIRCLE"]
    czerw = [c for c in circ if c.dxf.color == 1]
    zolte = [e for e in (arcs + circ) if e.dxf.color == gw.KOLOR_UWAGA]
    _, gwinty = gw.thread_arcs(m)
    return len(arcs), len(circ), len(gwinty), czerw, zolte


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        a0, c0, g0, cz0, zo0 = _stan(GOLDEN)
        check("wzorzec_8_gwintow", g0 == 8 and a0 == 8 and c0 == 8 and len(cz0) == 0,
              f"wzorzec: arcs={a0} circ={c0} gwinty={g0} czerwone={len(cz0)} (oczekiwano 8/8/8/0)")

        # --- 1) DEFAULT: oznacz_gwinty -> gwint ZOSTAJE, ZOLTY, status zolty ---
        p1 = tmp / "default.dxf"
        shutil.copy(GOLDEN, p1)
        n, kom, stat = gw.oznacz_gwinty(p1)
        a1, c1, g1, cz1, zo1 = _stan(p1)
        check("default_8_oznaczone", n == 8, f"n={n} (oczekiwano 8)")
        check("default_luki_zostaja", a1 == 8, f"arcs po={a1} (oczekiwano 8 - gwint ZACHOWANY)")
        check("default_okregi_zostaja", c1 == 8, f"circ po={c1} (oczekiwano 8)")
        check("default_zero_czerwonych", len(cz1) == 0, f"czerwone={len(cz1)} (oczekiwano 0)")
        check("default_16_zoltych", len(zo1) == 16,
              f"zolte(luk+okrag)={len(zo1)} (oczekiwano 16 = 8 lukow + 8 okregow)")
        check("default_status_zolty", stat == "zolty", f"status={stat} (oczekiwano 'zolty')")
        check("default_komentarz_m12", "M12" in kom and "x8" in kom, f"komentarz='{kom[:70]}'")

        # --- 2) transform trudnoscieralne (M12->10.6) ---
        p2 = tmp / "hardox.dxf"
        shutil.copy(GOLDEN, p2)
        n2, kom2, stat2 = gw.zastosuj_do_pliku(p2, "Blech s=8 HB450", TAB_PELNA)
        a2, c2, g2, cz2, zo2 = _stan(p2)
        check("hardox_8_zmienione", n2 == 8, f"n={n2} (oczekiwano 8)")
        check("hardox_luki_usuniete", a2 == 0, f"arcs po={a2} (oczekiwano 0)")
        check("hardox_8_czerwonych", len(cz2) == 8, f"czerwone={len(cz2)} (oczekiwano 8)")
        prom2 = sorted(set(round(c.dxf.radius, 2) for c in cz2))
        check("hardox_srednica_10_6", prom2 == [5.3], f"promienie={prom2} (oczekiwano [5.3]=o10.6)")
        check("hardox_status_none", stat2 is None, f"status={stat2} (wszystko zmienione)")

        # --- 3) transform zwykle (S355 -> M12->10.2) [NOWE: zwykly TEZ transformuje] ---
        p3 = tmp / "zwykly.dxf"
        shutil.copy(GOLDEN, p3)
        n3, kom3, stat3 = gw.zastosuj_do_pliku(p3, "S355JR", TAB_PELNA)
        a3, c3, g3, cz3, zo3 = _stan(p3)
        check("zwykly_8_zmienione", n3 == 8, f"n={n3} (oczekiwano 8)")
        check("zwykly_luki_usuniete", a3 == 0, f"arcs po={a3} (oczekiwano 0)")
        prom3 = sorted(set(round(c.dxf.radius, 2) for c in cz3))
        check("zwykly_srednica_10_2", prom3 == [5.1], f"promienie={prom3} (oczekiwano [5.1]=o10.2)")
        check("zwykly_inna_srednica_niz_hardox", prom2 != prom3,
              f"hardox={prom2} zwykly={prom3} (klasa materialu MUSI dawac inna srednice)")

        # --- 4) transform + pusta wartosc -> gwint zostaje ZOLTY ---
        p4 = tmp / "null.dxf"
        shutil.copy(GOLDEN, p4)
        n4, kom4, stat4 = gw.zastosuj_do_pliku(p4, "HB450", TAB_NULL)
        a4, c4, g4, cz4, zo4 = _stan(p4)
        check("null_zostaw", n4 == 0 and a4 == 8, f"n={n4} arcs={a4} (oczekiwano 0/8 - gwint zostaje)")
        check("null_zolte", len(zo4) == 16, f"zolte={len(zo4)} (oczekiwano 16 - oznaczone do decyzji)")
        check("null_status_zolty", stat4 == "zolty", f"status={stat4} (oczekiwano 'zolty')")

        # --- golden NIETKNIETY ---
        ag, cg, gg, czg, zog = _stan(GOLDEN)
        check("golden_nietkniety", ag == 8 and cg == 8 and len(czg) == 0 and len(zog) == 0,
              f"golden po testach: arcs={ag} circ={cg} czerwone={len(czg)} zolte={len(zog)} (MUSI 8/8/0/0)")

        # --- 5) INTEGRACJA raport.scal ---
        import csv
        import openpyxl
        sys.path.insert(0, str(ROOT / "produkcja"))
        import raport
        zeinr = "SL10582645"

        def _setup_scal(nazwa):
            folder = tmp / nazwa
            folder.mkdir()
            with open(folder / f"{zeinr}_ocena.csv", "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, delimiter=";",
                                   fieldnames=["posn", "semafor", "powod",
                                               "plik_produkcyjny", "zwyciezca"])
                w.writeheader()
                w.writerow(dict(posn="5", semafor="zielony", powod="",
                                plik_produkcyjny=f"{zeinr}_p5.dxf", zwyciezca="W-C"))
            shutil.copy(GOLDEN, folder / f"{zeinr}_p5.dxf")
            wb = openpyxl.Workbook()
            wsx = wb.active
            wsx.append(["Zeinr", "Posn", "Bezeichnung"])
            wsx.append([zeinr, 5, "Blech s=8 HB450"])
            wykaz = folder / "wykaz.xlsx"
            wb.save(wykaz)
            return folder, wykaz

        # 5a) DOMYSLNIE (bez flagi): gwint ZOSTAJE, ZOLTY, status obnizony zielony->zolty
        folder_a, wykaz_a = _setup_scal("scal_default")
        _, rek_a = raport.scal(str(folder_a), None, str(wykaz_a))
        aa, ca, _g, cza, zoa = _stan(folder_a / f"{zeinr}_p5.dxf")
        check("scal_default_zostaje", aa == 8 and len(cza) == 0 and len(zoa) == 16,
              f"scal default: arcs={aa} czerwone={len(cza)} zolte={len(zoa)} (oczekiwano 8/0/16)")
        check("scal_default_status_zolty", rek_a and rek_a[0]["semafor"] == "zolty",
              f"semafor={rek_a[0]['semafor'] if rek_a else '?'} (oczekiwano 'zolty' - obnizony)")
        check("scal_default_tech_gwint?", rek_a and "gwint?" in rek_a[0]["technologia"],
              f"technologia={rek_a[0]['technologia'] if rek_a else '?'} (oczekiwano 'gwint?')")

        # 5b) --transformuj-gwint HB450: luk out, okrag CZERWONY o10.6
        folder_b, wykaz_b = _setup_scal("scal_transform")
        _, rek_b = raport.scal(str(folder_b), None, str(wykaz_b), transformuj_gwint=True)
        ab, cb, _g2, czb, zob = _stan(folder_b / f"{zeinr}_p5.dxf")
        check("scal_transform_czerwone", ab == 0 and len(czb) == 8,
              f"scal --transformuj: arcs={ab} czerwone={len(czb)} (oczekiwano 0/8)")
        prom_b = sorted(set(round(c.dxf.radius, 2) for c in czb))
        check("scal_transform_10_6", prom_b == [5.3], f"promienie={prom_b} (oczekiwano [5.3]=o10.6 Hardox)")
        check("scal_transform_tech_gwint", rek_b and "gwint" in rek_b[0]["technologia"]
              and "gwint?" not in rek_b[0]["technologia"],
              f"technologia={rek_b[0]['technologia'] if rek_b else '?'} (oczekiwano 'gwint' bez ?)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"CHECKS={CHECKS}  FAILS={len(FAILS)}")
    for f in FAILS:
        print("  FAIL:", f)
    if FAILS:
        print("\n[GWINT CZERWONY]")
        sys.exit(1)
    print("[GWINT ZIELONY] — default zachowany+zolty; transform na zadanie 10.6/10.2 czerwony; brak->zolty.")
    sys.exit(0)


if __name__ == "__main__":
    main()
