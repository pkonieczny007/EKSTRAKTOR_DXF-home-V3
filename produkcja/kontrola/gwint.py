# -*- coding: utf-8 -*-
"""Gwinty na materialach trudnoscieralnych (Hardox / HB4xx / XAR / RAEX).

DOCELOWO: produkcja/kontrola/gwint.py + config/gwinty_hardox.yaml
(przenosi orkiestrator przez system testowy; ten plik to prototyp fable).

Zasada (operator 2026-07-08, zasady/propozycje/2026-07-08_gwint_hardox_transformacja.md):
- material trudnoscieralny: wyciagac JAK NORMALNE; w miejscu gwintu
  (okrag wiercenia + wspolsrodkowy luk ~270 st) LUK USUN, OKRAG POWIEKSZ
  wg tablicy (config/gwinty_hardox.yaml), zmieniony okrag na CZERWONO (kolor 1);
- brak wartosci w tablicy / M nierozpoznane -> ZOSTAW luk+okrag (kotwica
  operatora) + status pozycji minimum ZOLTY;
- material zwykly: BEZ zmian (gwint-okrag-luk-dimension.md: zostaw oba);
- luk gwintu NIGDY nie liczy sie do otwartych koncow bramki 2 (zaden material).

Sygnatura gwintu (deterministyczna; zmierzone 0 falszywych na 88 plikach +
wzorcach golden): ARC o rozpietosci 200-330 st, wspolsrodkowy (<=0.3 mm)
z CIRCLE o MNIEJSZYM promieniu, R_luk/R_okr w [1.08, 1.30]
(tabela metryczna M3..M24 daje 1.14-1.19; 1.30 odcina pary fertzing 1.36+).

Rozmiar M z NOMINALU luku (luk rysowany na srednicy nominalnej: luk o6 = M6);
DIMENSION "M.." u tego klienta NIE wystepuje (zmierzone 0/12) - dziala tylko
na plikach 1:1 (wyniki po ekstrakcji), NIE na zrodle w skali.
"""
import math
import re

from ezdxf import path as ezpath

# --- sygnatura gwintu (progi zmierzone, patrz naglowek) ---
SPAN_MIN, SPAN_MAX = 200.0, 330.0
RATIO_MIN, RATIO_MAX = 1.08, 1.30
CENTER_TOL = 0.3          # mm, wspolsrodkowosc okrag-luk
SAG = 0.05                # flattening dla open_ends
END_TOL = 0.05            # mm, parowanie koncow (jak bramka 2)

# --- rozmiar M z nominalu luku (tylko pliki 1:1!) ---
M_NOMINALY = (3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 14.0,
              16.0, 18.0, 20.0, 22.0, 24.0)
M_TOL = 0.3               # mm, dopasowanie srednicy luku do nominalu

# --- rozpoznanie materialu trudnoscieralnego (zmierzone na wykazie ZUBEHOR) ---
MATERIAL_RE = re.compile(r"HB\s*4\d\d|HARDOX|XAR|RAEX", re.IGNORECASE)


def czy_trudnoscieralny(text):
    """True gdy tekst (Bezeichnung/gatunek z wykazu) wskazuje material
    trudnoscieralny (Hardox HB400/HB450, XAR, RAEX)."""
    return bool(MATERIAL_RE.search(str(text or "")))


def _arc_span(a):
    s = a.dxf.start_angle % 360.0
    e = a.dxf.end_angle % 360.0
    sp = (e - s) % 360.0
    return sp if sp > 0 else 360.0


def _wcs_center(e):
    c = e.ocs().to_wcs(e.dxf.center)
    return (c.x, c.y)


def thread_arcs(msp):
    """Detekcja gwintow: (set(handle lukow gwintu), lista gwintow).

    Gwint = dict(arc, circle, cx, cy, r_okr, r_luk, span).
    Srodki zawsze OCS->WCS (lustra!)."""
    arcs, circles = [], []
    for e in msp:
        t = e.dxftype()
        if t == "ARC":
            arcs.append(e)
        elif t == "CIRCLE":
            circles.append(e)
    handles, gwinty = set(), []
    for a in arcs:
        sp = _arc_span(a)
        if not (SPAN_MIN <= sp <= SPAN_MAX):
            continue
        ca = _wcs_center(a)
        for c in circles:
            cc = _wcs_center(c)
            if math.hypot(ca[0] - cc[0], ca[1] - cc[1]) > CENTER_TOL:
                continue
            r_ok, r_lu = float(c.dxf.radius), float(a.dxf.radius)
            if r_ok <= 0 or not (RATIO_MIN <= r_lu / r_ok <= RATIO_MAX):
                continue
            handles.add(a.dxf.handle)
            gwinty.append(dict(arc=a, circle=c, cx=ca[0], cy=ca[1],
                               r_okr=r_ok, r_luk=r_lu, span=sp))
            break
    return handles, gwinty


def m_z_luku(r_luk, tol=M_TOL):
    """Rozmiar gwintu z nominalu luku (luk o6.0 -> 'M6'). None gdy srednica
    nie pasuje do zadnego nominalu M3..M24 w tolerancji (pliki 1:1!)."""
    d = 2.0 * float(r_luk)
    best, bd = None, tol
    for nom in M_NOMINALY:
        dd = abs(d - nom)
        if dd <= bd:
            bd, best = dd, nom
    return None if best is None else "M%d" % int(best)


def wczytaj_tablice(path):
    """Tablica srednic palenia: config/gwinty_hardox.yaml -> dict {'M6': 6.6|None}.
    Wartosci null = operator jeszcze nie wpisal = gwint zostaje nietkniety."""
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    out = {}
    for k, v in data.items():
        ks = str(k).upper().strip()
        if not ks.startswith("M"):
            continue
        out[ks] = None if v is None else float(v)
    return out


def transformuj(msp, tablica):
    """Transformacja gwintow dla materialu TRUDNOSCIERALNEGO (caller sprawdza
    material przez czy_trudnoscieralny; na zwyklym NIE wolno wolac).

    Dla kazdego wykrytego gwintu:
    - M rozpoznane i tablica[M] ma wartosc -> luk USUNIETY, okrag powiekszony
      do tablica[M], kolor okregu = 1 (czerwony); akcja='zmieniony'
    - brak wartosci / M nierozpoznane / anomalia (>1 luk na okrag) ->
      NIC nie ruszone; akcja='zostaw' + powod (status pozycji min. ZOLTY)

    Zwraca liste zmian: dict(m, cx, cy, d_luku, d_przed, d_po, akcja, powod).
    Pusta tablica ({} lub same null) => zero modyfikacji pliku.
    """
    tablica = tablica or {}
    _, gwinty = thread_arcs(msp)
    # anomalia: wiecej niz jeden luk dopasowany do tego samego okregu
    per_circle = {}
    for g in gwinty:
        per_circle.setdefault(g["circle"].dxf.handle, []).append(g)
    zmiany = []
    for hc, grupa in per_circle.items():
        g = grupa[0]
        m = m_z_luku(g["r_luk"])
        rec = dict(m=m or "M?", cx=round(g["cx"], 3), cy=round(g["cy"], 3),
                   d_luku=round(2 * g["r_luk"], 3),
                   d_przed=round(2 * g["r_okr"], 3), d_po=None)
        if len(grupa) > 1:
            rec.update(akcja="zostaw",
                       powod="anomalia: %d luki na jednym okregu" % len(grupa))
            zmiany.append(rec)
            continue
        if m is None:
            rec.update(akcja="zostaw",
                       powod="M nierozpoznane (luk o%.2f poza nominalami)"
                             % (2 * g["r_luk"]))
            zmiany.append(rec)
            continue
        wartosc = tablica.get(m)
        if wartosc is None:
            rec.update(akcja="zostaw", powod="%s bez wartosci w tablicy" % m)
            zmiany.append(rec)
            continue
        # TRANSFORMACJA: luk out, okrag -> srednica palenia, CZERWONY
        msp.delete_entity(g["arc"])
        g["circle"].dxf.radius = float(wartosc) / 2.0
        g["circle"].dxf.color = 1
        rec.update(d_po=float(wartosc), akcja="zmieniony",
                   powod="gwint %s -> o%g (zmieniony)" % (m, wartosc))
        zmiany.append(rec)
    return zmiany


def status_po_transformacji(zmiany):
    """Minimalny status pozycji po transformacji: 'zolty' gdy jakikolwiek
    gwint zostal (bez wartosci/M?/anomalia), inaczej None (bez wplywu)."""
    return "zolty" if any(z["akcja"] == "zostaw" for z in zmiany) else None


def open_ends(msp, exclude_handles=frozenset(), tol=END_TOL):
    """Otwarte konce (bramka 2): parowanie koncow realna odlegloscia <= tol.
    CIRCLE i encje zamkniete pomijane; giecie (kolor 6 / warstwa GIECIE) poza.
    exclude_handles: encje wylaczone z liczenia (luki gwintu)."""
    pts = []
    for e in msp:
        t = e.dxftype()
        if t not in {"LINE", "ARC", "LWPOLYLINE", "POLYLINE", "SPLINE",
                     "ELLIPSE"}:
            continue
        if e.dxf.handle in exclude_handles:
            continue
        if e.dxf.layer.upper() == "GIECIE" or e.dxf.color == 6:
            continue
        try:
            p = ezpath.make_path(e)
            fl = [(v.x, v.y) for v in p.flattening(distance=SAG)]
        except Exception:
            continue
        if len(fl) < 2:
            continue
        d = math.hypot(fl[0][0] - fl[-1][0], fl[0][1] - fl[-1][1])
        if d < 1e-9 or bool(getattr(e, "closed", False)):
            continue
        pts.append(fl[0])
        pts.append(fl[-1])
    used = [False] * len(pts)
    n_open = 0
    for i in range(len(pts)):
        if used[i]:
            continue
        best, bd = None, tol
        for j in range(len(pts)):
            if j == i or used[j]:
                continue
            d = math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
            if d <= bd:
                bd, best = d, j
        if best is None:
            n_open += 1
        else:
            used[i] = used[best] = True
    return n_open


def wyklucz_z_bramki2(msp):
    """Bramka 2 swiadoma gwintu (KAZDY material): liczy otwarte konce
    Z WYKLUCZENIEM lukow gwintu. Zwraca dict:
    otwarte_surowe, otwarte_bez_gwintow, n_gwintow."""
    handles, gwinty = thread_arcs(msp)
    return dict(otwarte_surowe=open_ends(msp),
                otwarte_bez_gwintow=open_ends(msp, exclude_handles=handles),
                n_gwintow=len(gwinty))
