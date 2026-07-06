# -*- coding: utf-8 -*-
"""PRZEGLAD CZLOWIEKA (Etap 4) - galeria kafelkow V3 + zbieranie werdyktow.

Galeria = wynik OBOK zrodla (zoom + ramka skad-wycieto) OBOK nakladki wynik-na-
zrodlo (jesli sprawdzanie AI uruchomione). Semafor V3 = FINALNY: semafor_ai ze
sprawdzania (juz obnizony, zasada 5) albo semafor oceny wariantow. Czlowiek
porownuje OBRAZKI, nie otwiera CAD (zasada 3). Kolejnosc: 🔴 -> 🟡 -> 🟢 (najpierw
decyzje). 🔴/🟡 = przeglad OBOWIAZKOWY; 🟢 = PROBKA (co N-ty, zasada: odsetek maleje
ze wzrostem zaufania) - reszta zielonych zliczona, nie renderowana (czas przegladu).

Zrodla (wszystkie opcjonalne poza ekstrakcja): reuzywa raport.scal (semafor+plik+
wymiar) + raport._index_raporty (box zrodla) + sprawdzanie_ai.csv (nakladka+obnizenie)
+ galeria V2 (render czarne tlo). Zaden krok nie dubluje logiki - tylko ja spina.

WERDYKT: galeria zapisuje worklist <zeinr>_werdykty_do_wypelnienia.csv (posn, semafor,
sugestia, PUSTE werdykt/kategoria/uwagi). Czlowiek wpisuje OK/BLAD, potem:
  python sprawdzanie\\czlowiek\\przeglad.py --werdykty <csv>
importuje je do nauka/etykiety/ (werdykty.py). BLAD -> przypomnienie golden PRZED
naprawa (zasada 11). Galeria NIE zgaduje werdyktu - decyduja oczy (zasada 6).

Uzycie:
  python sprawdzanie\\czlowiek\\przeglad.py <folder_wynikow> [--rysunki F] [--probka N] [--out H]
  python sprawdzanie\\czlowiek\\przeglad.py --werdykty <wypelniony.csv> [--kto czlowiek|ai]

Po zmianie tutaj: python testy\\test_przeglad.py (PASS).
"""
import csv
import html
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "produkcja"))
sys.path.insert(0, str(REPO / "produkcja" / "silniki" / "v2"))
sys.path.insert(0, str(HERE))
import raport  # noqa: E402
import werdykty  # noqa: E402

_LUSTRO_RE = re.compile(r"LUSTRO\s+z\s+poz\.?\s*(\d+)", re.IGNORECASE)
_SEM_RZAD = {"czerwony": 0, "zolty": 1, "zielony": 2}
_SEM_KOLOR = {"czerwony": "#e03131", "zolty": "#f59f00", "zielony": "#2f9e44"}
POLA_WERDYKT = ["zeinr", "posn", "plik_dxf", "semafor", "sugestia",
                "werdykt", "kategoria", "uwagi"]


def _twin_posn(status):
    m = _LUSTRO_RE.search(status or "")
    return int(m.group(1)) if m else None


def _box(raporty, posn):
    """Box zrodla pozycji: wlasny albo (dla lustra) blizniaka; None gdy brak."""
    rap = raporty.get(posn)
    if rap is None:
        return None
    try:
        b = tuple(float(rap[k]) for k in ("src_x1", "src_y1", "src_x2", "src_y2"))
        return b
    except (KeyError, ValueError, TypeError):
        twin = _twin_posn(rap.get("status", ""))
        if twin is not None:
            return _box(raporty, twin)
        return None


def wczytaj_sprawdzanie_ai(folder):
    """{posn: wiersz} z <zeinr>_sprawdzanie_ai.csv (jesli sprawdzanie AI zrobione)."""
    out = {}
    for p in sorted(Path(folder).glob("*_sprawdzanie_ai.csv")):
        with open(p, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f, delimiter=";"):
                try:
                    out[int(r["posn"])] = r
                except (KeyError, ValueError):
                    continue
    return out


def _final_semafor(rec, ai_row):
    """Semafor FINALNY: obnizenie AI ma pierwszenstwo (zasada 5: tylko obniza)."""
    if ai_row and ai_row.get("semafor_ai"):
        return ai_row["semafor_ai"]
    return rec["semafor"]


def zbuduj_pozycje(folder):
    """Scala rekordy przegladu: raport.scal + sprawdzanie_ai + box zrodla.
    Zwraca (zeinr, lista rekordow z semafor_final, box, powody, nakladka_png)."""
    zeinr, rek = raport.scal(folder)
    ai = wczytaj_sprawdzanie_ai(folder)
    raporty = raport._index_raporty(folder)
    poz = []
    for r in rek:
        posn = r["posn"]
        ai_row = ai.get(posn)
        sem = _final_semafor(r, ai_row)
        if sem not in _SEM_RZAD:
            sem = "czerwony"      # nieznany semafor traktuj jako do-decyzji
        powody = []
        if r.get("uwagi"):
            powody.append(r["uwagi"])
        if r.get("uwagi_wymiar") and not str(r["uwagi_wymiar"]).startswith("ok"):
            powody.append(f"wymiar: {r['uwagi_wymiar']}")
        if ai_row and ai_row.get("powod_ai"):
            powody.append(f"AI: {ai_row['powod_ai']}")
        poz.append(dict(
            zeinr=zeinr, posn=posn, semafor=sem, plik_dxf=r["plik_dxf"],
            wymiar_dxf_x=r.get("wymiar_dxf_x", ""), wymiar_dxf_y=r.get("wymiar_dxf_y", ""),
            wykaz_x=r.get("wykaz_x", ""), wykaz_y=r.get("wykaz_y", ""),
            technologia=r.get("technologia", ""), uwagi_wymiar=r.get("uwagi_wymiar", ""),
            powod=" | ".join(powody) or "-", box=_box(raporty, posn),
            nakladka=(ai_row or {}).get("png", "")))
    return zeinr, poz


def zaznacz_probke(poz, prog_probka):
    """Oznacza ktore pozycje idą do przegladu: WSZYSTKIE 🔴/🟡 + co N-ty 🟢.
    Reszta zielonych = pomijana w renderze (liczona). prog_probka<=0 -> wszystkie."""
    licznik_z = 0
    for p in sorted(poz, key=lambda x: (_SEM_RZAD[x["semafor"]], x["posn"])):
        if p["semafor"] != "zielony":
            p["przeglad"] = True
            p["probka"] = False
        else:
            licznik_z += 1
            p["probka"] = prog_probka <= 0 or (licznik_z % max(prog_probka, 1) == 1)
            p["przeglad"] = p["probka"]
    return poz


# ----------------------------------------------------------------- RENDER (reuse V2)
def _domyslne_rendery():
    import galeria as g2  # V2: render czarne tlo (import leniwy - matplotlib)
    return g2.render_wynik, g2.render_zrodla_z_ramkami


def _renderuj(folder, folder_rysunkow, zeinr, poz_do_przegladu,
              render_wynik_fn, render_zrodla_fn):
    """Renderuje miniatury wyniku + zrodla (zoom+ramka) dla pozycji do przegladu.
    Nakladki juz istnieja w sprawdzanie_ai/ (sprawdz_folder). Zwraca katalog miniatur."""
    import galeria as g2
    miniatury = Path(folder) / "przeglad_miniatury"
    miniatury.mkdir(exist_ok=True)
    conv = g2.znajdz_rysunek(folder_rysunkow, zeinr)
    if conv is not None:
        pozycje = [(str(p["posn"]), p["box"]) for p in poz_do_przegladu]
        mapa = render_zrodla_fn(conv, pozycje, miniatury, zeinr)
        for p in poz_do_przegladu:
            zc = mapa.get(str(p["posn"]))
            if zc:
                p["png_zrodlo"], p["png_zrodlo_caly"] = zc
    else:
        print(f"  UWAGA: brak rysunku zrodlowego dla {zeinr} w {folder_rysunkow} (GLOSNO)")
    for p in poz_do_przegladu:
        plik = p["plik_dxf"]
        if plik and plik != "-" and (Path(folder) / plik).exists():
            png = Path(plik).with_suffix(".png").name
            render_wynik_fn(Path(folder) / plik, miniatury / png)
            p["png_wynik"] = png
    return miniatury


# ----------------------------------------------------------------- HTML
def _cmd_werdykt(plik):
    p = html.escape(plik or "-")
    return (f"python sprawdzanie\\czlowiek\\werdykty.py {p} OK   "
            f"| ... BLAD &lt;kategoria&gt;")


def _kafelek(p, mini_dir, ai_dir):
    sem = p["semafor"]
    posn, zeinr = p["posn"], p["zeinr"]
    wx, wy = p.get("wymiar_dxf_x"), p.get("wymiar_dxf_y")
    kx, ky = p.get("wykaz_x"), p.get("wykaz_y")
    znak = "&#10003;" if str(p.get("uwagi_wymiar", "")).startswith("ok") else "&#10007;"
    if wx not in ("", None):
        wymiar = f"<b>{wx} &times; {wy}</b> {znak}"
        if kx not in ("", None):
            wymiar += f" <small>(wykaz {kx} &times; {ky})</small>"
    else:
        wymiar = "&mdash;"

    def img(src, alt, opener=None):
        if not src:
            return f'<div class="brak">{alt}</div>'
        op = opener or src
        return (f'<a href="{op}" target="_blank">'
                f'<img src="{src}" alt="{alt}"></a>')

    lewy = img(f"{mini_dir}/{p['png_wynik']}" if p.get("png_wynik") else None,
               "BRAK PLIKU")
    prawy = img(f"{mini_dir}/{p['png_zrodlo']}" if p.get("png_zrodlo") else None,
                "BRAK RYSUNKU",
                f"{mini_dir}/{p.get('png_zrodlo_caly', '')}" if p.get("png_zrodlo_caly") else None)
    nak = img(f"{ai_dir}/{p['nakladka']}" if p.get("nakladka") else None,
              "brak nakladki<br><small>(uruchom sprawdz_folder)</small>")

    badge = ' <span class="probka">PROBKA</span>' if p.get("probka") else ""
    return f"""
  <div class="kafelek s-{sem}">
    <div class="naglowek"><b>{html.escape(zeinr)}</b> &middot; poz. {posn}
      <span class="etykieta e-{sem}">{sem.upper()}</span>{badge}</div>
    <div class="obrazki">{lewy}{prawy}{nak}</div>
    <div class="liczby">wymiar: {wymiar} &middot; tech: <b>{html.escape(p.get('technologia') or '-')}</b>
      &middot; plik: {html.escape(p['plik_dxf'])}</div>
    <div class="powod">{html.escape(p['powod'])}</div>
    <div class="werdykt">werdykt: <code>{_cmd_werdykt(p['plik_dxf'])}</code></div>
  </div>"""


_SZABLON = """<!DOCTYPE html>
<html lang="pl"><head><meta charset="UTF-8">
<title>Przeglad czlowieka - {tytul}</title>
<style>
 body{{margin:0;padding:22px 26px;background:#14171c;color:#dfe5ec;font:14px/1.45 "Segoe UI",system-ui,sans-serif}}
 h1{{font-size:20px;margin:0 0 4px}}
 .pasek{{color:#9aa4b1;margin:0 0 16px}} .pasek b{{padding:1px 9px;border-radius:12px;color:#fff}}
 .plansza{{display:grid;grid-template-columns:repeat(auto-fill,minmax(560px,1fr));gap:16px}}
 .kafelek{{border:3px solid;border-radius:12px;background:#1b2027;padding:10px}}
 {style_sem}
 .naglowek{{margin:0 0 8px}} .etykieta{{float:right;font-size:11px;border-radius:12px;padding:1px 9px;color:#fff}}
 .probka{{float:right;font-size:10px;border-radius:10px;padding:1px 7px;margin-right:6px;background:#3b5bdb;color:#fff}}
 .obrazki{{display:flex;gap:6px}} .obrazki a{{flex:1;min-width:0}}
 .obrazki img{{width:100%;height:165px;object-fit:contain;background:#000;border:1px solid #333;border-radius:6px;display:block}}
 .brak{{flex:1;height:165px;border:1px dashed #555;border-radius:6px;display:flex;align-items:center;justify-content:center;color:#778;text-align:center;font-size:12px}}
 .liczby{{margin-top:8px;font-size:12.5px;color:#b9c2cc}} .liczby b{{color:#8fd19e}}
 .powod{{margin-top:5px;font-size:12px;color:#ffcc66;font-style:italic;word-break:break-word}}
 .werdykt{{margin-top:6px;font-size:11px;color:#8aa}} code{{background:#0e1116;padding:1px 5px;border-radius:4px;color:#9ec}}
 a{{color:#6ea8fe}}
</style></head><body>
<h1>Przeglad czlowieka &mdash; {tytul}</h1>
<p class="pasek">wynik &middot; zrodlo (zoom, klik=caly arkusz) &middot; nakladka wynik-na-zrodlo &middot; kolejnosc: najpierw decyzje &middot;
 <b style="background:#e03131">{n_c} czerwone</b> <b style="background:#b07d00">{n_z} zolte</b>
 <b style="background:#2f9e44">{n_g} zielone</b> &middot; do przegladu: <b style="background:#444">{n_p}</b>
 (🟢 poza probka pominieto: {n_pomin})</p>
<p class="pasek">WERDYKT: wpisz OK/BLAD w <code>{werdykt_csv}</code>, potem
 <code>przeglad.py --werdykty {werdykt_csv}</code> (BLAD -&gt; golden PRZED naprawa, zasada 11)</p>
<div class="plansza">{kafelki}
</div></body></html>
"""


def generuj_przeglad(folder_wynikow, folder_rysunkow=None, prog_probka=10,
                     out_html=None, render_wynik_fn=None, render_zrodla_fn=None):
    """Buduje galerie przegladu + worklist werdyktow. Zwraca (html_path, csv_path, poz)."""
    folder = Path(folder_wynikow)
    if folder_rysunkow is None:
        folder_rysunkow = REPO / "testy" / "rysunki"
    if render_wynik_fn is None or render_zrodla_fn is None:
        rw, rz = _domyslne_rendery()
        render_wynik_fn = render_wynik_fn or rw
        render_zrodla_fn = render_zrodla_fn or rz

    zeinr, poz = zbuduj_pozycje(folder)
    if not poz:
        print(f"[PRZEGLAD] brak pozycji w {folder} (GLOSNO)")
        return None, None, []
    zaznacz_probke(poz, prog_probka)
    do_przegladu = [p for p in poz if p["przeglad"]]
    _renderuj(folder, folder_rysunkow, zeinr, do_przegladu,
              render_wynik_fn, render_zrodla_fn)

    # worklist werdyktow (tylko pozycje do przegladu)
    werdykt_csv = folder / f"{zeinr}_werdykty_do_wypelnienia.csv"
    with open(werdykt_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=POLA_WERDYKT, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for p in sorted(do_przegladu, key=lambda x: (_SEM_RZAD[x["semafor"]], x["posn"])):
            w.writerow(dict(zeinr=zeinr, posn=p["posn"], plik_dxf=p["plik_dxf"],
                            semafor=p["semafor"], sugestia=p["powod"][:120],
                            werdykt="", kategoria="", uwagi=""))

    licz = {s: sum(1 for p in poz if p["semafor"] == s) for s in _SEM_RZAD}
    n_pomin = sum(1 for p in poz if p["semafor"] == "zielony" and not p["przeglad"])
    style = "\n ".join(f".s-{s}{{border-color:{k}}} .e-{s}{{background:{k}}}"
                       for s, k in _SEM_KOLOR.items())
    do_przegladu.sort(key=lambda p: (_SEM_RZAD[p["semafor"]], p["posn"]))
    kafelki = "".join(_kafelek(p, "przeglad_miniatury", "sprawdzanie_ai")
                      for p in do_przegladu)
    out_html = Path(out_html) if out_html else folder / "przeglad.html"
    out_html.write_text(_SZABLON.format(
        tytul=html.escape(zeinr), style_sem=style,
        n_c=licz["czerwony"], n_z=licz["zolty"], n_g=licz["zielony"],
        n_p=len(do_przegladu), n_pomin=n_pomin, werdykt_csv=werdykt_csv.name,
        kafelki=kafelki), encoding="utf-8")
    print(f"[PRZEGLAD] {out_html}  ({len(do_przegladu)}/{len(poz)} do przegladu: "
          f"{licz['czerwony']}🔴 {licz['zolty']}🟡 {licz['zielony']}🟢, "
          f"{n_pomin} zielonych poza probka)")
    print(f"[PRZEGLAD] worklist werdyktow: {werdykt_csv.name} "
          f"(wpisz OK/BLAD -> --werdykty)")
    return out_html, werdykt_csv, poz


def wczytaj_werdykty_csv(csv_path, kto="czlowiek"):
    """Importuje wypelniony worklist do nauka/etykiety/ (werdykty.py). Liczy tylko
    wiersze z niepustym werdykt. BLAD -> werdykty.py przypomni o golden (zasada 11)."""
    n = 0
    bledy = 0
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            werdykt = (r.get("werdykt") or "").strip().upper()
            if werdykt not in ("OK", "BLAD"):
                continue
            plik = r.get("plik_dxf") or f"{r.get('zeinr','')}_p{r.get('posn','')}.dxf"
            kategoria = (r.get("kategoria") or "").strip()
            uwagi = (r.get("uwagi") or "").strip()
            try:
                werdykty.dopisz_werdykt(plik, werdykt, kategoria, kto, uwagi)
                n += 1
                if werdykt == "BLAD":
                    bledy += 1
            except ValueError as e:
                print(f"[PRZEGLAD] pomijam {plik}: {e} (GLOSNO)")
    print(f"[PRZEGLAD] zaimportowano {n} werdyktow ({bledy} BLAD -> golden PRZED naprawa!)")
    return n


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    if argv[0] == "--werdykty":
        if len(argv) < 2:
            print("podaj plik csv: --werdykty <plik.csv> [--kto czlowiek|ai]")
            return 2
        kto = argv[argv.index("--kto") + 1] if "--kto" in argv else "czlowiek"
        wczytaj_werdykty_csv(argv[1], kto)
        return 0
    folder = argv[0]
    rest = argv[1:]
    rysunki = rest[rest.index("--rysunki") + 1] if "--rysunki" in rest else None
    probka = int(rest[rest.index("--probka") + 1]) if "--probka" in rest else 10
    out = rest[rest.index("--out") + 1] if "--out" in rest else None
    generuj_przeglad(folder, rysunki, probka, out)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
