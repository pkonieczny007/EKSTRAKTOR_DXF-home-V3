# -*- coding: utf-8 -*-
"""Test golden GRUPY gr4 (zlecenie 38_1847) - sweep kompletnosci end-to-end.

Grupa 6 rysunkow, 10 pozycji: 8 poprawnych + 2 REALNE bledy z produkcji (zasada 11).
Sprawdza, ze sweep (bramka 5 / bilans_konturow) na PRAWDZIWEJ partii:

  HEADLINE - SL40052110_p1 = ZWODNICZA ZIELEN: wynik ma kontur DOMKNIETY i wymiar
    1000x345 co do mm, sam plik przechodzi bramke 5 bez flagi (interior=4, spojny).
    Dopiero porownanie z REGIONEM ZRODLA (12 konturow) ujawnia strate 8 cech
    -> delta=8 -> ZOLTY. To blad, ktory stary licznik cyklomatyczny przepuscil
    (zrodlo zasmiecone 176 wymiarami zmylilo kontrole liczbowa) - dowod, ze
    samokontrola wyniku NIE wystarcza, sweep-vs-zrodlo jest obowiazkowy.

  SL40852200_p1 = OTWARTY KONTUR + strata: silnik zgubil sloty (5->3) i zostawil
    otwarty kontur -> bramka 2 (NIEDOMKNIETE) -> CZERWONY (nie na laser).

  8 poprawnych pozycji (846315, 851203 x3, 851344 x2, 851345 x2) = ZIELONY, delta=0
    -> ZERO falszywych flag (perforacja SBM 63=63, sloty, okregi domkniete).

Uwaga: ZIELONY sweepa = KOMPLETNOSC OK (0 zgubionych konturow, kontur domkniety).
Status 🟡 z ANALIZA_gr4.md dla 851203_p2 / 851344_p2 / 851345_p2 dotyczy INNEJ osi
(giecie / para P-L do potwierdzenia) - nie kompletnosci, wiec sprzecznosci brak.

Uzycie:  python testy\\test_gr4.py     (exit 0 = PASS)
"""
import io
import sys
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
GOLD = HERE / "golden" / "38_1847_gr4"
sys.path.insert(0, str(HERE.parent / "produkcja" / "kontrola"))
from sweep import sweep_zlecenie                                    # noqa: E402
from bilans_konturow import count_interior_contours_shapely        # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


# ground truth calej partii (zmierzone sweepem, potwierdzone wzrokiem w ANALIZA_gr4.md)
OCZEK = {
    ("SL40846315", "1"): dict(zrodlo=4,  wynik=4,  delta=0, semafor="zielony"),
    ("SL40851203", "1"): dict(zrodlo=3,  wynik=3,  delta=0, semafor="zielony"),
    ("SL40851203", "2"): dict(zrodlo=0,  wynik=0,  delta=0, semafor="zielony"),
    ("SL40851203", "3"): dict(zrodlo=2,  wynik=2,  delta=0, semafor="zielony"),
    ("SL40851344", "1"): dict(zrodlo=63, wynik=63, delta=0, semafor="zielony"),
    ("SL40851344", "2"): dict(zrodlo=4,  wynik=4,  delta=0, semafor="zielony"),
    ("SL40851345", "1"): dict(zrodlo=63, wynik=63, delta=0, semafor="zielony"),
    ("SL40851345", "2"): dict(zrodlo=4,  wynik=4,  delta=0, semafor="zielony"),
    ("SL40852200", "1"): dict(zrodlo=5,  wynik=3,  delta=2, semafor="czerwony"),  # otwarty
    ("SL40052110", "1"): dict(zrodlo=12, wynik=4,  delta=8, semafor="zolty"),     # zwodnicza zielen
}


def _load(rel):
    return ezdxf.readfile(GOLD / rel).modelspace()


def test_sweep_grupy():
    print("--- A) SWEEP calej grupy gr4 (10 pozycji) ---")
    wiersze, braki = sweep_zlecenie(GOLD / "wynikow", GOLD / "wejscie")
    check("brak brakow zrodla", not braki, f"braki={braki}")
    check("10 pozycji", len(wiersze) == len(OCZEK), f"pozycji={len(wiersze)}")

    by = {(w["zeinr"], str(w["posn"])): w for w in wiersze}
    for key, oc in OCZEK.items():
        w = by.get(key)
        if w is None:
            check(f"{key} obecna", False, "brak w wynikach sweepa")
            continue
        znak = {"zielony": "🟢", "zolty": "🟡", "czerwony": "🔴"}[w["semafor"]]
        for pole in ("zrodlo", "wynik", "delta", "semafor"):
            check(f"{key[0]}_p{key[1]} {pole}", w[pole] == oc[pole],
                  f"{pole}={w[pole]} != {oc[pole]}")
        print(f"  {znak} {key[0]}_p{key[1]:2} zrodlo={w['zrodlo']:>3} wynik="
              f"{'?' if w['wynik'] is None else w['wynik']:>3} delta="
              f"{'?' if w['delta'] is None else w['delta']:>2}  {w['semafor']}")

    licz = {s: sum(1 for w in wiersze if w["semafor"] == s)
            for s in ("zielony", "zolty", "czerwony")}
    check("8 zielonych", licz["zielony"] == 8, f"zielony={licz['zielony']}")
    check("1 zolty", licz["zolty"] == 1, f"zolty={licz['zolty']}")
    check("1 czerwony", licz["czerwony"] == 1, f"czerwony={licz['czerwony']}")
    print(f"  bilans grupy: {licz['zielony']}🟢 / {licz['zolty']}🟡 / {licz['czerwony']}🔴")

    # HEADLINE: zwodnicza zielen 052110 wykryta wlasnie przez sweep-vs-zrodlo
    w52 = by[("SL40052110", "1")]
    check("052110 delta=8 (zwodnicza zielen zlapana)", w52["delta"] == 8,
          f"delta={w52['delta']}")
    check("052110 tryb warstwa_geom", w52["tryb"] == "warstwa_geom", f"tryb={w52['tryb']}")

    # 852200 czerwony z powodu OTWARTEGO konturu (bramka 2), nie samej delty
    w22 = by[("SL40852200", "1")]
    check("852200 powod = otwarty kontur", "otwarty kontur" in w22["powod"],
          f"powod={w22['powod'][:60]}")
    return wiersze


def test_bramka5_wprost():
    """Dowod, ze samokontrola WYNIKU nie wystarcza dla 052110 - potrzebny sweep."""
    print("\n--- B) BRAMKA 5 wprost na dostarczonych plikach ---")

    # 052110: kontur domkniety, spojny sam w sobie -> ZERO flag mimo utraty 8 cech
    n52, d52 = count_interior_contours_shapely(_load("wynikow/SL40052110/SL40052110_p1.dxf"))
    check("052110 interior=4", n52 == 4, f"interior={n52}")
    check("052110 bez flag (samokontrola slepa na strate)", not d52["flags"],
          f"flags={d52['flags']}")
    print(f"  SL40052110_p1: interior={n52} flags={d52['flags'] or 'BRAK'} "
          f"-> sam plik wyglada OK, strate widac TYLKO vs zrodlo (=12)")

    # 852200: otwarty kontur -> bramka 5 sama flaguje NIEDOMKNIETE (twarda bramka 2)
    n22, d22 = count_interior_contours_shapely(_load("wynikow/SL40852200/SL40852200_p1.dxf"))
    otwarty = any(fl.startswith("NIEDOMKNIETE") for fl in d22["flags"])
    check("852200 NIEDOMKNIETE", otwarty, f"flags={d22['flags']}")
    print(f"  SL40852200_p1: interior={n22} NIEDOMKNIETE={otwarty} "
          f"-> otwarty kontur = nie na laser (bramka 2)")


def main():
    print("=== TEST GOLDEN gr4 (38_1847) - sweep kompletnosci ===\n")
    test_sweep_grupy()
    test_bramka5_wprost()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== gr4: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== gr4: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
