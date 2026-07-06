# Widok zlozeniowy vs widok do palenia (dospawywane elementy)

**Zrodlo:** operator, korekta na 38_1847 gr6 SL10585238 p1 (2026-07-07).

Rysunki spawanych zespolow (typowo SBM) maja na jednym arkuszu DWA widoki tej samej
pozycji blaszanej:

- **Widok ZLOZENIOWY** - czesc RAZEM z **dospawywanymi elementami** (inne czesci, ktore sie
  do niej przyspawuje). Dospawienia rysowane sa **kolorem 6 (magenta)** i STYKAJA sie z
  konturem czesci. Pokazuje wyglad po spawaniu.
- **Widok DO PALENIA** (obok, zwykle z prawej) - TA SAMA czesc CZYSTA: sam kontur ciecia +
  otwory + ew. fazowanie. **To jest to, co idzie na laser.**

## Pulapka dla pipeline

Oba widoki sa na tej samej warstwie pozycyjnej (np. 101) i maja te same wymiary z wykazu,
wiec ranking klastrow moze wybrac ZLOZENIOWY. Wtedy dospawienia (magenta) trafiaja do
wyniku jako ciete elementy -> zly detal. **Nie zakladac semantyki magenta** - kolor 6 to
moze byc: linia giecia (w poprzek rozwiniecia), fazowanie (rownolegle do krawedzi) ALBO
dospawywany element (styka sie z konturem na widoku zlozeniowym). Rozstrzyga ogledziny
calego arkusza, nie sama encja.

## Sygnal i obejscie

- **Rozbieznosc wariantow = sygnal zlego (zlozeniowego) widoku:** jesli W-A/W-B/W-C daja
  rozny interior na tym samym klastrze (SL10585238 p1: 9 vs 9 vs 11), to zwykle znak, ze
  zlapano widok z dospawieniami. Na widoku do palenia warianty sie zgadzaja.
- Dzis takie pozycje ida w 🟡 (rozbieznosc) do czlowieka - bezpiecznie, nic nie ucieka na
  laser jako 🟢. Docelowo: preferuj widok czystszy (propozycja `widok_zlozeniowy_vs_do_palenia`).

Powiazane: [[gwint-okrag-luk-dimension]] (inna semantyka magenta/luku), fazowanie (osobna
notatka), golden `SL10585238_p1_widok_zlozeniowy`.
