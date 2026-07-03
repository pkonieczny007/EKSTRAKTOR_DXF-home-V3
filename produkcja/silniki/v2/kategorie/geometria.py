# -*- coding: utf-8 -*-
"""
Kategoria 3: PO CECHACH GEOMETRII - ktory kandydat to CZYSTY, wycinalny widok?

Kategoria RATUNKOWA: szuka widokow, ktore przepadly na zwyklej tolerancji
dopasowania (3%), ale maja DOMKNIETY kontur (0 otwartych koncow = warunek
lasera) i mieszcza sie w luznej tolerancji (1.5x). Tacy kandydaci sa ZAWSZE
niepewni (zapis tylko jako NIEPEWNE/_DO_SPRAWDZENIA) - nie zgadujemy
geometrii, niepewne = do czlowieka. Nigdy nie przebijaja kandydatow
z kategorii struktura/wymiary (priorytet 3).

Cechy geometrii (otwarte konce, statystyka encji, izometria) dzialaja tez
jako metryki rankingu (v1.rank_value) i bramki weryfikatora - to jest wklad
tej kategorii do WSZYSTKICH kandydatow.
"""
from v2 import wspolne
from v2.wspolne import v1


def _match_luzny(c, dim_max, dim_min, tol):
    """Jak v1.match_scale, ale z luzniejsza tolerancja zgodnosci skali x/y."""
    cw, ch = max(c["w"], c["h"]), min(c["w"], c["h"])
    if cw < 1e-6 or ch < 1e-6:
        return None
    s_major, s_minor = dim_max / cw, dim_min / ch
    if s_major <= 0:
        return None
    rel = abs(s_major - s_minor) / s_major
    if rel > tol:
        return None
    return (s_major + s_minor) / 2, rel


def _domkniety(c):
    solid = [e for e in c["entities"]
             if not (e.dxf.linetype or "").upper().startswith(("DASHED", "HIDDEN"))]
    return v1.open_ends(solid) == 0


def znajdz(geo, wiersz, profil=None):
    """Kandydaci-ratunkowi: domkniety kontur + luzna tolerancja wymiaru."""
    dims = wiersz.get("dims")
    if not dims:
        return []
    profil = profil or {}
    tol = profil.get("luzna_tolerancja", 0.045)
    encje = geo.geom + geo.dashed
    out = []
    for gap in v1.FALLBACK_GAPS:
        clusters = geo.klastry("all", encje, gap)
        for c in clusters:
            if v1.match_scale(c, dims[0], dims[1]):
                continue    # zwykle dopasowanie obsluzy kategoria wymiary
            m = _match_luzny(c, dims[0], dims[1], tol)
            if not m:
                continue
            if len(c["entities"]) < 3 or not _domkniety(c):
                continue    # smieci / kontur otwarty - to nie wycinalny widok
            out.append(wspolne.zbuduj_kandydata(
                clusters, c, m, geo, kategoria="geometria",
                technika=f"czysty-kontur-luzna-tol gap={gap:g}",
                priorytet=3, pewnosc=0.4, absorpcja="klastry",
                etykieta_warstwy=f"(bez warstw, geometria, gap={gap:g})",
                niepewny=True, tie=3))
    return out
