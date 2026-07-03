# EKSTRAKTOR_DXF — automatyczna ekstrakcja pozycji blaszanych z rysunków warsztatowych

> Cel: rysunek złożeniowy (DWG/DXF) + wykaz materiałowy (xlsx) → gotowe pliki DXF 1:1
> pojedynczych pozycji blaszanych, prosto do Lantek Expert (nesting + laser).
> Docelowo: **aplikacja samodoskonaląca się** — każda ręczna korekta operatora uczy system.

## Status (29.06.2026)

Działający prototyp CLI + zainstalowany skill **`/wyciagnij-dxf`** (SB + `~/.claude/skills`).
Wynik na rysunkach testowych: ~19/20 pozycji automatycznie, reszta półautomatycznie.
Przetestowane na kilku zleceniach realnych (49_3776, 56_5388, 59_6940) — różne konwencje
klientów (Lantek-style, SBM kolorowa, niemiecka blokowa). Test regresyjny: PASS.
Pełen plan rozwoju: `PLAN.md`. Geneza i pomysły: `docs/`. Skrót pipeline'u i przypadków:
`docs/SKILL_szkic_wyciagnij-dxf.md`.

## Szybki start

```bash
# 1. Konwersja DWG->DXF (pliki "rysunkowe" .dxf to czesto DWG w przebraniu!)
python src/convert_dwg.py <rysunek.dxf|dwg> <wyjscie_conv.dxf>

# 2. Ekstrakcja wszystkich pozycji + raport CSV
python src/extract_positions.py <rysunek_conv.dxf> <wykaz.xlsx> <folder_wynikow>

# 3. PO KAZDEJ zmianie w src/ — regresja (musi byc PASS zanim cokolwiek oddasz!)
python testy/regresja.py
```

## Struktura

```
EKSTRAKTOR_DXF/
├── CLAUDE.md            ← ten plik
├── PLAN.md              ← plan aplikacji + treningu (etapy 0-5)
├── requirements.txt
├── config/              ← (przyszłość) profile klientów, progi — YAML
├── src/
│   ├── extract_positions.py   ← serce: klastrowanie, ranking widoków, zapis 1:1
│   └── convert_dwg.py         ← DWG→DXF przez GstarCAD wsadowo
├── docs/
│   ├── SKILL_szkic_wyciagnij-dxf.md     ← pełny opis pipeline'u i przypadków
│   └── trening_na_starych_dxf.html      ← pomysły na korpus/trening
├── testy/
│   ├── regresja.py      ← test 21 sprawdzeń, kod wyjścia 0 = OK
│   ├── rysunki/         ← 3 rysunki testowe (DWG + skonwertowane _conv) + wykaz
│   └── wzorce/          ← referencja operatora (p1 ręcznie wycięta — złoty wzorzec)
├── korpus/              ← (przyszłość) złoty korpus do treningu
└── wyniki/              ← wyjścia robocze (nie commitować)
```

## Wiedza dziedzinowa — NIE UCZ SIĘ TEGO OD NOWA

### Pliki wejściowe
- Pliki `.dxf` od klienta bywają **DWG ze zmienionym rozszerzeniem** (nagłówek binarny
  `AC1021`). Wykrywać po nagłówku, nie po rozszerzeniu — robi to `convert_dwg.py`.
- Konwersja: GstarCAD wsadowo `gcad.exe plik.dwg /b skrypt.scr`
  (skrypt: `_FILEDIA 0` / `_SAVEAS _DXF 16 "out.dxf"` / `_QUIT _N`).
  **UNC nie działa** — kopiować do %TEMP%. `dwxconv.exe` nie przyjmuje argumentów CLI.
  GstarCAD bywa zajęty poprzednim plikiem ⇒ przy seriach dać **ponowienie** konwersji.
- **Rysunki blokowe (INSERT-only)**: cała geometria bywa w blokach (modelspace = same
  INSERT-y). Engine ignoruje INSERT → „NIE ZNALEZIONO". Trzeba **rozbić**:
  `for ins in msp.query('INSERT'): ins.virtual_entities()` do nowego modelspace.
- **Krótkie nazwy rysunków bez prefiksu `SL`**: nazwa pliku bywa z **zerem wiodącym**
  (wykaz `Zeinr=55648`, plik `055648.dxf`). `load_wykaz` filtruje `zeinr in str(Zeinr)`
  → `"055648"` NIE pasuje do `"55648"`. Mapować ręcznie (strip zera / po końcówce).
  Zob. [[krotkie-nazwy-bloki-zero]].

### Wykaz (xlsx/xlsm, pierwsza zakładka)
- Pierwsza zakładka (nazwa zwykle „Produktionsstückliste", ale klient bywa zmienia —
  zawsze brać **pierwszą** zakładkę).
- Kolumny: `Zeinr` (nr rysunku), `Posn` (pozycja), `ZAKUPY == "BLACHA"/"blacha"` (filtr,
  porównanie `.upper()`), `Abmess_1` × `Abmes_2` (wymiary docelowe).
- Wymiary bywają stringami w formacie niemieckim: `"      2.232,000"` (`parse_dim`).
- Lista bywa zdublowana (domówienie) — brać pierwszy wpis pozycji.
- **Wykaz roboczy** (`ROBOCZY_*`/`AI_ROBOCZY_*`, robi go skill [[wykaz-roboczy]]) ma
  dodatkowo: `NAZWA`/`Nazwa_skrócona` (nazwa robocza), `propozycja` (gdy niepuste — DXF
  już jest w bazie), `INDEX` (`P`/`L`), `folder`. **Robimy pozycje `ZAKUPY=blacha`
  bez `propozycji`.** `NAZWA` bywa FORMUŁĄ — zob. „Nazewnictwo wyniku" niżej.

### Konwencje rysunków (różni klienci = różne konwencje!)
| Konwencja | Separator pozycji | Przykład |
|---|---|---|
| Lantek-style | warstwa `1NN` = pozycja NN (101→1) | SL10478356, SL10583143 |
| łamana | kontur rozrzucony po warstwach | poz.4 SL10524825 |
| SBM 1-warstwowa | **KOLOR**: kontur=2 żółty, wymiary=3 zielony, gięcie=6 magenta | SL10582053 |
| niemiecka blokowa | cała geometria w blokach INSERT, linetype DE | 055648 (Abstützung) |

#### Linia gięcia — KLUCZOWE, różne konwencje
- Domyślnie: osie = `CENTER` (wycinamy), **linia gięcia = `DASHDOT`** (zostaje,
  warstwa `GIECIE` kolor 6 magenta). Obecność gięcia ⇒ widok jest ROZWINIĘCIEM.
- **ALE u części klientów gięcie jest narysowane jako `PHANTOM` albo `MITTE`, kolor 6
  (magenta)** — a silnik traktuje PHANTOM/MITTE jak oś i je USUWA (zob. [[giecie-phantom-kolor6]]).
  Najpewniejszy wyznacznik gięcia = **kolor 6 (magenta)**, niezależnie od linetype.
  Przy ręcznym dobieraniu brać LINE/ARC `color==6` w obrysie → warstwa GIECIE.
- **Krzyż osi otworu też bywa magenta+MITTE!** Odróżniać po długości: linia gięcia
  idzie przez całą część (L ≥ ~0,6 × krótszy bok), krzyż osi jest krótki.

#### Lustra (prawy/lewy = gespiegelt)
- Adnotacja `gespiegelt / mirrored` ⇒ pozycja lustrzana (generujemy odbicie bliźniaka).
- Para P/L (kolumna `INDEX` w wykazie roboczym: `P`=prawy, `L`=lewy) → poz. lewa =
  lustro prawej. **Linie gięcia MUSZĄ zostać i zostać odbite razem z konturem** — bez
  nich nie wiadomo gdzie/w którą stronę giąć, a to jedyne co różni P od L.

#### Niemiecka konwencja linetype (rysunki blokowe)
- `AUSGEZOGEN` = ciągła (kontur), `MITTE` = oś, `VERDECKT` = ukryta (zarys).
- Engine `AXIS_LINETYPES` nie zna `MITTE` → dołożyłby osie do konturu; pomijać ręcznie.

### Pułapki algorytmiczne (każda kosztowała debugging — szczegóły w docs/SKILL_szkic)
1. **GUBIENIE OTWORÓW**: otwór w środku dużej blachy bywa dalej od konturu niż próg
   klastrowania → po wyborze widoku głównego ZAWSZE wchłonąć klastry wewnątrz bbox.
   W trybie per-kolor wchłaniać tylko CIRCLE/ELLIPSE (inaczej wrócą linie wymiarowe).
2. **Wybór widoku spośród kilku pasujących skalą**: najmniej OTWARTYCH KOŃCÓW geometrii
   (widok w złożeniu ma krawędzie poprzerywane sąsiadami, okręgi pofragmentowane).
   Laser i tak wymaga zamkniętych konturów.
3. **Widoki sklejają się** przy dużym progu klastrowania → fallback próbuje 8→4→2 mm.
4. **Rejestr zajętych widoków**: pozycja lustrzana o identycznych wymiarach NIE może
   ukraść widoku bliźniaka (wyszłaby niezlustrowana = złom).
5. Detal gięty narysowany tylko PO gięciu (rzut skrócony o cos kąta) → NIE zgadujemy
   konturu, status DO_SPRAWDZENIA. **Uwaga**: ekstraktor potrafi złapać RZUT IZOMETRYCZNY
   (3D) z warstwy pozycyjnej i podać złe proporcje — rozwinięcie płaskie tej samej pozycji
   leży zwykle gdzie indziej i łapie się trybem „bez warstw" (sprawdzić proporcje vs wykaz!).
6. **GEOMETRIA W BLOKACH (INSERT)**: gdy modelspace = same INSERT-y, rozbić przez
   `virtual_entities()` zanim cokolwiek (inaczej „NIE ZNALEZIONO"). Zob. [[krotkie-nazwy-bloki-zero]].
7. **QC po samym bbox to za mało**: test wymiaru sprawdza tylko bounding box. „Pierścień"
   z ~230 krótkich odcinków (koło osiowe/podziałowe), albo <3 encje, albo widok izometryczny
   o pasującym bbox = FAŁSZYWY TRAFIK. Dodatkowo liczyć: liczbę encji, średnią długość LINE,
   otwarte końce. Zob. [[sbm-okragle-niewyciagalne]].
8. **Pozycje okrągłe / płaszcze zwinięte / rysunki wariantowe (SBM)** często NIE są
   auto-ekstrahowalne (płaszcz pokazany tylko po zwinięciu, tabela `a[mm]` wielu wariantów).
   Płaszcz: dłuższy bok ≈ obwód koła. Status DO_SPRAWDZENIA / do ręki. Zob. [[sbm-okragle-niewyciagalne]].

### Wymogi operatora
- Wynikowy DXF **zawsze wyśrodkowany** (środek bbox w (0,0)) — łatwiej przeglądać w CAD.
- Kontury muszą być zamknięte, otworów nie wolno zgubić — weryfikacja nie może trwać
  dłużej niż narysowanie od nowa.
- Pliki niepewne dostają sufiks `_DO_SPRAWDZENIA` / `_LUSTRO_z_pN` — nie wchodzą
  do nestingu bez zatwierdzenia.

### Podgląd PNG — ZAWSZE czarne tło
- Do każdego DXF generujemy PNG. **Renderować WYŁĄCZNIE przez `testy/pretesty/_render_png.py`**
  (`facecolor="black"`). Linie rysunku są jasne — na białym tle część jest NIEWIDOCZNA.
  Komenda: `python testy/pretesty/_render_png.py "<folder>/*.dxf"`.

### Nazewnictwo wyniku (wykaz roboczy)
- Plik bazowy z ekstrakcji: `{Zeinr}_p{N}.dxf` (przy parze P/L: `{Zeinr}_p{N}_P` / `_L`).
- Docelowa nazwa produkcyjna = kolumna **`NAZWA`** w wykazie roboczym
  (`{grubość}_{gatunek}_{Zeinr}_p{N}_{ilość}st_{gięcie}_{4ost.zlecenia}_{INDEX}`).
- Mapowanie wiersz↔plik: kolumna **`dopasowanie`** = nazwa bazowego DXF (bez `.dxf`);
  `NAZWA` = nazwa nowego pliku. Nowy plik = kopia bazowego pod `NAZWA`.dxf.
- **`NAZWA`/`ZAKUPY` w wykazie bywają FORMUŁAMI.** `openpyxl.save` **kasuje cache formuł**
  → potem `data_only` zwraca `None`. Wartości policzone czytać przez **Excel COM**
  (`CalculateFull`, read-only) albo z wartości sprzed zapisu. `keep_vba=True` zachowuje makra.

## Środowisko

- Windows, Python 3.13 (`ezdxf`, `openpyxl`, `matplotlib` — patrz requirements.txt).
- GstarCAD 2022 w `C:\Program Files\Gstarsoft\GstarCAD2022\` (tylko do konwersji DWG).
- Dane na `\\QNAP-ENERGO\` (UNC) — do konwersji CAD kopiować lokalnie.

## Konwencje pracy

- Komentarze/dokumentacja po polsku (bez ogonków w kodzie .py), nazwy funkcji po angielsku.
- Po każdej zmianie w `src/`: `python testy/regresja.py` → musi być PASS.
- Nowy trudny przypadek ⇒ dopisać do `testy/regresja.py` (OCZEKIWANE) + rysunek do
  `testy/rysunki/`. Tak rośnie korpus — patrz PLAN.md etap 2.
- Stare materiały robocze (sesje testowe FABLE/OPUS): `..\analiza\testy\wyniki\`.

## Higiena repo (mniej tokenów / szybsze przeszukiwanie przez AI)

Folder nadrzędny `PROJEKT_dxf_cleaner` zawiera śmieci, które zaśmiecają każdy
glob/grep asystenta i palą tokeny. Trzymać `.claudeignore` w korzeniu z m.in.:
`.venv/`, `*.zip` (jest tam `DXF_cleaner.zip` ~47 MB), `__MACOSX/`, `**/_dev/`,
`**/cala_rozmowa.md` (zrzut całej rozmowy), `analiza/testy/wyniki/`.
Aktywny jest **tylko `EKSTRAKTOR_DXF/`** — `DXF_cleaner/` (stara wersja) i `analiza/`
(sesje testowe) to archiwum; docelowo przenieść do `_archiwum/` (też ignorowanego),
żeby asystent nie zgadywał co sesję, która kopia jest żywa.
