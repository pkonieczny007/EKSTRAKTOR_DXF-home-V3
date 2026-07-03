# -*- coding: utf-8 -*-
"""
Kategoria 1: PO STRUKTURZE RYSUNKU - jak klient zakodowal pozycje w pliku?

Techniki (opakowuja funkcje silnika V1, nie kopiuja ich):
  A. warstwa pozycyjna 1NN = pozycja NN (Lantek-style) - klastrowanie encji
     warstwy, dopasowanie do wymiarow z wykazu; gdy nic nie pasuje, kandydat
     AWARYJNY jak w V1 (najwiekszy klaster, skala z dluzszego boku, NIEPEWNY),
  B. per KOLOR (rysunki 1-warstwowe, np. SBM: kontur=2 zolty, wymiary=3,
     giecie=6 magenta) - klaster samego koloru konturu daje domkniety obrys;
     przy zapisie wchlaniamy tylko OTWORY (inaczej wrocilyby linie wymiarowe),
  C. bloki INSERT (niemiecka blokowa) - rozbicie robi Geometria PRZED
     kategoriami (virtual_entities), tu nic dodatkowego.
"""
from collections import defaultdict

from v2 import wspolne
from v2.wspolne import v1


def znajdz(geo, wiersz, profil=None):
    """Kandydaci ze struktury rysunku dla jednej pozycji wykazu."""
    dims = wiersz.get("dims")
    if not dims:
        return []
    out = []

    # --- technika A: warstwa pozycyjna 1NN ---
    layer = geo.pos_layers.get(wiersz["posn"])
    if layer:
        g, _a, d, _b, _an = v1.partition(geo.na_warstwie[layer])
        if g:
            clusters = geo.klastry(f"warstwa:{layer}", g + d, v1.CLUSTER_GAP)
            posort = sorted(clusters, key=lambda c: c["w"] * c["h"], reverse=True)
            trafiony = False
            for c in posort:
                m = v1.match_scale(c, dims[0], dims[1])
                if m:
                    out.append(wspolne.zbuduj_kandydata(
                        clusters, c, m, geo, kategoria="struktura",
                        technika=f"warstwa-{layer}", priorytet=1, pewnosc=0.85,
                        absorpcja="klastry", etykieta_warstwy=layer,
                        n_dashed=len(d), tie=0))
                    trafiony = True
            if not trafiony and posort:
                # awaryjnie jak V1: najwiekszy klaster warstwy, skala z dluzszego
                # boku - NIE zgadujemy, kandydat jawnie NIEPEWNY (do czlowieka)
                c = posort[0]
                cw = max(c["w"], c["h"])
                skala = dims[0] / cw if cw > 0 else 1.0
                out.append(wspolne.zbuduj_kandydata(
                    clusters, c, (skala, 999.0), geo, kategoria="struktura",
                    technika=f"warstwa-{layer}-awaryjnie", priorytet=4,
                    pewnosc=0.2, absorpcja="klastry", etykieta_warstwy=layer,
                    n_dashed=len(d), niepewny=True))

    # --- technika B: separacja po kolorze (rysunki 1-warstwowe) ---
    by_color = defaultdict(list)
    for e in geo.geom:
        by_color[e.dxf.color].append(e)
    if len(by_color) > 1:
        for col, ents in sorted(by_color.items()):
            if len(ents) < 3:
                continue
            for gap in v1.FALLBACK_GAPS:
                clusters = geo.klastry(f"kolor:{col}", ents, gap)
                for c in clusters:
                    m = v1.match_scale(c, dims[0], dims[1])
                    if m:
                        out.append(wspolne.zbuduj_kandydata(
                            clusters, c, m, geo, kategoria="struktura",
                            technika=f"po-kolorze-{col} gap={gap:g}",
                            priorytet=2, pewnosc=0.6, absorpcja="otwory",
                            etykieta_warstwy=f"(bez warstw, col{col}, gap={gap:g})",
                            tie=2))
    return out
