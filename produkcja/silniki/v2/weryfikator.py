# -*- coding: utf-8 -*-
"""
Weryfikator V2 - poziom 1 obrony: 8 bramek QC liczonych z geometrii.
WSPOLNY dla wszystkich kategorii szukania (zaden kandydat nie omija QC).

Bramki (kontekst/metody_sprawdzania.html):
  1. wymiar bbox vs wykaz          (tolerancja jak w silniku V1)
  2. kontur domkniety              (0 otwartych koncow - warunek lasera)
  3. filtr smieci                  (za malo encji / kolo segmentowane z krotkich odcinkow)
  4. bilans otworow                (otwory w wyniku vs okregi w widoku zrodlowym)
  5. detekcja izometrii            (piki dlugosci linii pod ~30/150 stopni = rzut 3D)
  6. bramka giecia                 (linie kolor 6 w zrodle musza trafic na warstwe GIECIE)
  7. rejestr widokow               (widok nie moze byc uzyty dwa razy - lustra!)
  8. sanity 1:1                    (wynik wysrodkowany, srodek bbox w (0,0))

Wynik = semafor: ZIELONY (wszystkie OK) / ZOLTY (niepewne - kazdy ZOLTY
ma JAWNY powod-string) / CZERWONY (bramka twarda nie przeszla - do reki).

Uzycie z kodu:
  from v2.weryfikator import weryfikuj_kandydata, weryfikuj_wynik_dxf
Uzycie z CLI (post-hoc na gotowym DXF):
  python src\\v2\\weryfikator.py <plik.dxf> <dim_max> <dim_min>
"""
import sys
import io
import math
from dataclasses import dataclass, field
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bbox

# silnik V1 = jedyne zrodlo prawdy geometrii (import, nie kopiuj-wklej)
_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
import extract_positions as v1

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OK, ZOLTY, CZERWONY, POMINIETA = "OK", "ZOLTY", "CZERWONY", "POMINIETA"
_RANGA = {OK: 0, POMINIETA: 0, ZOLTY: 1, CZERWONY: 2}


@dataclass
class Bramka:
    nr: int
    nazwa: str
    status: str
    powod: str = ""

    def __post_init__(self):
        # zasada nadrzedna: kazdy status niepewny MUSI miec jawny powod
        if self.status in (ZOLTY, CZERWONY) and not self.powod:
            raise ValueError(f"bramka {self.nr} ({self.nazwa}): "
                             f"status {self.status} bez jawnego powodu")


@dataclass
class WynikQC:
    bramki: list = field(default_factory=list)

    @property
    def semafor(self):
        r = max((_RANGA[b.status] for b in self.bramki), default=0)
        return {0: "ZIELONY", 1: "ZOLTY", 2: "CZERWONY"}[r]

    def powody(self):
        return [f"[{b.nr}.{b.nazwa}] {b.powod}" for b in self.bramki
                if b.status in (ZOLTY, CZERWONY)]

    def opis(self):
        return "; ".join(self.powody())


# ---------------------------------------------------------------- pomocnicze

def _dlugosc_linii(e):
    dx = e.dxf.end.x - e.dxf.start.x
    dy = e.dxf.end.y - e.dxf.start.y
    return math.hypot(dx, dy)


def _solid(encje):
    """Encje konturu bez linii kreskowanych (jak w rankingu V1)."""
    return [e for e in encje
            if not (e.dxf.linetype or "").upper().startswith(("DASHED", "HIDDEN"))]


def policz_otwory(encje):
    """Otwory = CIRCLE + pelne ELLIPSE (zamkniete krzywe bez koncow)."""
    n = 0
    for e in encje:
        t = e.dxftype()
        if t == "CIRCLE":
            n += 1
        elif t == "ELLIPSE" and getattr(e, "closed", True):
            n += 1
    return n


def policz_linie_giecia_zrodla(encje, min_dim):
    """Linie-kandydatki giecia w widoku zrodlowym: kolor 6 (magenta) -
    najpewniejszy wyznacznik giecia NIEZALEZNIE od linetype (wiedza:
    giecie-phantom-kolor6). Krzyz osi otworu tez bywa magenta - odrozniamy
    po dlugosci: linia giecia idzie przez cala czesc (L >= ~0.6 min wymiaru)."""
    n = 0
    prog = 0.6 * min_dim
    for e in encje:
        if e.dxf.color != 6:
            continue
        t = e.dxftype()
        if t == "LINE" and _dlugosc_linii(e) >= prog:
            n += 1
        elif t in ("ARC", "LWPOLYLINE", "POLYLINE", "SPLINE"):
            b = v1.ent_bbox(e)
            if b and max(b[2] - b[0], b[3] - b[1]) >= prog:
                n += 1
    return n


# ------------------------------------------------------------------- bramki

def bramka1_wymiar(out_w, out_h, dim_max, dim_min):
    """1. Wymiar bbox vs wykaz - tolerancja max(1mm, 0.2%) jak w V1."""
    if out_w is None or dim_max is None:
        return Bramka(1, "wymiar", POMINIETA)
    ok_w = abs(out_w - dim_max) <= max(1.0, dim_max * 0.002)
    ok_h = abs(out_h - dim_min) <= max(1.0, dim_min * 0.002)
    if ok_w and ok_h:
        return Bramka(1, "wymiar", OK)
    return Bramka(1, "wymiar", CZERWONY,
                  f"wynik {out_w:g} x {out_h:g} mm vs wykaz {dim_max:g} x {dim_min:g} mm")


def bramka1_wymiar_zgrubna(rel_err, prog=0.03):
    """1. Wymiar PRZED zapisem - zgrubnie po bledzie proporcji dopasowania.
    Szybki bbox klastra PRZESZACOWUJE krzywe (SPLINE po punktach kontrolnych),
    wiec scisla walidacja mm nastepuje dopiero PO zapisie na realnych extents
    (jak w V1). Tu odpada tylko kandydat bez zgodnosci proporcji (awaryjny)."""
    if rel_err is None:
        return Bramka(1, "wymiar", POMINIETA)
    if rel_err <= prog:
        return Bramka(1, "wymiar", OK)
    return Bramka(1, "wymiar", CZERWONY,
                  f"blad proporcji {rel_err * 100:.0f}% > {prog * 100:.0f}% "
                  f"(brak zgodnosci skali x/y)")


def bramka2_kontur(encje):
    """2. Kontur domkniety - 0 otwartych koncow (laser wymaga zamknietych)."""
    oe = v1.open_ends(_solid(encje))
    if oe == 0:
        return Bramka(2, "kontur", OK)
    return Bramka(2, "kontur", ZOLTY, f"{oe} otwartych koncow konturu")


def bramka3_smieci(encje):
    """3. Filtr smieci - wycina falszywe trafiki o pasujacym bbox:
    <3 encje albo 'pierscien' z wielu krotkich odcinkow (kolo osiowe
    segmentowane; wiedza: sbm-okragle-niewyciagalne). Sito z drobnymi
    wycieciami NIE jest smieciem - ma kontur domkniety (open_ends=0)."""
    n = len(encje)
    if n == 0:
        return Bramka(3, "smieci", CZERWONY, "0 encji geometrii")
    if n < 3:
        return Bramka(3, "smieci", ZOLTY,
                      f"tylko {n} encje/i - sprawdz czy to realny kontur")
    linie = [e for e in encje if e.dxftype() == "LINE"]
    if len(linie) >= 40:
        boxes = [v1.ent_bbox(e) for e in encje]
        boxes = [b for b in boxes if b]
        w = max(b[2] for b in boxes) - min(b[0] for b in boxes)
        h = max(b[3] for b in boxes) - min(b[1] for b in boxes)
        sr = sum(_dlugosc_linii(e) for e in linie) / len(linie)
        if sr < 0.02 * max(w, h) and v1.open_ends(_solid(encje)) > 0:
            return Bramka(3, "smieci", ZOLTY,
                          f"podejrzenie kola segmentowanego: {len(linie)} "
                          f"odcinkow o sr. dlugosci {sr:.1f} przy widoku "
                          f"{w:.0f} x {h:.0f} - to nie kontur ciecia")
    return Bramka(3, "smieci", OK)


def bramka4_otwory(n_otworow_wynik, n_otworow_zrodlo):
    """4. Bilans otworow - otwory sa swiete: liczba okregow w wyniku nie moze
    byc mniejsza niz w widoku zrodlowym."""
    if n_otworow_zrodlo is None:
        return Bramka(4, "otwory", POMINIETA)
    if n_otworow_wynik >= n_otworow_zrodlo:
        return Bramka(4, "otwory", OK)
    return Bramka(4, "otwory", ZOLTY,
                  f"w widoku zrodlowym {n_otworow_zrodlo} okregow, "
                  f"w wyniku {n_otworow_wynik} - zgubiony otwor?")


def bramka5_izometria(encje):
    """5. Detekcja izometrii - rzut 3D o pasujacym bbox: dlugosc linii
    skupiona pod ~30/150 stopni zamiast 0/90 (pulapka nr 5 z CLAUDE_v1)."""
    wagi = {"iso": 0.0, "orto": 0.0, "inne": 0.0}
    total = 0.0
    for e in encje:
        if e.dxftype() != "LINE":
            continue
        dl = _dlugosc_linii(e)
        if dl < 1e-9:
            continue
        kat = math.degrees(math.atan2(e.dxf.end.y - e.dxf.start.y,
                                      e.dxf.end.x - e.dxf.start.x)) % 180.0
        total += dl
        if min(abs(kat - 30), abs(kat - 150)) <= 4:
            wagi["iso"] += dl
        elif min(kat, abs(kat - 90), abs(kat - 180)) <= 4:
            wagi["orto"] += dl
        else:
            wagi["inne"] += dl
    if total < 1e-9:
        return Bramka(5, "izometria", OK)
    frak = wagi["iso"] / total
    if frak > 0.45 and wagi["iso"] > wagi["orto"]:
        return Bramka(5, "izometria", ZOLTY,
                      f"podejrzenie rzutu izometrycznego: {frak * 100:.0f}% "
                      f"dlugosci linii pod ~30/150 stopni")
    return Bramka(5, "izometria", OK)


def bramka6_giecie(n_giec_wynik, n_giec_zrodlo):
    """6. Bramka giecia - gdy widok zrodlowy ma linie giecia (kolor 6),
    musza trafic na warstwe GIECIE w wyniku (bez nich nie wiadomo gdzie
    i w ktora strone giac; jedyne co rozni pare P/L)."""
    if n_giec_zrodlo is None:
        return Bramka(6, "giecie", POMINIETA)
    if n_giec_zrodlo > 0 and n_giec_wynik == 0:
        return Bramka(6, "giecie", ZOLTY,
                      f"w widoku zrodlowym {n_giec_zrodlo} linii koloru 6 "
                      f"(giecie?), na warstwie GIECIE 0 - zgubione giecie?")
    return Bramka(6, "giecie", OK)


def bramka7_rejestr(box, zajete):
    """7. Rejestr widokow - zaden widok nie moze byc uzyty dwa razy
    (pozycja lustrzana nie moze ukrasc widoku blizniaka - pulapka nr 4)."""
    if box is None or zajete is None:
        return Bramka(7, "rejestr", POMINIETA)
    if v1.overlaps_claimed(box, zajete):
        return Bramka(7, "rejestr", CZERWONY,
                      "widok juz przypisany innej pozycji")
    return Bramka(7, "rejestr", OK)


def bramka8_sanity(extmin, extmax):
    """8. Sanity 1:1 - wynik wysrodkowany (srodek bbox w (0,0)), niezerowy."""
    if extmin is None:
        return Bramka(8, "sanity", POMINIETA)
    w, h = extmax[0] - extmin[0], extmax[1] - extmin[1]
    if w <= 0 or h <= 0:
        return Bramka(8, "sanity", CZERWONY, "pusty bbox wyniku")
    cx, cy = (extmin[0] + extmax[0]) / 2, (extmin[1] + extmax[1]) / 2
    if abs(cx) > 0.5 or abs(cy) > 0.5:
        return Bramka(8, "sanity", ZOLTY,
                      f"wynik niewysrodkowany: srodek bbox w ({cx:.1f}, {cy:.1f})")
    return Bramka(8, "sanity", OK)


def aktualizuj_bramke_wymiaru(wynik_qc, out_w, out_h, dims):
    """Po zapisie: podmienia zgrubna bramke 1 na scisla walidacje mm
    z realnych extents zapisanego pliku (jak walidacja V1 w save_view)."""
    dim_max, dim_min = dims if dims else (None, None)
    nowa = bramka1_wymiar(out_w, out_h, dim_max, dim_min)
    wynik_qc.bramki = [nowa if b.nr == 1 else b for b in wynik_qc.bramki]
    return wynik_qc


# ------------------------------------------------------- funkcje zbiorcze

def weryfikuj_kandydata(kandydat, dims, zrodlo=None, zajete=None):
    """QC kandydata PRZED zapisem (przestrzen zrodlowa, encje + skala).

    kandydat: obiekt z polami encje, giecia, bbox, skala (v2.wspolne.Kandydat)
    dims:     (dim_max, dim_min) z wykazu albo None
    zrodlo:   dict kontekstu zrodloweg (opcjonalny):
              n_otworow (okregi w widoku zrodlowym), n_giec (linie kolor 6)
    zajete:   rejestr bboxow widokow juz przypisanych innym pozycjom
    """
    b = kandydat.bbox
    zrodlo = zrodlo or {}

    wynik = WynikQC()
    # wymiar zgrubnie (szybki bbox przeszacowuje SPLINE) - scisla walidacja
    # mm robi orkiestrator PO zapisie (aktualizuj_bramke_wymiaru)
    wynik.bramki.append(bramka1_wymiar_zgrubna(
        kandydat.rel_err if dims else None))
    wynik.bramki.append(bramka2_kontur(kandydat.encje))
    wynik.bramki.append(bramka3_smieci(kandydat.encje))
    wynik.bramki.append(bramka4_otwory(policz_otwory(kandydat.encje),
                                       zrodlo.get("n_otworow")))
    wynik.bramki.append(bramka5_izometria(kandydat.encje))
    wynik.bramki.append(bramka6_giecie(len(kandydat.giecia),
                                       zrodlo.get("n_giec")))
    wynik.bramki.append(bramka7_rejestr(b, zajete))
    # sanity 1:1 dotyczy pliku PO zapisie - tu wynik jeszcze nie zapisany
    wynik.bramki.append(Bramka(8, "sanity", POMINIETA))
    return wynik


def weryfikuj_wynik_dxf(dxf_path, dims, zrodlo=None):
    """QC post-hoc na GOTOWYM pliku DXF (1:1, po wysrodkowaniu) - do
    benchmarku i galerii; dziala tez na wynikach V1."""
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    kontur = [e for e in msp if e.dxf.layer != "GIECIE"]
    giecia = [e for e in msp if e.dxf.layer == "GIECIE"]
    ext = _bbox.extents(msp)
    if ext.has_data:
        extmin = (ext.extmin.x, ext.extmin.y)
        extmax = (ext.extmax.x, ext.extmax.y)
        w, h = ext.size.x, ext.size.y
        out_w, out_h = max(w, h), min(w, h)
    else:
        extmin = extmax = out_w = out_h = None
    dim_max, dim_min = dims if dims else (None, None)
    zrodlo = zrodlo or {}

    wynik = WynikQC()
    wynik.bramki.append(bramka1_wymiar(out_w, out_h, dim_max, dim_min))
    wynik.bramki.append(bramka2_kontur(kontur))
    wynik.bramki.append(bramka3_smieci(kontur))
    wynik.bramki.append(bramka4_otwory(policz_otwory(kontur),
                                       zrodlo.get("n_otworow")))
    wynik.bramki.append(bramka5_izometria(kontur))
    wynik.bramki.append(bramka6_giecie(len(giecia), zrodlo.get("n_giec")))
    wynik.bramki.append(bramka7_rejestr(None, None))   # rejestr = etap szukania
    wynik.bramki.append(bramka8_sanity(extmin, extmax))
    return wynik


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    dxf = sys.argv[1]
    dims = None
    if len(sys.argv) >= 4:
        dims = (float(sys.argv[2]), float(sys.argv[3]))
    wynik = weryfikuj_wynik_dxf(dxf, dims)
    print(f"{Path(dxf).name}: semafor = {wynik.semafor}")
    for b in wynik.bramki:
        info = f" - {b.powod}" if b.powod else ""
        print(f"  {b.nr}. {b.nazwa:<10} {b.status}{info}")
    sys.exit(0 if wynik.semafor != "CZERWONY" else 1)


if __name__ == "__main__":
    main()
