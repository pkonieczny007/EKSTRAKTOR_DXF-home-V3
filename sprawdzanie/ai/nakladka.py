# -*- coding: utf-8 -*-
"""NAKLADKA wynik-na-zrodlo - najpewniejsza kontrola kompletnosci (strategia #1).

Rysuje wyekstrahowany WYNIK (polprzezroczysty CZERWONY, gruba linia) NA regionie
ZRODLA (przygaszony bialy/szary), w ukladzie i skali ZRODLA, na CZARNYM tle.
Cecha OBECNA w zrodle a NIEOBECNA w wyniku (fasola/slot/blok perforacji) = "gola"
szara geometria BEZ czerwonej nakladki na sobie - oko widzi ja w 1 s.

ALIGNMENT = BBOX-FIT (wynik stracil absolutna pozycje przez rewysrodkowanie do 0,0):
  s = dopasowanie bbox wyniku do bbox geometrii regionu (warstwa_geom, bez giecia),
  przesuniecie srodka bbox wyniku na srodek bbox regionu. LUSTRO: probujemy oba
  warianty (normal + odbicie X), wybieramy wyzsze pokrycie konturu (auto-P/L).

POKRYCIE (miary auto-flagi, FLAGER - decyduja OCZY, zasada 6):
  pokrycie        = % dlugosci WYNIKU blisko geometrii zrodla (zly alignment/lustro spada)
  pokrycie_zrodla = % dlugosci geometrii zrodla pokrytej wynikiem (BRAK CECHY -> spada;
                    to sygnal kompletnosci: <97% -> MOZLIWY BRAK, ogledziny render)

ZAKRESLANIE BRAKOW (automatyczne): fragmenty zrodla DALEJ niz tol od wyniku sa
klasteryzowane w skupiska (_braki_skupiska); kazde skupisko powyzej progu szumu
= jaskrawy czerwony przerywany OKRAG na renderze + wpis w braki_bboxy (bbox +
dl_niepokryta, malejaco). Czlowiek/AI widzi w 1 s GDZIE jest brak, nie tylko ZE
pokrycie spadlo. Skupiska ponizej progu = jitter, odfiltrowane (licznik w align).

Rdzen (alignment + miary) zaprojektowany i zwalidowany wizualnie przez fable-advisor,
zweryfikowany renderem i wpiety przez orkiestratora (etap 2 PLAN.md). Reuzywa
sweep.kontury_regionu_zrodla (wybor regionu, warstwa geometrii) + bramka 5.

Wejscie sprawdzania AI: render pary + miary -> AI/czlowiek OGLADA, zakresla brak
na czerwono, werdykt z powodem (moze tylko obnizyc status). Od NAJWIEKSZYCH roznic.

Uzycie:
  python sprawdzanie\\ai\\nakladka.py <wynik.dxf> <zrodlo_conv.dxf> x1 y1 x2 y2 <out.png>
      [--scale S] [--lustro]
"""
import io
import json
import math
import sys
from pathlib import Path

import ezdxf
from ezdxf import path as ezpath

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle as MplCircle

from shapely.geometry import LineString, MultiLineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "produkcja" / "kontrola"))
from sweep import kontury_regionu_zrodla, center, in_bbox, effective_color  # noqa: E402
from bilans_konturow import GEOM_TYPES  # noqa: E402

SAGITTA = 0.05          # dyskretyzacja krzywych (jednostki danego pliku)
PROG_POKRYCIE_ZRODLA = 97.0    # < prog -> MOZLIWY BRAK CECHY (sygnal kompletnosci)
PROG_POKRYCIE_WYNIK = 90.0     # < prog -> zly alignment / obca geometria
PROG_ANIZOTROPIA = 3.0         # % - bbox-fit anizotropowy -> zly region
PROG_ODCH_SKALA = 5.0          # % - s_fit vs 1/scale z raportu
# filtr szumu skupisk braku: skupisko o dl niepokrytej < PROG_SZUM_BRAKU*tol = jitter
# dopasowania, NIE brak cechy. Pomiar (golden SL10596945, skala 1/5, tol=0.461):
# jitter/kikuty naroznikow 1.26-1.39*tol, najmniejsza realna cecha (pol fasoli r=7)
# 7.4*tol, caly otwor 6.5 -> 17.7*tol. Prog 3.0 = 2.2x nad szumem, 2.5x pod cecha.
PROG_SZUM_BRAKU = 3.0          # x tol - min dlugosc niepokryta skupiska braku
EPS_KLASTRA = 2.0              # x tol - promien laczenia fragmentow w skupisko


def _flatten(e, sagitta):
    p = ezpath.make_path(e)
    return [(v.x, v.y) for v in p.flattening(distance=sagitta)]


def _polylines(entities, sagitta):
    out, failed = [], []
    for e in entities:
        try:
            pts = _flatten(e, sagitta)
        except Exception as ex:
            failed.append(f"{e.dxftype()}: {ex}")
            continue
        if len(pts) >= 2:
            out.append(pts)
    return out, failed


def _bbox_pts(polys):
    xs = [x for pts in polys for x, _ in pts]
    ys = [y for pts in polys for _, y in pts]
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def _lines_union(polys):
    ls = [LineString(pts) for pts in polys if len(pts) >= 2]
    return unary_union(ls) if ls else None


def _coverage(target_polys, reference_union, tol):
    """% dlugosci target lezacej w buforze tol wokol reference."""
    if reference_union is None or not target_polys:
        return 0.0
    tgt = MultiLineString([LineString(p) for p in target_polys if len(p) >= 2])
    total = tgt.length
    if total <= 0:
        return 0.0
    return 100.0 * tgt.intersection(reference_union.buffer(tol)).length / total


def _braki_skupiska(src_geom, res_union, tol):
    """Skupiska geometrii ZRODLA niepokrytej wynikiem = kandydaci na BRAK CECHY.

    Dual _coverage: difference kazdej polilinii zrodla z buforem tol wokol wyniku
    daje fragmenty NIEPOKRYTE; klasteryzacja buforem EPS_KLASTRA*tol scala je w
    skupiska (cala zgubiona fasola = JEDNO skupisko); filtr szumu odrzuca skupiska
    o dl < PROG_SZUM_BRAKU*tol (jitter dopasowania, kikuty na krawedzi).
    Zwraca (braki, n_odfiltrowane); braki = [dict(bbox=(x1,y1,x2,y2),
    dl_niepokryta=...)] posortowane MALEJACO po dl (najwieksze roznice pierwsze,
    zasada 6). FLAGER - decyduja OCZY na renderze, nie sama liczba.
    """
    if res_union is None or not src_geom:
        return [], 0
    buf = res_union.buffer(tol)
    frags = []
    for pts in src_geom:
        if len(pts) < 2:
            continue
        d = LineString(pts).difference(buf)
        for g in getattr(d, "geoms", [d]):
            if g.geom_type == "LineString" and g.length > 0:
                frags.append(g)
    if not frags:
        return [], 0
    blobs = unary_union([f.buffer(EPS_KLASTRA * tol) for f in frags])
    braki, odfiltrowane = [], 0
    for blob in getattr(blobs, "geoms", [blobs]):
        mine = [f for f in frags if f.intersects(blob)]
        dl = sum(f.length for f in mine)
        if dl < PROG_SZUM_BRAKU * tol:
            odfiltrowane += 1
            continue
        xs1, ys1, xs2, ys2 = zip(*(f.bounds for f in mine))
        braki.append(dict(bbox=(round(min(xs1), 2), round(min(ys1), 2),
                                round(max(xs2), 2), round(max(ys2), 2)),
                          dl_niepokryta=round(dl, 2)))
    braki.sort(key=lambda b: -b["dl_niepokryta"])
    return braki, odfiltrowane


def _transform(polys, s, res_cx, res_cy, src_cx, src_cy, mirror_x):
    out = []
    for pts in polys:
        q = []
        for x, y in pts:
            if mirror_x:
                x = 2.0 * res_cx - x
            q.append((src_cx + s * (x - res_cx), src_cy + s * (y - res_cy)))
        out.append(q)
    return out


def pick_region(src_msp, box, margin=1.0):
    """Encje regionu zrodla: geom (warstwa_geom) / bend (kolor 6) / other (reszta).
    + diag ze sweep.kontury_regionu_zrodla (warstwa geometrii, uwagi)."""
    diag = kontury_regionu_zrodla(src_msp, box)
    geom_layer = diag["diag"]["warstwa_geom"]
    x1, y1, x2, y2 = box
    layer_colors = {}
    doc = getattr(src_msp, "doc", None)
    if doc is not None:
        for ly in doc.layers:
            layer_colors[ly.dxf.name] = ly.dxf.color
    geom, bend, other = [], [], []
    for e in src_msp:
        if e.dxftype() not in GEOM_TYPES:
            continue
        c = center(e)
        if not in_bbox(c, x1, y1, x2, y2, margin):
            continue
        ec = effective_color(e, layer_colors)
        if ec == 6 or e.dxf.layer.upper() == "GIECIE":
            bend.append(e)
        elif geom_layer is not None and e.dxf.layer == geom_layer:
            geom.append(e)
        else:
            other.append(e)
    return geom, bend, other, diag


def pick_region_czysty(src_msp, box, margin=1.0):
    """ROOT-FIX szumu nakladki: jak pick_region, ale gdy istnieje CZYSTY tryb
    kolorowy (col7/col2/col4 z n_ents>0, outer==1, 0 flag) - geometrie bierzemy
    z NIEGO, nie z fallbacku warstwowego.

    Powod (fable-advisor 2026-07-07, zweryfikowane): na rysunkach typu SL40061302
    WSZYSTKO lezy na warstwie '1' (geometria = KOLOR 2, adnotacje = kolory 30/4/3).
    Fallback warstwowy wrzuca adnotacje do 'geom' -> bbox-fit anizotropowy (3.15%),
    auto-lustro sie przelacza i diff tonie w FALSZYWEJ czerwieni (pokrycie_zrodla
    34% na POPRAWNYM wzorcu) - a falszywe flagi ucza ignorowania flag (zasada 6).
    Sweep JUZ liczy per_tryb_detale (CLAUDE.md: prawda z trybow CZYSTYCH n_outer==1),
    wiec tylko z tego korzystamy. Brak trybu czystego (geometria na wlasnej warstwie
    numerycznej, np. golden SL10596945 warstwa 53) -> zachowanie BEZ ZMIAN (warstwa_geom).
    Zwraca (geom, bend, other, diag, tryb)."""
    geom, bend, other, diag = pick_region(src_msp, box, margin)
    det = diag["diag"].get("per_tryb_detale", {})
    tryb = "warstwa_geom"
    for t in ("col7", "col2", "col4"):
        d = det.get(t) or {}
        if d.get("n_ents", 0) > 0 and d.get("outer") == 1 and not d.get("flags"):
            tryb = t
            break
    if tryb == "warstwa_geom":
        return geom, bend, other, diag, tryb
    kolor = int(tryb[3:])
    layer_colors = {}
    doc = getattr(src_msp, "doc", None)
    if doc is not None:
        for ly in doc.layers:
            layer_colors[ly.dxf.name] = ly.dxf.color
    geom2, other2 = [], []
    for e in geom + other:                # bend zostaje (kolor 6 osobno)
        (geom2 if effective_color(e, layer_colors) == kolor else other2).append(e)
    return geom2, bend, other2, diag, tryb


def nakladka(wynik_dxf, zrodlo_conv, box, out_png, scale=None, lustro=False):
    """Nakladka wyniku (czerwony) na region zrodla (szary), czarne tlo.
    Zwraca dict(align_info, pokrycie, pokrycie_zrodla, uwagi, png)."""
    uwagi = []
    src_msp = ezdxf.readfile(zrodlo_conv).modelspace()
    geom_e, bend_e, other_e, diag, tryb_geom = pick_region_czysty(src_msp, box)
    uwagi += diag["diag"]["uwagi"]
    if tryb_geom != "warstwa_geom":
        uwagi.append(f"region z trybu czystego: {tryb_geom} (root-fix szumu nakladki)")

    src_sag = SAGITTA if scale in (None, 0) else max(SAGITTA / scale, 0.01)
    src_geom, f1 = _polylines(geom_e, src_sag)
    src_bend, f2 = _polylines(bend_e, src_sag)
    src_other, f3 = _polylines(other_e, src_sag)
    for f in (f1 + f2 + f3):
        uwagi.append(f"zrodlo nieprzetworzone (GLOSNO): {f}")

    res_msp = ezdxf.readfile(wynik_dxf).modelspace()
    res_geom_e = [e for e in res_msp if e.dxftype() in GEOM_TYPES
                  and not (e.dxf.layer.upper() == "GIECIE" or e.dxf.color == 6)]
    res_bend_e = [e for e in res_msp if e.dxftype() in GEOM_TYPES
                  and (e.dxf.layer.upper() == "GIECIE" or e.dxf.color == 6)]
    res_geom, f4 = _polylines(res_geom_e, SAGITTA)
    res_bend, f5 = _polylines(res_bend_e, SAGITTA)
    for f in (f4 + f5):
        uwagi.append(f"wynik nieprzetworzony (GLOSNO): {f}")

    align = dict(metoda="bbox-fit", lustro_wejscie=bool(lustro), tryb_geom=tryb_geom)
    ok_align = True
    src_fit_bb = _bbox_pts(src_geom) or _bbox_pts(src_geom + src_other)
    res_bb = _bbox_pts(res_geom)
    if res_bb is None:
        uwagi.append("WYNIK PUSTY (0 encji geometrii) - nakladka niemozliwa, rysuje "
                     "samo zrodlo (GLOSNO, czerwona flaga)")
        ok_align = False
    if src_fit_bb is None:
        uwagi.append("BRAK GEOMETRII ZRODLA w regionie - sprawdz bbox (GLOSNO)")
        ok_align = False

    res_t_geom, res_t_bend = [], []
    pokrycie = pokrycie_zrodla = 0.0
    braki = []
    if ok_align:
        sx1, sy1, sx2, sy2 = src_fit_bb
        rx1, ry1, rx2, ry2 = res_bb
        src_w, src_h = sx2 - sx1, sy2 - sy1
        res_w, res_h = rx2 - rx1, ry2 - ry1
        if res_w <= 0 or res_h <= 0 or src_w <= 0 or src_h <= 0:
            uwagi.append(f"bbox zdegenerowany: src={src_fit_bb} res={res_bb} (GLOSNO)")
            ok_align = False
        else:
            fx, fy = src_w / res_w, src_h / res_h
            s = (fx + fy) / 2.0
            anizo = abs(fx - fy) / s * 100.0
            align.update(s_fit=s, s_fit_x=fx, s_fit_y=fy, anizotropia_proc=anizo)
            if anizo > PROG_ANIZOTROPIA:
                uwagi.append(f"ANIZOTROPIA bbox-fit {anizo:.1f}% (sx={fx:.4f} sy={fy:.4f}) "
                             "- zly region (sasiad w bbox?) albo zly wynik - OGLADAC")
            if scale:
                exp = 1.0 / float(scale)
                odch = abs(s - exp) / exp * 100.0
                align.update(s_raport=exp, odchylka_vs_raport_proc=odch)
                if odch > PROG_ODCH_SKALA:
                    uwagi.append(f"SKALA fit {s:.4f} vs raport 1/{scale}={exp:.4f} "
                                 f"(odchylka {odch:.1f}%>{PROG_ODCH_SKALA}%) - alignment PODEJRZANY")
            src_cx, src_cy = (sx1 + sx2) / 2.0, (sy1 + sy2) / 2.0
            res_cx, res_cy = (rx1 + rx2) / 2.0, (ry1 + ry2) / 2.0

            diagl = math.hypot(src_w, src_h)
            tol = max(0.006 * diagl, 1.5 * s if scale else 0.3)
            align["tol_pokrycia"] = tol
            src_union_all = _lines_union(src_geom + src_bend)

            warianty = {}
            for mir in (False, True):
                tg = _transform(res_geom, s, res_cx, res_cy, src_cx, src_cy, mir)
                warianty[mir] = (tg, _coverage(tg, src_union_all, tol))
            align.update(pokrycie_normal=round(warianty[False][1], 1),
                         pokrycie_lustro=round(warianty[True][1], 1))
            if lustro:
                mir_used = True
            else:
                mir_used = warianty[True][1] > warianty[False][1] + 1.0
                if mir_used:
                    uwagi.append(f"AUTO-LUSTRO: odbicie X pokrywa lepiej "
                                 f"({warianty[True][1]:.1f}% vs {warianty[False][1]:.1f}%) - "
                                 "wynik wyglada na LUSTRO widoku (P/L)")
            if abs(warianty[True][1] - warianty[False][1]) < 1.0:
                uwagi.append("lustro NIEROZROZNIALNE (czesc ~symetryczna) - pokrycia "
                             "rownowazne" + (" - uzyto flagi --lustro" if lustro else
                                             ", przyjeto wariant bez odbicia"))
            align["lustro_uzyte"] = mir_used
            res_t_geom = warianty[mir_used][0]
            res_t_bend = _transform(res_bend, s, res_cx, res_cy, src_cx, src_cy, mir_used)

            pokrycie = warianty[mir_used][1]
            res_union = _lines_union(res_t_geom + res_t_bend)
            pokrycie_zrodla = _coverage(src_geom, res_union, tol)
            if pokrycie < PROG_POKRYCIE_WYNIK:
                uwagi.append(f"POKRYCIE WYNIKU {pokrycie:.1f}%<{PROG_POKRYCIE_WYNIK}% - "
                             "zly alignment lub obca geometria w wyniku - OGLADAC")
            if pokrycie_zrodla < PROG_POKRYCIE_ZRODLA:
                uwagi.append(f"POKRYCIE ZRODLA {pokrycie_zrodla:.1f}%<{PROG_POKRYCIE_ZRODLA}% "
                             "- w zrodle jest geometria BEZ czerwonej nakladki = MOZLIWY "
                             "BRAK CECHY w wyniku - OGLADAC render (zasada 6)")

            # skupiska braku: geometria zrodla ktorej wynik NIE pokrywa,
            # zakreslane na renderze jaskrawym okregiem (czlowiek/AI widzi GDZIE)
            braki, braki_szum = _braki_skupiska(src_geom, res_union, tol)
            align["braki_szum_odfiltrowane"] = braki_szum
            if braki:
                uwagi.append(f"BRAK CECHY: {len(braki)} skupisk zrodla bez pokrycia "
                             f"wynikiem (najwieksze dl={braki[0]['dl_niepokryta']}) - "
                             "ZAKRESLONE czerwonym okregiem, OGLADAC (zasada 6)")

    # ------------------------------- RENDER -------------------------------
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    fig_h = max(12.0 * h / w, 4.0)
    fig = plt.figure(figsize=(12.0, min(fig_h, 12.0)), facecolor="black")
    ax = fig.add_axes([0.02, 0.02, 0.96, 0.90])
    ax.set_facecolor("black")
    ax.set_aspect("equal")
    ax.axis("off")

    def draw(polys, **kw):
        for pts in polys:
            xs, ys = zip(*pts)
            ax.plot(xs, ys, **kw)

    draw(src_other, color="#555555", lw=0.6, alpha=0.8)      # adnotacje: ledwo widoczne
    draw(src_geom, color="#d8d8d8", lw=1.1)                  # geometria zrodla: jasna
    draw(src_bend, color="#b040b0", lw=1.0, alpha=0.9)       # giecie zrodla: magenta
    draw(res_t_geom, color="#ff2020", lw=2.6, alpha=0.55)    # WYNIK: czerwony
    draw(res_t_bend, color="#ff9020", lw=2.2, alpha=0.55)    # giecie wyniku: pomaranczowy
    ax.plot([x1, x2, x2, x1, x1], [y1, y1, y2, y2, y1],
            color="#3060ff", lw=0.8, ls="--", alpha=0.7)     # ramka regionu
    # ZAKRESLENIA BRAKOW: jaskrawy PELNY (bez alpha) przerywany okrag - odcina sie
    # od polprzezroczystej nakladki wyniku; zorder wysoki (na wierzchu wszystkiego)
    tol_r = align.get("tol_pokrycia", 0.3)
    for b in braki:
        bx1, by1, bx2, by2 = b["bbox"]
        rr = 0.5 * math.hypot(bx2 - bx1, by2 - by1) + 3.0 * tol_r
        ax.add_patch(MplCircle(((bx1 + bx2) / 2.0, (by1 + by2) / 2.0), rr,
                               fill=False, ec="#ff3030", lw=3.0,
                               ls=(0, (5, 3)), zorder=12))

    m = 0.04 * max(w, h)
    ax.set_xlim(x1 - m, x2 + m)
    ax.set_ylim(y1 - m, y2 + m)
    tytul = (f"NAKLADKA  wynik={Path(wynik_dxf).name}  na  {Path(zrodlo_conv).name}\n"
             f"s_fit={align.get('s_fit', float('nan')):.4f}"
             f" (raport {align.get('s_raport', float('nan')):.4f})"
             f"  lustro={align.get('lustro_uzyte', '?')}"
             f"  pokrycie_wyniku={pokrycie:.1f}%  pokrycie_zrodla={pokrycie_zrodla:.1f}%"
             f"  braki={len(braki)}")
    fig.text(0.02, 0.965, tytul, color="white", fontsize=9, va="top", family="monospace")
    if uwagi:
        fig.text(0.02, 0.905, "\n".join("! " + u[:110] for u in uwagi[:3]),
                 color="#ffcc00", fontsize=7.5, va="top", family="monospace")
    fig.savefig(out_png, dpi=150, facecolor="black")
    plt.close(fig)

    return dict(align_info=align, pokrycie=round(pokrycie, 1),
                pokrycie_zrodla=round(pokrycie_zrodla, 1), braki_bboxy=braki,
                uwagi=uwagi, png=str(out_png))


def main(argv):
    if len(argv) < 7:
        print(__doc__)
        return 2
    wynik, zrodlo = argv[0], argv[1]
    box = tuple(float(v) for v in argv[2:6])
    out_png = argv[6]
    scale = float(argv[argv.index("--scale") + 1]) if "--scale" in argv else None
    lustro = "--lustro" in argv
    res = nakladka(wynik, zrodlo, box, out_png, scale=scale, lustro=lustro)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
