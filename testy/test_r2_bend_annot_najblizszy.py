# -*- coding: utf-8 -*-
"""Test R2 — adnotacja giecia przypisana do NAJBLIZSZEGO klastra, nie do kazdego bbox.

Cel (RYZYKO 2, audyt rankingu): `features.bend_annot` liczyl +2 dla KAZDEGO kandydata,
ktorego bbox zawiera punkt adnotacji giecia - a bend_texts sa z CALEGO msp. Adnotacja
giecia widoku A, wpadajaca geometrycznie w (wiekszy) bbox kandydata B o tych samych
proporcjach wykazu, dawala B falszywe +2 do geo i mogla PRZEWROCIC ranking na zly klaster.

Fix (`_bend_annot_nearest`): kazda adnotacja giecia -> jeden NAJBLIZSZY klaster (srodkiem
bbox, jak babelek kategorii 4). Scenariusz: A maly wlasciwy widok, B duzy klaster o bbox
zawierajacym region A; adnotacja na A (w bbox OBU) nalezy tylko do A.

Uzycie:  python testy\\test_r2_bend_annot_najblizszy.py     (exit 0 = PASS)
"""
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "produkcja" / "silniki"))
sys.path.insert(0, str(ROOT / "produkcja" / "kontrola"))
import detektor_rozwiniecia as det      # noqa: E402

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _old_bbox_count(cluster, bend_texts):
    """Stara logika 'punkt w bbox' - do udokumentowania fałszywego +2."""
    b = cluster["bbox"]
    return sum(1 for (x, y, _) in bend_texts
               if b[0] <= x <= b[2] and b[1] <= y <= b[3])


def main():
    # A = wlasciwy widok (maly, wycentrowany na adnotacji); B = duzy kandydat,
    # ktorego bbox zawiera region A (np. rozproszony klaster o tej samej proporcji).
    A = {"bbox": (0.0, 0.0, 60.0, 40.0)}
    B = {"bbox": (-20.0, -20.0, 200.0, 120.0)}
    clusters = [A, B]
    bend = [(30.0, 20.0, "gekantet")]   # adnotacja na A; lezy w bbox A ORAZ B

    # --- NOWE: adnotacja nalezy TYLKO do A (najblizszy srodek bbox) ---
    check("nowy_A_ma_adnotacje", det._bend_annot_nearest(A, clusters, bend) == 1,
          f"A bend_annot={det._bend_annot_nearest(A, clusters, bend)} (oczekiwano 1)")
    check("nowy_B_bez_falszywego", det._bend_annot_nearest(B, clusters, bend) == 0,
          f"B bend_annot={det._bend_annot_nearest(B, clusters, bend)} (oczekiwano 0 - "
          f"adnotacja nalezy do A, nie do B mimo ze w bbox B)")

    # --- STARE (dowod ze R2 realne): 'w bbox' dawaloby OBA -> B falszywe +2 ---
    check("stary_A_liczyl", _old_bbox_count(A, bend) == 1, "stare: A w bbox")
    check("stary_B_falszywy", _old_bbox_count(B, bend) == 1,
          f"stare: B tez w bbox={_old_bbox_count(B, bend)} -> falszywe +2 (to naprawiamy)")

    # --- niezmiennik: adnotacja poza wszystkimi -> najblizszy i tak dostaje (jak kat.4) ---
    daleko = [(500.0, 500.0, "gekantet")]
    suma = (det._bend_annot_nearest(A, clusters, daleko) +
            det._bend_annot_nearest(B, clusters, daleko))
    check("adnotacja_daleko_do_jednego", suma == 1,
          f"adnotacja daleko: przypisana do dokladnie 1 klastra (suma={suma})")

    # --- integracja przez features(): bend_annot uzywa nowej reguly ---
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    ra = [msp.add_line((0, 0), (60, 0)), msp.add_line((60, 0), (60, 40)),
          msp.add_line((60, 40), (0, 40)), msp.add_line((0, 40), (0, 0))]
    rb = [msp.add_line((-20, -20), (200, -20)), msp.add_line((-20, 120), (200, 120))]
    A2 = {"entities": ra, "bbox": (0.0, 0.0, 60.0, 40.0), "w": 60.0, "h": 40.0}
    B2 = {"entities": rb, "bbox": (-20.0, -20.0, 200.0, 120.0), "w": 220.0, "h": 140.0}
    cl2 = [A2, B2]
    fa = det.features(A2, cl2, None, bend)
    fb = det.features(B2, cl2, None, bend)
    check("features_A_bend1", fa["bend_annot"] == 1, f"features(A).bend_annot={fa['bend_annot']}")
    check("features_B_bend0", fb["bend_annot"] == 0,
          f"features(B).bend_annot={fb['bend_annot']} (bez falszywego +2)")

    print(f"CHECKS={CHECKS}  FAILS={len(FAILS)}")
    for f in FAILS:
        print("  FAIL:", f)
    if FAILS:
        print("\n[R2 CZERWONY] — sprawdz _bend_annot_nearest.")
        sys.exit(1)
    print("[R2 ZIELONY] — adnotacja giecia -> najblizszy klaster (brak falszywego +2).")
    sys.exit(0)


if __name__ == "__main__":
    main()
