---
name: sbm-legenda-lustro
description: "Konwencja SBM - przy numerze pozycji \"as drawn\" i \"mirrored\" => pozycja 2 to lustro; trzymac sie opisu"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e7f327a0-aeb3-4df0-b8f6-9b183f2a2fcf
---

Standardowy rysunek SBM ma w legendzie przy numerach pozycji opis pary blach:
pierwsza pozycja = "wie gezeichnet / as drawn" (jak narysowano), nastepna o tych
samych wymiarach = "spiegelbildlich / mirrored" (lustro). Czyli np. 001 = as drawn,
002 = lustrzane.

**Why:** Na SL10581913 (zlecenie 43_2404) ekstraktor przypisal realne rozwiniecie
do pozycji 2, a dla pozycji 1 wygenerowal lustro - ODWROTNIE niz legenda. Tak wyciete
oba detale wyszlyby w zlej rece = zlom (pulapka #4 z CLAUDE.md). Przyczyna: warstwa
pozycyjna 101 trzymala WIDOK Z BOKU (838 x ~100), nie rozwiniecie, wiec poz.1 padla
na proporcjach i zrobila lustro bliznika; prawdziwe rozwiniecie z warstwy zbiorczej
"1" zgarnela poz.2. Ekstraktor NIE czyta adnotacji as drawn/spiegelbildlich.

**How to apply:** Trzymac sie opisu PRZY NUMERZE POZYCJI. Realna wyciagnieta geometria
(jak narysowano) idzie do pozycji oznaczonej "as drawn"; lustro do pozycji
"spiegelbildlich". Gdy ekstraktor zrobi na krzyz - zamienic etykiety plikow
(as-drawn -> _pN bez sufiksu, lustro -> _p(N+1)_LUSTRO). Docelowo: ekstraktor
powinien czytac legende i przypisywac reke do wlasciwego numeru.

**Stan regresji (11.06.2026):** poprawne pary lustrzane SA juz w testy/regresja.py
(SL10578701, SL400521100 - tam poz.1 znajduje wlasny widok, wiec poz.2=LUSTRO
przypisane dobrze). SL10581513 jest CELOWO POZA regresja - to przypadek z bledna
reka (poz.1 ma na warstwie widok z boku, wpada w lustro na zlym numerze). Nie
wpisywac go jako "PASS" bo zalockuje bug; dodac z poprawnym oczekiwaniem dopiero
gdy powstanie czytanie legendy as drawn/spiegelbildlich.
