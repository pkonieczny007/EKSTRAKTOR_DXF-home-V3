---
name: otwory-wspolsrodkowe-zdublowane
description: "Otwor narysowany jako dwa wspolsrodkowe okregi (przelot + poglebienie/adnotacja) - do lasera zostaje najmniejszy; identyczne zdublowane okregi odduplikowac"
metadata:
  type: project
---

Zlecenie 54_4867, wsporniki SL10596945 p3/p4. Ekstrakcja zostawila otwor jako
**dwa wspolsrodkowe okregi**: Ø13 (rzeczywisty przelot) + Ø14.7 (wieksza srednica
= poglebienie/countersink/adnotacja, po niemiecku uwaga "wieksza srednica przy
Verzinkung/galwanizacji"). Do wycinania laserem zostaje **tylko najmniejszy**.

Osobno: SL10602681_p1 mial ten sam otwor narysowany 2x (identyczny Ø6, ten sam
srodek) = duplikat do usuniecia.

**Why:** podwojny okrag idzie do nestingu jako dwa wyciecia (wewnetrzne kolo
przepada albo laser tnie dwa razy); zla srednica otworu. Wymiar zewnetrzny sie
zgadza, wiec kontrola wymiaru tego NIE lapie.

**How to apply:** grupuj CIRCLE po srodku (tol 0.1 mm); jesli >1 na srodek - zostaw
o **min promieniu**, reszte skasuj (obejmuje i wiekszy koncentryczny, i identyczny
duplikat). Decyzja operatora przy galwanizacji: zostawiamy MNIEJSZA srednice.
Skan calego zlecenia po wspolsrodkowych okregach = tania bramka QC. Patrz
[[cechy-odseparowane-region-warstwa]].
