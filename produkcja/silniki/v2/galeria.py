# -*- coding: utf-8 -*-
"""
Galeria kafelkow HTML per zlecenie (poziom 2 weryfikatora V2).

Kafelek pozycji = miniatura WYNIKU (czarne tlo) obok miniatury CALEGO rysunku
zrodlowego z czerwona ramka "skad wycieto" (bbox zrodlowy z raportu CSV,
kolumny src_x1..src_y2 - Krok 1) + liczby (wymiar vs wykaz, otwory, giecia).
Obwodka kafelka = semafor: zielony / zolty / czerwony (szary = poza wykazem).
Sortowanie: czerwone najpierw, potem zolte, zielone, szare - najpierw decyzje,
potem kiwanie glowa. Kazdy zolty kafelek pokazuje JAWNY powod (status z raportu).

Zasada: czlowiek porownuje OBRAZKI, nie otwiera CAD-a. PNG zawsze na czarnym
tle (na bialym jasne linie znikaja) - reuzycie renderu z _demo_porownanie.py.

Uzycie:
  python src\\v2\\galeria.py <folder_wynikow> [--rysunki <folder_rysunkow>] [--out <plik.html>]

<folder_wynikow> musi zawierac {zeinr}_raport.csv + pliki DXF z ekstrakcji.
<folder_rysunkow> to folder z rysunkami zrodlowymi {zeinr}_1_conv.dxf
(domyslnie: testy/rysunki).
"""
import sys
import io
import csv
import html
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

_ROOT = Path(__file__).resolve().parents[3]  # V3: produkcja/silniki/v2 -> korzen repo
sys.path.insert(0, str(_ROOT / "testy" / "pretesty"))
from _demo_porownanie import render_into   # render DXF na czarnym tle (reuse)

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# kolejnosc sortowania kafelkow: najpierw decyzje, potem kiwanie glowa
_SEMAFOR_RZAD = {"czerwony": 0, "zolty": 1, "zielony": 2, "szary": 3}
_SEMAFOR_KOLOR = {"czerwony": "#e03131", "zolty": "#f59f00",
                  "zielony": "#2f9e44", "szary": "#5a5a5a"}


def semafor_statusu(status):
    """Mapuje status z raportu CSV na kolor semafora.
    Zolty ZAWSZE niesie jawny powod - powodem jest sam status (flagi)."""
    s = (status or "").strip()
    if s.startswith("BRAK W WYKAZIE"):
        return "szary"      # pozycja spoza zakresu - informacyjnie, nie robimy jej
    if s.startswith("OK"):
        # flaga "sprawdz" (np. linie kreskowane - moze giecie?) => do czlowieka
        return "zolty" if "sprawdz" in s else "zielony"
    if "LUSTRO" in s or "NIEPEWNE" in s or "ZWERYFIKUJ" in s or "DO_SPRAWDZENIA" in s:
        return "zolty"
    return "czerwony"       # NIE ZNALEZIONO / BRAK GEOMETRII / WYMIAR NIEZGODNY


def _fl(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def wymiar_ok(out_w, out_h, wyk_w, wyk_h):
    """Walidacja wymiaru jak w silniku V1 (tolerancja max(1mm, 0.2%))."""
    if None in (out_w, out_h, wyk_w, wyk_h):
        return None
    ok_w = abs(out_w - wyk_w) <= max(1.0, wyk_w * 0.002)
    ok_h = abs(out_h - wyk_h) <= max(1.0, wyk_h * 0.002)
    return ok_w and ok_h


def wczytaj_raporty(folder):
    """Czyta wszystkie {zeinr}_raport.csv z folderu wynikow -> lista wierszy."""
    wiersze = []
    for csv_path in sorted(Path(folder).glob("*_raport.csv")):
        zeinr = csv_path.name[:-len("_raport.csv")]
        with open(csv_path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f, delimiter=";"):
                row["zeinr"] = zeinr
                wiersze.append(row)
    return wiersze


def znajdz_rysunek(folder_rysunkow, zeinr):
    """Szuka skonwertowanego rysunku zrodlowego dla zeinr."""
    folder = Path(folder_rysunkow)
    for wzor in (f"{zeinr}_1_conv.dxf", f"{zeinr}_conv.dxf", f"{zeinr}*_conv.dxf"):
        trafienia = sorted(folder.glob(wzor))
        if trafienia:
            return trafienia[0]
    return None


def render_wynik(dxf_path, out_png):
    """Miniatura wyniku ekstrakcji - czarne tlo (zasada nr 7)."""
    fig = plt.figure(figsize=(4.6, 3.6))
    ax = fig.add_axes([0, 0, 1, 1])
    render_into(ax, str(dxf_path))
    fig.savefig(out_png, dpi=100, facecolor="black")
    plt.close(fig)


def render_zrodla_z_ramkami(conv_path, pozycje, out_dir, zeinr):
    """Renderuje CALY rysunek zrodlowy RAZ, potem dla kazdej pozycji dokleja
    czerwona ramke bbox i zapisuje DWA PNG:
      - ZOOM na element (kafelek - caly arkusz byl za maly do porownania),
      - caly arkusz z ramka (kontekst skad wycieto - otwiera sie po kliku).
    pozycje: lista (posn, bbox|None). Zwraca {posn: (png_zoom, png_caly)}."""
    fig = plt.figure(figsize=(7.2, 5.0))
    ax = fig.add_axes([0, 0, 1, 1])
    render_into(ax, str(conv_path))
    # box zamiast datalim: przy zoomie limity osi maja byc respektowane
    # (datalim rozszerza okno i sypie ostrzezeniami)
    ax.set_aspect("equal", adjustable="box")
    pelny_x, pelny_y = ax.get_xlim(), ax.get_ylim()
    out = {}
    for posn, box in pozycje:
        patch = None
        png_zoom = png_caly = None
        if box:
            x1, y1, x2, y2 = box
            m = max(x2 - x1, y2 - y1) * 0.03 + 2.0   # margines, zeby ramka nie zlewala sie z konturem
            patch = ax.add_patch(Rectangle((x1 - m, y1 - m),
                                           (x2 - x1) + 2 * m, (y2 - y1) + 2 * m,
                                           fill=False, edgecolor="red",
                                           linewidth=1.6, zorder=1000))
            # ZOOM: okno = bbox + ~25% kontekstu dookola
            mz = max(x2 - x1, y2 - y1) * 0.25 + 5.0
            ax.set_xlim(x1 - mz, x2 + mz)
            ax.set_ylim(y1 - mz, y2 + mz)
            png_zoom = f"{zeinr}_p{posn}_zrodlo.png"
            fig.savefig(out_dir / png_zoom, dpi=100, facecolor="black")
            ax.set_xlim(*pelny_x)
            ax.set_ylim(*pelny_y)
        png_caly = f"{zeinr}_p{posn}_zrodlo_caly.png"
        fig.savefig(out_dir / png_caly, dpi=100, facecolor="black")
        if patch:
            patch.remove()
        out[posn] = (png_zoom or png_caly, png_caly)
    plt.close(fig)
    return out


def _kafelek_html(w, miniatury_dir):
    """HTML jednego kafelka pozycji."""
    zeinr, posn = w["zeinr"], w["posn"]
    sem = w["semafor"]
    status = html.escape(w.get("status") or "")
    out_w, out_h = _fl(w.get("out_w")), _fl(w.get("out_h"))
    wyk_w, wyk_h = _fl(w.get("wykaz_w")), _fl(w.get("wykaz_h"))
    wym_ok = wymiar_ok(out_w, out_h, wyk_w, wyk_h)

    if out_w is not None:
        znak = "&#10003;" if wym_ok else ("?" if wym_ok is None else "&#10007;")
        wymiar = f"<b>{out_w:g} &times; {out_h:g}</b> {znak}"
        if wyk_w is not None:
            wymiar += f" <small>(wykaz {wyk_w:g} &times; {wyk_h:g})</small>"
    elif wyk_w is not None:
        wymiar = f"wykaz {wyk_w:g} &times; {wyk_h:g}"
    else:
        wymiar = "&mdash;"

    img_wynik = w.get("png_wynik")
    img_zrodlo = w.get("png_zrodlo")          # ZOOM na element (do porownania)
    img_caly = w.get("png_zrodlo_caly")       # caly arkusz z ramka (kontekst)
    if img_wynik:
        lewy = (f'<a href="{miniatury_dir}/{img_wynik}" target="_blank">'
                f'<img src="{miniatury_dir}/{img_wynik}" alt="wynik"></a>')
    else:
        lewy = '<div class="brak">BRAK PLIKU<br><small>pozycja nie wycieta</small></div>'
    if img_zrodlo:
        # miniatura = zoom na widok; klik otwiera CALY arkusz z ramka
        prawy = (f'<a href="{miniatury_dir}/{img_caly or img_zrodlo}" target="_blank">'
                 f'<img src="{miniatury_dir}/{img_zrodlo}" alt="zrodlo (zoom)"></a>')
    else:
        prawy = '<div class="brak">BRAK RYSUNKU<br><small>zrodlowego</small></div>'

    plik = w.get("file") or ""
    link_dxf = f' &middot; <a href="{html.escape(plik)}">DXF</a>' if plik else ""
    skala = w.get("scale") or "-"
    return f"""
  <div class="kafelek s-{sem}">
    <div class="naglowek"><b>{html.escape(zeinr)}</b> &middot; poz. {html.escape(str(posn))}
      <span class="etykieta e-{sem}">{sem.upper()}</span></div>
    <div class="obrazki">{lewy}{prawy}</div>
    <div class="liczby">wymiar: {wymiar} &middot; otwory: <b>{w.get('n_holes') or 0}</b>
      &middot; giecia: <b>{w.get('n_bend') or 0}</b> &middot; skala {html.escape(str(skala))}{link_dxf}</div>
    <div class="powod">{status}</div>
  </div>"""


_SZABLON = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>Galeria kafelkow - {tytul}</title>
<style>
  body{{margin:0;padding:24px 28px;background:#14171c;color:#dfe5ec;
       font:14px/1.45 "Segoe UI",system-ui,sans-serif}}
  h1{{font-size:20px;margin:0 0 4px}}
  .pasek{{color:#9aa4b1;margin:0 0 18px}}
  .pasek b{{padding:1px 9px;border-radius:12px;color:#fff}}
  .plansza{{display:grid;grid-template-columns:repeat(auto-fill,minmax(480px,1fr));gap:16px}}
  .kafelek{{border:3px solid;border-radius:12px;background:#1b2027;padding:10px}}
  {style_semaforow}
  .naglowek{{margin:0 0 8px;font-size:14px}}
  .etykieta{{float:right;font-size:11px;border-radius:12px;padding:1px 9px;color:#fff}}
  .obrazki{{display:flex;gap:8px}}
  .obrazki a{{flex:1;min-width:0}}
  .obrazki img{{width:100%;height:170px;object-fit:contain;background:#000;
               border:1px solid #333;border-radius:6px;display:block}}
  .brak{{flex:1;height:170px;border:1px dashed #555;border-radius:6px;display:flex;
        flex-direction:column;align-items:center;justify-content:center;color:#778}}
  .liczby{{margin-top:8px;font-size:12.5px;color:#b9c2cc}}
  .liczby b{{color:#8fd19e}}
  .powod{{margin-top:5px;font-size:12px;color:#93a0ad;font-style:italic;
         white-space:normal;word-break:break-word}}
  a{{color:#6ea8fe}}
</style>
</head>
<body>
<h1>Galeria kafelkow &mdash; {tytul}</h1>
<p class="pasek">wynik obok ZOOMU zrodla (klik = caly arkusz z ramka skad-wycieto) &middot; kolejnosc: najpierw decyzje &middot;
  <b style="background:#e03131">{n_czerwone} czerwone</b>
  <b style="background:#b07d00">{n_zolte} zolte</b>
  <b style="background:#2f9e44">{n_zielone} zielone</b>
  <b style="background:#5a5a5a">{n_szare} poza wykazem</b></p>
<div class="plansza">{kafelki}
</div>
</body>
</html>
"""


def generuj_galerie(folder_wynikow, folder_rysunkow, out_html=None):
    """Buduje galerie kafelkow dla wszystkich raportow CSV w folderze wynikow.
    Zwraca sciezke do HTML albo None, gdy brak raportow."""
    folder_wynikow = Path(folder_wynikow)
    wiersze = wczytaj_raporty(folder_wynikow)
    if not wiersze:
        print(f"Brak *_raport.csv w {folder_wynikow} - galeria nie powstala")
        return None

    miniatury = folder_wynikow / "miniatury"
    miniatury.mkdir(exist_ok=True)

    # miniatury zrodel: jeden render rysunku per zeinr, ramka per pozycja
    for zeinr in sorted({w["zeinr"] for w in wiersze}):
        conv = znajdz_rysunek(folder_rysunkow, zeinr)
        moje = [w for w in wiersze if w["zeinr"] == zeinr]
        if conv is None:
            print(f"  UWAGA: brak rysunku zrodlowego dla {zeinr} w {folder_rysunkow}")
            continue
        pozycje = []
        for w in moje:
            box = tuple(_fl(w.get(k)) for k in ("src_x1", "src_y1", "src_x2", "src_y2"))
            pozycje.append((w["posn"], None if None in box else box))
        mapa = render_zrodla_z_ramkami(conv, pozycje, miniatury, zeinr)
        for w in moje:
            zoom_i_caly = mapa.get(w["posn"])
            if zoom_i_caly:
                w["png_zrodlo"], w["png_zrodlo_caly"] = zoom_i_caly

    # miniatury wynikow
    for w in wiersze:
        w["semafor"] = semafor_statusu(w.get("status"))
        plik = w.get("file")
        if plik and (folder_wynikow / plik).exists():
            png = Path(plik).with_suffix(".png").name
            render_wynik(folder_wynikow / plik, miniatury / png)
            w["png_wynik"] = png

    wiersze.sort(key=lambda w: (_SEMAFOR_RZAD[w["semafor"]], w["zeinr"],
                                int(w["posn"]) if str(w["posn"]).isdigit() else 0))
    liczniki = {s: sum(1 for w in wiersze if w["semafor"] == s) for s in _SEMAFOR_RZAD}

    style = "\n  ".join(
        f".s-{s}{{border-color:{k}}} .e-{s}{{background:{k}}}"
        for s, k in _SEMAFOR_KOLOR.items())
    kafelki = "".join(_kafelek_html(w, "miniatury") for w in wiersze)

    out_html = Path(out_html) if out_html else folder_wynikow / "galeria.html"
    out_html.write_text(_SZABLON.format(
        tytul=html.escape(folder_wynikow.name), style_semaforow=style,
        n_czerwone=liczniki["czerwony"], n_zolte=liczniki["zolty"],
        n_zielone=liczniki["zielony"], n_szare=liczniki["szary"],
        kafelki=kafelki), encoding="utf-8")
    print(f"Galeria: {out_html}  ({len(wiersze)} kafelkow: "
          f"{liczniki['czerwony']} czerwonych, {liczniki['zolty']} zoltych, "
          f"{liczniki['zielony']} zielonych, {liczniki['szary']} poza wykazem)")
    return out_html


def main():
    ap = argparse.ArgumentParser(description="Galeria kafelkow HTML per zlecenie (V2)")
    ap.add_argument("folder_wynikow", help="folder z DXF + *_raport.csv z ekstrakcji")
    ap.add_argument("--rysunki", default=str(_ROOT / "testy" / "rysunki"),
                    help="folder z rysunkami zrodlowymi {zeinr}_1_conv.dxf")
    ap.add_argument("--out", default=None, help="sciezka wynikowego HTML")
    args = ap.parse_args()
    generuj_galerie(args.folder_wynikow, args.rysunki, args.out)


if __name__ == "__main__":
    main()
