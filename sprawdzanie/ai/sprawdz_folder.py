# -*- coding: utf-8 -*-
"""SPRAWDZANIE AI folderu wynikow (Etap 4) - procedura flag kompletnosci.

Dla KAZDEJ wyekstrahowanej pozycji generuje nakladke wynik-na-zrodlo (sprawdzanie/ai/
nakladka.py) i klasyfikuje flage kompletnosci. Zamyka petle: raport.scal (semafor +
plik + uwagi_wymiar) + raport._index_raporty (box + skala + status LUSTRO) -> nakladka
-> pokrycie_zrodla -> flaga -> (opcjonalnie) obnizenie statusu.

ZASADY (CLAUDE.md):
  - #5: AI moze status tylko OBNIZYC (zielony->zolty), nigdy podniesc. Tu: pokrycie_zrodla
    < progu (MOZLIWY BRAK CECHY) obniza zielony do zoltego z jawnym powodem.
  - #6: KAZDA flaga = ogledziny wzrokowe. Ten driver PRODUKUJE material (PNG + miary),
    decyzje podejmuja OCZY (AI/czlowiek). Nie zamyka flagi zielono automatem.
  - #7: nakladka to strategia #1 kompletnosci - najpewniejszy flager (~0 falszywych).

Flaga (do ogledzin 100%) gdy: semafor != zielony LUB pokrycie_zrodla < progu
LUB nakladka zglosila uwagi kompletnosci (POKRYCIE ZRODLA / WYNIK PUSTY).

Wyjscie: <folder>/sprawdzanie_ai/<zeinr>_p{N}_nakladka.png + <zeinr>_sprawdzanie_ai.csv
(posn, semafor_we, pokrycie, pokrycie_zrodla, flaga, semafor_ai, powod_ai, png).

WERDYKTY AI (opcjonalnie, --werdykty-ai): dla FLAGOWANYCH pozycji driver dopisuje do
nauka/etykiety/ werdykt "WATPLIWOSC" (zrodlo=ai) - to jest RECORD wątpliwosci AI, NIE
zamkniecie flagi (AI nie zgaduje "BLAD"/"OK" flagi - to robi czlowiek wzrokiem, zasada
6). Zasila destylacje i pomiar precyzji AI. Domyslnie WYLACZONE (driver idempotentny).

Uzycie:
  python sprawdzanie\\ai\\sprawdz_folder.py <folder_wynikow> <zrodlo_conv.dxf> [--werdykty-ai]

Po zmianie tutaj: python testy\\test_sprawdz_folder.py (PASS).
"""
import csv
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "produkcja"))
sys.path.insert(0, str(REPO / "sprawdzanie" / "czlowiek"))
sys.path.insert(0, str(HERE))
import raport  # noqa: E402
import werdykty  # noqa: E402
from nakladka import nakladka, PROG_POKRYCIE_ZRODLA  # noqa: E402

WERDYKT_AI_FLAGA = "WATPLIWOSC"   # AI RECORDuje wątpliwosc (nie zamyka flagi, zasada 6)

_LUSTRO_RE = re.compile(r"LUSTRO\s+z\s+poz\.?\s*(\d+)", re.IGNORECASE)


def _twin_posn(status):
    m = _LUSTRO_RE.search(status or "")
    return int(m.group(1)) if m else None


def _box_scale(rap_row):
    """(box, scala) z wiersza raportu silnika; (None, None) gdy brak (np. lustro)."""
    if not rap_row:
        return None, None
    try:
        box = tuple(float(rap_row[k]) for k in ("src_x1", "src_y1", "src_x2", "src_y2"))
    except (KeyError, ValueError, TypeError):
        return None, None
    try:
        scala = float(rap_row.get("scale")) if rap_row.get("scale") else None
    except (ValueError, TypeError):
        scala = None
    return box, scala


def _obniz(semafor):
    """AI moze tylko obnizyc (zasada 5): zielony->zolty; zolty/czerwony bez zmian."""
    return "zolty" if semafor == "zielony" else semafor


def _zapisz_werdykty_ai(zeinr, wiersze):
    """Dla flagowanych pozycji dopisuje WATPLIWOSC (zrodlo=ai) do nauka/etykiety.
    NIE zamyka flagi (zasada 6) - to RECORD watpliwosci AI. Zwraca liczbe zapisow."""
    n = 0
    for r in wiersze:
        if r["flaga"] != "TAK":
            continue
        plik = r["plik_dxf"] if r["plik_dxf"] not in ("", "-") else f"{zeinr}_p{r['posn']}.dxf"
        try:
            werdykty.dopisz_werdykt(plik, WERDYKT_AI_FLAGA, "", "ai",
                                    (r["powod_ai"] or "flaga kompletnosci")[:200])
            n += 1
        except Exception as e:  # zapis werdyktu nie moze wywrocic sprawdzania
            print(f"[SPRAWDZ-AI] nie zapisano werdyktu AI p{r['posn']} ({e}) (GLOSNO)")
    if n:
        print(f"[SPRAWDZ-AI] zapisano {n} werdyktow AI (WATPLIWOSC, zrodlo=ai) do etykiet "
              f"- czlowiek nadal OGLADA flagi (zasada 6)")
    return n


def sprawdz_folder(folder_wynikow, zrodlo_conv, out_dir=None,
                   prog=PROG_POKRYCIE_ZRODLA, nakladka_fn=nakladka, werdykty_ai=False):
    """Generuje nakladki + klasyfikuje flagi dla wszystkich pozycji folderu.
    Zwraca (zeinr, wiersze). nakladka_fn wstrzykiwana (test podaje stub).
    werdykty_ai=True: dopisuje WATPLIWOSC (zrodlo=ai) dla flag do nauka/etykiety."""
    folder = Path(folder_wynikow)
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    zeinr, rekordy = raport.scal(folder)
    if not rekordy:
        print(f"[SPRAWDZ-AI] brak ocen/raportow w {folder} (GLOSNO)")
        return zeinr, []
    raporty = raport._index_raporty(folder)

    out_dir = Path(out_dir) if out_dir else folder / "sprawdzanie_ai"
    out_dir.mkdir(parents=True, exist_ok=True)

    wiersze = []
    for r in rekordy:
        posn = r["posn"]
        semafor_we = r["semafor"]
        plik = r["plik_dxf"]
        rap = raporty.get(posn)
        status = (rap or {}).get("status", "")

        # box: wlasny (widok) albo blizniaka (lustro odbite z twina)
        box, scala = _box_scale(rap)
        twin = _twin_posn(status)
        is_pl = twin is not None or "LUSTRO" in (status or "").upper()
        if box is None and twin is not None:
            box, scala = _box_scale(raporty.get(twin))

        wynik_dxf = folder / plik if plik and plik != "-" else None
        rekord = dict(zeinr=zeinr, posn=posn, semafor_we=semafor_we, plik_dxf=plik,
                      pokrycie="", pokrycie_zrodla="", flaga="", semafor_ai=semafor_we,
                      powod_ai="", uwagi_wymiar=r.get("uwagi_wymiar", ""), png="")

        if wynik_dxf is None or not wynik_dxf.exists():
            rekord.update(flaga="TAK", semafor_ai=_obniz(semafor_we),
                          powod_ai="brak wyjsciowego DXF (czerwony) - czlowiek rysuje")
            wiersze.append(rekord)
            continue
        if box is None:
            rekord.update(flaga="TAK", semafor_ai=semafor_we,
                          powod_ai="brak boxa zrodla w raporcie - nakladka niemozliwa (GLOSNO)")
            print(f"[SPRAWDZ-AI] {zeinr} p{posn}: brak boxa zrodla - nakladka pominieta (GLOSNO)")
            wiersze.append(rekord)
            continue

        png = out_dir / f"{zeinr}_p{posn}_nakladka.png"
        try:
            res = nakladka_fn(str(wynik_dxf), str(zrodlo_conv), box, str(png),
                              scale=scala, lustro=is_pl)
        except Exception as e:  # nakladka nie moze wywrocic sprawdzania calego folderu
            rekord.update(flaga="TAK", semafor_ai=_obniz(semafor_we),
                          powod_ai=f"blad nakladki ({e}) - ogledziny reczne (GLOSNO)")
            print(f"[SPRAWDZ-AI] {zeinr} p{posn}: blad nakladki ({e}) - GLOSNO")
            wiersze.append(rekord)
            continue

        pokrycie = res.get("pokrycie", 0.0)
        pokrycie_zrodla = res.get("pokrycie_zrodla", 0.0)
        uw = res.get("uwagi", [])
        braki_bboxy = res.get("braki_bboxy") or []
        # skupisko braku flaguje takze przy pokryciu >=prog (mala cecha zgubiona,
        # ktora nie zbija % - zakreslenie jest czulsze niz sam prog pokrycia)
        brak_cechy = pokrycie_zrodla < prog or bool(braki_bboxy) or any(
            ("POKRYCIE ZRODLA" in u or "WYNIK PUSTY" in u or "MOZLIWY BRAK" in u) for u in uw)

        flaga = brak_cechy or semafor_we != "zielony"
        semafor_ai = semafor_we
        powody = []
        if brak_cechy:
            semafor_ai = _obniz(semafor_we)
            if braki_bboxy:
                powody.append(f"MOZLIWY BRAK CECHY: {len(braki_bboxy)} skupisk "
                              f"ZAKRESLONYCH (najw. dl={braki_bboxy[0]['dl_niepokryta']}, "
                              f"pokrycie_zrodla {pokrycie_zrodla:.1f}%) -> ogledziny (zasada 6)")
            else:
                powody.append(f"pokrycie_zrodla {pokrycie_zrodla:.1f}%<{prog:.0f}% "
                              "= MOZLIWY BRAK CECHY -> ogledziny (zasada 6)")
        if semafor_we != "zielony":
            powody.append(f"semafor wejsciowy {semafor_we} (ocena wariantow)")

        rekord.update(pokrycie=round(pokrycie, 1), pokrycie_zrodla=round(pokrycie_zrodla, 1),
                      flaga="TAK" if flaga else "nie", semafor_ai=semafor_ai,
                      powod_ai=" | ".join(powody), png=png.name if flaga else "")
        wiersze.append(rekord)

    wiersze.sort(key=lambda w: w["posn"])
    csv_path = folder / f"{zeinr}_sprawdzanie_ai.csv"
    pola = ["zeinr", "posn", "semafor_we", "pokrycie", "pokrycie_zrodla", "flaga",
            "semafor_ai", "powod_ai", "uwagi_wymiar", "png"]
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pola, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(wiersze)
    if werdykty_ai:
        _zapisz_werdykty_ai(zeinr, wiersze)
    return zeinr, wiersze


def drukuj(zeinr, wiersze, out_dir):
    flagi = [w for w in wiersze if w["flaga"] == "TAK"]
    obnizone = [w for w in wiersze if w["semafor_ai"] != w["semafor_we"]]
    print(f"\n=== SPRAWDZANIE AI {zeinr}: {len(wiersze)} pozycji, "
          f"{len(flagi)} flag do ogledzin ===")
    for w in flagi:
        print(f"  🔎 p{w['posn']:<3} {w['semafor_we']}->{w['semafor_ai']:8} "
              f"pokr_zrodla={w['pokrycie_zrodla']!s:6} | {w['powod_ai'][:70]}")
    if obnizone:
        print(f"\n  AI OBNIZYLO status (zasada 5): {len(obnizone)} pozycji "
              f"-> {', '.join('p'+str(w['posn']) for w in obnizone)}")
    print(f"\n  PNG flag: {out_dir}  (OGLEDZINY 100% flag - zasada 6, od najwiekszych roznic)")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    folder, zrodlo = argv[0], argv[1]
    if not Path(zrodlo).exists():
        print(f"[SPRAWDZ-AI] zrodlo nie istnieje: {zrodlo} (GLOSNO)")
        return 1
    out_dir = Path(folder) / "sprawdzanie_ai"
    zeinr, wiersze = sprawdz_folder(folder, zrodlo, out_dir=out_dir,
                                    werdykty_ai="--werdykty-ai" in argv)
    if not wiersze:
        return 1
    drukuj(zeinr, wiersze, out_dir)
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
