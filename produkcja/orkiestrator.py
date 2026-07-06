# -*- coding: utf-8 -*-
"""
ORKIESTRATOR V3 - wejscie systemu produkcyjnego (CLAUDE.md: pipeline).

ETAP 3 (PLAN.md) - DEFAULT WIELOWARIANTOWOSC: generuje 2-3 warianty (W-A klaster /
W-B kategorie / W-C region+warstwa) i ocena wybiera zwyciezce na laser (bramki
1/2/5/10, produkcja/warianty.py). benchmark_v3 potwierdzil V3>=V2 (zasada 10).
TYPOWANIE rysunku dokladane na wejsciu (informacyjnie).
  --parytet = stary tryb (sam W-B, szybszy, do debugowania/porownania).

Historia: etap 1 = parytet 1:1 do W-B (V3 == V2 od pierwszego dnia); etapy 2-3
dolozyly kompletnosc (bramka 5, sweep, nakladka, W-C) i wybor wariantu bez regresu.

Uzycie:
  python produkcja\\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>
                                    [--parytet]  # opt-out do samego W-B

Po kazdej zmianie tutaj: python testy\\testy_v2.py + testy\\benchmark_v3.py (PASS!).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SILNIK_WB = HERE / "silniki" / "v2" / "orkiestrator.py"
WARIANTY = HERE / "warianty.py"

sys.path.insert(0, str(HERE))
import typowanie  # noqa: E402


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    rysunek = Path(argv[0])
    if rysunek.suffix.lower() == ".dxf" and rysunek.exists():
        try:
            typy = typowanie.okresl_typy(rysunek)
            opis = ", ".join(f"{t['typ']} ({t['pewnosc']}, {t['powod']})" for t in typy)
            print(f"[V3] typowanie: {opis}", flush=True)
        except Exception as e:  # typowanie jest informacyjne - nie blokuje produkcji
            print(f"[V3] typowanie pominiete ({e})", flush=True)

    # ETAP 3 - DEFAULT: wielowariantowosc W-A/W-B/W-C + ocena wybiera zwyciezce
    # (benchmark_v3 V3>=V2 PASS - zasada 10 spelniona). --parytet = stary tryb (sam
    # W-B), szybszy (1 silnik), do debugowania/porownania.
    if "--parytet" in argv:
        rest = [a for a in argv if a != "--parytet"]
        print(f"[V3] tryb PARYTET (opt-out): delegacja do W-B ({SILNIK_WB.name})",
              flush=True)
        return subprocess.call([sys.executable, str(SILNIK_WB), *rest])

    rest = [a for a in argv if a != "--warianty"]
    print("[V3] etap 3 - WIELOWARIANTOWOSC (default): W-A/W-B/W-C + ocena wybiera zwyciezce",
          flush=True)
    return subprocess.call([sys.executable, str(WARIANTY), *rest])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
