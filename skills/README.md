# Skille V3 — źródła (deploy: ~/.claude/skills + SecondBrain)

Tu trzymamy ŹRÓDŁA skilli (jedno źródło prawdy). Deploy = kopia do
`~/.claude/skills/<nazwa>/` oraz `\\Qnap-energo\baza\.data\SecondBrain\03_Zasoby\Skille\`.
Każdy skill ma wpis w `zarzadzanie/rejestr.yaml` (wersja podbijana przy każdej
zmianie — zasada 13); zgodność instalacji pilnuje `python zarzadzanie\audyt.py`.

Stan:
- `/wyciagnij-dxf` — działa (zainstalowany; źródło jeszcze w ~/.claude/skills —
  migracja źródła tutaj + podmiana na orkiestrator V3 = PLAN etap 5).
- `/dxf-testy`, `/dxf-sprawdz`, `/dxf-przeglad`, `/dxf-zasada`, `/dxf-nauka`,
  `/dxf-audyt` — plan (PLAN etapy 4–6).

Konwencja: skill = PROCEDURA (recall wiedzy z `kontekst/wiedza/MEMORY.md` +
`kontekst/` przed działaniem) + wywołania skryptów z tego repo. Logika w Pythonie,
nie w prozie skilla.
