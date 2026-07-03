# -*- coding: utf-8 -*-
"""
Logger decyzji do korpusu samodoskonalenia (PLAN_v1 Etap 3 - wariant minimalny).

Kazde ZDARZENIE UCZACE z przebiegu orkiestratora (pozycja niepewna, odpalona
bramka QC, brak widoku, lustro do weryfikacji, brak w wykazie) dopisuje wiersz
do korpus/decyzje.csv. To jest "slad w korpusie" - zasada 4 z PLAN_v1.md:
kazda watpliwa decyzja zostawia dane do nauki, inaczej uczenie nie ma paliwa.

WAZNE: logger tylko ZBIERA surowe zdarzenia (deterministycznie, zero LLM).
Awans zdarzenia do trwalej REGULY (kontekst/wiedza/*.md) idzie PRZEZ CZLOWIEKA
- destylacja po zleceniu, patrz szkolenia/README.md. Nie utrwalamy regul
automatycznie, bo "uczenie = jawne reguly, nie czarna skrzynka".

Nie dotyka geometrii ani plikow DXF - czysty artefakt boczny.
"""
import csv
from pathlib import Path

# kolumny logu - stabilne, zeby dalo sie akumulowac miedzy zleceniami
POLA = ["zeinr", "posn", "status", "qc_semafor", "qc_powody",
        "kategoria", "technika", "pewnosc", "n_kandydatow",
        "wykaz_w", "wykaz_h", "out_w", "out_h", "file", "powod_logu"]


def powod_logu(rep):
    """Dlaczego pozycja jest zdarzeniem uczacym (badz '' gdy czysty OK/zielony).
    Kolejnosc = priorytet: najpierw twarde braki, potem semafory QC."""
    status = rep.get("status") or ""
    semafor = rep.get("qc_semafor") or ""
    if status.startswith("BRAK W WYKAZIE"):
        return "brak_w_wykazie"
    if "NIE ZNALEZIONO" in status:
        return "brak_widoku"
    if status.startswith("NIEPEWNE"):
        return "niepewne"
    if status.startswith("LUSTRO"):          # status lustra tez ma "ZWERYFIKUJ"
        return "lustro_do_weryfikacji"
    if "_DO_SPRAWDZENIA" in status or "ZWERYFIKUJ" in status:
        return "do_sprawdzenia"
    if semafor == "CZERWONY":
        return "qc_czerwony"
    if semafor == "ZOLTY":
        return "qc_zolty"
    return ""   # czysty OK / zielony - nie uczy


def zdarzenia_uczace(reports):
    """Lista (rep, powod) dla reportow, ktore niosa nauke."""
    out = []
    for rep in reports:
        powod = powod_logu(rep)
        if powod:
            out.append((rep, powod))
    return out


def zapisz_decyzje(reports, zeinr, korpus_path):
    """Dopisz zdarzenia uczace do korpus/decyzje.csv (append; naglowek + BOM
    tylko przy tworzeniu pliku). korpus_path falsy -> nic nie robi (domyslnie
    logowanie WYLACZONE, zeby testy nie zasmiecaly korpusu). Zwraca liczbe
    dopisanych wierszy."""
    if not korpus_path:
        return 0
    korpus_path = Path(korpus_path)
    korpus_path.parent.mkdir(parents=True, exist_ok=True)
    zdarzenia = zdarzenia_uczace(reports)
    nowy = not korpus_path.exists()
    # append w utf-8 (bez utf-8-sig: ten kodek dopisalby BOM przy KAZDYM
    # otwarciu -> smieci w srodku pliku); BOM raz, recznie, dla Excela
    with open(korpus_path, "a", newline="", encoding="utf-8") as f:
        if nowy:
            f.write("﻿")
        w = csv.DictWriter(f, fieldnames=POLA, extrasaction="ignore",
                           delimiter=";")
        if nowy:
            w.writeheader()
        for rep, powod in zdarzenia:
            wiersz = {k: rep.get(k, "") for k in POLA}
            wiersz["zeinr"] = zeinr
            wiersz["powod_logu"] = powod
            w.writerow(wiersz)
    return len(zdarzenia)
