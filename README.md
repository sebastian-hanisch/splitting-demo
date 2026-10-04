# Seltene Ereignisse: Multilevel-Splitting (Streamlit-Demo)

**[→ Demo live ausprobieren](https://sebastianhanisch-splitting-demo.streamlit.app/)**

Interaktive Demo zur **Simulation sehr seltener Ereignisse** am Terminal-Gate. **Neuntes Stück der Konzepte-Linie „Warteschlangentheorie und Simulation“**
im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net) (Operations Research und Machine Learning): ein Verfahren, ein wachsendes Beispiel, jedes
Folgestück hebt genau eine Annahme auf.

In [erlang-b-demo](https://github.com/sebastian-hanisch/erlang-b-demo) (Stück 8) wird ein Lkw abgewiesen, wenn alle Spuren belegt sind. Mit vielen Spuren und
wenig Last ist das **extrem selten**: Bei 20 Spuren und 3 Erlang Angebot trifft es einen von 14 Milliarden Lkw. Eine gewöhnliche Simulation sieht dann auch nach
Millionen Ankünften keinen Verlust. **Multilevel-Splitting** teilt den Weg zum Ereignis in Stufen (immer mehr belegte Spuren) und vervielfältigt die Läufe, die
eine Stufe erreicht haben. Die exakte Erlang-B-Formel ist der Prüfstein.

## Kernfrage

Wie weit trägt Splitting: bis zu welcher Seltenheit schätzt es erwartungstreu und genau, was spart es gegenüber gewöhnlicher Simulation, und wo entartet es?

## Modell und Methodik

- **Ereignis:** Alle c Spuren sind belegt (5 bis 30 Spuren, Angebot 2, 3, 5 oder 8 Erlang, Dauer exponentiell, fest oder gleichverteilt, Mittel 3 min); der Anteil der
  Zeit dafür ist der Verlust B = Erlang B, für jede Dauer gleich (Stück 8).
- **Regenerative Zerlegung** (`spl_formulas.py`): Zyklus = Ankunft in ein leeres Gate bis das Gate wieder leer ist. B = P(Zyklus erreicht c) · h / E[Zykluslänge] mit
  h = mittlere Zeit mit c Belegten, E[Zykluslänge] = 1/(a·π₀). Für exponentielle Dauer sind alle Teile exakt (Spielerruin): P(von lo zu hi vor leer) = S(lo)/S(hi) mit
  S(m) = Σⱼ<m j!/aʲ, P(erreicht c) = 1/S(c), h = (aᶜ⁻¹/c!)·S(c). Gegenprobe: lineares Gleichungssystem der Geburts-Sterbe-Kette.
- **Splitting** (`spl_simulation.py`, Fixed Effort): Stufen sind Zahlen belegter Spuren. Stufe 1: N Teilchen (frische Ankunft). Von Stufe lo zu hi: N Teilchen aus den
  Zuständen, die lo erreicht haben (mit Zurücklegen), laufen bis hi (Erfolg) oder leeres Gate (Misserfolg); p̂ = Erfolge/N. Ein Teilchen ist der **volle Zustand**
  (Abgangszeiten der Belegten), daher gilt das Verfahren auch für nicht-exponentielle Dauer. Von der letzten Stufe aus wird die Zeit mit c Belegten gemessen, die
  Zykluslänge kommt aus gewöhnlicher Simulation. Die **Wurzel** jedes Teilchens ist das Stufe-1-Teilchen, aus dem es hervorging; wie viele verschiedene Wurzeln
  überleben, misst die **Entartung** der Ahnenreihen. SplitMix64 mit getrennten Strömen für Zwischenankunft, Dauer und Auswahl.
- **Gegenproben:** (1) jede Stufenwahrscheinlichkeit der Simulation gegen S(lo)/S(hi) (auch mit gröberen Stufen); (2) mittlere Zeit mit c Belegten, Zykluslänge und
  Erreichwahrscheinlichkeit gegen die exakten Werte; (3) die Busy Period gegen den exakten Wert für alle drei Verteilungen; (4) von Hand gerechnete Einheiten
  (ein Teilchen bis zur Zielstufe, bis leer, Zeit mit allen Spuren belegt, eine Stufe, die Busy Period, die gewöhnliche Simulation); (5) Splitting gegen Erlang B für
  exponentielle, feste und gleichverteilte Dauer.
- **Vorgerechnete Studie** (`generate_precomputed.py` → `precomputed_sweep.json`, rund anderthalb Minuten parallel): 5 Spurzahlen (10 bis 30) × 3 Teilchenzahlen (250, 1000,
  4000) × 2 Verteilungen, je 16 Läufe; gewöhnliche Simulation mit zwei Ereignisbudgets (400 000 und 4 000 000) bei 10, 15, 20 Spuren; Stufenabstand 1, 2, 3, 5, 8 bei
  20 Spuren und 2000 Teilchen. Live läuft ein Splitting-Lauf plus eine gewöhnliche Simulation mit etwa gleichem Ereignisbudget.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`. Angebot 3 Erlang; Verlust bei 10 / 15 / 20 / 25 / 30 Spuren: 8.1·10⁻⁴ / 5.5·10⁻⁷ / 7.1·10⁻¹¹ / 2.7·10⁻¹⁵ / 3.9·10⁻²⁰.
„Streuung“ ist die relative Standardabweichung eines Laufs, aus 16 Läufen geschätzt.

| Frage | Befund |
|---|---|
| Was sieht die gewöhnliche Simulation? | Läufe ohne einen einzigen Verlust von 16 (Budget 400 000 / 4 000 000 Ereignisse): bei 10 Spuren **0 / 0**, bei 15 Spuren **13 / 5**, bei 20 Spuren **16 / 16**. Mittel/exakt bei 10 Spuren 1.02 / 1.00, bei 15 Spuren 2.29 / 1.26 (wenige Treffer). |
| Splitting bei mäßiger Seltenheit? | 10 Spuren: in allen sechs Zellen Mittel/exakt **0.95 bis 1.02**, Streuung **5 % bis 20 %**. Sie sinkt mit der Teilchenzahl. |
| Bei 15 Spuren (5.5·10⁻⁷)? | 4000 Teilchen: Mittel/exakt 0.94 (Streuung 17 %) exponentiell, 1.00 (22 %) fest. Streuung exponentiell 85 / 58 / 17 % bei 250 / 1000 / 4000 Teilchen. |
| Bei 20, 25, 30 Spuren? | **Unzuverlässig.** 4000 Teilchen, Mittel/exakt (Streuung): 20 Spuren 0.79 (41 %) exponentiell, 0.84 (42 %) fest; 25 Spuren 2.23 (281 %) / 1.11 (116 %); 30 Spuren 0.61 (156 %) / 1.02 (131 %). Das Vorzeichen der Abweichung wechselt: schwere Schwänze. |
| Was ist die Entartung? | Verschiedene Wurzeln auf der letzten Stufe (von 4000 Teilchen) bei 10 / 15 / 20 / 25 / 30 Spuren: **400 / 119 / 36 / 12 / 5**, bei 1000 Teilchen 104 / 29 / 10 / 3.5 / 2.2. Bei 30 Spuren und 4000 Teilchen stammen alle Teilchen der letzten Stufe von 0.13 % der Wurzeln. |
| Was spart Splitting? | Für ±10 % bräuchte gewöhnliche Simulation bei 15 Spuren 3.7·10⁸ Ereignisse, Splitting (4000 Teilchen) 5.3·10⁶: das **69-Fache** weniger (fest 56-fach). Bei 20 Spuren 2.8·10¹² gegen 5.7·10⁷ (**4.9·10⁴-fach**, fest 7.2·10⁴). Bei 10 Spuren nur das **1.1- bis 2.1-Fache**. |
| Wie dicht sollen die Stufen liegen? | 20 Spuren, 2000 Teilchen, Stufenabstand 1 / 2 / 3 / 5 / 8: Läufe ohne Treffer **0 / 0 / 0 / 8 / 16** von 16, Mittel/exakt 1.09 / 1.47 / 0.48 / 0.71 / 0, Ereignisse je Lauf 1.67 / 1.16 / 0.92 / 0.46 / 0.21 Mio. Gröbere Stufen sparen Ereignisse, aber ab Abstand 5 sterben die Läufe. |
| Kommen Verluste einzeln? | **Nein, in Gruppen:** Bei 10 Spuren ist die Varianz der Verlustzahl der gewöhnlichen Simulation das **1.5-Fache** (400 000 Ereignisse) bzw. **1.8-Fache** (4 000 000) des Poisson-Werts. Die Aufwandsformel (100/B Ankünfte) ist eine Untergrenze. |
| Standardlauf der App? | 15 Spuren, 1000 Teilchen, Seed 35: Splitting 4.3·10⁻⁷ (0.78 des exakten Werts) mit 505 508 Ereignissen, 26 Wurzeln auf der letzten Stufe. Die gewöhnliche Simulation zählt **3 Verluste** in 252 754 Ankünften (1.2·10⁻⁵, **22-fach zu hoch**; erwartet 0.14). |

## Befunde und Korrekturen gegenüber der Vorab-Messreihe

- **Die Vorab-Messreihe war zu glatt.** Sie nannte Streuungen von 9 / 36 / 73 / 140 / 154 % für 10 bis 30 Spuren bei 2000 Teilchen, also einen gleichmäßigen Anstieg. In der Studie
  (4000 Teilchen, andere Seeds) sind es 5 / 17 / 41 / 281 / 156 %: der Anstieg ist **nicht monoton** (bei 30 Spuren weniger als bei 25), weil die Streuung selbst aus nur
  16 Läufen geschätzt ist und bei schweren Schwänzen stark schwankt.
- **Das Vorzeichen der Verzerrung steht nicht fest.** Die Vorab-Messreihe zeigte bei 30 Spuren Mittel/exakt 0.16 („unterschätzt“); die Studie 0.61 (4000 Teilchen) und 1.35
  (1000 Teilchen). Richtig ist nur: bei 20 Spuren und mehr ist das Mittel aus 16 Läufen nicht verlässlich, mal zu hoch, mal zu niedrig.
- **Aufwandsfaktoren:** Die Vorab-Messreihe nannte „29-fach bei 15 Spuren, 26 000-fach bei 20“; die Studie (4000 Teilchen) 69-fach und 4.9·10⁴-fach. Die Größenordnung stimmt, die
  Zahlen hängen von Teilchenzahl und Seeds ab.
- **Neu gefunden: Verluste kommen in Gruppen.** Die Poisson-Formel unterschätzt den Aufwand der gewöhnlichen Simulation; der Standardlauf zählt drei Verluste, wo 0.14 zu erwarten
  waren. Das ist kein Fehler der Simulation, sondern Gruppenbildung: ein Besuch von „alle Spuren belegt“ weist oft mehrere Ankünfte ab.

## Ehrliche Grenzen

- Die Stufenfunktion (Zahl der Belegten) ist hier naheliegend und wurde nicht optimiert; bei Netzen oder Prioritäten ist sie nicht vorgegeben.
- **Importance Sampling** (Raten umkehren) ist nicht enthalten; es kommt ohne Entartung der Ahnenreihen aus, braucht aber ein passendes Maß.
- Die Streuung ist aus 16 Läufen geschätzt und bei schweren Schwänzen unsicher; die Aufwandsangaben für Splitting bei Streuung über 100 % sind nur Größenordnungen.
- Die Studie gilt nur für Angebot 3 Erlang, die Verteilungen exponentiell und fest und die Teilchenzahlen 250, 1000, 4000; die App zeigt für andere Werte die nächste Zelle und
  sagt es. Gleichverteilte Dauer gibt es nur live (die Studien-Abschnitte zeigen dann die exponentiellen Zellen).
- Splitting mit fester Teilchenzahl je Stufe (Fixed Effort); adaptive Verfahren (Stufen aus den Daten, feste Erfolgszahl) sind nicht gerechnet.
- Die Genauigkeit der Zykluslänge kommt aus gewöhnlicher Simulation mit N Zyklen; das ist billig (Zyklen sind kurz), aber ein eigener Fehleranteil.
- Der Live-Lauf ist ein einzelner Lauf: er streut bei seltenem Verlust um Zehntel bis Vielfache des Werts; bei vielen Spuren und 4000 Teilchen dauert er bis zu einer halben Minute.

## Verwandte Demos im Portfolio

- [`markov-queue-demo`](https://github.com/sebastian-hanisch/markov-queue-demo) (Zusatzstück: die Zeit bis zum ersten Verlust, bis 20 Spuren exakt aus der Kette, wo die Simulation sie nie erlebt).
- [`erlang-b-demo`](https://github.com/sebastian-hanisch/erlang-b-demo) (Stück 8): der Verlust, Erlang B und seine Unempfindlichkeit gegen die Dauer.
- [`output-analysis-demo`](https://github.com/sebastian-hanisch/output-analysis-demo) (Stück 2): Wiederholungen, Streuung und Konfidenzintervalle.
- [`mm1-queue-demo`](https://github.com/sebastian-hanisch/mm1-queue-demo) (Stück 1): der Aufwand für Genauigkeit bei starker Auslastung.
- [`ems-demo`](https://github.com/sebastian-hanisch/ems-demo): Rettungsdienst; Verlustsystem als Hypercube-Modell, geprüft an Erlang B.

## Bewusst nicht umgesetzt

Jede dieser Annahmen hebt ein Folgestück der Linie auf:

| Annahme | Folgestück |
|---|---|
| Dauer exponentiell, fest oder gleichverteilt | [M/G/1, Kingman-Näherung](https://github.com/sebastian-hanisch/mg1-kingman-demo) |
| Alle Lkw gleich wichtig | [Prioritätsklassen](https://github.com/sebastian-hanisch/priority-queue-demo) |
| Konstante Ankunftsrate | [Zeitvariable Ankünfte](https://github.com/sebastian-hanisch/time-varying-arrivals-demo) |
| Ein Gate | [Jackson-Netze](https://github.com/sebastian-hanisch/jackson-network-demo) |

Kein Folgestück: Wahl der Stufenfunktion für andere Systeme, Importance Sampling.

## Tests

114 Tests, rund 40 Sekunden: Erlang B von Hand, Spielerruin-Stufenwahrscheinlichkeiten von Hand und gegen ein lineares System, die regenerative Zerlegung (Erlang B aus Zyklus-
Größen), die Verteilungen der Dauer, jede Einheit des Splittings von Hand gerechnet (Teilchen bis zum Ziel, bis leer, Zeit mit allen Spuren belegt, Stufe, Busy Period,
Stufenliste, gewöhnliche Simulation), Stufenwahrscheinlichkeiten und Zykluskenngrößen der Simulation gegen die exakten Werte, Erwartungstreue für alle drei Verteilungen, Splitting findet,
was die gewöhnliche Simulation verpasst, Invarianten (Wurzeln können nur verschwinden), gestorbener Lauf, gleicher Seed gleiches Ergebnis, Vollständigkeit der vorgerechneten Datei,
Presets und Permalink, Diagramme (gesperrte Achsen), AppTest-Rauchtests mit festem Würfel-Seed, der Smoke-Test der Portfolio-Vorlage, ein Quelltext-Test gegen Satz-Komma-Fehler und
`test_claims.py` für jede Zahl dieser README.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `spl_formulas.py` | Erlang B, Spielerruin, regenerative Zerlegung, Aufwandsformel |
| `spl_simulation.py` | Teilchen, Stufen, Splitting, gewöhnliche Simulation |
| `spl_evaluation.py` | Live-Lauf, Studienzellen, Kennzahlen |
| `generate_precomputed.py` | rechnet die Studie vor → `precomputed_sweep.json` |
| `spl_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `spl_presets.py`, `spl_constants.py` | Presets, Permalink, Grenzen |
| `tests/` | siehe oben |

## Literatur

- Kahn, H., Harris, T. E. (1951): Splitting als Idee der Varianzreduktion (genannt als Ursprung des Verfahrens in der Übersicht zu Splitting; Titel und Quelle nicht einzeln belegt).
- Villén-Altamirano, M., Villén-Altamirano, J. (1991): RESTART, eine Splitting-Methode für seltene Ereignisse in Bediensystemen (Quelle und Seiten nicht einzeln belegt).
- Glasserman, P., Heidelberger, P., Shahabuddin, P., Zajic, T. (1999): Multilevel splitting for estimating rare event probabilities. *Operations Research* 47(4), 585–600
  (Analyse als Verzweigungsprozess; optimaler Grad der Aufspaltung je Stufe: die erwartete Zahl der Teilpfade, die eine Stufe erreichen, bleibt etwa konstant, wie hier mit N Teilchen je Stufe).

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests/ -v`. Studie neu rechnen: `python generate_precomputed.py`.

Gebaut mit Streamlit und Plotly.
