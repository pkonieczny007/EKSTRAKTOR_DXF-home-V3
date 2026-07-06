# -*- coding: utf-8 -*-
"""
Kategoria 4: PO ADNOTACJACH TEKSTOWYCH - tekst wskazuje ktory widok to ktora pozycja.

Uzyteczna gdy pozycje NIE sa na warstwach 1NN ani nie ida czysto po kolorze, ale
rysunek ma DYMKI z numerem pozycji (babelek "12") albo adnotacje lustra.

Techniki (konserwatywnie - wysoka precyzja, nie zasmiecac kandydatow):
  A. BABELEK NUMERU POZYCJI: TEXT/MTEXT o tresci == numer pozycji (albo "Pos. N"/
     "Poz. N"/"Position N") -> najblizszy klaster geometrii -> KANDYDAT, ale TYLKO
     gdy wymiar klastra pasuje do wykazu (match_scale). Filtr wymiarem chroni przed
     zlym babelkiem/tekstem wymiarowym: nawet gdy najblizszy klaster jest zly,
     kandydat powstaje wylacznie przy zgodnym wymiarze.
  B. HINT LUSTRA: obecnosc "gespiegelt"/"mirrored"/"lustro" w adnotacjach rysunku ->
     kandydat oznaczony NIEPEWNY (asymetria/lustro do potwierdzenia, zasada CLAUDE.md).
     Wlasciwa obsluga P/L (odbicie) zostaje w orkiestratorze - tu tylko flaga.

Priorytet 2 / pewnosc 0.55: nie przebija pewnej struktury (warstwa 1NN), ale daje
kandydata tam, gdzie struktura milczy. Wtyczka wpina sie jak 1-3 (config/kategorie.yaml);
DOMYSLNIE WYLACZONA - wlaczenie po benchmarku (zasada 10).
"""
import math
import re

from v2 import wspolne
from v2.wspolne import v1

_POZ_RE = re.compile(r"^\s*(?:pos\.?|poz\.?|position|teil)\s*0*(\d+)\s*$", re.IGNORECASE)
_LUSTRO_RE = re.compile(r"gespiegelt|mirrored|lustro", re.IGNORECASE)


def _tekst(e):
    """Znormalizowana tresc TEXT/MTEXT (MTEXT: plain_text bez kodow formatowania)."""
    tp = e.dxftype()
    try:
        if tp == "TEXT":
            return (e.dxf.text or "").strip()
        if tp == "MTEXT":
            return (e.plain_text() if hasattr(e, "plain_text") else e.text or "").strip()
    except Exception:
        pass
    return ""


def _punkt(e):
    """Punkt wstawienia adnotacji (x, y); None gdy brak."""
    try:
        p = e.dxf.insert
        return (float(p.x), float(p.y))
    except Exception:
        return None


def _is_babelek(txt, posn):
    """Czy tekst to dymek numeru pozycji posn? Exact numer albo 'Pos./Poz. N'."""
    txt = (txt or "").strip()
    if not txt:
        return False
    if txt == str(posn):
        return True
    m = _POZ_RE.match(txt)
    return bool(m and int(m.group(1)) == int(posn))


def _dist_center(bbox, pt):
    cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0
    return math.hypot(cx - pt[0], cy - pt[1])


def znajdz(geo, wiersz, profil=None):
    """Kandydaci z adnotacji tekstowych dla jednej pozycji wykazu."""
    dims = wiersz.get("dims")
    posn = wiersz.get("posn")
    if not dims or posn is None:
        return []
    gap = (profil or {}).get("gap", v1.CLUSTER_GAP) if isinstance(profil, dict) else v1.CLUSTER_GAP

    teksty = [(e, _tekst(e)) for e in geo.annot]
    babelki = [e for e, t in teksty if _is_babelek(t, posn)]
    if not babelki:
        return []
    clusters = geo.klastry("adnotacje", geo.geom, gap)
    if not clusters:
        return []
    ma_lustro = any(_LUSTRO_RE.search(t) for _, t in teksty)

    out = []
    uzyte = set()
    for b in babelki:
        pt = _punkt(b)
        if pt is None:
            continue
        # najblizszy klaster do dymka; filtr = zgodnosc wymiaru z wykazem
        for c in sorted(clusters, key=lambda cl: _dist_center(cl["bbox"], pt)):
            klucz = tuple(round(v, 2) for v in c["bbox"])
            if klucz in uzyte:
                continue
            m = v1.match_scale(c, dims[0], dims[1])
            if m:
                tech = f"babelek-poz{posn}" + ("-gespiegelt" if ma_lustro else "")
                out.append(wspolne.zbuduj_kandydata(
                    clusters, c, m, geo, kategoria="adnotacje", technika=tech,
                    priorytet=2, pewnosc=0.55, niepewny=ma_lustro, tie=2))
                uzyte.add(klucz)
                break   # jeden dymek -> jeden (najblizszy pasujacy) klaster
    return out
