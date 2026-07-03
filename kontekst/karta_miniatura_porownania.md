---
opis: Miniatura PNG surowego rysunku obok wyniku do weryfikacji
---
# Druga miniatura: rysunek "bez oczyszczenia"

Obok miniatury PNG wynikowego DXF (oczyszczona pojedyncza pozycja)
generowac druga miniature PNG **surowego rysunku** - tak jak wyglada
przed ekstrakcja (wszystkie warstwy: wymiary, osie, opisy, wszystkie widoki).

## Po co
Szybka weryfikacja poprawnosci: operator widzi obok siebie
- CO wycielismy (czysty kontur)  vs
- skad to wycielismy (caly rysunek zrodlowy)
i od razu ocenia, czy wziety zostal wlasciwy widok i czy nic nie zginelo,
bez otwierania CAD-a.

## Zrodlo surowej miniatury (do ustalenia)
- render calego _conv.dxf (wszystkie encje) - spojny z geometria, ktora
  widzi ekstraktor, albo
- konwersja TIF -> PNG ("prawda wydrukowana", niezalezna od warstw/kolorow,
  TIF istnieje do kazdego rysunku) - lepsza do wychwycenia bledow warstw.
  Najlepiej OBA, plus zaznaczona ramka wzietego widoku na surowym rysunku.

## Powiazania
- wpisuje sie w raport HTML z Etapu 1 (miniatury PNG, klik = DXF) oraz
  w interfejs wyjatkow z Etapu 3 (render kandydata + wycinek TIF tego obszaru).
- pomocnik renderu juz jest: testy/pretesty/_render_png.py.

## Demo (11.06.2026) - ZROBIONE, latwe
- skrypt: testy/pretesty/_demo_porownanie.py (3 panele: TIF | surowy _conv.dxf | wynik)
- przyklad: testy/pretesty/46_2998/dxf/SL10584244_DEMO_porownanie.png
- WNIOSEK: side-by-side (TIF lub render conv obok wyniku) = latwe, ~40 linii,
  reuzycie istniejacego renderu. TIF najczytelniejszy do weryfikacji.
- JEDYNA trudniejsza czesc: ramka "tu byl wziety widok" na surowym rysunku -
  ekstraktor musi zapisac ORYGINALNY bbox pozycji PRZED wysrodkowaniem do (0,0)
  (mala zmiana w extract_positions.py: dodac bbox zrodlowy do raportu CSV).
