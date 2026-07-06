# -*- coding: utf-8 -*-
"""
OCENA WARIANTOW - porownanie kilku wersji tej samej pozycji (bramka 10).

CLAUDE.md "Wielowariantowosc": kazda pozycja moze byc wygenerowana przez 2-3
niezalezne silniki (W-A/W-B/W-C); zgodnosc >=2 metod = wysoka pewnosc,
rozbieznosc = eskalacja do czlowieka (NIGDY cichy wybor).

DZIALA JUZ: sygnatura geometryczna DXF + porownanie pary/zbioru wariantow (CLI).
ETAP 3 (PLAN.md): wpiecie w orkiestrator (generowanie wariantow, wybor zwyciezcy,
scoring z bramkami, zapis ocena.csv, przegrane warianty -> material do nauki).

Uzycie:
  python produkcja\\ocena.py <plik_A.dxf> <plik_B.dxf> [plik_C.dxf ...]
  python produkcja\\ocena.py <folder_warianty>            # grupuje po {poz}__w?.dxf
"""
import re
import sys
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bbox

import yaml

HERE = Path(__file__).resolve().parent
CFG = HERE.parent / "config" / "warianty.yaml"
SUFFIX = re.compile(r"__w(\w+)$")   # {Zeinr}_p{N}__wA.dxf

sys.path.insert(0, str(HERE / "kontrola"))
from bilans_konturow import count_interior_contours_shapely  # noqa: E402

# R5 - priorytet przy PRAWDZIWYM remisie (uzasadnienie pomiarem: W-C odtwarza
# kompletnosc zrodla 3/3 wzorcow golden, W-A gubi cechy 3/3). Przy remisie
# sygnatury zgodne, wiec priorytet tylko ustala ktory PLIK kopiujemy.
PRIO_SILNIKA = {"W-C": 0, "W-B": 1, "W-A": 2}


def sygnatura_dxf(path):
    """Sygnatura geometryczna pliku: wymiary bbox + liczniki encji."""
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    typy = Counter(e.dxftype() for e in msp)
    ext = _bbox.extents(msp, fast=False)   # scisle (fast przeszacowuje SPLINE!)
    w = h = 0.0
    if ext.has_data:
        w = ext.size.x
        h = ext.size.y
    return {"plik": Path(path).name, "w": round(w, 2), "h": round(h, 2),
            "n_encji": sum(typy.values()), "n_circle": typy.get("CIRCLE", 0),
            "typy": dict(typy)}


def _tolerancja(cfg):
    z = (cfg or {}).get("zgodnosc", {})
    return float(z.get("tolerancja_wymiaru_mm", 1.0)), \
        float(z.get("tolerancja_wymiaru_proc", 0.2))


def porownaj(sig_a, sig_b, tol_mm=1.0, tol_proc=0.2):
    """Porownanie dwoch sygnatur -> (zgodne: bool, rozjazdy: [str])."""
    rozjazdy = []
    for os_ in ("w", "h"):
        a, b = sig_a[os_], sig_b[os_]
        tol = max(tol_mm, tol_proc / 100.0 * max(a, b))
        if abs(a - b) > tol:
            rozjazdy.append(f"wymiar {os_}: {a} vs {b} (tol {tol:.2f})")
    if sig_a["n_circle"] != sig_b["n_circle"]:
        rozjazdy.append(f"okregi: {sig_a['n_circle']} vs {sig_b['n_circle']}")
    # TODO etap 2: liczba konturow wewnetrznych (shapely.polygonize) zamiast n_encji
    if sig_a["n_encji"] != sig_b["n_encji"]:
        rozjazdy.append(f"encje: {sig_a['n_encji']} vs {sig_b['n_encji']} (info)")
    zgodne = not any(not r.endswith("(info)") for r in rozjazdy)
    return zgodne, rozjazdy


def ocen_zbior(pliki):
    """Porownuje kazdy wariant z kazdym; zwraca (sygnatury, pary, werdykt)."""
    cfg = yaml.safe_load(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
    tol_mm, tol_proc = _tolerancja(cfg)
    sygnatury = [sygnatura_dxf(p) for p in pliki]
    pary = []
    n_zgodnych = 0
    for i in range(len(sygnatury)):
        for j in range(i + 1, len(sygnatury)):
            zgodne, rozjazdy = porownaj(sygnatury[i], sygnatury[j], tol_mm, tol_proc)
            n_zgodnych += zgodne
            pary.append((sygnatury[i]["plik"], sygnatury[j]["plik"], zgodne, rozjazdy))
    werdykt = "ZGODNE" if pary and all(z for _, _, z, _ in pary) else \
        ("ROZBIEZNE -> eskalacja do czlowieka" if pary else "za malo wariantow")
    return sygnatury, pary, werdykt


# ===================== OCENA WARIANTOW (score_variants) =======================
# Etap 3: wybor zwyciezcy na laser laczac bramki 2 (kontur domkniety), 1 (wymiar
# vs wykaz), 5 (bilans konturow vs zrodlo_prawda ze sweepa), 10 (zgodnosc metod).
# Rdzen zaprojektowany i zwalidowany pomiarem (fable-advisor, 3 golden + 6 brzegow),
# zweryfikowany i wpiety przez orkiestratora. REGULY (kolejnosc=priorytet):
#   R1 dyskwalifikacja laserowa: otwarty kontur (brud>0) nie moze wygrac.
#   R2 dyskwalifikacja wymiarowa: wymiar bbox scisly vs wykaz, tol max(1mm,0.2%).
#   R3 kompletnosc: delta=zrodlo_prawda-interior; 0(pelny) > <0(nadmiar/smieci) > >0(brak).
#   R4 zgodnosc: zwyciezca potwierdzony >=1 KWALIFIKOWANYM wariantem = pewnosc wysoka;
#      brak = ROZBIEZNOSC -> eskalacja (zolty), NIGDY cichy wybor.
#   R5 remis: priorytet W-C > W-B > W-A (W-C odtwarza kompletnosc zrodla 3/3 golden).


def zmierz_wariant(w, sagitta=0.1, snap_tol=0.1):
    """Pomiar wariantu: interior/okregi (bramka 5), otwarte konce (bramka 2),
    wymiar bbox scisly (bramka 1). w: {nazwa, dxf_path|msp}."""
    if w.get("msp") is not None:
        ents = list(w["msp"])
        plik = w.get("plik", w["nazwa"])
    else:
        ents = list(ezdxf.readfile(str(w["dxf_path"])).modelspace())
        plik = Path(w["dxf_path"]).name
    interior, det = count_interior_contours_shapely(ents, sagitta=sagitta, snap_tol=snap_tol)
    brud = det["dangles"] + det["cuts"] + det["invalid"]
    ext = _bbox.extents(ents, fast=False)     # scisle: fast przeszacowuje SPLINE
    wx = round(ext.size.x, 2) if ext.has_data else 0.0
    wy = round(ext.size.y, 2) if ext.has_data else 0.0
    return dict(nazwa=w["nazwa"], plik=plik, interior=interior,
                circles_dedup=det["circles_dedup"], niedomkniete=brud > 0,
                brud=brud, outer=det["outer"], wymiar_x=wx, wymiar_y=wy, flags=det["flags"])


def _tol(want, tol_mm, tol_proc):
    return max(tol_mm, tol_proc / 100.0 * want)


def wymiar_zgodny(wx, wy, wykaz_dim, tol_mm, tol_proc):
    """(max,min) wyniku vs (max,min) wykazu. Zwraca (True/False/None, opis)."""
    if not wykaz_dim:
        return None, "brak wymiaru z wykazu"
    dmax, dmin = max(wykaz_dim), min(wykaz_dim)
    gmax, gmin = max(wx, wy), min(wx, wy)
    zle = []
    for got, want in ((gmax, dmax), (gmin, dmin)):
        if abs(got - want) > _tol(want, tol_mm, tol_proc):
            zle.append(f"{got:.2f} vs wykaz {want:.2f} (tol {_tol(want, tol_mm, tol_proc):.2f})")
    return (not zle), "; ".join(zle)


def sygnatury_zgodne(a, b, tol_mm, tol_proc):
    """Bramka 10: zgodnosc sygnatur (wymiar+interior+okregi+domknietosc)."""
    rozjazdy = []
    for k in ("wymiar_x", "wymiar_y"):
        t = _tol(max(a[k], b[k], 1.0), tol_mm, tol_proc)
        if abs(a[k] - b[k]) > t:
            rozjazdy.append(f"{k}: {a[k]} vs {b[k]} (tol {t:.2f})")
    if a["interior"] != b["interior"]:
        rozjazdy.append(f"interior: {a['interior']} vs {b['interior']}")
    if a["circles_dedup"] != b["circles_dedup"]:
        rozjazdy.append(f"okregi_dedup: {a['circles_dedup']} vs {b['circles_dedup']}")
    if a["niedomkniete"] != b["niedomkniete"]:
        rozjazdy.append(f"niedomkniete: {a['niedomkniete']} vs {b['niedomkniete']}")
    return (not rozjazdy), rozjazdy


def _score_display(p):
    """Liczba do raportu (czytelnosc). WYBOR robi _key, nie ta liczba."""
    if p["dyskw"]:
        return 0
    s = 100
    if p["delta"] > 0:
        s -= 40 * p["delta"]          # zgubiona cecha - najciezsza kara
    elif p["delta"] < 0:
        s -= 15 * (-p["delta"])       # nadmiar - flaga smieci
    return max(s, 0)


def _key(p):
    """Klucz rankingu kwalifikowanych (rosnaco=lepszy): klasa, |delta|, brud, priorytet."""
    return (p["klasa"], abs(p["delta"]), p["brud"], PRIO_SILNIKA.get(p["nazwa"], 9), p["nazwa"])


def score_variants(warianty, zrodlo_prawda, wykaz_dim=None, tol_mm=1.0, tol_proc=0.2):
    """Ocena wariantow -> dict(ranking, zwyciezca, zwyciezca_plik, pewnosc, semafor,
    powody, pary). warianty: [{nazwa:'W-A'|'W-B'|'W-C', dxf_path|msp}];
    zrodlo_prawda: kontury regionu zrodla (sweep); wykaz_dim: (w,h)|None."""
    powody, pary = [], []
    pomiary = [zmierz_wariant(w) for w in warianty]
    if not pomiary:
        return dict(zrodlo_prawda=zrodlo_prawda, wykaz_dim=wykaz_dim, ranking=[], pary=[],
                    zwyciezca=None, zwyciezca_plik=None, pewnosc=None, semafor="czerwony",
                    powody=["brak wariantow -> czlowiek"])
    for p in pomiary:
        p["delta"] = zrodlo_prawda - p["interior"]
        p["klasa"] = 0 if p["delta"] == 0 else (1 if p["delta"] < 0 else 2)
        p["wymiar_ok"], p["wymiar_opis"] = wymiar_zgodny(
            p["wymiar_x"], p["wymiar_y"], wykaz_dim, tol_mm, tol_proc)
        p["dyskw"] = []
        if p["niedomkniete"]:
            p["dyskw"].append(f"bramka 2: OTWARTY KONTUR (brud={p['brud']}) - NIE na laser")
        if p["wymiar_ok"] is False:
            p["dyskw"].append(f"bramka 1: wymiar niezgodny: {p['wymiar_opis']}")
        p["score"] = _score_display(p)

    for i in range(len(pomiary)):
        for j in range(i + 1, len(pomiary)):
            zg, roz = sygnatury_zgodne(pomiary[i], pomiary[j], tol_mm, tol_proc)
            pary.append((pomiary[i]["nazwa"], pomiary[j]["nazwa"], zg, roz))

    kwalifikowani = sorted([p for p in pomiary if not p["dyskw"]], key=_key)
    odpadli = [p for p in pomiary if p["dyskw"]]
    ranking = kwalifikowani + odpadli

    if not kwalifikowani:
        if all(p["niedomkniete"] for p in pomiary):
            powody.append("WSZYSTKIE warianty maja otwarty kontur (bramka 2) -> czerwony, czlowiek")
        else:
            powody.append("zaden wariant nie przeszedl dyskwalifikacji (bramki 1/2) -> czerwony")
        for p in odpadli:
            powody.append(f"  {p['nazwa']}: " + "; ".join(p["dyskw"]))
        return dict(zrodlo_prawda=zrodlo_prawda, wykaz_dim=wykaz_dim, ranking=ranking,
                    pary=pary, zwyciezca=None, zwyciezca_plik=None, pewnosc=None,
                    semafor="czerwony", powody=powody)

    zw = kwalifikowani[0]
    problemy = []
    if zw["delta"] > 0:
        problemy.append(f"zwyciezca NIEKOMPLETNY: interior={zw['interior']} < zrodlo_prawda="
                        f"{zrodlo_prawda} (delta={zw['delta']} zgubione cechy) -> ogledziny (zasada 6)")
    elif zw["delta"] < 0:
        problemy.append(f"interior={zw['interior']} > zrodlo_prawda={zrodlo_prawda} - "
                        f"podejrzane SMIECI/obca geometria -> ogledziny render")
    if zw["wymiar_ok"] is None:
        problemy.append("wymiar niepotwierdzony (brak wykazu) - zielony niemozliwy")

    potwierdzony = any(
        zg for a, b, zg, _ in pary
        if zw["nazwa"] in (a, b)
        and next(p for p in pomiary if p["nazwa"] == ({a, b} - {zw["nazwa"]}).pop()) in kwalifikowani)
    if len(pomiary) == 1:
        problemy.append("tylko 1 wariant - brak potwierdzenia niezalezna metoda (bramka 10)")
        pewnosc = "obnizona"
    elif potwierdzony:
        pewnosc = "wysoka"
    else:
        pewnosc = "obnizona"
        roz = "; ".join(f"{a} vs {b}: {', '.join(r)}" for a, b, zg, r in pary if not zg)
        problemy.append(f"ROZBIEZNOSC wariantow (bramka 10): zwyciezca niepotwierdzony -> "
                        f"eskalacja, NIGDY cichy wybor [{roz}]")

    for p in odpadli:
        powody.append(f"info: {p['nazwa']} zdyskwalifikowany: " + "; ".join(p["dyskw"]))

    semafor = "zielony" if not problemy else "zolty"
    powody = problemy + powody
    if semafor == "zielony":
        powody.insert(0, f"zgodne >=2 niezalezne metody + interior==zrodlo_prawda"
                         f"({zrodlo_prawda}) + kontur domkniety + wymiar OK")
    return dict(zrodlo_prawda=zrodlo_prawda, wykaz_dim=wykaz_dim, ranking=ranking, pary=pary,
                zwyciezca=zw["nazwa"], zwyciezca_plik=zw["plik"], pewnosc=pewnosc,
                semafor=semafor, powody=powody)


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    if len(argv) == 1 and Path(argv[0]).is_dir():
        folder = Path(argv[0])
        grupy = {}
        for p in sorted(folder.glob("*.dxf")):
            m = SUFFIX.search(p.stem)
            grupy.setdefault(SUFFIX.sub("", p.stem) if m else p.stem, []).append(p)
        pliki_grup = [(poz, pliki) for poz, pliki in grupy.items() if len(pliki) > 1]
        if not pliki_grup:
            print("brak grup wariantow ({poz}__w?.dxf) w folderze")
            return 1
    else:
        pliki_grup = [("(argumenty)", [Path(a) for a in argv])]

    kod = 0
    for poz, pliki in pliki_grup:
        syg, pary, werdykt = ocen_zbior(pliki)
        print(f"\n=== {poz}: {werdykt} ===")
        for s in syg:
            print(f"  {s['plik']:<40} {s['w']}x{s['h']}  encje={s['n_encji']} okregi={s['n_circle']}")
        for a, b, zgodne, rozjazdy in pary:
            if rozjazdy:
                print(f"  {a} vs {b}: {'OK' if zgodne else 'ROZJAZD'} - {'; '.join(rozjazdy)}")
        if "ROZBIEZNE" in werdykt:
            kod = 1
    return kod


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
