# -*- coding: utf-8 -*-
"""Ekstrakcja REGION+WARSTWA - root-fix na zgubione cechy odseparowane.

Klaster po sasiedztwie (V1) gubi fasole/sloty/wyspy niepolaczone z konturem
zewnetrznym. Ale te cechy LEZA WEWNATRZ obwiedni konturu -> mieszcza sie w bbox
widoku z raportu. Wiec: bierzemy WSZYSTKIE encje WARSTWY GEOMETRII w bbox widoku
(nie tylko spojny klaster), transformujemy tak jak kontur, czyscimy.

Reguly czyszczenia (kontekst/wiedza/):
  - okregi wspolsrodkowe/zdublowane -> zostaw NAJMNIEJSZY na srodek.
  - linie giecia (kolor 6): zostaw gdy P/L albo skos>5st od osi; nie-P/L proste -> usun.
Uzycie: python _region_warstwa.py   (przetwarza liste CASES nizej)
"""
import sys, io, csv, math
from pathlib import Path
from collections import Counter, defaultdict
import ezdxf
from ezdxf.math import Matrix44
from ezdxf import bbox as _bb

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HERE = Path(__file__).resolve().parent
WYN = HERE / "wyniki_rysowanie"
OUT = HERE / "poprawki_region_warstwa"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))
from _licznik_konturow import count_interior_contours

GEOM_TYPES = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE", "SPLINE", "ELLIPSE"}
SKIP_TYPES = {"DIMENSION", "MTEXT", "TEXT", "LEADER", "INSERT", "POINT"}


def report_row(zeinr, posn):
    rap = WYN / zeinr / f"{zeinr}_raport.csv"
    with open(rap, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if int(r["posn"]) == posn:
                return r
    return None


def center(e):
    try:
        return _bb.extents([e]).center
    except Exception:
        return None


def in_bbox(c, x1, y1, x2, y2, m=1.0):
    return c is not None and x1 - m <= c.x <= x2 + m and y1 - m <= c.y <= y2 + m


def detect_geom_layer(msp, box):
    """Warstwa geometrii = najczestsza warstwa encji GEOM koloru 7 w bbox."""
    cnt = Counter()
    for e in msp:
        if e.dxftype() not in GEOM_TYPES:
            continue
        if e.dxf.color != 7:
            continue
        c = center(e)
        if in_bbox(c, *box):
            cnt[e.dxf.layer] += 1
    return cnt.most_common(1)[0][0] if cnt else None


def is_skos(e, tol_deg=5.0):
    """Linia pod skosem = kat > tol od poziomu/pionu."""
    if e.dxftype() != "LINE":
        return True  # ARC/poly na warstwie giecia traktuj jak skos (zostaw)
    dx = e.dxf.end.x - e.dxf.start.x
    dy = e.dxf.end.y - e.dxf.start.y
    if abs(dx) < 1e-6 and abs(dy) < 1e-6:
        return False
    ang = math.degrees(math.atan2(abs(dy), abs(dx)))  # 0..90
    d = min(ang, abs(90 - ang))                        # odleglosc od osi
    return d > tol_deg


def extract(zeinr, posn, is_pl, name):
    r = report_row(zeinr, posn)
    x1, y1 = float(r["src_x1"]), float(r["src_y1"])
    x2, y2 = float(r["src_x2"]), float(r["src_y2"])
    scale = float(r["scale"])
    box = (x1, y1, x2, y2)
    doc = ezdxf.readfile(WYN / zeinr / f"{zeinr}_1_conv.dxf")
    msp = doc.modelspace()
    geom_layer = detect_geom_layer(msp, box)

    picked, bends = [], []
    for e in msp:
        if e.dxf.layer != geom_layer:
            continue
        if e.dxftype() in SKIP_TYPES or e.dxftype() not in GEOM_TYPES:
            continue
        c = center(e)
        if not in_bbox(c, *box):
            continue
        (bends if e.dxf.color == 6 else picked).append(e)

    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    m = Matrix44.translate(-cx, -cy, 0) @ Matrix44.scale(scale, scale, 1)

    new = ezdxf.new(dxfversion="AC1021")
    new.layers.add("GIECIE", color=6)
    nmsp = new.modelspace()

    # kontur + otwory
    circles = []
    for e in picked:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = "0"
        ne.dxf.color = 7
        if ne.dxftype() == "CIRCLE":
            circles.append(ne)
        else:
            nmsp.add_entity(ne)
    # okregi wspolsrodkowe/zdublowane -> najmniejszy na srodek
    by = defaultdict(list)
    for ne in circles:
        by[(round(ne.dxf.center.x, 1), round(ne.dxf.center.y, 1))].append(ne)
    n_circ_raw = len(circles)
    for grp in by.values():
        grp.sort(key=lambda c: c.dxf.radius)
        nmsp.add_entity(grp[0])
    n_circ = len(by)

    # linie giecia
    kept_bends = 0
    for e in bends:
        keep = is_pl or is_skos(e)
        if not keep:
            continue
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = "GIECIE"
        ne.dxf.color = 6
        nmsp.add_entity(ne)
        kept_bends += 1

    ext = _bb.extents(nmsp)
    mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2,
                            -(ext.extmin.y + ext.extmax.y) / 2, 0)
    for e in nmsp:
        e.transform(mv)
    ext = _bb.extents(nmsp)
    nmsp.reset_extents((ext.extmin.x, ext.extmin.y, 0), (ext.extmax.x, ext.extmax.y, 0))

    out_path = OUT / f"{name}.dxf"
    new.saveas(out_path)
    ic, det = count_interior_contours(nmsp)
    return dict(name=name, w=round(max(ext.size.x, ext.size.y), 1),
                h=round(min(ext.size.x, ext.size.y), 1), circ=n_circ,
                circ_raw=n_circ_raw, bends_src=len(bends), bends_kept=kept_bends,
                interior=ic, layer=geom_layer, path=out_path)


def mirror(base_name, dst_name):
    doc = ezdxf.readfile(OUT / f"{base_name}.dxf")
    msp = doc.modelspace()
    for e in msp:
        try:
            e.transform(Matrix44.scale(-1, 1, 1))
        except Exception:
            pass
    ext = _bb.extents(msp)
    mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2,
                            -(ext.extmin.y + ext.extmax.y) / 2, 0)
    for e in msp:
        e.transform(mv)
    ext = _bb.extents(msp)
    msp.reset_extents((ext.extmin.x, ext.extmin.y, 0), (ext.extmax.x, ext.extmax.y, 0))
    doc.saveas(OUT / f"{dst_name}.dxf")
    ic, _ = count_interior_contours(msp)
    return dict(name=dst_name, w=round(max(ext.size.x, ext.size.y), 1),
                h=round(min(ext.size.x, ext.size.y), 1), interior=ic, mirror_of=base_name)


# (zeinr, posn, is_pl, name, mirror_name|None)
CASES = [
    ("SL10585490", 1, True,  "SL10585490_p1P", "SL10585490_p2L"),
    ("SL40051182", 1, True,  "SL40051182_p1P", "SL40051182_p2L"),
    ("SL10596954", 1, False, "SL10596954_p1",  None),
    ("SL40071953", 1, True,  "SL40071953_p1P", "SL40071953_p2L"),
    ("SL10596953", 1, False, "SL10596953_p1",  None),
    ("SL10596953", 2, False, "SL10596953_p2",  None),
    ("SL10596954", 2, False, "SL10596954_p2",  None),
    ("SL10599245", 1, True,  "SL10599245_p1",  None),
    ("SL10599245", 2, True,  "SL10599245_p2",  None),  # p2 = OSOBNY widok (nie lustro)
    ("SL41061329", 1, False, "SL41061329_p1",  None),
    ("SL10599171", 1, False, "SL10599171_p1",  None),  # wykryte sweepem: +4 sloty poziome
]


def main():
    print(f"=== REGION+WARSTWA -> {OUT} ===\n")
    print(f"{'nazwa':22} {'wymiar':14} {'okr':>4} {'okr_raw':>7} {'gie_src':>7} {'gie_ok':>6} {'kontury':>7}  warstwa")
    for zeinr, posn, is_pl, name, mname in CASES:
        try:
            res = extract(zeinr, posn, is_pl, name)
        except Exception as e:
            print(f"{name:22} BLAD: {e}")
            continue
        print(f"{res['name']:22} {str(res['w'])+'x'+str(res['h']):14} {res['circ']:>4} "
              f"{res['circ_raw']:>7} {res['bends_src']:>7} {res['bends_kept']:>6} {res['interior']:>7}  L{res['layer']}")
        if mname:
            mr = mirror(name, mname)
            print(f"{mr['name']:22} {str(mr['w'])+'x'+str(mr['h']):14} {'':>4} {'':>7} {'':>7} {'':>6} {mr['interior']:>7}  (lustro z {name})")


if __name__ == "__main__":
    main()
