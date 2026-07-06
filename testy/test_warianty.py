# -*- coding: utf-8 -*-
"""Testy WIELOWARIANTOWOSCI (Etap 3): produkcja/ocena.py::score_variants +
produkcja/warianty.py::warianty_pozycji / is_pl_z_raportu.

A) score_variants - 6 przypadkow (zwalidowane pomiarem przez fable-advisor):
   pelny vs niepelny -> W-C wygrywa, zolty (rozbieznosc);
   2 zgodne pelne -> zielony (pewnosc wysoka);
   wszystkie otwarte -> czerwony (bramka 2);
   wymiar niezgodny -> czerwony (bramka 1);
   interior>prawda -> zolty (smieci);
   brak wykazu -> zolty (wymiar niepotwierdzony).
B) warianty_pozycji na golden - W-C generowany REALNIE (region+warstwa) wygrywa
   z ubogim W-A (wzorzec bez okregow); zrodlo_prawda ze sweepa.
C) is_pl_z_raportu - status LUSTRO wykrywa pare P/L.

Uzycie:  python testy\\test_warianty.py     (exit 0 = PASS)
"""
import io
import shutil
import sys
import tempfile
from pathlib import Path

import ezdxf

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
GOLDEN = HERE / "golden"
sys.path.insert(0, str(HERE.parent / "produkcja"))
import ocena  # noqa: E402
import warianty  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


WZ = GOLDEN / "SL10596945_fasola_odseparowana/wzorzec/SL10596945_p3.dxf"
ZR = GOLDEN / "SL10596945_fasola_odseparowana/wejscie/SL10596945_1_conv.dxf"
BOX = (434.17, 153.97, 490.68, 206.05)
SCALE = 5.0
WYKAZ_DIM = (282.4, 260.24)


def _msp_full():
    return ezdxf.readfile(WZ).modelspace()          # interior 4


def _msp_bez_okregow():
    doc = ezdxf.readfile(WZ)
    m = doc.modelspace()
    for e in list(m):
        if e.dxftype() == "CIRCLE":
            m.delete_entity(e)
    return m                                          # interior 2 (ubogi)


def _msp_otwarty():
    doc = ezdxf.readfile(WZ)
    m = doc.modelspace()
    for e in list(m):
        if e.dxftype() == "LINE":
            m.delete_entity(e)                        # rozerwij kontur
            break
    return m


def test_score_variants():
    print("--- A) score_variants ---")
    # pelny vs niepelny -> W-C wygrywa, zolty
    r = ocena.score_variants(
        [{"nazwa": "W-C", "msp": _msp_full(), "plik": "wc"},
         {"nazwa": "W-A", "msp": _msp_bez_okregow(), "plik": "wa"}],
        zrodlo_prawda=4, wykaz_dim=WYKAZ_DIM)
    check("A1 zwyciezca W-C", r["zwyciezca"] == "W-C", f"zw={r['zwyciezca']}")
    check("A1 semafor zolty", r["semafor"] == "zolty", f"sem={r['semafor']}")

    # 2 zgodne pelne -> zielony
    r = ocena.score_variants(
        [{"nazwa": "W-C", "msp": _msp_full(), "plik": "wc"},
         {"nazwa": "W-B", "msp": _msp_full(), "plik": "wb"}],
        zrodlo_prawda=4, wykaz_dim=WYKAZ_DIM)
    check("A2 zielony", r["semafor"] == "zielony", f"sem={r['semafor']} powody={r['powody'][:1]}")
    check("A2 pewnosc wysoka", r["pewnosc"] == "wysoka", f"pewnosc={r['pewnosc']}")

    # wszystkie otwarte -> czerwony
    r = ocena.score_variants(
        [{"nazwa": "W-C", "msp": _msp_otwarty(), "plik": "wc"},
         {"nazwa": "W-A", "msp": _msp_otwarty(), "plik": "wa"}],
        zrodlo_prawda=4, wykaz_dim=WYKAZ_DIM)
    check("A3 czerwony", r["semafor"] == "czerwony", f"sem={r['semafor']}")
    check("A3 brak zwyciezcy", r["zwyciezca"] is None, f"zw={r['zwyciezca']}")

    # wymiar niezgodny -> czerwony
    r = ocena.score_variants(
        [{"nazwa": "W-C", "msp": _msp_full(), "plik": "wc"}],
        zrodlo_prawda=4, wykaz_dim=(999.0, 111.0))
    check("A4 czerwony wymiar", r["semafor"] == "czerwony", f"sem={r['semafor']}")

    # interior > prawda dla ZWYCIEZCY -> zolty (smieci): wszystkie nadmiarowe
    # (prawda=1, W-C=4, W-A=2 -> zwyciezca W-A delta=-1 < 0 -> flaga smieci)
    r = ocena.score_variants(
        [{"nazwa": "W-C", "msp": _msp_full(), "plik": "wc"},
         {"nazwa": "W-A", "msp": _msp_bez_okregow(), "plik": "wa"}],
        zrodlo_prawda=1, wykaz_dim=WYKAZ_DIM)
    check("A5 zolty smieci", r["semafor"] == "zolty", f"sem={r['semafor']}")
    check("A5 powod smieci", any("SMIECI" in p for p in r["powody"]), f"powody={r['powody']}")

    # brak wykazu -> zolty
    r = ocena.score_variants(
        [{"nazwa": "W-C", "msp": _msp_full(), "plik": "wc"},
         {"nazwa": "W-B", "msp": _msp_full(), "plik": "wb"}],
        zrodlo_prawda=4, wykaz_dim=None)
    check("A6 zolty bez wykazu", r["semafor"] == "zolty", f"sem={r['semafor']}")
    print("  6 przypadkow: pelny/niepelny, 2-zgodne, otwarte, zly-wymiar, smieci, bez-wykazu")


def test_warianty_pozycji():
    print("\n--- B) warianty_pozycji (W-C realny vs ubogi W-A) ---")
    tmp = Path(tempfile.mkdtemp(prefix="war_poz_"))
    try:
        # W-A ubogi = wzorzec bez okregow (interior 2), zapisany na dysk
        doc = ezdxf.readfile(WZ)
        m = doc.modelspace()
        for e in list(m):
            if e.dxftype() == "CIRCLE":
                m.delete_entity(e)
        wa = tmp / "SL10596945_p3__wA.dxf"
        doc.saveas(wa)

        src_msp = ezdxf.readfile(ZR).modelspace()
        decyzja, info_c = warianty.warianty_pozycji(
            src_msp, BOX, SCALE, WYKAZ_DIM, is_pl=True,
            wariantowe=[{"nazwa": "W-A", "dxf_path": str(wa)}],
            out_wc=tmp / "SL10596945_p3__wC.dxf")
        check("B zrodlo_prawda 4", decyzja["zrodlo_prawda"] == 4,
              f"prawda={decyzja['zrodlo_prawda']}")
        check("B W-C interior 4", info_c["interior"] == 4, f"interior={info_c['interior']}")
        check("B zwyciezca W-C", decyzja["zwyciezca"] == "W-C", f"zw={decyzja['zwyciezca']}")
        check("B W-C plik zapisany", (tmp / "SL10596945_p3__wC.dxf").exists())
        print(f"  zwyciezca={decyzja['zwyciezca']} prawda={decyzja['zrodlo_prawda']} "
              f"semafor={decyzja['semafor']} "
              f"(W-A interior={info_c['interior'] - decyzja['zrodlo_prawda'] + info_c['interior']})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_is_pl():
    print("\n--- C) is_pl_z_raportu ---")
    rows = [{"posn": "1", "status": "OK"},
            {"posn": "2", "status": "LUSTRO z poz. 1 - ZWERYFIKUJ"}]
    check("C poz1 P/L (blizniak lustrem)", warianty.is_pl_z_raportu(rows, 1) is True)
    check("C poz2 P/L (sama lustrem)", warianty.is_pl_z_raportu(rows, 2) is True)
    rows2 = [{"posn": "1", "status": "OK (TRYB BEZ WARSTW)"}]
    check("C poz1 nie-P/L", warianty.is_pl_z_raportu(rows2, 1) is False)
    print("  status LUSTRO -> P/L (obie strony pary)")


def main():
    print("=== TESTY WIELOWARIANTOWOSCI (Etap 3) ===\n")
    test_score_variants()
    test_warianty_pozycji()
    test_is_pl()
    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== WARIANTY: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== WARIANTY: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
