# korpus/ — dane samodoskonalenia ekstraktora

> „Każda ręczna decyzja musi zostawić ślad w korpusie — inaczej uczenie nie ma
> paliwa." (zasada 4, `kontekst/PLAN_v1.md`)

## `decyzje.csv` — log zdarzeń uczących (WRITE, automatyczny)

Podczas przetwarzania zlecenia z flagą `--korpus`, orkiestrator dopisuje tu
**jeden wiersz na każde zdarzenie uczące**: pozycję niepewną, odpaloną bramkę
QC, brak widoku, lustro do weryfikacji, brak w wykazie. Zbieranie jest
deterministyczne (`src/v2/decyzje.py`, zero LLM) — to surowy materiał, **nie**
gotowa reguła.

Kolumny: `zeinr; posn; status; qc_semafor; qc_powody; kategoria; technika;
pewnosc; n_kandydatow; wykaz_w; wykaz_h; out_w; out_h; file; powod_logu`.

`powod_logu` ∈ `brak_w_wykazie | brak_widoku | niepewne | do_sprawdzenia |
lustro_do_weryfikacji | qc_czerwony | qc_zolty`.

Włączenie w produkcji:
```bash
python src\v2\orkiestrator.py <rysunek_conv.dxf> <wykaz.xlsx> <wyniki> --korpus
# --korpus bez wartosci -> korpus/decyzje.csv; --korpus <plik> -> wlasna sciezka
```
Bez flagi `--korpus` logowanie jest **wyłączone** (regresja/benchmark nie
zaśmiecają korpusu danymi testowymi).

## Pętla: log → destylacja → reguła (promocja za potwierdzeniem człowieka)

`decyzje.csv` sam z siebie nie zmienia ekstraktora. Po zleceniu AI **destyluje**
powtarzające się wzorce w kandydatów `wnioski.md` (format jak
`szkolenia/_szablon/wnioski.md`), a Ty je **potwierdzasz** przed zapisem do
`kontekst/wiedza/*.md`. Dopiero notatka w `wiedza/` (READ, krok „recall" w
skillu) faktycznie uczy ekstraktor. Nie ma auto-awansu surowego zdarzenia do
reguły — „uczenie = jawne reguły, nie czarna skrzynka".

## Git

Surowy `decyzje.csv` jest **poza gitem** (rośnie z każdym przebiegiem, dane
zleceń). Trwała wiedza wersjonuje się w `kontekst/wiedza/`, nie tutaj.
