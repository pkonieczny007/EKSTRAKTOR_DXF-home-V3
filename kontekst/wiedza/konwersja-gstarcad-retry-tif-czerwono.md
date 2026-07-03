---
name: konwersja-gstarcad-retry-tif-czerwono
description: "GstarCAD w batchu bywa przejsciowo niestabilny (retry naprawia); odtworzenie geometrii z TIF tylko w ostatecznosci, na czerwono, do sprawdzenia przez operatora"
metadata:
  type: feedback
---

Zlecenie 54_4867, dwie zasady operacyjne:

**1. Konwersja DWG->DXF (GstarCAD) - retry.** W batchu 39 rysunkow jeden
(SL40051182) nie skonwertowal sie (RuntimeError), a chwile pozniej z osobnego
wywolania poszedl w 11 s. Przyczyna: przejsciowy stan GstarCAD po dlugim zadaniu
(SL10599245 zzarl 473 s), nie uszkodzony plik. **Dodac RETRY** w driverze (2-3
proby, swieze wywolanie) - to nie ".bak byl lepszy", tylko czysta instancja.
UNC nie dziala, kopiowac do %TEMP% (juz w convert_dwg.py). Operator moze tez
skonwertowac hurtem sam i dostarczyc _conv.dxf - odciaza model na latwym etapie.

**2. Odtwarzanie z TIF = ostatecznosc, na CZERWONO.** TIF (rysunek warsztatowy)
sluzy do **weryfikacji wzrokowej** i **technologii**, NIE do geometrii. Gdy jakas
cecha jest tylko na TIF a nie da sie jej wziac z DWG, mozna ja odtworzyc RECZNIE,
ale wtedy:
- rysowac ja **kolorem czerwonym (kolor 1)** na DXF,
- oznaczyc pozycje **czerwono w wykazie** + adnotacja co odtworzone,
- to robimy tylko w ostatecznosci - operator MUSI to sprawdzic.
Lustra P/L generowac z DXF-a blizniaka (odbicie), NIE z TIF.

**Why:** geometria z TIF (rastra) jest niepewna wymiarowo; czerwony = jawny sygnal
"zweryfikuj". **How to apply:** default = geometria z DWG; TIF-reconstruction
tylko gdy brak innej drogi, zawsze czerwono i do akceptacji.
