# Fazowanie (chamfer) - linia rownolegla do krawedzi + rzut boczny

**Zrodlo:** operator, 38_1847 gr6 SL10585238 p2 / SL10585242 p2 (2026-07-07).

FAZOWANIE = sfazowana (skosna) krawedz detalu - obrobka pod spaw lub estetyczna. **NIE jest
cieciem lasera** (to osobna operacja na krawedzi). Na rysunku:

- **linia rownolegla do krawedzi konturu**, blisko niej (typowo ~5 mm), na dlugosci tej
  krawedzi, w kolorze GEOMETRII (kol. 7, nie magenta);
- widoczne na **rzucie bocznym obok** widoku glownego (skos krawedzi).

## Pulapka dla pipeline

Linia fazowania rownolegla do krawedzi tworzy **T-zlacza** z bokami konturu -> bramka 2
liczy je jako "2 otwarte konce" i pozycja idzie w 🟡 z mylacym powodem. To NIE jest
otwarty kontur - obrys zewnetrzny jest domkniety, a linia fazowania to znacznik obrobki.

## Co robic (docelowo, propozycja `wykrywanie_fazowania`)

- Rozpoznac linie fazowania (rownolegla do krawedzi, T-zlacza, ew. potwierdzenie rzutem
  bocznym) i NIE liczyc jej jako konturu ciecia.
- Oznaczyc pozycje: **technologia = "fazowanie"** (obok G/S/GS) + uwaga. Zostawic 🟡 do
  potwierdzenia, ale z jawnym powodem "wykryto fazowanie".
- Operator: "takie p2 gdy zolte to sprawdze i jest ok - tylko dobrze jakbys wylapal
  fazowanie". Czyli 🟡 jest akceptowalne; wartosc = OZNACZENIE fazowania, nie zgadywanie.

Powiazane: [[widok-zlozeniowy-vs-do-palenia]] (inna semantyka linii przy czesci),
propozycja `2026-07-07_wykrywanie_fazowania`.
