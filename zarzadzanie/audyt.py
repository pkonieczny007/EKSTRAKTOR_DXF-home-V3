# -*- coding: utf-8 -*-
"""
AUDYT rejestru narzedzi - rejestr.yaml vs rzeczywistosc (CLAUDE.md "Zarzadzanie").

Sprawdza dla kazdego wpisu:
  - aplikacja: czy `plik` istnieje w repo,
  - skill (status=dziala): czy zainstalowany we wszystkich `instalacje`,
  - status=dziala bez `test` -> ostrzezenie (brak weryfikacji),
  - status inny niz dziala/szkielet/plan/archiwum -> blad wpisu.

Wyjscie: tabela + lista rozjazdow. Kod wyjscia 0 = zgodne, 1 = rozjazdy.

Uzycie: python zarzadzanie\\audyt.py [--pelny]   (--pelny: takze wpisy OK)
"""
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REJESTR = HERE / "rejestr.yaml"
STATUSY = {"dziala", "szkielet", "plan", "archiwum"}


def rozwin(sciezka):
    """~/... -> profil uzytkownika; reszta bez zmian (UNC zostaje UNC)."""
    s = str(sciezka)
    if s.startswith("~"):
        return Path.home() / s.lstrip("~/\\")
    return Path(s)


def audytuj(wpis):
    """Zwraca liste problemow wpisu (pusta = OK)."""
    problemy = []
    status = wpis.get("status", "")
    if status not in STATUSY:
        problemy.append(f"nieznany status '{status}'")
    if wpis.get("typ") == "aplikacja":
        plik = ROOT / wpis.get("plik", "")
        if not wpis.get("plik"):
            problemy.append("brak pola `plik`")
        elif not plik.exists():
            problemy.append(f"plik nie istnieje: {wpis['plik']}")
    elif wpis.get("typ") == "skill":
        if status == "dziala":
            for inst in wpis.get("instalacje") or []:
                if not rozwin(inst).exists():
                    problemy.append(f"nie zainstalowany: {inst}")
            if not wpis.get("instalacje"):
                problemy.append("status=dziala a brak `instalacje`")
    else:
        problemy.append(f"nieznany typ '{wpis.get('typ')}'")
    if status == "dziala" and not wpis.get("test"):
        problemy.append("OSTRZEZENIE: dziala bez `test`")
    return problemy


def main(argv):
    pelny = "--pelny" in argv
    cfg = yaml.safe_load(REJESTR.read_text(encoding="utf-8")) or {}
    narzedzia = cfg.get("narzedzia", [])
    if not narzedzia:
        print(f"pusty rejestr: {REJESTR}")
        return 1

    rozjazdy = 0
    ostrzezenia = 0
    print(f"{'nazwa':<24} {'typ':<10} {'wersja':<7} {'status':<9} wynik")
    print("-" * 78)
    for wpis in narzedzia:
        problemy = audytuj(wpis)
        twarde = [p for p in problemy if not p.startswith("OSTRZEZENIE")]
        rozjazdy += bool(twarde)
        ostrzezenia += len(problemy) - len(twarde)
        if problemy or pelny:
            wynik = "OK" if not problemy else "; ".join(problemy)
            print(f"{wpis.get('nazwa', '?'):<24} {wpis.get('typ', '?'):<10} "
                  f"{str(wpis.get('wersja', '?')):<7} {wpis.get('status', '?'):<9} {wynik}")
    print("-" * 78)
    print(f"wpisow: {len(narzedzia)} | rozjazdy: {rozjazdy} | ostrzezenia: {ostrzezenia}")
    print("=== AUDYT: " + ("PASS ===" if rozjazdy == 0 else "ROZJAZDY ==="))
    return 0 if rozjazdy == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
