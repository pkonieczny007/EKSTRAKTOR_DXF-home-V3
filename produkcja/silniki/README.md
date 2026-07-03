# Silniki ekstrakcji (kopie z V1/V2 — tu żyją, tam NIE piszemy)

| Silnik | Plik | Pochodzenie | Status |
|---|---|---|---|
| **W-A** | `extract_positions.py` | V1 (kopia robocza z repo V2) — klastrowanie union-find + ranking widoków + zapis 1:1 | działa (regresja 43/43) |
| **W-B** | `v2/orkiestrator.py` + `v2/*` | V2 — kategorie szukania (wtyczki YAML) → weryfikator 8 bramek → galeria | działa (testy_v2 35/35, benchmark PASS) |
| **W-C** | `region_warstwa.py` | narzędzie `_region_warstwa.py` ze zlecenia 54_4867 — WSZYSTKIE encje warstwy geometrii w bbox widoku (cechy odseparowane nie wypadają) | narzędzie CLI; integracja jako silnik = PLAN etap 2 |
| — | `convert_dwg.py` | V1 — konwersja DWG→DXF przez GstarCAD (UNC→%TEMP%, retry) | działa |

Zasady (CLAUDE.md 9–10): do `EKSTRAKTOR_DXF-home` i `-home-V2` nie piszemy NIC —
kopie przeniesione RAZ (04.07.2026), od teraz rozwijane tutaj. W-B importuje W-A
(`wspolne.py` → `import extract_positions as v1`) — jedno źródło prawdy geometrii.
Po każdej zmianie: `python testy\regresja.py` + `python testy\testy_v2.py` PASS.

Ścieżki spatchowane przy przenosinach (różnice vs V2): `v2/kategorie/__init__.py`
(parents[4] → config/), `v2/galeria.py` (parents[3] → testy/pretesty),
`v2/orkiestrator.py` (korpus → `nauka/korpus/decyzje.csv`).
