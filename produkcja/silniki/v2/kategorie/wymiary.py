# -*- coding: utf-8 -*-
"""
Kategoria 2: PO WYMIARACH Z WYKAZU - ktory widok pasuje do Abmess_1 x Abmes_2?

Klastrowanie CALEGO rysunku (bez patrzenia na strukture) malejacymi progami
gap 8 -> 4 -> 2 mm (widoki bywaja narysowane blisko siebie i przy 8 mm sie
sklejaja); kandydat = klaster, ktorego proporcje pasuja do wykazu przy tej
samej skali x i y (v1.match_scale). Techniki:
  A. bbox wprost 1:1  - skala ~1.0 (rysunek w skali rzeczywistej), pewniejszy,
  B. bbox ze skala    - dowolna wspolna skala (preferencja NICE_SCALES w rankingu).

Pomysly na kolejne sesje (kontekst/kategorie_szukania.html):
  - obwod zamiast boku (plaszcze zwiniete: dluzszy bok ~= pi * D),
  - rzut skrocony gieciem (bok pomniejszony o cos kata - wykryc, NIE zgadywac).
"""
from v2 import wspolne
from v2.wspolne import v1


def znajdz(geo, wiersz, profil=None):
    """Kandydaci dopasowani wymiarami do wiersza wykazu."""
    dims = wiersz.get("dims")
    if not dims:
        return []
    profil = profil or {}
    gapy = profil.get("gapy", list(v1.FALLBACK_GAPS))
    encje = geo.geom + geo.dashed
    out = []
    for gap in gapy:
        clusters = geo.klastry("all", encje, gap)
        for c in clusters:
            m = v1.match_scale(c, dims[0], dims[1])
            if not m:
                continue
            wprost = abs(m[0] - 1.0) < 0.02
            out.append(wspolne.zbuduj_kandydata(
                clusters, c, m, geo, kategoria="wymiary",
                technika=("bbox-1:1" if wprost else "bbox-ze-skala") + f" gap={gap:g}",
                priorytet=2, pewnosc=0.7 if wprost else 0.6,
                absorpcja="klastry",
                etykieta_warstwy=f"(bez warstw, all, gap={gap:g})", tie=1))
    return out
