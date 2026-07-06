# -*- coding: utf-8 -*-
"""
Kategoria 5: PO ARCHIWUM / KORPUSIE - czy ta pozycja byla juz kiedys ekstrahowana?

Gdy korpus (archiwum znanych ekstrakcji) ma wpis dla tej pozycji (po Zeinr+Posn albo
po wymiarach), znamy jej SYGNATURE GEOMETRYCZNA (ile okregow, ile encji, proporcja).
Wtedy sposrod klastrow pasujacych wymiarem wybieramy ten, ktorego sygnatura zgadza
sie z archiwum -> kandydat wyzszej pewnosci. Rozjazd sygnatury (wymiar OK, ale inna
liczba otworow) = kandydat NIEPEWNY (moze zgubiona cecha albo inna rewizja czesci).

Sygnatura LEKKA (bez shapely - kategoria ma byc tania): liczba okregow PO DEDUPIE
wspolsrodkowych + liczba encji geometrii + proporcja bboxu. Wystarcza do dopasowania
archiwalnego (wymiar + liczba otworow + ksztalt).

Korpus: CSV ';' o kolumnach zeinr;posn;dim_max;dim_min;n_circ;n_geom (domyslnie
nauka/korpus/sygnatury.csv; sciezke mozna podac w profilu 'korpus'). BRAK korpusu /
brak wpisu -> [] (kategoria milczy - nie zgaduje). DOMYSLNIE WYLACZONA (opt-in).
"""
import csv
from pathlib import Path

from v2 import wspolne
from v2.wspolne import v1

_REPO = Path(__file__).resolve().parents[4]
KORPUS_DOMYSLNY = _REPO / "nauka" / "korpus" / "sygnatury.csv"
DEDUP_TOL = 0.3          # mm - grupowanie okregow wspolsrodkowych
RATIO_TOL = 0.08         # tolerancja proporcji bboxu


def _dedup_okregi(entities):
    """Liczba okregow po dedupie wspolsrodkowych (fertzing = 1 cecha)."""
    centra = []
    for e in entities:
        if e.dxftype() != "CIRCLE":
            continue
        try:
            c = e.ocs().to_wcs(e.dxf.center)
        except Exception:
            c = e.dxf.center
        if not any(abs(c.x - x) <= DEDUP_TOL and abs(c.y - y) <= DEDUP_TOL
                   for x, y in centra):
            centra.append((c.x, c.y))
    return len(centra)


def _sygnatura(cluster):
    """Lekka sygnatura klastra: (n_circ_dedup, n_geom, ratio w/h)."""
    ents = cluster["entities"]
    n_circ = _dedup_okregi(ents)
    n_geom = sum(1 for e in ents if e.dxftype() in v1.GEOM_TYPES)
    w, h = cluster.get("w", 0.0), cluster.get("h", 0.0)
    ratio = (max(w, h) / min(w, h)) if min(w, h) > 1e-6 else 0.0
    return {"n_circ": n_circ, "n_geom": n_geom, "ratio": round(ratio, 3)}


def _wczytaj_korpus(sciezka=None):
    """{(zeinr, posn): wpis} + lista wpisow (do dopasowania po wymiarach)."""
    p = Path(sciezka) if sciezka else KORPUS_DOMYSLNY
    if not p.exists():
        return {}, []
    po_kluczu, wszystkie = {}, []
    try:
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                try:
                    wpis = {"zeinr": str(r.get("zeinr", "")).strip(),
                            "posn": str(r.get("posn", "")).strip(),
                            "dim_max": float(r["dim_max"]), "dim_min": float(r["dim_min"]),
                            "n_circ": int(float(r.get("n_circ", 0) or 0)),
                            "n_geom": int(float(r.get("n_geom", 0) or 0))}
                except (KeyError, ValueError, TypeError):
                    continue
                wszystkie.append(wpis)
                po_kluczu[(wpis["zeinr"], wpis["posn"])] = wpis
    except Exception:
        return {}, []
    return po_kluczu, wszystkie


def _po_wymiarach(wszystkie, dims, tol=1.0, proc=0.002):
    """Wpis korpusu pasujacy wymiarem (max/min) - gdy brak trafienia po kluczu."""
    dmax, dmin = max(dims), min(dims)
    for w in wszystkie:
        if abs(w["dim_max"] - dmax) <= max(tol, proc * dmax) and \
           abs(w["dim_min"] - dmin) <= max(tol, proc * dmin):
            return w
    return None


def _sig_zgodna(sig, wpis):
    """Sygnatura klastra zgodna z archiwum? Liczba okregow MUSI sie zgadzac
    (otwory swiete); n_geom i ratio z tolerancja."""
    if sig["n_circ"] != wpis["n_circ"]:
        return False
    if wpis["n_geom"] and abs(sig["n_geom"] - wpis["n_geom"]) > max(2, 0.15 * wpis["n_geom"]):
        return False
    return True


def znajdz(geo, wiersz, profil=None):
    """Kandydat z dopasowania do archiwum (sygnatura). [] gdy brak korpusu/wpisu."""
    dims = wiersz.get("dims")
    if not dims:
        return []
    sciezka = (profil or {}).get("korpus") if isinstance(profil, dict) else None
    po_kluczu, wszystkie = _wczytaj_korpus(sciezka)
    if not wszystkie:
        return []
    zeinr, posn = str(wiersz.get("zeinr", "")), str(wiersz.get("posn", ""))
    wpis = po_kluczu.get((zeinr, posn)) or _po_wymiarach(wszystkie, dims)
    if not wpis:
        return []

    clusters = geo.klastry("korpus", geo.geom, v1.CLUSTER_GAP)
    kand = []
    for c in clusters:
        m = v1.match_scale(c, dims[0], dims[1])
        if not m:
            continue
        sig = _sygnatura(c)
        kand.append((c, m, _sig_zgodna(sig, wpis)))
    if not kand:
        return []
    kand.sort(key=lambda x: (not x[2],))    # zgodne sygnatury pierwsze
    c, m, zgodna = kand[0]
    tech = "korpus-zgodny" if zgodna else "korpus-wymiar-ok-sygnatura-rozjazd"
    return [wspolne.zbuduj_kandydata(
        clusters, c, m, geo, kategoria="korpus", technika=tech,
        priorytet=2, pewnosc=0.7 if zgodna else 0.35, niepewny=not zgodna, tie=2)]
