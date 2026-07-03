# -*- coding: utf-8 -*-
"""
Rejestr kategorii szukania - auto-discovery z config/kategorie.yaml.

Kazda kategoria to wtyczka: modul w tym pakiecie z funkcja
  znajdz(geometria, wiersz_wykazu, profil) -> [Kandydat]
Dodanie kategorii = nowy plik + wpis w YAML. Zero zmian w orkiestratorze.
"""
import importlib
from pathlib import Path
from types import SimpleNamespace

import yaml

_ROOT = Path(__file__).resolve().parents[4]  # V3: silniki/v2/kategorie -> korzen repo
DOMYSLNY_CONFIG = _ROOT / "config" / "kategorie.yaml"


def zaladuj_kategorie(sciezka=None):
    """Czyta rejestr YAML i importuje wlaczone kategorie w kolejnosci."""
    sciezka = Path(sciezka) if sciezka else DOMYSLNY_CONFIG
    cfg = yaml.safe_load(sciezka.read_text(encoding="utf-8")) or {}
    out = []
    for wpis in cfg.get("kategorie", []):
        if not wpis.get("wlaczona", True):
            continue
        modul = importlib.import_module(f"v2.kategorie.{wpis['modul']}")
        if not hasattr(modul, "znajdz"):
            raise AttributeError(
                f"kategoria {wpis['modul']}: brak funkcji znajdz(geo, wiersz, profil)")
        out.append(SimpleNamespace(
            nazwa=wpis.get("nazwa", wpis["modul"]),
            modul=modul,
            ustawienia=wpis.get("ustawienia") or {},
            kolejnosc=wpis.get("kolejnosc", 99)))
    out.sort(key=lambda k: k.kolejnosc)
    return out
