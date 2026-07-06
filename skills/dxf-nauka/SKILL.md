---
name: dxf-nauka
description: Destylacja wiedzy EKSTRAKTOR_DXF V3 - zamyka petle uczenia. Agreguje korpus decyzji + etykiety (werdykty czlowieka i AI) w szkic wnioskow (co zadzialalo, co zawiodlo, propozycje), BEZ LLM. Wnioski akceptuje CZLOWIEK -> kontekst/wiedza/ + nowy przypadek golden + ewentualna propozycja reguly/typu. Uzyj gdy uzytkownik prosi "destylacja", "czego sie nauczylismy", "wnioski ze zlecenia", "zaktualizuj wiedze", albo wywola /dxf-nauka.
---

# Skill: dxf-nauka

Destylacja korpus+etykiety -> szkic wnioskow. Logika w `nauka/destylacja.py`
(zero LLM, deterministyczna agregacja). Ten skill to procedura + brama akceptacji.

**Zasada 12:** uczenie = jawne reguly (md/yaml), nie czarna skrzynka. Awans obserwacji
do reguly/typu ZAWSZE za potwierdzeniem czlowieka. Wnioski NIE zmieniaja produkcji
bezposrednio - zawsze przez zasady -> testy -> merge (zasada 8).

## Wywolanie
`/dxf-nauka` - najlepiej po zleceniu z zebranymi werdyktami (`/dxf-przeglad`).

## Procedura
1. Uruchom destylacje z korzenia repo:
   `python nauka\destylacja.py`
   Czyta `nauka/korpus/decyzje.csv` (slad zdarzen uczacych) + `nauka/etykiety/etykiety.csv`
   (werdykty czlowiek/AI) -> szkic wnioskow (co zadzialalo, co zawiodlo, dlaczego,
   propozycje).
2. Przedstaw szkic czlowiekowi. Dla KAZDEGO wniosku zapytaj o akceptacje - NIC nie
   wchodzi do wiedzy/produkcji bez potwierdzenia (zasada 12).
3. Dla zaakceptowanych wnioskow:
   - dopisz notatke `kontekst/wiedza/<nazwa>.md` + linie w `kontekst/wiedza/MEMORY.md`,
   - dodaj przypadek do `testy/golden/` (utrwala nauke jako test),
   - gdy wniosek to nowa regula/typ -> `zasady/propozycje/` (nie od razu do produkcji).
4. Propozycje regul/typow ida sciezka awansu: propozycja -> golden + regresja +
   benchmark (0 regresji) -> potwierdzenie czlowieka -> merge (`/dxf-zasada`).

## Uwagi
- Korpus rosnie przez flage `--korpus` w silnikach (1 wiersz na zdarzenie uczace).
- Baza typow rosnie przez nauke: nowy wzorzec rysunku -> propozycja typu -> testy.
- Porownanie ze starymi: nowe silniki na historycznych zleceniach vs to, co poszlo
  na laser (wejscie do benchmarku).
