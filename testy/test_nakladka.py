# -*- coding: utf-8 -*-
"""Testy NAKLADKI wynik-na-zrodlo (sprawdzanie/ai/nakladka.py) - kryteria bez ogladania.

Walidacja WIZUALNA zrobiona przez fable-advisor + orkiestratora (PNG obejrzane);
tu test LICZBOWY progow, ktore te obrazy potwierdzily:
  1. pelny wzorzec p3: pokrycie_zrodla wysokie, lustro_uzyte False, s_fit ~ 1/scale;
  2. uszkodzony (usuniete otwory+fasola): pokrycie_zrodla < 97 + uwaga MOZLIWY BRAK CECHY;
  3. lustro p4: lustro_uzyte True;
  4. pusty wynik: uwaga WYNIK PUSTY + pokrycie 0.
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
        print(f"  pelny:     pokrycie={r['pokrycie']} pokrycie_zrodla={r['pokrycie_zrodla']} "
              f"lustro={r['align_info']['lustro_uzyte']} s_fit={r['align_info']['s_fit']:.4f}")

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
        print(f"  uszkodzony: pokrycie_zrodla={r2['pokrycie_zrodla']} "
              f"(flaga MOZLIWY BRAK: {_has(r2['uwagi'], 'MOZLIWY BRAK')})")

        # (3) lustro p4 na regionie p3 -> auto-lustro
        if WZ_LUSTRO.exists():
            r3 = nakladka(str(WZ_LUSTRO), str(ZR), BOX, str(tmp / "lustro.png"),
                          scale=SCALE)
            check("lustro auto-wykryte", r3["align_info"].get("lustro_uzyte") is True,
                  f"lustro_uzyte={r3['align_info'].get('lustro_uzyte')} "
                  f"norm={r3['align_info'].get('pokrycie_normal')} "
                  f"mir={r3['align_info'].get('pokrycie_lustro')}")
            print(f"  lustro p4: lustro_uzyte={r3['align_info'].get('lustro_uzyte')} "
                  f"(norm={r3['align_info'].get('pokrycie_normal')}% "
                  f"mir={r3['align_info'].get('pokrycie_lustro')}%)")

        # (4) pusty wynik -> GLOSNO, pokrycie 0
        pusty = tmp / "pusty.dxf"
        ezdxf.new(dxfversion="AC1021").saveas(pusty)
        r4 = nakladka(str(pusty), str(ZR), BOX, str(tmp / "pusty.png"), scale=SCALE)
        check("pusty flaga", _has(r4["uwagi"], "WYNIK PUSTY"), f"uwagi={r4['uwagi']}")
        check("pusty pokrycie 0", r4["pokrycie"] == 0.0, f"pokrycie={r4['pokrycie']}")
        check("pusty PNG mimo braku", (tmp / "pusty.png").stat().st_size > 0)
        print(f"  pusty:     pokrycie={r4['pokrycie']} (flaga WYNIK PUSTY: "
              f"{_has(r4['uwagi'], 'WYNIK PUSTY')})")
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
