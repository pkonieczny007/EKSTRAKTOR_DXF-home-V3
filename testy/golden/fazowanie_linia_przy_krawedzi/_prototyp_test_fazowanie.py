# -*- coding: utf-8 -*-
"""Pomiar prototypu flagera fazowania: pozytywy golden + negatywy + sweep gr6
+ bonus: korelacja z rzutem bocznym w zrodle."""
import os
import sys

import ezdxf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fazowanie_flager import wykryj_fazowanie, potwierdz_rzutem_bocznym

ROOT = r"C:\Python_CLaude\EKSTRAKTOR_DXF\EKSTRAKTOR_DXF-home-V3"
GOLD = os.path.join(ROOT, r"testy\golden\fazowanie_linia_przy_krawedzi")
GR6 = os.path.join(ROOT, r"wyniki\38_1847\gr6")

# (plik, oczekiwane_fazowanie)
CASES = [
    (os.path.join(GOLD, r"wynikow_biezacy\SL10585238_p2.dxf"), True),
    (os.path.join(GOLD, r"wynikow_biezacy\SL10585242_p2.dxf"), True),
    (os.path.join(GR6, "SL10584847_p2.dxf"), False),
    (os.path.join(GR6, "SL10409233_p1.dxf"), False),
    (os.path.join(GR6, "SL10585238_p1.dxf"), False),
    # sweep rozszerzony (dodatkowe negatywy + kopie pozytywow w gr6)
    (os.path.join(GR6, "SL10584847_p1.dxf"), False),
    (os.path.join(GR6, "SL10584847_p3.dxf"), False),
    (os.path.join(GR6, "SL10585242_p1.dxf"), False),
    (os.path.join(GR6, "SL10585238_p2.dxf"), True),
    (os.path.join(GR6, "SL10585242_p2.dxf"), True),
]

tp = fp = tn = fn = 0
print("=" * 78)
for path, expected in CASES:
    name = os.path.basename(path)
    doc = ezdxf.readfile(path)
    kand = wykryj_fazowanie(doc.modelspace())
    got = len(kand) > 0
    ok = got == expected
    if expected and got:
        tp += 1
    elif expected and not got:
        fn += 1
    elif not expected and got:
        fp += 1
    else:
        tn += 1
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name:22s} oczekiwane={'FAZA' if expected else 'brak'} "
          f"wykryto={len(kand)} kandydatow")
    for k in kand:
        print(f"       d={k['dystans_mm']}mm L={k['dlugosc_mm']}mm "
              f"krawedz={k['dlugosc_krawedzi_mm']}mm ratio={k['ratio']} "
              f"T-zlacza={k['t_zlacza']} pas_pusty={k['pas_pusty']} "
              f"pewnosc={k['pewnosc']}")

print("=" * 78)
prec = tp / (tp + fp) if tp + fp else float("nan")
rec = tp / (tp + fn) if tp + fn else float("nan")
print(f"TP={tp} FP={fp} TN={tn} FN={fn}  precision={prec:.2f} recall={rec:.2f}")

# ---------------------------------------------------------------- BONUS
print()
print("BONUS: korelacja z rzutem bocznym w zrodle")


def explode(msp):
    out = []
    for e in msp:
        if e.dxftype() == "INSERT":
            try:
                out.extend(list(e.virtual_entities()))
            except Exception:
                pass
        else:
            out.append(e)
    return out


# mapowanie kandydata z wyniku (mm 1:1) do wsp. zrodla: y_src = y1 - (y_top - y)/skala
BONUS = [
    # (zrodlo, bbox widoku, warstwa, skala, wynik)
    (os.path.join(GOLD, r"wejscie\SL10585238_1.dxf"),
     (267.62, 117.09, 311.62, 123.09), "102", 5.0,
     os.path.join(GOLD, r"wynikow_biezacy\SL10585238_p2.dxf")),
    (os.path.join(GOLD, r"wejscie\SL10585242_1.dxf"),
     (271.03, 107.90, 300.03, 113.90), "102", 5.0,
     os.path.join(GOLD, r"wynikow_biezacy\SL10585242_p2.dxf")),
]
for src_path, bbox, layer, scale, res_path in BONUS:
    doc_r = ezdxf.readfile(res_path)
    kand = wykryj_fazowanie(doc_r.modelspace())
    assert kand, "brak kandydata w wyniku"
    k = kand[0]
    # wynik jest wysrodkowany; krawedz fazowana pozioma -> os y.
    # ekstenty wyniku:
    ys = [p[1] for p in (k["edge"][0], k["edge"][1])]
    y_edge_res = ys[0]
    y_line_res = k["t_zlacza"][0][1]
    # zaloz: gorna krawedz wyniku odpowiada gornej krawedzi bboxu widoku
    x0, y0, x1, y1 = bbox
    if y_edge_res > y_line_res:      # krawedz nad linia -> gora widoku
        t_edge_src = y1
        t_line_src = y1 - (y_edge_res - y_line_res) / scale
    else:
        t_edge_src = y0
        t_line_src = y0 + (y_line_res - y_edge_res) / scale
    ents = explode(ezdxf.readfile(src_path).modelspace())
    hit = potwierdz_rzutem_bocznym(ents, bbox, layer, t_line_src, t_edge_src,
                                   axis="y")
    print(f"{os.path.basename(src_path):20s} t_line_src={t_line_src:.2f} "
          f"t_edge_src={t_edge_src:.2f} -> rzut boczny: {hit}")
