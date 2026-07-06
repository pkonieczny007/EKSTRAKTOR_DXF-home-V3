# -*- coding: utf-8 -*-
"""DEPLOY SKILLI (Etap 5) - kopiuje zrodla skilli z skills/ do miejsc instalacji.

Jedno zrodlo prawdy = skills/<nazwa>/ w repo (CLAUDE.md). Deploy = kopia do miejsc
z rejestr.yaml (`instalacje`): ~/.claude/skills/<nazwa> + SecondBrain UNC. Po deployu
`python zarzadzanie\\audyt.py` powinien pokazac 0 rozjazdow instalacji.

DOMYSLNIE DRY-RUN (tylko wypisuje plan) - nic nie kopiuje. `--wykonaj` = faktyczna kopia.
UNC nieosiagalny / brak zrodla = GLOSNO (zasada 15), NIE wywraca reszty deployu.

Deployuje skille rejestru ktore MAJA zrodlo skills/<nazwa>/ + niepusta `instalacje`.

Uzycie:
  python zarzadzanie\\deploy_skilli.py            # DRY-RUN (plan)
  python zarzadzanie\\deploy_skilli.py --wykonaj  # faktyczny deploy
  python zarzadzanie\\deploy_skilli.py --tylko dxf-sprawdz dxf-przeglad  # wybrane
"""
import io
import shutil
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
REJESTR = HERE / "rejestr.yaml"
SKILLS_SRC = REPO / "skills"


def _rozwin(sciezka):
    """Rozwija ~ (HOME) w sciezce instalacji; UNC/backslash zostawia."""
    s = sciezka.strip()
    if s.startswith("~"):
        return Path.home() / s[2:].lstrip("/\\")
    return Path(s)


def plan_deployu(tylko=None):
    """Lista (nazwa, zrodlo, [cele]) skilli do deployu. tylko=None -> wszystkie z zrodlem."""
    dane = yaml.safe_load(REJESTR.read_text(encoding="utf-8"))
    plan = []
    for n in dane.get("narzedzia", []):
        if n.get("typ") != "skill":
            continue
        nazwa = n["nazwa"]
        if tylko and nazwa not in tylko:
            continue
        zrodlo = SKILLS_SRC / nazwa
        instalacje = n.get("instalacje") or []
        if not (zrodlo / "SKILL.md").exists():
            if tylko and nazwa in tylko:
                print(f"[DEPLOY] {nazwa}: brak zrodla {zrodlo}\\SKILL.md - pomijam (GLOSNO)")
            continue
        if not instalacje:
            continue
        plan.append((nazwa, zrodlo, [_rozwin(p) for p in instalacje]))
    return plan


def deploy(tylko=None, wykonaj=False):
    """Kopiuje (albo tylko planuje) skille. Zwraca (ok, bledy) - liczby."""
    plan = plan_deployu(tylko)
    if not plan:
        print("[DEPLOY] brak skilli ze zrodlem do deployu (sprawdz skills/ i rejestr)")
        return 0, 0
    tryb = "WYKONANIE" if wykonaj else "DRY-RUN (nic nie kopiuje; --wykonaj = faktyczny deploy)"
    print(f"=== DEPLOY SKILLI [{tryb}] ===\n")
    ok = bledy = 0
    for nazwa, zrodlo, cele in plan:
        print(f"skill {nazwa}  (zrodlo: {zrodlo})")
        for cel in cele:
            if not wykonaj:
                print(f"    -> {cel}")
                continue
            try:
                cel.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(zrodlo, cel, dirs_exist_ok=True)
                print(f"    OK -> {cel}")
                ok += 1
            except Exception as e:  # UNC nieosiagalny / brak uprawnien - GLOSNO, jedz dalej
                print(f"    BLAD -> {cel} ({e}) (GLOSNO)")
                bledy += 1
    if wykonaj:
        print(f"\n[DEPLOY] skopiowano {ok} celow, bledow {bledy}. "
              f"Sprawdz: python zarzadzanie\\audyt.py")
        if bledy:
            print("[DEPLOY] BLEDY powyzej (np. SecondBrain UNC offline) - popraw i powtorz")
    else:
        print(f"\n[DEPLOY] plan: {len(plan)} skilli. Uruchom z --wykonaj aby skopiowac.")
    return ok, bledy


def main(argv):
    if "-h" in argv or "--help" in argv:
        print(__doc__)
        return 0
    wykonaj = "--wykonaj" in argv
    tylko = None
    if "--tylko" in argv:
        i = argv.index("--tylko")
        tylko = [a for a in argv[i + 1:] if not a.startswith("--")]
    _, bledy = deploy(tylko, wykonaj)
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(main(sys.argv[1:]))
