# -*- coding: utf-8 -*-
"""
ORKIESTRATOR V3 - wejscie systemu produkcyjnego (CLAUDE.md: pipeline).

ETAP 1 (PLAN.md) - PARYTET: deleguje 1:1 do silnika W-B (V2: kategorie+weryfikator),
dokladajac na wejsciu TYPOWANIE rysunku (informacyjnie). Dzieki temu V3 dziala
od pierwszego dnia dokladnie tak dobrze jak V2 (benchmark), a kolejne etapy
(warianty W-A/W-C, ocena, bramki 5/10) dokladaja sie bez psucia parytetu.

Uzycie (argumenty jak silnik W-B, przekazywane wprost):
  python produkcja\\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>
                                    [--galeria] [--korpus [plik.csv]]

Po kazdej zmianie tutaj: python testy\\regresja.py + testy\\testy_v2.py (PASS!).
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SILNIK_WB = HERE / "silniki" / "v2" / "orkiestrator.py"

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

    print(f"[V3] etap 1 - parytet: delegacja do silnika W-B ({SILNIK_WB.name})",
          flush=True)
    return subprocess.call([sys.executable, str(SILNIK_WB), *argv])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
