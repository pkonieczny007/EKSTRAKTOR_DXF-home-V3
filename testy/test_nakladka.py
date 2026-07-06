# -*- coding: utf-8 -*-
"""Testy NAKLADKI wynik-na-zrodlo (sprawdzanie/ai/nakladka.py) - kryteria bez ogladania.

Walidacja WIZUALNA zrobiona przez fable-advisor + orkiestratora (PNG obejrzane);
tu test LICZBOWY progow, ktore te obrazy potwierdzily:
  1. pelny wzorzec p3: pokrycie_zrodla wysokie, lustro_uzyte False, s_fit ~ 1/scale,
     ZERO zakreslen braku (braki_bboxy==[]);
  2. uszkodzony (usuniete otwory+fasola): pokrycie_zrodla < 97 + uwaga MOZLIWY BRAK CECHY
     + skupiska braku wykryte (braki_bboxy malejaco, najwieksze realne);
  3. lustro p4: lustro_uzyte True, ZERO falszywych zakreslen (braki_bboxy==[]);
  4. pusty wynik: uwaga WYNIK PUSTY + pokrycie 0 + braki_bboxy==[].
PNG musi powstac (>0 B).

Uzycie:  python testy\\test_nakladka.py     (exit 0 = PASS)
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
sys.path.insert(0, str(HERE.parent / "sprawdzanie" / "ai"))
from nakladka import nakladka  # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


ZR = GOLDEN / "SL10596945_fasola_odseparowana/wejscie/SL10596945_1_conv.dxf"
WZ = GOLDEN / "SL10596945_fasola_odseparowana/wzorzec/SL10596945_p3.dxf"
WZ_LUSTRO = GOLDEN / "SL10596945_fasola_odseparowana/wzorzec/SL10596945_p4_LUSTRO_z_p3.dxf"
BOX = (434.17, 153.97, 490.68, 206.05)
SCALE = 5.0

# root-fix szumu (wszystko na warstwie '1', geometria KOLOR 2)
ZR61 = GOLDEN / "SL40061302_sloty_odseparowane/wejscie/SL40061302_1_conv.dxf"
WZ61 = GOLDEN / "SL40061302_sloty_odseparowane/wzorzec/SL40061302_p1.dxf"
BOX61 = (50.83, 136.99, 194.3, 241.99)
SCALE61 = 2.0


def _has(uwagi, frag):
    return any(frag in u for u in uwagi)


def main():
    print("=== TESTY NAKLADKI wynik-na-zrodlo ===\n")
    tmp = Path(tempfile.mkdtemp(prefix="nakladka_"))
    try:
        # (1) pelny wzorzec -> wysokie pokrycie, brak lustra, skala fit ~ 1/scale
        r = nakladka(str(WZ), str(ZR), BOX, str(tmp / "pelny.png"), scale=SCALE)
        check("pelny pokrycie_zrodla", r["pokrycie_zrodla"] >= 99,
              f"pokrycie_zrodla={r['pokrycie_zrodla']}")
        check("pelny pokrycie", r["pokrycie"] >= 99, f"pokrycie={r['pokrycie']}")
        check("pelny bez lustra", r["align_info"]["lustro_uzyte"] is False,
              f"lustro_uzyte={r['align_info'].get('lustro_uzyte')}")
        check("pelny skala fit", abs(r["align_info"]["s_fit"] - 1 / SCALE) / (1 / SCALE) <= 0.05,
              f"s_fit={r['align_info']['s_fit']} vs {1/SCALE}")
        check("pelny anizotropia", r["align_info"]["anizotropia_proc"] <= 3.0,
              f"anizo={r['align_info']['anizotropia_proc']}")
        check("pelny PNG", (tmp / "pelny.png").stat().st_size > 0)
        check("pelny bez falszywej flagi braku", not _has(r["uwagi"], "MOZLIWY BRAK"),
              f"uwagi={r['uwagi']}")
        check("pelny 0 zakreslen braku", r["braki_bboxy"] == [], f"braki={r['braki_bboxy']}")
        check("pelny 0 szumu braku", r["align_info"].get("braki_szum_odfiltrowane") == 0,
              f"szum={r['align_info'].get('braki_szum_odfiltrowane')}")
        print(f"  pelny:     pokrycie={r['pokrycie']} pokrycie_zrodla={r['pokrycie_zrodla']} "
              f"lustro={r['align_info']['lustro_uzyte']} s_fit={r['align_info']['s_fit']:.4f} "
              f"braki={len(r['braki_bboxy'])}")

        # (2) uszkodzony: usun okregi + luki (fasole) -> BRAK cechy wykryty
        doc = ezdxf.readfile(WZ)
        msp = doc.modelspace()
        for e in list(msp):
            if e.dxftype() in ("CIRCLE", "ARC"):
                msp.delete_entity(e)
        usz = tmp / "uszkodzony.dxf"
        doc.saveas(usz)
        r2 = nakladka(str(usz), str(ZR), BOX, str(tmp / "uszkodzony.png"), scale=SCALE)
        check("uszkodzony pokrycie_zrodla<97", r2["pokrycie_zrodla"] < 97,
              f"pokrycie_zrodla={r2['pokrycie_zrodla']}")
        check("uszkodzony flaga braku", _has(r2["uwagi"], "MOZLIWY BRAK"),
              f"uwagi={r2['uwagi']}")
        check("uszkodzony braki wykryte", len(r2["braki_bboxy"]) >= 2,
              f"braki={len(r2['braki_bboxy'])}")
        check("uszkodzony braki malejaco", all(
            r2["braki_bboxy"][i]["dl_niepokryta"] >= r2["braki_bboxy"][i + 1]["dl_niepokryta"]
            for i in range(len(r2["braki_bboxy"]) - 1)), f"braki={r2['braki_bboxy']}")
        check("uszkodzony najwieksze skupisko realne",
              r2["braki_bboxy"][0]["dl_niepokryta"] >= 15,
              f"dl={r2['braki_bboxy'][0]['dl_niepokryta']}")
        print(f"  uszkodzony: pokrycie_zrodla={r2['pokrycie_zrodla']} "
              f"(flaga MOZLIWY BRAK: {_has(r2['uwagi'], 'MOZLIWY BRAK')}) "
              f"braki={len(r2['braki_bboxy'])} najw={r2['braki_bboxy'][0]['dl_niepokryta']}")

        # (3) lustro p4 na regionie p3 -> auto-lustro
        if WZ_LUSTRO.exists():
            r3 = nakladka(str(WZ_LUSTRO), str(ZR), BOX, str(tmp / "lustro.png"),
                          scale=SCALE)
            check("lustro auto-wykryte", r3["align_info"].get("lustro_uzyte") is True,
                  f"lustro_uzyte={r3['align_info'].get('lustro_uzyte')} "
                  f"norm={r3['align_info'].get('pokrycie_normal')} "
                  f"mir={r3['align_info'].get('pokrycie_lustro')}")
            check("lustro 0 falszywych zakreslen", r3["braki_bboxy"] == [],
                  f"braki={r3['braki_bboxy']}")
            print(f"  lustro p4: lustro_uzyte={r3['align_info'].get('lustro_uzyte')} "
                  f"(norm={r3['align_info'].get('pokrycie_normal')}% "
                  f"mir={r3['align_info'].get('pokrycie_lustro')}%)")

        # (4) pusty wynik -> GLOSNO, pokrycie 0
        pusty = tmp / "pusty.dxf"
        ezdxf.new(dxfversion="AC1021").saveas(pusty)
        r4 = nakladka(str(pusty), str(ZR), BOX, str(tmp / "pusty.png"), scale=SCALE)
        check("pusty flaga", _has(r4["uwagi"], "WYNIK PUSTY"), f"uwagi={r4['uwagi']}")
        check("pusty pokrycie 0", r4["pokrycie"] == 0.0, f"pokrycie={r4['pokrycie']}")
        check("pusty 0 zakreslen", r4["braki_bboxy"] == [], f"braki={r4['braki_bboxy']}")
        check("pusty PNG mimo braku", (tmp / "pusty.png").stat().st_size > 0)
        print(f"  pusty:     pokrycie={r4['pokrycie']} (flaga WYNIK PUSTY: "
              f"{_has(r4['uwagi'], 'WYNIK PUSTY')})")

        # (5) ROOT-FIX szumu: SL40061302 - WSZYSTKO na warstwie '1', geometria KOLOR 2,
        # adnotacje kolory 30/4/3. Fallback warstwowy wrzuca adnotacje do geom ->
        # POPRAWNY wzorzec dostawal pokrycie_zrodla 34% + 3 FALSZYWE skupiska (falszywe
        # flagi ucza ignorowania flag). pick_region_czysty bierze tryb czysty col2.
        # (bez fixu ten blok PADA - to jest jego sens: zmierzone 34.2% i 3 skupiska)
        if ZR61.exists() and WZ61.exists():
            r5 = nakladka(str(WZ61), str(ZR61), BOX61, str(tmp / "sl61302.png"), scale=SCALE61)
            check("root-fix tryb czysty col2",
                  r5["align_info"].get("tryb_geom") == "col2",
                  f"tryb_geom={r5['align_info'].get('tryb_geom')}")
            check("root-fix pokrycie_zrodla>=99 (bylo 34)",
                  r5["pokrycie_zrodla"] >= 99, f"pokrycie_zrodla={r5['pokrycie_zrodla']}")
            check("root-fix 0 falszywych skupisk (bylo 3)",
                  r5["braki_bboxy"] == [], f"braki={r5['braki_bboxy']}")
            check("root-fix bez falszywej flagi braku",
                  not _has(r5["uwagi"], "MOZLIWY BRAK"), f"uwagi={r5['uwagi']}")
            check("root-fix anizotropia <1% (bylo 3.15)",
                  r5["align_info"].get("anizotropia_proc", 99) < 1.0,
                  f"anizo={r5['align_info'].get('anizotropia_proc')}")
            print(f"  SL61302:   pokrycie_zrodla={r5['pokrycie_zrodla']} "
                  f"tryb={r5['align_info'].get('tryb_geom')} "
                  f"anizo={r5['align_info'].get('anizotropia_proc'):.2f}% "
                  f"braki={len(r5['braki_bboxy'])} (root-fix: bylo 34.2%/3 skupiska)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
    if FAILS:
        print("\n=== NAKLADKA: FAIL ===")
        for x in FAILS:
            print(f"  - {x}")
        return 1
    print("\n=== NAKLADKA: PASS ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
