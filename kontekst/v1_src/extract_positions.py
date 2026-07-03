# -*- coding: utf-8 -*-
"""
Ekstrakcja pozycji blaszanych z rysunku warsztatowego DXF.

Zasada dzialania (rysunki z warstwami numerycznymi 1NN = pozycja NN):
  1. Dla kazdej warstwy pozycyjnej zbierz encje GEOMETRYCZNE
     (LINE/ARC/CIRCLE/ELLIPSE/SPLINE/POLYLINE) - pomija wymiary, teksty,
     osie (CENTER/PHANTOM/DASHDOT) i kreskowania.
  2. Klastruj geometrie przestrzennie (union-find po bbox z tolerancja)
     -> kazdy klaster to jeden widok na rysunku.
  3. Dopasuj klaster do wymiarow z wykazu (Abmess_1 x Abmes_2):
     widok glowny = klaster, ktorego proporcje pasuja do wykazu,
     a skala x i y jest ta sama (rysunki sa w podzialce).
  4. Przeskaluj widok glowny do 1:1, WYSRODKUJ (srodek bbox w (0,0)),
     zapisz DXF + raport. Wysrodkowanie = wymog operatora (11.06.2026):
     wycentrowane elementy latwiej sie przeglada w CAD.

Uzycie:
  python extract_positions.py <rysunek.dxf> <wykaz.xlsx> <folder_wynikow>
"""
import sys
import io
import math
import csv
from pathlib import Path
from collections import defaultdict

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44
import openpyxl

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

GEOM_TYPES = {"LINE", "ARC", "CIRCLE", "ELLIPSE", "SPLINE", "LWPOLYLINE", "POLYLINE"}
ANNOT_TYPES = {"DIMENSION", "MTEXT", "TEXT", "LEADER", "POINT", "HATCH", "INSERT"}
AXIS_LINETYPES = {"CENTER", "PHANTOM", "CENTER2", "PHANTOM2"}      # osie symetrii/otworow
BEND_LINETYPES = {"DASHDOT", "DASHDOT2"}   # konwencja: linia giecia na rozwinieciu
# DASHED zostawiamy osobno - moze byc linia giecia (raportujemy, nie usuwamy w widoku glownym)

CLUSTER_GAP = 8.0          # mm na papierze - odstep laczacy encje w jeden widok
FALLBACK_GAPS = (8.0, 4.0, 2.0)  # tryb bez warstw: widoki bywaja blizej siebie
SCALE_TOL = 0.03           # 3% tolerancji na zgodnosc skali x vs y
NICE_SCALES = [1, 2, 2.5, 4, 5, 8, 10, 20]


def parse_dim(v):
    """Wykaz ma wymiary jako liczby albo stringi '      2.232,000' (format niemiecki)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def load_wykaz(xlsx_path, zeinr):
    """Zwraca {posn: (dim_max, dim_min)} dla pozycji BLACHA danego rysunku."""
    wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = {str(h).strip(): i for i, h in enumerate(next(rows)) if h is not None}
    out = {}
    for r in rows:
        if r[header["Zeinr"]] is None or zeinr not in str(r[header["Zeinr"]]):
            continue
        if str(r[header["ZAKUPY"]]).strip().upper() != "BLACHA":
            continue
        posn = int(r[header["Posn"]])
        d1 = parse_dim(r[header["Abmess_1"]])
        d2 = parse_dim(r[header["Abmes_2"]])
        if d1 and d2 and posn not in out:   # lista bywa zdublowana (domowienie)
            out[posn] = (max(d1, d2), min(d1, d2))
    return out


def ent_bbox(e):
    ext = bbox.extents([e], fast=True)
    if not ext.has_data:
        return None
    return (ext.extmin.x, ext.extmin.y, ext.extmax.x, ext.extmax.y)


def boxes_close(a, b, gap):
    return not (a[2] + gap < b[0] or b[2] + gap < a[0] or
                a[3] + gap < b[1] or b[3] + gap < a[1])


def cluster_entities(ents, gap=CLUSTER_GAP):
    """Union-find po bbox: encje blizej niz `gap` -> jeden klaster (widok)."""
    boxes = []
    valid = []
    for e in ents:
        b = ent_bbox(e)
        if b:
            boxes.append(b)
            valid.append(e)
    n = len(valid)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if boxes_close(boxes[i], boxes[j], gap):
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj

    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    clusters = []
    for idxs in groups.values():
        es = [valid[i] for i in idxs]
        bs = [boxes[i] for i in idxs]
        cb = (min(b[0] for b in bs), min(b[1] for b in bs),
              max(b[2] for b in bs), max(b[3] for b in bs))
        clusters.append({"entities": es, "bbox": cb,
                         "w": cb[2] - cb[0], "h": cb[3] - cb[1]})
    return clusters


def endpoints(e):
    """Konce krzywej (do badania domknietosci konturu). Pelne okregi/elipsy: brak."""
    t = e.dxftype()
    if t == "LINE":
        return [e.dxf.start, e.dxf.end]
    if t == "ARC":
        return [e.start_point, e.end_point]
    if t in ("LWPOLYLINE", "POLYLINE"):
        if getattr(e, "closed", False) or (e.dxf.hasattr("flags") and e.dxf.flags & 1):
            return []
        try:
            pts = list(e.vertices()) if t == "POLYLINE" else list(e.get_points("xy"))
            return [pts[0], pts[-1]] if pts else []
        except Exception:
            return []
    if t == "SPLINE":
        try:
            cp = e.control_points
            return [cp[0], cp[-1]]
        except Exception:
            return []
    return []  # CIRCLE, pelna ELLIPSE


def open_ends(ents, tol=0.05):
    """Liczba niesparowanych koncow geometrii. Zamkniety kontur -> 0.
    Widok detalu w zlozeniu (krawedzie poprzerywane sasiadami) -> duzo."""
    pts = []
    for e in ents:
        for p in endpoints(e):
            pts.append((round(float(p[0]) / tol), round(float(p[1]) / tol)))
    from collections import Counter as _C
    return sum(1 for v in _C(pts).values() if v % 2 == 1)


def interior_clusters(clusters, main, margin=0.5):
    """Klastry lezace w calosci wewnatrz bbox klastra glownego (= otwory)."""
    mb = main["bbox"]
    out = []
    for c in clusters:
        if c is main:
            continue
        b = c["bbox"]
        if (b[0] >= mb[0] - margin and b[1] >= mb[1] - margin and
                b[2] <= mb[2] + margin and b[3] <= mb[3] + margin):
            out.append(c)
    return out


def match_scale(cluster, dim_max, dim_min):
    """Sprawdza czy klaster pasuje do wymiarow z wykazu. Zwraca (skala, blad) lub None."""
    cw, ch = max(cluster["w"], cluster["h"]), min(cluster["w"], cluster["h"])
    if cw < 1e-6 or ch < 1e-6:
        return None
    s_major = dim_max / cw
    s_minor = dim_min / ch
    if s_major <= 0:
        return None
    rel = abs(s_major - s_minor) / s_major
    if rel > SCALE_TOL:
        return None
    scale = (s_major + s_minor) / 2
    # preferuj "ladne" skale rysunkowe, ale nie wymuszaj
    for ns in NICE_SCALES:
        if abs(scale - ns) / ns < 0.02:
            scale = float(ns)
            break
    return scale, rel


def partition(ents):
    """Dzieli encje: kontur / osie / kreskowane / linie giecia (DASHDOT) / adnotacje."""
    geom, axis, dashed, bend, annot = [], [], [], [], []
    for e in ents:
        t = e.dxftype()
        if t in ANNOT_TYPES:
            annot.append(e)
        elif t in GEOM_TYPES:
            lt = (e.dxf.linetype or "").upper()
            if lt in AXIS_LINETYPES:
                axis.append(e)
            elif lt in BEND_LINETYPES:
                bend.append(e)
            elif lt.startswith("DASHED") or lt.startswith("HIDDEN"):
                dashed.append(e)
            else:
                geom.append(e)
    return geom, axis, dashed, bend, annot


def rank_value(clusters, cand):
    """Ranking kandydata na widok glowny:
    1) skala "ladna" rysunkowa (1,2,2.5,4,5,8,10,20),
    2) NAJMNIEJ otwartych koncow konturu (laser wymaga zamknietych konturow;
       widok w zlozeniu ma krawedzie poprzerywane sasiadami),
    3) najwiecej encji PO wchlonieciu wnetrza (otwory!),
    4) najmniejszy blad proporcji."""
    c, (scale, rel_err) = cand
    nice = any(abs(scale - ns) / ns < 0.02 for ns in NICE_SCALES)
    ents = list(c["entities"])
    for i in interior_clusters(clusters, c):
        ents.extend(i["entities"])
    solid = [e for e in ents
             if not (e.dxf.linetype or "").upper().startswith(("DASHED", "HIDDEN"))]
    return (nice, -open_ends(solid), len(ents), -rel_err)


def inside_bbox(ents, box, margin=0.5):
    out = []
    for e in ents:
        b = ent_bbox(e)
        if b and (b[0] >= box[0] - margin and b[1] >= box[1] - margin and
                  b[2] <= box[2] + margin and b[3] <= box[3] + margin):
            out.append(e)
    return out


def save_view(cluster, absorbed, bend_inside, scale, layer_name,
              out_dir, zeinr, posn, rep, dims):
    """Buduje nowy DXF 1:1 z widoku glownego + otwory + linie giecia."""
    ents = list(cluster["entities"])
    for ic in absorbed:
        ents.extend(ic["entities"])
    rep["n_absorbed"] = len(absorbed)

    new_doc = ezdxf.new(dxfversion="AC1021")
    if layer_name not in new_doc.layers:
        new_doc.layers.add(layer_name)
    if bend_inside:
        new_doc.layers.add("GIECIE", color=6)
    new_msp = new_doc.modelspace()

    # ZAWSZE wysrodkowany wynik: srodek bbox widoku -> (0,0)
    cx = (cluster["bbox"][0] + cluster["bbox"][2]) / 2
    cy = (cluster["bbox"][1] + cluster["bbox"][3]) / 2
    m = Matrix44.translate(-cx, -cy, 0) @ Matrix44.scale(scale, scale, 1)

    n_holes = 0
    for e in ents:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = layer_name
        new_msp.add_entity(ne)
        if ne.dxftype() == "CIRCLE":
            n_holes += 1
    # linie giecia: osobna warstwa GIECIE, kolor magenta (konwencja DXF_cleaner)
    for e in bend_inside:
        ne = e.copy()
        try:
            ne.transform(m)
        except Exception:
            continue
        ne.dxf.layer = "GIECIE"
        ne.dxf.color = 6
        new_msp.add_entity(ne)
    rep["n_holes"] = n_holes
    rep["n_bend"] = len(bend_inside)

    ext = bbox.extents(new_msp)
    # $EXTMIN/$EXTMAX w R2000+ zyja w obiekcie Layout modelspace -
    # przypisanie do doc.header[...] jest nadpisywane przy zapisie (ezdxf 1.4.4)
    new_msp.reset_extents((ext.extmin.x, ext.extmin.y, 0),
                          (ext.extmax.x, ext.extmax.y, 0))
    rep["out_w"] = round(max(ext.size.x, ext.size.y), 2)
    rep["out_h"] = round(min(ext.size.x, ext.size.y), 2)

    # walidacja jak w skanerze operatora
    dim_max, dim_min = dims
    ok_w = abs(rep["out_w"] - dim_max) <= max(1.0, dim_max * 0.002)
    ok_h = abs(rep["out_h"] - dim_min) <= max(1.0, dim_min * 0.002)
    if not rep["status"]:
        rep["status"] = "OK" if (ok_w and ok_h) else "WYMIAR NIEZGODNY"
    if rep["n_bend"]:
        rep["status"] += f" [{rep['n_bend']} linii giecia -> warstwa GIECIE]"
    if rep["n_dashed"]:
        rep["status"] += f" [+{rep['n_dashed']} linii kreskowanych - sprawdz giecie]"

    suffix = "_DO_SPRAWDZENIA" if "NIEPEWNE" in rep["status"] else ""
    out_path = Path(out_dir) / f"{zeinr}_p{posn}{suffix}.dxf"
    new_doc.saveas(out_path)
    rep["file"] = out_path.name
    return rep


def overlaps_claimed(box, claimed, thresh=0.5):
    """Czy bbox kandydata pokrywa sie z widokiem zajetym przez inna pozycje."""
    area = max((box[2] - box[0]) * (box[3] - box[1]), 1e-9)
    for cb in claimed:
        ix = max(0.0, min(box[2], cb[2]) - max(box[0], cb[0]))
        iy = max(0.0, min(box[3], cb[3]) - max(box[1], cb[1]))
        if ix * iy / area > thresh:
            return True
    return False


def extract_position(src_doc, layer, posn, dims, out_dir, zeinr, claimed=None):
    """Tryb warstwowy: pozycja NN = warstwa 1NN. Zwraca dict raportu."""
    msp = src_doc.modelspace()
    all_on_layer = [e for e in msp if e.dxf.layer == layer]
    geom, axis_lines, dashed, bend, annot = partition(all_on_layer)

    rep = {"posn": posn, "layer": layer, "n_layer_total": len(all_on_layer),
           "n_geom": len(geom), "n_axis": len(axis_lines), "n_dashed": len(dashed),
           "n_annot": len(annot), "status": "", "scale": None,
           "out_w": None, "out_h": None, "wykaz_w": None, "wykaz_h": None,
           "n_holes": 0, "n_bend": 0, "n_clusters": 0, "file": ""}

    if not geom:
        rep["status"] = "BRAK GEOMETRII"
        return rep
    if dims is None:
        rep["status"] = "BRAK W WYKAZIE"
        return rep
    dim_max, dim_min = dims
    rep["wykaz_w"], rep["wykaz_h"] = dim_max, dim_min

    clusters = cluster_entities(geom + dashed)
    rep["n_clusters"] = len(clusters)
    clusters.sort(key=lambda c: c["w"] * c["h"], reverse=True)

    candidates = []
    for c in clusters:
        m = match_scale(c, dim_max, dim_min)
        if m:
            candidates.append((c, m))
    if candidates:
        best = max(candidates, key=lambda cand: rank_value(clusters, cand))
    else:
        # awaryjnie: najwiekszy klaster, skala z dluzszego boku
        c = clusters[0]
        cw = max(c["w"], c["h"])
        scale = dim_max / cw if cw > 0 else 1.0
        best = (c, (scale, 999))
        rep["status"] = "NIEPEWNE (brak zgodnosci proporcji)"
    cluster, (scale, rel_err) = best
    rep["scale"] = round(scale, 4)
    if claimed is not None and not rep["status"]:
        claimed.append(cluster["bbox"])

    # KRYTYCZNE: otwory wewnatrz obrysu moga byc osobnymi klastrami
    # (np. fasolka w srodku duzej blachy, daleko od konturu).
    absorbed = interior_clusters(clusters, cluster)
    bend_inside = inside_bbox(bend, cluster["bbox"])
    return save_view(cluster, absorbed, bend_inside, scale, layer,
                     out_dir, zeinr, posn, rep, dims)


def extract_fallback(src_doc, posn, dims, out_dir, zeinr, claimed=None):
    """Tryb BEZ WARSTW: szuka widoku pasujacego do wykazu w calym rysunku.
    Dla rysunkow z jedna warstwa / lamiacych konwencje 1NN.
    Probuje kilku progow klastrowania - widoki bywaja narysowane blisko siebie."""
    msp = src_doc.modelspace()
    geom, axis_lines, dashed, bend, annot = partition(list(msp))
    rep = {"posn": posn, "layer": "(bez warstw)", "n_geom": len(geom),
           "n_axis": len(axis_lines), "n_dashed": len(dashed), "n_annot": len(annot),
           "status": "", "scale": None, "out_w": None, "out_h": None,
           "wykaz_w": dims[0], "wykaz_h": dims[1],
           "n_holes": 0, "n_bend": 0, "n_clusters": 0, "file": ""}

    # Generujemy zbiory geometrii do klastrowania:
    #  - calosc (widoki rozdzielone przestrzennie - rysunki Lantek),
    #  - PER KOLOR (rysunki 1-warstwowe: kontur i wymiary roznia sie kolorem,
    #    nie warstwa; np. SBM: kontur=2 zolty, wymiary=3 zielony, ramka=inne).
    #    Klastrowanie samego koloru konturu eliminuje linie wymiarowe i daje
    #    domkniety obrys (open_ends=0), ktory ranking premiuje.
    geom_sets = [("all", geom + dashed)]
    by_color = defaultdict(list)
    for e in geom:
        by_color[e.dxf.color].append(e)
    if len(by_color) > 1:
        for col, ents in by_color.items():
            if len(ents) >= 3:
                geom_sets.append((f"col{col}", ents))

    best = None  # (rank_tuple, clusters, cand, gap, tag)
    for tag, gset in geom_sets:
        for gap in FALLBACK_GAPS:
            clusters = cluster_entities(gset, gap=gap)
            for c in clusters:
                m = match_scale(c, dims[0], dims[1])
                if not m:
                    continue
                # widok zajety przez inna pozycje (np. blizniacze wymiary
                # poz. lustrzanej) NIE moze byc uzyty drugi raz
                if claimed is not None and overlaps_claimed(c["bbox"], claimed):
                    continue
                rv = rank_value(clusters, (c, m))
                if best is None or rv > best[0]:
                    best = (rv, clusters, (c, m), gap, tag)
    if best is None:
        rep["status"] = "NIE ZNALEZIONO WIDOKU (takze bez warstw)"
        return rep
    _, clusters, (cluster, (scale, rel_err)), gap, tag = best
    rep["scale"] = round(scale, 4)
    rep["n_clusters"] = len(clusters)
    rep["layer"] = f"(bez warstw, {tag}, gap={gap:g})"
    if claimed is not None:
        claimed.append(cluster["bbox"])

    # Wchlanianie otworow wewnatrz obrysu:
    #  - tryb "all": klastry z tego samego zbioru (jak w trybie warstwowym),
    #  - tryb per-kolor: NIE wciagamy obcej geometrii (linie wymiarowe leza
    #    wewnatrz bbox!). Dobieramy tylko zamkniete otwory (CIRCLE / pelna
    #    ELLIPSE) lezace wewnatrz, niezaleznie od koloru.
    if tag == "all":
        absorbed = interior_clusters(clusters, cluster)
    else:
        holes = [{"entities": [e], "bbox": ent_bbox(e)}
                 for e in geom
                 if e.dxftype() in ("CIRCLE", "ELLIPSE")
                 and e not in cluster["entities"] and ent_bbox(e)]
        absorbed = interior_clusters([cluster] + holes, cluster)
    bend_inside = inside_bbox(bend, cluster["bbox"])
    rep["n_dashed"] = len(inside_bbox(dashed, cluster["bbox"]))
    rep = save_view(cluster, absorbed, bend_inside, scale, "0",
                    out_dir, zeinr, posn, rep, dims)
    if rep["status"].startswith("OK"):
        rep["status"] = rep["status"].replace("OK", "OK (TRYB BEZ WARSTW)", 1)
    return rep


def make_mirror(out_dir, zeinr, src_posn, dst_posn):
    """Pozycja-lustro: kopiuje DXF pozycji zrodlowej i odbija w pionie."""
    src = Path(out_dir) / f"{zeinr}_p{src_posn}.dxf"
    if not src.exists():
        return None
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    m = Matrix44.scale(-1, 1, 1)
    for e in msp:
        try:
            e.transform(m)
        except Exception:
            pass
    ext = bbox.extents(msp)
    mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2,
                            -(ext.extmin.y + ext.extmax.y) / 2, 0)
    for e in msp:
        try:
            e.transform(mv)
        except Exception:
            pass
    ext = bbox.extents(msp)
    msp.reset_extents((ext.extmin.x, ext.extmin.y, 0),
                      (ext.extmax.x, ext.extmax.y, 0))
    out = Path(out_dir) / f"{zeinr}_p{dst_posn}_LUSTRO_z_p{src_posn}.dxf"
    doc.saveas(out)
    return out.name


def main():
    src_path, xlsx_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    zeinr = Path(src_path).stem.split("_")[0]
    out_dir = Path(out_dir)
    out_dir.mkdir(exist_ok=True)

    wykaz = load_wykaz(xlsx_path, zeinr)
    print(f"Wykaz {zeinr}: pozycje BLACHA -> {sorted(wykaz)}")

    doc = ezdxf.readfile(src_path)
    msp = doc.modelspace()
    layers_used = sorted({e.dxf.layer for e in msp})
    pos_layers = {}
    for ln in layers_used:
        if ln.isdigit() and len(ln) == 3 and ln.startswith("1"):
            pos_layers[int(ln) - 100] = ln
    print(f"Warstwy pozycyjne: {pos_layers}")

    reports = []
    claimed = []   # bboxy widokow juz przypisanych pozycjom
    for posn in sorted(set(pos_layers) | set(wykaz)):
        layer = pos_layers.get(posn)
        if layer is None:
            # brak warstwy 1NN -> od razu tryb bez warstw
            rep = extract_fallback(doc, posn, wykaz[posn], out_dir, zeinr, claimed)
            reports.append(rep)
            continue
        rep = extract_position(doc, layer, posn, wykaz.get(posn), out_dir, zeinr, claimed)
        if not rep["status"].startswith(("OK", "BRAK W WYKAZIE")) and posn in wykaz:
            # warstwa zawiodla (np. kontur rozrzucony po warstwach) -> bez warstw
            rep2 = extract_fallback(doc, posn, wykaz[posn], out_dir, zeinr, claimed)
            if rep2["status"].startswith("OK"):
                old = rep.get("file")
                if old and old != rep2.get("file"):
                    (out_dir / old).unlink(missing_ok=True)
                rep = rep2
            else:
                # nieudany fallback NIE moze zostawic pliku na dysku
                # (plik bez sufiksu _DO_SPRAWDZENIA poszedlby do nestingu!)
                bad = rep2.get("file")
                if bad and bad != rep.get("file"):
                    (out_dir / bad).unlink(missing_ok=True)
        reports.append(rep)

    # POZYCJE-LUSTRA: pozycja bez poprawnego widoku, ale o identycznych
    # wymiarach w wykazie jak pozycja wyciagnieta OK -> generujemy odbicie.
    # (typowa adnotacja na rysunku: "Pos.00X gespiegelt / mirrored")
    ok_by_dims = {}
    for r in reports:
        if r.get("status", "").startswith("OK") and r.get("wykaz_w"):
            ok_by_dims.setdefault((r["wykaz_w"], r["wykaz_h"]), r["posn"])
    for r in reports:
        if r.get("status", "").startswith("OK") or not r.get("wykaz_w"):
            continue
        twin = ok_by_dims.get((r["wykaz_w"], r["wykaz_h"]))
        if twin and twin != r["posn"]:
            fname = make_mirror(out_dir, zeinr, twin, r["posn"])
            if fname:
                old = r.get("file")
                if old and old != fname:
                    (out_dir / old).unlink(missing_ok=True)
                    (out_dir / old).with_suffix(".png").unlink(missing_ok=True)
                r["status"] = f"LUSTRO z poz. {twin} - ZWERYFIKUJ ({r['status']})"
                r["file"] = fname

    # raport
    print()
    print(f"{'poz':>3} {'warstwa':>7} {'skala':>7} {'DXF [mm]':>18} {'wykaz [mm]':>18} {'otw':>4}  status")
    for r in reports:
        dxf_dim = f"{r.get('out_w','-')} x {r.get('out_h','-')}" if r.get("out_w") else "-"
        wyk_dim = f"{r.get('wykaz_w','-')} x {r.get('wykaz_h','-')}" if r.get("wykaz_w") else "-"
        print(f"{r['posn']:>3} {r.get('layer','-'):>7} {str(r.get('scale','-')):>7} "
              f"{dxf_dim:>18} {wyk_dim:>18} {r.get('n_holes',0):>4}  {r['status']}")

    csv_path = out_dir / f"{zeinr}_raport.csv"
    keys = ["posn", "layer", "scale", "out_w", "out_h", "wykaz_w", "wykaz_h",
            "n_holes", "n_bend", "n_absorbed", "n_geom", "n_axis", "n_dashed",
            "n_annot", "n_clusters", "status", "file"]
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", delimiter=";")
        w.writeheader()
        w.writerows(reports)
    print(f"\nRaport: {csv_path}")


if __name__ == "__main__":
    main()
