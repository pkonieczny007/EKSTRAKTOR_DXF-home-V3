# -*- coding: utf-8 -*-
"""
Orkiestrator V2: dobor kategorii szukania + porownanie kandydatow.

Orkiestrator NIE zna srodka kategorii - odpala wtyczki z config/kategorie.yaml
(wspolny interfejs: znajdz(geometria, wiersz, profil) -> [Kandydat]), kazdy
kandydat przechodzi przez WSPOLNY weryfikator (8 bramek QC - nic nie omija
lejka), wygrywa najlepszy wg (priorytet techniki, ranking V1). Zapis wyniku
1:1 wykonuje silnik V1 (save_view) - jedno zrodlo prawdy geometrii.

Zasady:
  - kandydat CZERWONY na bramkach twardych (wymiar/rejestr) NIE jest zapisywany
    jako OK; kandydaci "niepewni" laduja wylacznie jako NIEPEWNE/_DO_SPRAWDZENIA,
  - rejestr zajetych widokow: pozycja lustrzana nie ukradnie widoku blizniaka,
  - pozycje bez wlasnego widoku o wymiarach blizniaka OK -> LUSTRO (jak V1),
  - raport CSV zgodny z V1 + kolumny V2: kategoria, technika, pewnosc,
    qc_semafor, qc_powody (kazdy ZOLTY z jawnym powodem).

Uzycie (CLI zgodne z V1):
  python src\\v2\\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>
                                  [--config <kategorie.yaml>] [--galeria]
                                  [--rysunki <folder_rysunkow>]
"""
import sys
import io
import csv
import argparse
from pathlib import Path

import ezdxf

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
import extract_positions as v1              # noqa: E402
from v2.wspolne import Geometria            # noqa: E402
from v2.kategorie import zaladuj_kategorie  # noqa: E402
from v2 import weryfikator                  # noqa: E402
from v2 import decyzje                       # noqa: E402

# domyslna sciezka korpusu dla flagi --korpus bez wartosci (repo/korpus/...)
KORPUS_DOMYSLNY = Path(__file__).resolve().parents[3] / "nauka" / "korpus" / "decyzje.csv"

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

KEYS_CSV = ["posn", "layer", "scale", "out_w", "out_h", "wykaz_w", "wykaz_h",
            "n_holes", "n_bend", "n_absorbed", "n_geom", "n_axis", "n_dashed",
            "n_annot", "n_clusters", "src_x1", "src_y1", "src_x2", "src_y2",
            "status", "file", "kategoria", "technika", "pewnosc",
            "n_kandydatow", "qc_semafor", "qc_powody"]


def _szkielet_rep(posn, geo, dims):
    rep = {"posn": posn, "layer": "-", "status": "", "scale": None,
           "out_w": None, "out_h": None,
           "wykaz_w": dims[0] if dims else None,
           "wykaz_h": dims[1] if dims else None,
           "n_holes": 0, "n_bend": 0, "n_absorbed": 0, "n_clusters": 0,
           "n_geom": len(geo.geom), "n_axis": len(geo.axis),
           "n_dashed": len(geo.dashed), "n_annot": len(geo.annot),
           "file": "", "kategoria": "", "technika": "", "pewnosc": "",
           "n_kandydatow": 0, "qc_semafor": "", "qc_powody": ""}
    return rep


def _klucz_wyboru(k):
    """Porzadek porownania kandydatow miedzy kategoriami:
    najpierw priorytet techniki (warstwa > bez struktury > ratunkowy),
    potem tuple rankingu V1 (ladna skala, najmniej otwartych koncow,
    najwiecej geometrii, najmniejszy blad proporcji); przy REMISIE rankingu
    kolejnosc zrodel jak w V1 (caly rysunek przed per-kolor - per-kolor
    wchlania tylko okragle otwory, wiec przy remisie gubilby np. kwadratowe
    wyciecia sita)."""
    return (-k.priorytet, k.metryki, -k.tie)


def _qc_kandydata(k, dims, geo, zajete):
    """Wspolny lejek QC: kontekst zrodlowy (okregi i linie giecia w bbox)."""
    zrodlo = {}
    if dims:
        w_bbox = v1.inside_bbox(geo.wszystkie, k.bbox)
        zrodlo["n_otworow"] = weryfikator.policz_otwory(
            v1.inside_bbox(geo.geom, k.bbox))
        # min wymiar czesci NA PAPIERZE (przed skala) - do odrozniania
        # linii giecia od krzyza osi otworu
        min_dim_papier = min(k.bbox[2] - k.bbox[0], k.bbox[3] - k.bbox[1])
        zrodlo["n_giec"] = weryfikator.policz_linie_giecia_zrodla(
            w_bbox, min_dim_papier)
    return weryfikator.weryfikuj_kandydata(k, dims, zrodlo=zrodlo, zajete=zajete)


def _zapisz_kandydata(k, rep, dims, out_dir, zeinr, posn):
    """Zapis przez silnik V1 (save_view) + status zgodny z konwencja V1."""
    rep["scale"] = round(k.skala, 4)
    rep["layer"] = k.etykieta_warstwy or "-"
    rep["n_clusters"] = k.n_clusters
    rep["n_dashed"] = k.n_dashed
    warstwa_wyniku = k.etykieta_warstwy if k.priorytet == 1 else "0"
    rep = v1.save_view(k.cluster, k.absorbed, k.giecia, k.skala,
                       warstwa_wyniku, out_dir, zeinr, posn, rep, dims)
    # konwencja statusow V1: warstwa pozycyjna -> OK; inne techniki -> TRYB BEZ WARSTW
    if k.priorytet != 1 and rep["status"].startswith("OK"):
        rep["status"] = rep["status"].replace("OK", "OK (TRYB BEZ WARSTW)", 1)
    rep["kategoria"] = k.kategoria
    rep["technika"] = k.technika
    rep["pewnosc"] = round(k.pewnosc, 2)
    return rep


def przetworz_rysunek(src_path, xlsx_path, out_dir, config_path=None,
                      korpus_path=None):
    """Caly rysunek: wykaz -> kategorie -> weryfikator -> zapis + lustra + CSV.

    korpus_path (opcjonalny): gdy podany, zdarzenia uczace (pozycje niepewne,
    bramki QC, braki widoku, lustra do weryfikacji) dopisywane sa do korpusu
    samodoskonalenia. None (domyslnie) -> logowanie WYLACZONE, zeby regresja
    i benchmark nie zasmiecaly korpusu danymi testowymi."""
    src_path = Path(src_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    zeinr = src_path.stem.split("_")[0]

    wykaz = v1.load_wykaz(xlsx_path, zeinr)
    print(f"Wykaz {zeinr}: pozycje BLACHA -> {sorted(wykaz)}")

    geo = Geometria(ezdxf.readfile(src_path))
    if geo.rozbite_bloki:
        print("Rysunek blokowy (INSERT-only) - bloki rozbite przed szukaniem")
    print(f"Warstwy pozycyjne: {geo.pos_layers}")

    kategorie = zaladuj_kategorie(config_path)
    print("Kategorie: " + ", ".join(k.nazwa for k in kategorie))

    reports = []
    zajete = []    # rejestr bboxow widokow juz przypisanych (bramka 7)
    for posn in sorted(set(geo.pos_layers) | set(wykaz)):
        dims = wykaz.get(posn)
        rep = _szkielet_rep(posn, geo, dims)
        if dims is None:
            rep["layer"] = geo.pos_layers.get(posn, "-")
            rep["status"] = "BRAK W WYKAZIE"
            reports.append(rep)
            continue

        wiersz = {"posn": posn, "dims": dims, "zeinr": zeinr}
        kandydaci = []
        for kat in kategorie:
            kandydaci.extend(kat.modul.znajdz(geo, wiersz, kat.ustawienia))
        rep["n_kandydatow"] = len(kandydaci)

        # bramka 7 na wejsciu: widok zajety przez inna pozycje odpada od razu
        kandydaci = [k for k in kandydaci
                     if not v1.overlaps_claimed(k.bbox, zajete)]

        # wspolny lejek QC - zaden kandydat nie omija weryfikatora
        for k in kandydaci:
            k.qc = _qc_kandydata(k, dims, geo, None)

        pewni = [k for k in kandydaci
                 if not k.niepewny and k.qc.semafor != "CZERWONY"]
        niepewni = [k for k in kandydaci if k.niepewny]

        # kandydaci po kolei wg rankingu: zgrubny bbox przeszacowuje krzywe,
        # wiec scisla walidacja mm jest mozliwa dopiero PO zapisie - nieudana
        # proba NIE moze zostawic pliku (bez sufiksu poszedlby do nestingu!)
        n_kandydatow = len(kandydaci)
        best = None
        for k in sorted(pewni, key=_klucz_wyboru, reverse=True):
            proba = _zapisz_kandydata(k, _szkielet_rep(posn, geo, dims),
                                      dims, out_dir, zeinr, posn)
            if proba["status"].startswith("OK"):
                best, rep = k, proba
                zajete.append(k.bbox)
                break
            if proba.get("file"):
                (out_dir / proba["file"]).unlink(missing_ok=True)
        if best is None and niepewni:
            best = max(niepewni, key=_klucz_wyboru)
            rep = _szkielet_rep(posn, geo, dims)
            rep["status"] = ("NIEPEWNE (brak zgodnosci proporcji)"
                             if best.priorytet == 4
                             else "NIEPEWNE (kandydat ratunkowy - luzna tolerancja)")
            rep = _zapisz_kandydata(best, rep, dims, out_dir, zeinr, posn)
        if best is None:
            rep["status"] = "NIE ZNALEZIONO WIDOKU (zadna kategoria)"
        rep["n_kandydatow"] = n_kandydatow
        if best is not None and rep.get("file"):
            # scisla walidacja wymiaru z realnych extents zapisanego pliku
            weryfikator.aktualizuj_bramke_wymiaru(
                best.qc, rep.get("out_w"), rep.get("out_h"), dims)
            rep["qc_semafor"] = best.qc.semafor
            rep["qc_powody"] = best.qc.opis()
        reports.append(rep)

    # POZYCJE-LUSTRA jak w V1: pozycja bez poprawnego widoku o wymiarach
    # blizniaka OK -> odbicie (silnik V1 robi lustro i wysrodkowanie)
    ok_by_dims = {}
    for r in reports:
        if r.get("status", "").startswith("OK") and r.get("wykaz_w"):
            ok_by_dims.setdefault((r["wykaz_w"], r["wykaz_h"]), r["posn"])
    for r in reports:
        if r.get("status", "").startswith("OK") or not r.get("wykaz_w"):
            continue
        twin = ok_by_dims.get((r["wykaz_w"], r["wykaz_h"]))
        if twin and twin != r["posn"]:
            fname = v1.make_mirror(out_dir, zeinr, twin, r["posn"])
            if fname:
                old = r.get("file")
                if old and old != fname:
                    (out_dir / old).unlink(missing_ok=True)
                    (out_dir / old).with_suffix(".png").unlink(missing_ok=True)
                r["status"] = f"LUSTRO z poz. {twin} - ZWERYFIKUJ ({r['status']})"
                r["file"] = fname
                twin_rep = next((t for t in reports if t["posn"] == twin), None)
                if twin_rep:
                    for kk in ("src_x1", "src_y1", "src_x2", "src_y2"):
                        r[kk] = twin_rep.get(kk)
                    r["kategoria"] = "lustro"
                    r["technika"] = f"odbicie p{twin}"

    # raport tekstowy + CSV
    print()
    print(f"{'poz':>3} {'kategoria':>10} {'pewnosc':>7} {'QC':>8} "
          f"{'DXF [mm]':>18} {'wykaz [mm]':>18}  status")
    for r in reports:
        dxf_dim = (f"{r.get('out_w', '-')} x {r.get('out_h', '-')}"
                   if r.get("out_w") else "-")
        wyk_dim = (f"{r.get('wykaz_w', '-')} x {r.get('wykaz_h', '-')}"
                   if r.get("wykaz_w") else "-")
        print(f"{r['posn']:>3} {str(r.get('kategoria') or '-'):>10} "
              f"{str(r.get('pewnosc') or '-'):>7} {str(r.get('qc_semafor') or '-'):>8} "
              f"{dxf_dim:>18} {wyk_dim:>18}  {r['status']}")

    csv_path = out_dir / f"{zeinr}_raport.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=KEYS_CSV, extrasaction="ignore",
                           delimiter=";")
        w.writeheader()
        w.writerows(reports)
    print(f"\nRaport: {csv_path}")

    # log zdarzen uczacych do korpusu (tylko gdy jawnie wlaczony flaga --korpus)
    if korpus_path:
        n_log = decyzje.zapisz_decyzje(reports, zeinr, korpus_path)
        print(f"Korpus: dopisano {n_log} zdarzen uczacych -> {korpus_path}")

    return reports


def main():
    ap = argparse.ArgumentParser(
        description="Orkiestrator V2 - kategorie szukania + weryfikator")
    ap.add_argument("rysunek", help="rysunek _conv.dxf")
    ap.add_argument("wykaz", help="wykaz materialowy .xlsx")
    ap.add_argument("folder_wynikow")
    ap.add_argument("--config", default=None, help="rejestr kategorii YAML")
    ap.add_argument("--korpus", nargs="?", const=str(KORPUS_DOMYSLNY),
                    default=None,
                    help="loguj zdarzenia uczace do korpusu samodoskonalenia "
                         "(--korpus -> korpus/decyzje.csv; --korpus <plik> -> "
                         "wlasna sciezka); bez flagi logowanie wylaczone")
    ap.add_argument("--galeria", action="store_true",
                    help="po przetworzeniu wygeneruj galerie kafelkow")
    ap.add_argument("--rysunki", default=None,
                    help="folder rysunkow zrodlowych dla galerii "
                         "(domyslnie folder rysunku)")
    args = ap.parse_args()

    przetworz_rysunek(args.rysunek, args.wykaz, args.folder_wynikow, args.config,
                      korpus_path=args.korpus)

    if args.galeria:
        from v2.galeria import generuj_galerie
        rysunki = args.rysunki or str(Path(args.rysunek).parent)
        generuj_galerie(args.folder_wynikow, rysunki)


if __name__ == "__main__":
    main()
