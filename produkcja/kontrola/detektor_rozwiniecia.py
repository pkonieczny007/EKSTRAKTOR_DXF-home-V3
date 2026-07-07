# -*- coding: utf-8 -*-
"""DETEKTOR ROZWINIECIA (anty-izometryk) - flager wyboru widoku glownego.

Ocenia klaster-kandydat: czy WYGLADA jak rozwiniecie blachy (plaski kontur na laser),
czy jak rzut izometryczny / widok 3D / rzut boczny o pasujacym bbox. Score sklada sie
z dwoch skladowych:
  geo   - cechy geometrii (domkniety kontur, brak elips-jako-okregow, adnotacja giecia,
          ortogonalnosc 0/45 stopni, udzial linii kreskowanych),
  skala - zgodnosc proporcji z wykazem (prop-match + ladna skala rysunkowa).
TOT = geo + skala. Prog: geo <= PROG_ANTY (-3) = anty-rozwiniecie (kandydat wyglada
na izometrie/rzut boczny mimo pasujacego bbox).

Rola: DODATKOWY, GLOWNY klucz rankingu widoku (additive - dokladany przed dawnym
kluczem nice/open_ends). Zasada 5: flager moze status tylko OBNIZYC - detektor NIE
odrzuca kandydata twardo, tylko premiuje rozwiniecia i podnosi flage NIEPEWNE, gdy
jedyny kandydat sciezki awaryjnej wyglada na rzut.

Prototyp zmierzony na golden: scratchpad/proto3_score2.py (separacja GOOD geo 4-8 vs
BAD/izometryk geo -4..-11). extract_positions importuje ten modul LENIWIE (patrz
_detektor()); tu importujemy extract_positions po bootstrapie sciezki silnikow -
oba kierunki bez cyklu (extract_positions nie importuje detektora na poziomie modulu).
"""
import math
import re
import sys
from pathlib import Path

# bootstrap: extract_positions lezy w ../silniki (dostarcza partition/open_ends/
# interior_clusters/match_scale/NICE_SCALES). Dokladamy sciezke, by import dzialal
# niezaleznie od cwd wolajacego.
_SILNIKI_DIR = Path(__file__).resolve().parent.parent / "silniki"
if str(_SILNIKI_DIR) not in sys.path:
    sys.path.insert(0, str(_SILNIKI_DIR))
import extract_positions as ep  # noqa: E402

# prog "anty-rozwiniecia": geo <= PROG_ANTY = kandydat wyglada na rzut/izometrie
PROG_ANTY = -3

# adnotacja giecia (DE/EN) wewnatrz widoku -> to rozwiniecie (nie rzut)
BEND_TEXT_RE = re.compile(
    r"(?i)(kantung|gekantet|biegung|abkant|bend|n\.?\s*oben|gebogen)")


def bend_texts_from_ents(ents):
    """Pozycje adnotacji giecia (x, y, tekst) z TEXT/MTEXT. Sygnal +2 do geo,
    gdy adnotacja lezy w bbox kandydata (widok z opisem giecia = rozwiniecie)."""
    out = []
    for e in ents:
        if e.dxftype() not in ("TEXT", "MTEXT"):
            continue
        try:
            txt = e.dxf.text if e.dxftype() == "TEXT" else e.text
        except Exception:
            continue
        if not (txt and BEND_TEXT_RE.search(txt)):
            continue
        try:
            ins = e.dxf.insert
            out.append((float(ins[0]), float(ins[1]), txt[:40]))
        except Exception:
            continue
    return out


def line_angles(ents, min_len=1.0):
    """Katy odcinkow LINE (mod 180) - do pomiaru ortogonalnosci 0/45 stopni."""
    out = []
    for e in ents:
        if e.dxftype() == "LINE":
            dx = e.dxf.end.x - e.dxf.start.x
            dy = e.dxf.end.y - e.dxf.start.y
            if math.hypot(dx, dy) >= min_len:
                out.append(math.degrees(math.atan2(dy, dx)) % 180.0)
    return out


def orto45_frac(angs, tol=2.0):
    """Udzial linii lezacych blisko wielokrotnosci 45 stopni. None gdy za malo linii.
    Rozwiniecie = duzo linii orto (0/90) i skosow giecia (45) -> wysoki udzial;
    rzut izometryczny/perspektywa -> katy rozproszone -> niski udzial."""
    if len(angs) < 4:
        return None
    return sum(1 for a in angs if min(a % 45.0, 45.0 - (a % 45.0)) <= tol) / len(angs)


def features(cluster, clusters, dims, bend_texts):
    """Cechy klastra-kandydata do score_rozwiniecie. Wchlania wnetrze (otwory)
    jak ranking: interior_clusters + zamkniete kontury wewnetrzne.

    cluster  - oceniany klaster (dict z 'entities'/'bbox'/'w'/'h');
    clusters - pelna lista klastrow tego samego zbioru (do wchlaniania wnetrza);
    dims     - (dim_max, dim_min) z wykazu albo None/falsy (bez oceny skali);
    bend_texts - lista (x, y, tekst) adnotacji giecia (bend_texts_from_ents)."""
    ents = list(cluster["entities"])
    absorbed = ep.interior_clusters(clusters, cluster)
    inner_closed = 0
    for ic in absorbed:
        ents.extend(ic["entities"])
        ic_solid = [e for e in ic["entities"]
                    if not (e.dxf.linetype or "").upper().startswith(("DASHED", "HIDDEN"))]
        if ic_solid and ep.open_ends(ic_solid) == 0:
            inner_closed += 1
    solid = [e for e in ents
             if not (e.dxf.linetype or "").upper().startswith(("DASHED", "HIDDEN"))]
    f = {}
    f["n_ents"] = len(ents)
    f["n_ellipse"] = sum(1 for e in ents if e.dxftype() == "ELLIPSE")
    f["n_circle"] = sum(1 for e in ents if e.dxftype() == "CIRCLE")
    f["inner_closed"] = inner_closed
    f["open_ends"] = ep.open_ends(solid)
    f["dashed_frac"] = round((len(ents) - len(solid)) / max(len(ents), 1), 2)
    f["orto45"] = orto45_frac(line_angles(solid))
    b = cluster["bbox"]
    f["bend_annot"] = sum(1 for (x, y, _) in bend_texts
                          if b[0] <= x <= b[2] and b[1] <= y <= b[3])
    f["prop_match"] = False
    f["nice"] = False
    f["scale"] = None
    if dims:
        m = ep.match_scale(cluster, dims[0], dims[1])
        if m:
            f["prop_match"] = True
            f["scale"] = round(m[0], 3)
            f["nice"] = any(abs(m[0] - ns) / ns < 0.02 for ns in ep.NICE_SCALES)
        else:
            cw = max(cluster["w"], cluster["h"])
            f["scale"] = round(dims[0] / cw, 3) if cw > 0 else None
    return f


def score_rozwiniecie(f):
    """Zwraca (geo, skala, tot=geo+skala). Punktacja dobrana empirycznie na golden
    (proto3): rozwiniecie -> geo dodatni, rzut/izometryk -> geo mocno ujemny.

    geo:
      +3 domkniety kontur (open_ends==0); -2 gdy silnie otwarty (>4) - rzut w zlozeniu;
      -4 gdy >=3 elipsy (okregi rzutowane jako elipsy = izometria); -2 gdy 1-2 elipsy
         (moze byc owal rysowany ELLIPSE);
      +1 gdy sa okregi lub zamkniete kontury wewnetrzne (otwory = rozwiniecie);
      +2 adnotacja giecia w bbox;
      +1 orto45>=0.9 / -2 orto45<0.6 (rozproszone katy = rzut);
      -1 duzo linii kreskowanych (>15%).
    skala:
      +1 prop-match i ladna skala rysunkowa; 0 prop-match nie-ladna; -3 brak prop-matchu.
    """
    geo = 0
    geo += 3 if f["open_ends"] == 0 else (0 if f["open_ends"] <= 4 else -2)
    if f["n_ellipse"] >= 3:
        geo -= 4          # rzut izometryczny/zlozony (okregi jako elipsy)
    elif f["n_ellipse"] > 0:
        geo -= 2          # 1-2 elipsy: moze byc owal narysowany jako ELLIPSE
    if f["n_circle"] > 0 or f["inner_closed"] > 0:
        geo += 1
    if f["bend_annot"] > 0:
        geo += 2
    if f["orto45"] is not None:
        geo += 1 if f["orto45"] >= 0.9 else (-2 if f["orto45"] < 0.6 else 0)
    if f["dashed_frac"] > 0.15:
        geo -= 1
    skala = 0
    if f["scale"] is not None:
        if f["prop_match"] and f["nice"]:
            skala = 1
        elif f["prop_match"]:
            skala = 0
        else:
            skala = -3
    return geo, skala, geo + skala


def score_klastra(cluster, clusters, dims, bend_texts=None):
    """Skrot: features + score_rozwiniecie -> (geo, skala, tot)."""
    f = features(cluster, clusters, dims, bend_texts or [])
    return score_rozwiniecie(f)
