# -*- coding: utf-8 -*-
"""WIELOWARIANTOWOSC (Etap 3) - generowanie 2-3 wariantow pozycji i wybor zwyciezcy.

CLAUDE.md / tablica: "jak mozna zrobic na 3 sposoby - robimy 3 i oceniamy". Kazda
pozycja moze byc wygenerowana przez niezalezne silniki:
  W-A = klaster+ranking (extract_positions)  |  W-B = kategorie+weryfikator (v2)
  W-C = region+warstwa (region_warstwa - root-fix cech odseparowanych)
Wszystkie przez te same bramki; ocena.score_variants wybiera zwyciezce na laser
(bramki 1/2/5/10), zgodnosc >=2 metod = pewnosc, rozbieznosc = eskalacja (nigdy
cichy wybor). zrodlo_prawda (ile konturow MA byc) = sweep.kontury_regionu_zrodla -
trzecia niezalezna miara rozstrzygajaca rozbieznosc pomiarem ZRODLA, nie glosowaniem.

Zwyciezca -> nazwa produkcyjna; przegrane zostaja w warianty/ (material dla nauki).
ocena.csv = wariant x metryki x werdykt.

Uzycie:
  python produkcja\\warianty.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>
"""
import csv
import io
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf import bbox as _bb
from ezdxf.math import Matrix44

HERE = Path(__file__).resolve().parent
_LUSTRO_RE = re.compile(r"LUSTRO\s+z\s+poz\.?\s*(\d+)", re.IGNORECASE)

# mapowanie polskich znakow diakrytycznych -> ASCII (kody unicode, by zrodlo .py
# bylo bez ogonkow) - naglowki wykazu roboczego bywaja z ogonkami ('sposob giecia')
_PL_DIAC = {0x105: "a", 0x107: "c", 0x119: "e", 0x142: "l", 0x144: "n", 0x0f3: "o",
            0x15b: "s", 0x17a: "z", 0x17c: "z", 0x104: "A", 0x106: "C", 0x118: "E",
            0x141: "L", 0x143: "N", 0x0d3: "O", 0x15a: "S", 0x179: "Z", 0x17b: "Z"}


def _deacc(s):
    """Naglowek/tekst bez polskich ogonkow, do dopasowania niezaleznego od diakrytow."""
    return (str(s) if s is not None else "").translate(_PL_DIAC)


def _twin_posn(status):
    """Numer pozycji-bliZniaka ze statusu 'LUSTRO z poz. N' (None gdy nie lustro)."""
    m = _LUSTRO_RE.search(status or "")
    return int(m.group(1)) if m else None


def _odbij_lustro(src_file, dst_file):
    """Odbicie P/L: mirror X + wysrodkowanie 1:1 (0,0). Zwyciezca lustra = odbicie
    zwyciezcy blizniaka -> zachowuje jego KOMPLETNOSC (V-C/W-B), nie re-ekstrakcja
    ze skala ratunkowa. Zwraca interior (bramka 5) odbitego pliku."""
    doc = ezdxf.readfile(src_file)
    msp = doc.modelspace()
    for e in msp:
        try:
            e.transform(Matrix44.scale(-1, 1, 1))
        except Exception:
            pass
    ext = _bb.extents(msp)
    mv = Matrix44.translate(-(ext.extmin.x + ext.extmax.x) / 2.0,
                            -(ext.extmin.y + ext.extmax.y) / 2.0, 0)
    for e in msp:
        e.transform(mv)
    ext = _bb.extents(msp)
    msp.reset_extents((ext.extmin.x, ext.extmin.y, 0), (ext.extmax.x, ext.extmax.y, 0))
    Path(dst_file).parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(dst_file)
    interior, _ = count_interior_contours_shapely(list(msp))
    return interior
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "kontrola"))
sys.path.insert(0, str(HERE / "silniki"))
import ocena  # noqa: E402
import extract_positions as ep  # noqa: E402
import openpyxl  # noqa: E402
from bilans_konturow import count_interior_contours_shapely  # noqa: E402
from sweep import kontury_regionu_zrodla  # noqa: E402
from region_warstwa import extract_region_warstwa, save_result  # noqa: E402

W_A = HERE / "silniki" / "extract_positions.py"
W_B = HERE / "silniki" / "v2" / "orkiestrator.py"


def is_pl_z_raportu(rows, posn):
    """Pozycja jest P/L (lustro) gdy jej status wspomina LUSTRO albo inna pozycja
    jest 'LUSTRO z poz. {posn}' (jest jej blizniakiem). Wplywa na linie giecia."""
    s = str(posn)
    for r in rows:
        st = (r.get("status") or "").upper()
        if int(r["posn"]) == int(posn) and "LUSTRO" in st:
            return True
        if f"LUSTRO Z POZ. {s}" in st or f"LUSTRO Z POZ {s}" in st:
            return True
    return False


def _wykaz_dim(r):
    try:
        w, h = float(r["wykaz_w"]), float(r["wykaz_h"])
        return (w, h) if w > 0 and h > 0 else None
    except (KeyError, ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# LUSTRO poz-parzystej (PATCH 4): rozpoznanie pary P/L, by pozycja-lustro powstala
# jako ODBICIE zwyciezcy blizniaka (kompletnosc twina), a nie jako slaby wlasny
# widok (np. dymek z nr pozycji o pasujacym bbox). Dwie reguly:
#   T1 (najsilniejsza): wykaz roboczy MOWI lustro ('sposob giecia' ~ lustro /
#       DODATKOWA KOLUMNA = L / Nazwa konczy _L, blizniak _P).
#   T2 (fallback bez kolumn): 2 pozycje te same dims + DOKLADNIE 1 sensowny widok
#       (nakladajace sie src-bbox albo jedna bez wlasnego widoku) -> poz. wyzsza =
#       LUSTRO nizszej. Asymetryczne blizniaki (2 rozne widoki) NIE sa sklejane
#       (54_4867 SL10599245 p1/p2 = dwie rozne czesci o tym samym obrysie).
# NIGDY auto-zieleN - lustra sa zawsze 🟡 (pass 2), blizniaki bywaja asymetryczne.
# ---------------------------------------------------------------------------

def _same_dims(a, b, tol=1.0):
    return a and b and abs(a[0] - b[0]) <= tol and abs(a[1] - b[1]) <= tol


def _src_box(r):
    """Bbox zrodlowy widoku z raportu (src_x1..src_y2) lub None gdy brak/pusty."""
    try:
        b = tuple(float(r[k]) for k in ("src_x1", "src_y1", "src_x2", "src_y2"))
    except (KeyError, ValueError, TypeError):
        return None
    return b if (b[2] - b[0] > 0 and b[3] - b[1] > 0) else None


def _anchor_dims(r):
    return _wykaz_dim(r)


def _ten_sam_widok(r1, r2):
    """True gdy obie pozycje wskazuja TEN SAM widok (nakladajace sie src-bbox) albo
    ktoras nie ma wlasnego widoku -> DOKLADNIE 1 sensowny widok = para P/L. False gdy
    dwa rozne, rozlaczne widoki (asymetryczne blizniaki - NIE lustro)."""
    b1, b2 = _src_box(r1), _src_box(r2)
    if b1 is None or b2 is None:
        return True
    return ep.overlaps_claimed(b2, [b1], thresh=0.3) or \
        ep.overlaps_claimed(b1, [b2], thresh=0.3)


def wczytaj_pl_wykaz(wykaz_path, zeinr):
    """Czyta wykaz DEFENSYWNIE -> {posn: {'dims','pl','lustro'}} dla pozycji BLACHA.
    pl: 'L'/'P'/None; lustro: bool (sposob giecia ~ 'lustro' albo pl=='L' albo
    Nazwa konczy '_L'). Brak kolumn / blad -> {} (T1 nie odpali, zostaje T2)."""
    try:
        wb = openpyxl.load_workbook(wykaz_path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        header = next(it)
    except Exception:
        return {}
    idx = {}
    for i, h in enumerate(header):
        k = _deacc(h).strip().lower()
        if k and k not in idx:
            idx[k] = i

    def col(row, name):
        i = idx.get(name)
        return row[i] if (i is not None and i < len(row)) else None

    out = {}
    for r in it:
        z = col(r, "zeinr")
        if z is None or zeinr not in str(z):
            continue
        if _deacc(col(r, "zakupy")).strip().upper() != "BLACHA":
            continue
        try:
            posn = int(col(r, "posn"))
        except (TypeError, ValueError):
            continue
        if posn in out:
            continue
        d1, d2 = ep.parse_dim(col(r, "abmess_1")), ep.parse_dim(col(r, "abmes_2"))
        dims = (max(d1, d2), min(d1, d2)) if (d1 and d2) else None
        dod = _deacc(col(r, "dodatkowa kolumna")).strip().upper()
        nazwa = _deacc(col(r, "nazwa")).strip()
        sposob = _deacc(col(r, "sposob giecia")).strip().lower()
        pl = None
        if dod in ("L", "P"):
            pl = dod
        elif nazwa[-2:].upper() == "_L":
            pl = "L"
        elif nazwa[-2:].upper() == "_P":
            pl = "P"
        lustro = ("lustro" in sposob) or (pl == "L")
        out[posn] = {"dims": dims, "pl": pl, "lustro": lustro}
    return out


def wykryj_pary_pl(pl_info, anchor_rows):
    """Zwraca {posn_lustra: posn_blizniaka} wg T1 (wykaz) i T2 (analiza widokow).
    pl_info: z wczytaj_pl_wykaz (moze byc puste). anchor_rows: wiersze raportu W-A."""
    pary = {}
    a_by_posn = {}
    for r in anchor_rows:
        try:
            a_by_posn[int(r["posn"])] = r
        except (KeyError, ValueError, TypeError):
            continue

    # --- T1: wykaz roboczy mowi lustro ---
    for p, v in pl_info.items():
        if not v.get("lustro") or not v.get("dims"):
            continue
        kand = [q for q, w in pl_info.items()
                if q != p and not w.get("lustro") and _same_dims(w.get("dims"), v["dims"])]
        if not kand:
            continue
        kand.sort(key=lambda q: (pl_info[q].get("pl") != "P", q))
        pary[p] = kand[0]

    # --- T2: brak sygnalu w wykazie -> analiza widokow (dokladnie 1 wspolny widok) ---
    grup = defaultdict(list)
    for p, r in a_by_posn.items():
        d = _anchor_dims(r)
        if d:
            grup[(round(d[0], 1), round(d[1], 1))].append(p)
    for _d, poss in grup.items():
        if len(poss) != 2:
            continue
        lo, hi = sorted(poss)
        if hi in pary or lo in pary:
            continue
        if any(pl_info.get(x, {}).get("lustro") for x in (lo, hi)):
            continue
        if _ten_sam_widok(a_by_posn[lo], a_by_posn[hi]):
            pary[hi] = lo
    return pary


def warianty_pozycji(src_msp, box, scale, wykaz_dim, is_pl, wariantowe, out_wc=None):
    """Rdzen: generuje W-C dla widoku, liczy zrodlo_prawda (sweep), ocenia wszystkie
    warianty (score_variants). wariantowe: [{nazwa, dxf_path}] juz-wygenerowane (W-A/W-B).
    Zwraca (decyzja, info_wc). out_wc: sciezka zapisu W-C (None = tylko w pamieci)."""
    # UWAGA (znane ograniczenie): dla pozycji LUSTRO ze SKALA RATUNKOWA raport
    # bywa ma bogus scale (np. 543) -> W-C da wymiar x543 -> bramka 1 (wymiar) go
    # ZDYSKWALIFIKUJE (bezpiecznie, zly DXF nie wygra). Docelowo: lustro generowac
    # przez odbicie wyniku BLIZNIAKA (twin), nie re-ekstrakcje z bogus scale.
    doc_c, info_c = extract_region_warstwa(src_msp, box, scale, is_pl=is_pl)
    if out_wc is not None:
        save_result(doc_c, out_wc)
        wariant_c = {"nazwa": "W-C", "dxf_path": str(out_wc)}
    else:
        wariant_c = {"nazwa": "W-C", "msp": doc_c.modelspace(), "plik": "W-C(pamiec)"}

    try:
        zrodlo = kontury_regionu_zrodla(src_msp, box)
        zrodlo_prawda = zrodlo["zrodlo_prawda"]
        zrodlo_uwagi = zrodlo["diag"]["uwagi"]
    except Exception as e:
        zrodlo_prawda, zrodlo_uwagi = info_c["interior"], [f"sweep blad: {e}"]

    warianty = list(wariantowe) + [wariant_c]
    decyzja = ocena.score_variants(warianty, zrodlo_prawda, wykaz_dim)
    decyzja["zrodlo_uwagi"] = zrodlo_uwagi
    # niepewna prawda zrodla (zaden tryb czysty) -> semafor nie moze byc zielony
    if any("NIEPEWN" in u or "ZADEN tryb czysty" in u for u in zrodlo_uwagi) \
            and decyzja["semafor"] == "zielony":
        decyzja["semafor"] = "zolty"
        decyzja["powody"].insert(0, "zrodlo_prawda NIEPEWNA (sweep) -> obnizono do zoltego")
    return decyzja, info_c


def _run_silnik(skrypt, conv, wykaz, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, str(skrypt), str(conv), str(wykaz), str(out_dir)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode == 0


def _wczytaj_raport(out_dir, zeinr):
    rap = out_dir / f"{zeinr}_raport.csv"
    if not rap.exists():
        return []
    with open(rap, encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f, delimiter=";")]


def warianty_zlecenia(conv, wykaz, out, silniki=("W-A", "W-B", "W-C")):
    """Orkiestracja zlecenia: generuje warianty per pozycja, ocenia, kopiuje zwyciezce
    pod nazwe produkcyjna, zapisuje ocena.csv. Zwraca (wiersze, sciezka_ocena_csv)."""
    conv, wykaz, out = Path(conv), Path(wykaz), Path(out)
    zeinr = conv.stem.replace("_1_conv", "").replace("_conv", "").replace("_1", "")
    war_dir = out / "warianty"
    src_msp = ezdxf.readfile(conv).modelspace()

    # 1) uruchom silniki bazowe (W-A/W-B) do podfolderow wariantow
    dirs = {}
    if "W-A" in silniki:
        dirs["W-A"] = war_dir / "wA"
        _run_silnik(W_A, conv, wykaz, dirs["W-A"])
    if "W-B" in silniki:
        dirs["W-B"] = war_dir / "wB"
        _run_silnik(W_B, conv, wykaz, dirs["W-B"])

    raporty = {nz: _wczytaj_raport(d, zeinr) for nz, d in dirs.items()}
    # anchor: raport z bbox/wykazem (preferuj W-A, potem W-B)
    anchor = raporty.get("W-A") or raporty.get("W-B") or []
    if not anchor:
        print(f"[WARIANTY] brak raportu bazowego dla {zeinr} - nic do oceny (GLOSNO)")
        return [], None

    # PATCH 4: pary P/L (T1 z wykazu roboczego, T2 z analizy widokow). Lustro powstanie
    # jako ODBICIE zwyciezcy blizniaka (pass 2), zamiast slabego wlasnego widoku.
    pary_pl = wykryj_pary_pl(wczytaj_pl_wykaz(wykaz, zeinr), anchor)

    def _plik_wariantu(nz, posn):
        for r in raporty.get(nz, []):
            if int(r["posn"]) == int(posn) and r.get("file"):
                p = dirs[nz] / r["file"]
                if p.exists():
                    return p
        return None

    out.mkdir(parents=True, exist_ok=True)
    wiersze = []
    zwyciezcy = {}          # posn -> sciezka zwycieskiego pliku (do odbicia luster)
    lustra = []             # (posn, twin, r) - pozycje P/L do odbicia w passie 2

    # PASS 1: pozycje realne (widok+skala). Lustra ('LUSTRO z poz. N') -> pass 2,
    # bo ich raport ma pusta/ratunkowa skale (odbicie, nie ekstrakcja).
    for r in anchor:
        try:
            posn = int(r["posn"])
        except (KeyError, ValueError):
            continue
        twin = _twin_posn(r.get("status", ""))
        if twin is None:
            twin = pary_pl.get(posn)   # T1/T2: wykaz/analiza mowi lustro
        if twin is not None:
            lustra.append((posn, twin, r))
            continue
        try:
            box = tuple(float(r[k]) for k in ("src_x1", "src_y1", "src_x2", "src_y2"))
            scale = float(r["scale"])
        except (KeyError, ValueError):
            continue
        wykaz_dim = _wykaz_dim(r)
        is_pl = is_pl_z_raportu(anchor, posn)

        wariantowe = []
        for nz in ("W-A", "W-B"):
            p = _plik_wariantu(nz, posn)
            if p is not None:
                wariantowe.append({"nazwa": nz, "dxf_path": str(p)})

        out_wc = war_dir / "wC" / f"{zeinr}_p{posn}__wC.dxf"
        try:
            decyzja, info_c = warianty_pozycji(src_msp, box, scale, wykaz_dim, is_pl,
                                               wariantowe, out_wc=out_wc)
        except Exception as e:
            print(f"[WARIANTY] {zeinr} p{posn}: blad oceny ({e}) - pomijam (GLOSNO)")
            continue

        zw_plik = None
        if decyzja["zwyciezca"]:
            nz = decyzja["zwyciezca"]
            zrodlo_pliku = out_wc if nz == "W-C" else _plik_wariantu(nz, posn)
            if zrodlo_pliku and Path(zrodlo_pliku).exists():
                zw_plik = out / f"{zeinr}_p{posn}.dxf"
                shutil.copy(zrodlo_pliku, zw_plik)
                zwyciezcy[posn] = zw_plik

        wiersze.append(dict(
            zeinr=zeinr, posn=posn, zwyciezca=decyzja["zwyciezca"] or "-",
            semafor=decyzja["semafor"], pewnosc=decyzja["pewnosc"] or "-",
            zrodlo_prawda=decyzja["zrodlo_prawda"],
            warianty=";".join(p["nazwa"] for p in decyzja["ranking"]),
            interior=";".join(f"{p['nazwa']}={p['interior']}" for p in decyzja["ranking"]),
            plik_produkcyjny=zw_plik.name if zw_plik else "-",
            powod=" | ".join(decyzja["powody"][:3])))

    # PASS 2: lustra = ODBICIE zwyciezcy blizniaka (zachowuje kompletnosc twina).
    # Blizniaki bywaja asymetryczne (p1 z owalem, p2 bez) -> zawsze zolty do potwierdzenia.
    for posn, twin, r in sorted(lustra):
        tw_plik = zwyciezcy.get(twin)
        if tw_plik is None or not Path(tw_plik).exists():
            print(f"[WARIANTY] {zeinr} p{posn}: LUSTRO z poz.{twin}, ale brak zwyciezcy "
                  f"blizniaka - nie odbijam (GLOSNO)")
            wiersze.append(dict(
                zeinr=zeinr, posn=posn, zwyciezca="-", semafor="czerwony", pewnosc="-",
                zrodlo_prawda="-", warianty="lustro", interior="-", plik_produkcyjny="-",
                powod=f"LUSTRO z poz.{twin} bez zwyciezcy blizniaka -> czlowiek"))
            continue
        dst = out / f"{zeinr}_p{posn}.dxf"
        interior = _odbij_lustro(tw_plik, dst)
        zwyciezcy[posn] = dst
        wiersze.append(dict(
            zeinr=zeinr, posn=posn, zwyciezca=f"LUSTRO(p{twin})", semafor="zolty",
            pewnosc="do potwierdzenia", zrodlo_prawda="=p" + str(twin),
            warianty="odbicie", interior=f"interior={interior}",
            plik_produkcyjny=dst.name,
            powod=f"odbicie zwyciezcy p{twin}; blizniaki bywaja asymetryczne -> "
                  f"potwierdz symetrie (zasada: asymetria=zolty)"))

    wiersze.sort(key=lambda w: w["posn"])
    ocena_csv = out / f"{zeinr}_ocena.csv"
    pola = ["zeinr", "posn", "zwyciezca", "semafor", "pewnosc", "zrodlo_prawda",
            "warianty", "interior", "plik_produkcyjny", "powod"]
    with open(ocena_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pola, delimiter=";")
        w.writeheader()
        for row in wiersze:
            w.writerow(row)
    return wiersze, ocena_csv


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    wiersze, ocena_csv = warianty_zlecenia(argv[0], argv[1], argv[2])
    if not wiersze:
        print("[WARIANTY] brak pozycji do oceny")
        return 3
    sem = {"zielony": "🟢", "zolty": "🟡", "czerwony": "🔴"}
    print(f"\n=== WARIANTY: {len(wiersze)} pozycji -> {ocena_csv} ===\n")
    for r in wiersze:
        print(f"  {sem.get(r['semafor'], '?')} p{r['posn']:<3} zwyciezca={r['zwyciezca']:4} "
              f"({r['interior']}) prawda={r['zrodlo_prawda']} pewnosc={r['pewnosc']}")
    return 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
