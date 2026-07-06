# SL10582608_p1 — owal odseparowany na środku, gubiony przez KLASTROWANIE (nie kolor!)

- Skąd: zlecenie 38_1847 (2026-07-04), rysunek `SL10582608_1.dxf`, wykaz poz. 1
  (449×365, blacha 5 mm S235JRC). Typ: lantek_1nn (geometria warstwa 51, kolor 7 biały).
- Co testuje: silnik W-B (po-kolorze-7, gap=8) zwrócił poz. 1 ze statusem ZIELONY/ŻÓŁTY,
  wymiar 449×365 zgadzał się co do mm — a ZGUBIŁ duży środkowy owal (stadion, 2 łuki
  r=8.5/7.0 + 2 linie) razem z jeszcze jedną środkową cechą (wynik 25 ARC+37 LINE vs
  źródło 29+41). Owal to WYSPA odseparowana → trafił do osobnego klastra i nie został
  dołączony do konturu głównego.
- **KLUCZOWE: to NIE był błąd doboru koloru.** Cała geometria (owal też) jest na warstwie
  51, kolor 7 (białe) — biały był poprawny. Błąd jest w KROKU KLASTROWANIA po gap, który
  odcina wyspę na środku. Metoda region+warstwa (weź CAŁĄ warstwę 51 w widoku, bez
  klastrowania) owalu nie gubi — to sposób ręczny operatora.
- Jak wykryte: kontrola kompletności DWIEMA metodami (bo sam wymiar nie łapie):
  (1) liczbowo bilans konturów region vs wynik PO dedupie: źródło 12 wewn./5 okr. vs
  wynik 10/5 (delta 2); (2) wizualnie render region-źródło vs wynik — owal nieobecny.
- Wzorzec: `wzorzec/SL10582608_p1.dxf` — ekstrakcja region+warstwa 51 (bez klastra),
  skala 5.0 ZWERYFIKOWANA z geometrii (major 5.0000 / minor 4.9964, rozjazd 0.07%),
  wyśrodkowany (0,0), gięcia (kolor 6) na warstwie GIECIE. Po naprawie: 12 wewn. = 12,
  wymiar 449.0×365.3, render zgodny ze źródłem cecha-po-cesze.
- Cel silnika (etap 2): W-C region+warstwa jako wariant obok W-B; bramka 5 (bilans
  konturów) + sweep kompletności muszą flagować tę utratę; NIE ufać zielonemu semaforowi
  gdy wymiar OK (fałszywa zieleń). Bliźniak poz. 2 = LUSTRO P/L tego widoku (jeden widok
  w rysunku, konwencja lantek_1nn: poz. N rysowana, poz. N+1 odbita).
