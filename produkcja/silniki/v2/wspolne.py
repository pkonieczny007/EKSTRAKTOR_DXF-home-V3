# -*- coding: utf-8 -*-
"""
Wspolne typy V2: Kandydat (wynik kategorii szukania) + Geometria (kontekst
rysunku dla kategorii: partycje encji, warstwy pozycyjne, cache klastrow,
rozbicie blokow INSERT).

Wspolny interfejs kategorii (wtyczka):
  znajdz(geometria, wiersz_wykazu, profil) -> [Kandydat]
Kazdy Kandydat ma pewnosc 0-1 i metryki QC; orkiestrator porownuje kandydatow
NIE znajac srodka kategorii.

Silnik V1 (extract_positions.py) = jedyne zrodlo prawdy geometrii - importujemy
jego funkcje (klastrowanie, dopasowanie skali, ranking, wchlanianie otworow),
nie kopiujemy ich.
"""
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import ezdxf

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
import extract_positions as v1   # noqa: E402


@dataclass
class Kandydat:
    """Kandydat na widok pozycji zwracany przez kategorie szukania."""
    cluster: dict            # klaster widoku jak w V1: entities, bbox, w, h
    absorbed: list           # klastry wchloniete do wnetrza (otwory sa swiete)
    giecia: list             # linie giecia (DASHDOT) w obrysie -> warstwa GIECIE
    skala: float
    rel_err: float
    kategoria: str           # nazwa kategorii, ktora znalazla
    technika: str            # np. warstwa-101, po-kolorze-2, bbox-1:1 gap=4
    priorytet: int           # 1=warstwa, 2=bez struktury/kolor, 3=ratunkowy, 4=awaryjny
    pewnosc: float           # 0-1 (do raportu i porownania miedzy kategoriami)
    metryki: tuple = ()      # tuple rankingu V1: (ladna_skala, -otwarte_konce, n_encji, -rel_err)
    niepewny: bool = False   # True => wolno zapisac tylko jako NIEPEWNE/_DO_SPRAWDZENIA
    tie: int = 9             # remis rankingu: mniejszy wygrywa (kolejnosc jak w V1:
                             # 0=warstwa, 1=caly rysunek, 2=per-kolor, 3=ratunkowy)
    etykieta_warstwy: str = ""   # co wpisac w kolumne layer raportu
    n_clusters: int = 0
    n_dashed: int = 0
    qc: object = None        # WynikQC z weryfikatora (wypelnia orkiestrator)

    @property
    def bbox(self):
        return self.cluster["bbox"]

    @property
    def encje(self):
        """Encje wyniku: klaster glowny + wchloniete wnetrze."""
        out = list(self.cluster["entities"])
        for a in self.absorbed:
            out.extend(a["entities"])
        return out


def zbuduj_kandydata(clusters, c, dopasowanie, geo, *, kategoria, technika,
                     priorytet, pewnosc, absorpcja="klastry",
                     etykieta_warstwy="", n_dashed=None, niepewny=False, tie=9):
    """Sklada Kandydata z klastra: wchlania wnetrze, dobiera giecia, liczy metryki.

    absorpcja: "klastry" = wchlon cale klastry wewnatrz bbox (tryb warstwowy/all);
               "otwory"  = tylko CIRCLE/ELLIPSE (tryb per-kolor - inaczej
                           wrocilyby linie wymiarowe lezace w bbox).
    """
    skala, rel = dopasowanie
    if absorpcja == "klastry":
        absorbed = v1.interior_clusters(clusters, c)
    else:
        otwory = [{"entities": [e], "bbox": v1.ent_bbox(e)}
                  for e in geo.geom
                  if e.dxftype() in ("CIRCLE", "ELLIPSE")
                  and e not in c["entities"] and v1.ent_bbox(e)]
        absorbed = v1.interior_clusters([c] + otwory, c)
    giecia = v1.inside_bbox(geo.bend, c["bbox"])
    metryki = v1.rank_value(clusters, (c, (skala, rel)))
    if n_dashed is None:
        n_dashed = len(v1.inside_bbox(geo.dashed, c["bbox"]))
    return Kandydat(cluster=c, absorbed=absorbed, giecia=giecia, skala=skala,
                    rel_err=rel, kategoria=kategoria, technika=technika,
                    priorytet=priorytet, pewnosc=pewnosc, metryki=metryki,
                    niepewny=niepewny, tie=tie, etykieta_warstwy=etykieta_warstwy,
                    n_clusters=len(clusters), n_dashed=n_dashed)


class Geometria:
    """Kontekst geometrii rysunku wspolny dla wszystkich kategorii.

    - rozbija bloki INSERT, gdy modelspace to same INSERT-y (niemiecka blokowa;
      wiedza: krotkie-nazwy-bloki-zero - rozbic ZANIM cokolwiek),
    - partycjonuje encje raz (kontur/osie/kreskowane/giecia/adnotacje),
    - indeksuje warstwy pozycyjne 1NN i encje per warstwa,
    - cache'uje klastrowania (V1 liczyl je wielokrotnie per pozycja).
    """

    def __init__(self, doc):
        msp = doc.modelspace()
        n_geom = sum(1 for e in msp if e.dxftype() in v1.GEOM_TYPES)
        n_ins = sum(1 for e in msp if e.dxftype() == "INSERT")
        self.rozbite_bloki = False
        if n_geom == 0 and n_ins > 0:
            nowy = ezdxf.new(dxfversion="AC1021")
            nmsp = nowy.modelspace()
            for ins in list(msp.query("INSERT")):
                try:
                    for ve in ins.virtual_entities():
                        try:
                            nmsp.add_entity(ve.copy())
                        except Exception:
                            continue
                except Exception:
                    continue
            doc, msp = nowy, nmsp
            self.rozbite_bloki = True
        self.doc = doc
        self.msp = msp
        self.wszystkie = list(msp)
        (self.geom, self.axis, self.dashed,
         self.bend, self.annot) = v1.partition(self.wszystkie)

        # warstwy pozycyjne: 1NN = pozycja NN (konwencja Lantek-style)
        self.pos_layers = {}
        for ln in sorted({e.dxf.layer for e in self.wszystkie}):
            if ln.isdigit() and len(ln) == 3 and ln.startswith("1"):
                self.pos_layers[int(ln) - 100] = ln

        self.na_warstwie = defaultdict(list)
        for e in self.wszystkie:
            self.na_warstwie[e.dxf.layer].append(e)

        self._cache = {}

    def klastry(self, klucz, encje, gap):
        """Klastrowanie z cache po (klucz, gap) - jeden przebieg na rysunek."""
        k = (klucz, gap)
        if k not in self._cache:
            self._cache[k] = v1.cluster_entities(encje, gap=gap)
        return self._cache[k]
