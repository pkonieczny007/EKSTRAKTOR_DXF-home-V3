# MANUAL UPGRADER — folder szkolenia ekstraktora

> Zlecenie wchodzi → AI analizuje → wypada gotowa notatka wiedzy.
> To **front-door** do produkcji notatek `kontekst/wiedza/*.md`, które
> zasilają pułapki w `CLAUDE.md`, kategorie szukania i testy `regresja.py`.

## Po co to jest

Nie uczymy sieci neuronowej. Zamieniamy **realne trudne zlecenie** w trwałą
regułę, którą ekstraktor (i następna sesja AI) będzie znać. Wynik każdego
szkolenia to plik `.md` w istniejącym formacie wiedzy — patrz przykłady w
`kontekst/wiedza/` (`giecie-phantom-kolor6.md`, `sbm-legenda-lustro.md`).

## Jak zrobić szkolenie (krok po kroku)

1. **Załóż projekt** — skopiuj `_szablon/` do
   `projekty/RRRR-MM-DD_temat/` (np. `2026-07-03_SBM_lustro`).
2. **Wrzuć wejście** do `wejscie/`:
   - **Tryb A (całe zlecenie / jeden typ):** rysunki DXF/DWG + wykaz.xlsx
     (+ ewentualne screeny z zaznaczeniem, gdy jest kilka podobnych rzutów).
   - **Tryb B (wykaz z plakietkami):** sam wykaz.xlsx z wypełnioną kolumną
     `SZKOLENIE` i `OPIS` (patrz niżej). DXF opcjonalnie.
3. **Opisz** w `opis.md` własnymi słowami: co tu jest nietypowe, czego uczysz.
4. **Uruchom AI na projekcie** — poproś o „przerób szkolenie
   `projekty/RRRR-MM-DD_temat`". AI:
   - **Tryb A:** przepuszcza zlecenie przez ekstraktor
     (`src/v2/orkiestrator.py`), porównuje wynik i opisuje co i dlaczego
     poszło nie tak.
   - **Tryb B:** czyta wykaz + Twój opis, sam ekstraktora nie odpala.
   - w obu: zapisuje `wnioski.md` w formacie wiedzy.
5. **Domknij pętlę** — gdy `wnioski.md` jest dobre, AI kopiuje je do
   `kontekst/wiedza/<nazwa>.md`, dopisuje linijkę w `kontekst/wiedza/MEMORY.md`
   i — jeśli to nowy trudny przypadek — dodaje sprawdzenie w `testy/regresja.py`
   + rysunek do `testy/rysunki/` (zasada 8 z `CLAUDE.md`).

## Forma wykazu (Tryb B)

Ten **sam** wykaz materiałowy co w produkcji (xlsx, 1. zakładka,
`ZAKUPY=blacha`), plus dwie kolumny:

| kolumna     | rola                                                            |
|-------------|-----------------------------------------------------------------|
| `SZKOLENIE` | **plakietka = tag lekcji** na wierszach pozycji, których dotyczy: `LUSTRO`, `GIECIE_MAGENTA`, `NIEWYCIAGALNE`, `BLOK_INSERT`, `ZERO_WIODACE`, ... |
| `OPIS`      | Twoje zdanie własnymi słowami — co w tej pozycji jest nietypowe  |

Tag wpisujesz **w kolumnie** (nie kolorem, nie komentarzem) — czytelne
deterministycznie. Jeden tag = jedna rodzina lekcji; nowe tagi dopisuj do
listy w tym README.

## Struktura folderu

```
szkolenia/
  README.md              ← ten plik
  _szablon/              szkielet jednego szkolenia (kopiuj)
    opis.md
    wnioski.md
    wejscie/
  projekty/
    RRRR-MM-DD_temat/
      wejscie/           DXF + wykaz + screeny   (git-ignored)
      opis.md            Twój opis
      wnioski.md         wynik AI
  analiza/               brudnopis / eksperymenty (git-ignored)
```

`wejscie/` i `analiza/` są **poza gitem** (duże pliki, dane produkcyjne).
Commitujemy tylko `.md`: `opis.md`, `wnioski.md`, README, szablon.

## Zasady (spójne z CLAUDE.md)

- Nie zgadujemy geometrii — niepewne = `_DO_SPRAWDZENIA`, do człowieka.
- Wnioski w formacie wiedzy: frontmatter `name/description/metadata.type`,
  potem treść, dla `feedback`/`project` linie `**Why:**` i `**How to apply:**`,
  linki `[[nazwa]]` do pokrewnych notatek.
- Wnioski po polsku (ogonki OK w `.md`); nazwy tagów po angielsku/bez ogonków.
- Nowy trudny przypadek ⇒ regresja + rysunek testowy.
