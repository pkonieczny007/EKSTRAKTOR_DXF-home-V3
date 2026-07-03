# -*- coding: utf-8 -*-
"""
Testy modulow V2 (weryfikator, kategorie, orkiestrator) - NIE ruszaja V1.
Regresja V1 (testy/regresja.py) pozostaje osobnym, nadrzednym strażnikiem.

Uzycie:  python testy\\testy_v2.py
Wynik:   PASS/FAIL + podsumowanie. Kod wyjscia 0 = wszystko OK.
"""
import sys
import io
import math
from pathlib import Path
from types import SimpleNamespace

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "produkcja" / "silniki"))

import ezdxf
from v2 import weryfikator as W

FAILS = []
CHECKS = 0


def check(nazwa, warunek, info=""):
    global CHECKS
    CHECKS += 1
    if not warunek:
        FAILS.append(f"{nazwa}: {info}")


def _msp():
    return ezdxf.new().modelspace()


def prostokat(msp, w=100, h=50, otwarty=False):
    """Prostokat z 4 (lub 3 gdy otwarty) linii + zwraca liste encji."""
    pts = [(0, 0), (w, 0), (w, h), (0, h)]
    n = 3 if otwarty else 4
    return [msp.add_line(pts[i], pts[(i + 1) % 4]) for i in range(n)]


# --- bramka 1: wymiar ---
b = W.bramka1_wymiar(100.0, 50.0, 100.0, 50.0)
check("b1 zgodny", b.status == W.OK, b.powod)
b = W.bramka1_wymiar(120.0, 50.0, 100.0, 50.0)
check("b1 niezgodny -> CZERWONY", b.status == W.CZERWONY, b.status)
check("b1 niezgodny ma powod", "120" in b.powod, b.powod)
b = W.bramka1_wymiar(None, None, 100.0, 50.0)
check("b1 brak wyniku -> POMINIETA", b.status == W.POMINIETA, b.status)

# --- bramka 2: kontur domkniety ---
m = _msp()
enc = prostokat(m)
check("b2 zamkniety", W.bramka2_kontur(enc).status == W.OK)
m = _msp()
enc = prostokat(m, otwarty=True)
b = W.bramka2_kontur(enc)
check("b2 otwarty -> ZOLTY", b.status == W.ZOLTY, b.status)
check("b2 otwarty ma powod", "otwartych koncow" in b.powod, b.powod)

# --- bramka 3: filtr smieci ---
m = _msp()
enc = prostokat(m)
enc.append(m.add_circle((50, 25), 5))
check("b3 zdrowy kontur", W.bramka3_smieci(enc).status == W.OK)
m = _msp()
enc = [m.add_line((0, 0), (10, 0)), m.add_line((10, 0), (10, 10))]
b = W.bramka3_smieci(enc)
check("b3 <3 encje -> ZOLTY", b.status == W.ZOLTY, b.status)
# pierscien segmentowany: 60 krotkich, NIEpolaczonych odcinkow po okregu R=100
m = _msp()
enc = []
for i in range(60):
    a1 = math.radians(i * 6)
    a2 = math.radians(i * 6 + 1.2)
    enc.append(m.add_line((100 * math.cos(a1), 100 * math.sin(a1)),
                          (100 * math.cos(a2), 100 * math.sin(a2))))
b = W.bramka3_smieci(enc)
check("b3 pierscien -> ZOLTY", b.status == W.ZOLTY, b.status)
check("b3 pierscien ma powod", "segmentowanego" in b.powod, b.powod)
# sito: duzo krotkich linii, ale kazdy kwadracik DOMKNIETY -> NIE smiec
m = _msp()
enc = []
for kx in range(10):
    for ky in range(3):
        x0, y0 = kx * 30.0, ky * 30.0
        pts = [(x0, y0), (x0 + 8, y0), (x0 + 8, y0 + 8), (x0, y0 + 8)]
        enc += [m.add_line(pts[i], pts[(i + 1) % 4]) for i in range(4)]
check("b3 sito domkniete OK", W.bramka3_smieci(enc).status == W.OK)

# --- bramka 4: bilans otworow ---
check("b4 rowne OK", W.bramka4_otwory(3, 3).status == W.OK)
b = W.bramka4_otwory(1, 3)
check("b4 zgubione -> ZOLTY", b.status == W.ZOLTY and "3" in b.powod, b.powod)
check("b4 brak zrodla -> POMINIETA", W.bramka4_otwory(1, None).status == W.POMINIETA)

# --- bramka 5: izometria ---
m = _msp()
enc = []
for kat in (30, 150, 30, 150):
    x = 100 * math.cos(math.radians(kat))
    y = 100 * math.sin(math.radians(kat))
    enc.append(m.add_line((0, 0), (x, y)))
b = W.bramka5_izometria(enc)
check("b5 rzut 3D -> ZOLTY", b.status == W.ZOLTY, b.status)
check("b5 ma powod", "izometrycznego" in b.powod, b.powod)
m = _msp()
enc = prostokat(m)
check("b5 rzut plaski OK", W.bramka5_izometria(enc).status == W.OK)

# --- bramka 6: giecie ---
check("b6 zgodne OK", W.bramka6_giecie(2, 2).status == W.OK)
b = W.bramka6_giecie(0, 2)
check("b6 zgubione -> ZOLTY", b.status == W.ZOLTY and "koloru 6" in b.powod, b.powod)
check("b6 brak zrodla -> POMINIETA", W.bramka6_giecie(0, None).status == W.POMINIETA)

# --- bramka 7: rejestr widokow ---
zajete = [(0, 0, 100, 50)]
b = W.bramka7_rejestr((5, 5, 95, 45), zajete)
check("b7 zajety -> CZERWONY", b.status == W.CZERWONY, b.status)
check("b7 wolny OK", W.bramka7_rejestr((200, 0, 300, 50), zajete).status == W.OK)

# --- bramka 8: sanity 1:1 ---
check("b8 wysrodkowany OK", W.bramka8_sanity((-50, -25), (50, 25)).status == W.OK)
b = W.bramka8_sanity((0, 0), (100, 50))
check("b8 niewysrodkowany -> ZOLTY", b.status == W.ZOLTY, b.status)

# --- zolty bez powodu = blad programisty (zasada nadrzedna) ---
try:
    W.Bramka(9, "test", W.ZOLTY)
    check("Bramka ZOLTY bez powodu -> wyjatek", False, "brak wyjatku")
except ValueError:
    check("Bramka ZOLTY bez powodu -> wyjatek", True)

# --- liczenie linii giecia w zrodle (kolor 6, dlugie vs krzyz osi) ---
m = _msp()
giecie = m.add_line((0, 0), (0, 100))       # przez cala czesc
giecie.dxf.color = 6
krzyz = m.add_line((50, 50), (54, 50))      # krotki krzyz osi otworu
krzyz.dxf.color = 6
zwykla = m.add_line((0, 0), (200, 0))       # kontur, kolor domyslny
n = W.policz_linie_giecia_zrodla([giecie, krzyz, zwykla], min_dim=100)
check("policz_giecia: dluga tak, krzyz nie", n == 1, f"n={n}")

# --- weryfikuj_kandydata (przestrzen zrodlowa, skala 5:1) ---
m = _msp()
enc = prostokat(m, w=20, h=10)              # na papierze 20x10, skala 5 -> 100x50
kand = SimpleNamespace(encje=enc, giecia=[], bbox=(0, 0, 20, 10), skala=5.0,
                       rel_err=0.005)
q = W.weryfikuj_kandydata(kand, (100.0, 50.0))
check("kandydat zdrowy -> ZIELONY", q.semafor == "ZIELONY", q.opis())
awaryjny = SimpleNamespace(encje=enc, giecia=[], bbox=(0, 0, 20, 10), skala=5.0,
                           rel_err=999.0)   # awaryjny V1: brak zgodnosci proporcji
q = W.weryfikuj_kandydata(awaryjny, (200.0, 50.0))
check("kandydat awaryjny -> CZERWONY", q.semafor == "CZERWONY", q.opis())
q = W.weryfikuj_kandydata(kand, (100.0, 50.0), zrodlo={"n_otworow": 2, "n_giec": 0})
check("kandydat zgubione otwory -> ZOLTY", q.semafor == "ZOLTY", q.opis())
check("kandydat: powod jawny", "okregow" in q.opis(), q.opis())
# scisla walidacja PO zapisie podmienia zgrubna bramke 1
q = W.weryfikuj_kandydata(kand, (100.0, 50.0))
W.aktualizuj_bramke_wymiaru(q, 100.0, 50.0, (100.0, 50.0))
check("aktualizacja b1: zgodny ZIELONY", q.semafor == "ZIELONY", q.opis())
W.aktualizuj_bramke_wymiaru(q, 120.0, 50.0, (100.0, 50.0))
check("aktualizacja b1: niezgodny CZERWONY", q.semafor == "CZERWONY", q.opis())

# --- post-hoc na zlotym wzorcu operatora (p1 = 2232 x 484, 1 otwor + fasolki) ---
wzorzec = HERE / "wzorce" / "SL10478356_p1_REFERENCJA_OPERATORA.dxf"
q = W.weryfikuj_wynik_dxf(wzorzec, (2232.0, 484.0))
check("wzorzec operatora: nie CZERWONY", q.semafor != "CZERWONY", q.opis())
check("wzorzec operatora: wymiar OK",
      next(b for b in q.bramki if b.nr == 1).status == W.OK, q.opis())

print(f"\nSprawdzen: {CHECKS} | Bledow: {len(FAILS)}")
for f in FAILS:
    print("  FAIL:", f)
print("\n=== TESTY V2: " + ("PASS ===" if not FAILS else "FAIL ==="))
sys.exit(1 if FAILS else 0)
