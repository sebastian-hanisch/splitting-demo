"""Seltene Ereignisse: Multilevel-Splitting - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Neuntes Stück der Konzepte-Linie "Warteschlangentheorie und Simulation": Der Verlust des Erlang-Systems (Stück 8) wird so klein, dass eine
gewöhnliche Simulation ihn nie sieht. Multilevel-Splitting teilt den Weg zum Ereignis in Stufen (belegte Spuren) und vervielfältigt Läufe, die eine Stufe
erreichen. Die exakte Erlang-B-Formel ist der Prüfstein: Die Demo zeigt, wie weit das Verfahren trägt, wo es entartet und was es kostet. Siehe README
für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import spl_constants as C
import spl_formulas as F
from spl_evaluation import (cell_bias, cell_mean_events, cell_rel_sd, effort_for_target, live_report, load_precomputed, nearest, plain_cell, step_cell,
                            study_cell)
from spl_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                         sync_query_params)
from spl_visualization import (build_bias_chart, build_effort_chart, build_relsd_chart, build_roots_chart, build_stage_chart, build_steps_chart,
                               kind_label)

st.set_page_config(page_title="Seltene Ereignisse – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _precomputed():
    return load_precomputed()


@st.cache_data(show_spinner=False)
def _live(c, a, kind, n, seed, step):
    return live_report(c, a, kind, n, seed, step)


st.title("🔎 Seltene Ereignisse: Multilevel-Splitting")
st.markdown(
    """
In Stück 8 wurde ein Lkw abgewiesen, wenn alle Spuren belegt waren. Mit vielen Spuren und wenig Last ist das **extrem selten**: Bei 20 Spuren und
3 Erlang Angebot trifft es einen von 10 Milliarden Lkw. Eine **gewöhnliche Simulation** sieht dann auch nach Millionen Ankünften keinen einzigen
Verlust. **Multilevel-Splitting** geht den Weg zum Ereignis in **Stufen** (immer mehr belegte Spuren) und **vervielfältigt** die Läufe, die eine
Stufe erreicht haben. Die exakte Erlang-B-Formel ist der Prüfstein; die Demo zeigt, **wie weit das Verfahren trägt** und **wo es versagt**.
"""
)
st.caption(
    "Neuntes Stück der Linie „Warteschlangentheorie und Simulation“, aufbauend auf "
    "[erlang-b-demo](https://sebastianhanisch-erlang-b-demo.streamlit.app/) (der Verlust und seine Formel) und "
    "[output-analysis-demo](https://sebastianhanisch-output-analysis-demo.streamlit.app/) (Wiederholungen und Streuung). Jedes Folgestück hebt eine der "
    "Annahmen unter „Wo die Annahmen enden“ auf."
)

with st.expander("So funktioniert Splitting", expanded=True):
    st.markdown(
        """
- **Ereignis:** Alle c Spuren sind belegt (dann geht jede weitere Ankunft verloren). Der Anteil der Zeit dafür ist der Verlust B (Erlang B, für jede Dauer
  gleich).
- **Zyklus:** von der Ankunft in ein leeres Gate bis das Gate wieder leer ist. B = (Zeit mit c Belegten je Zyklus) / (Länge eines Zyklus).
- **Stufen:** 1, 2, …, c belegte Spuren. **Stufe 1:** N Läufe starten mit einer Ankunft im leeren Gate. **Von Stufe i zu i + 1:** N Teilchen werden aus den Zuständen
  gezogen, die Stufe i erreicht haben (mit Zurücklegen), und laufen, bis sie Stufe i + 1 erreichen (Erfolg) oder das Gate leer wird (Misserfolg). Der Anteil
  der Erfolge schätzt die Stufenwahrscheinlichkeit pᵢ.
- **Schätzung:** P(Zyklus erreicht c) = Π pᵢ, dazu die mittlere Zeit mit c Belegten von der letzten Stufe aus und die Zykluslänge (aus gewöhnlicher Simulation).
  Ein Teilchen ist der volle Zustand (Abgangszeiten aller Belegten), deshalb gilt das auch für feste oder gleichverteilte Dauer.
- **Entartung:** Jedes Teilchen stammt von einer Wurzel (einem Stufe-1-Teilchen). Wie viele **verschiedene Wurzeln** bis zur letzten Stufe überleben,
  zeigt, wie viel unabhängige Information das Verfahren wirklich hat.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{name}", width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name] or None)

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    c = st.slider("Spuren c", *bounds("c_slider"), step=C.C_STEP, key="c_slider", help="Mehr Spuren bei gleichem Angebot: der Verlust wird seltener.")
    a = st.select_slider("Angebot a (Erlang)", options=C.A_OPTIONS, key="a_select", format_func=lambda v: f"{v:g}",
                         help="Mittlere Zahl beschäftigter Spuren, wenn niemand abgewiesen würde; mittlere Dauer 3 min.")
    n = st.select_slider("Teilchen je Stufe", options=C.N_OPTIONS, key="n_select", format_func=C.fmt_int,
                         help="Mehr Teilchen: genauer, aber teurer. Bei vielen Spuren und 4000 Teilchen dauert ein Lauf bis zu einer halben Minute.")
    step = st.select_slider("Stufenabstand", options=C.STEP_OPTIONS, key="step_select",
                            help="1 = jede belegte Spur ist eine Stufe; größere Abstände sparen Aufwand, machen die Stufenwahrscheinlichkeiten aber kleiner.")
    kind = st.selectbox("Verteilung der Abfertigungsdauer", C.KINDS, key="kind_select", format_func=kind_label, help="Alle mit dem gleichen Mittel von 3 min.")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1], step=1,
                           key="seed_input", help="Bestimmt alle Zufallszahlen der Simulation.")
    st.button("🎲 Neuen Lauf würfeln", on_click=randomize_seed)

c, n, step, seed = int(c), int(n), int(step), int(seed)
a = float(a)
sync_query_params({"c_slider": c, "a_select": a, "n_select": n, "step_select": step, "kind_select": kind, "seed_input": seed})

pre = _precomputed()
study_c, study_n = nearest(C.STUDY_C, c), nearest(C.STUDY_N, n)
study_kind = kind if kind in C.STUDY_KINDS else "exp"
with st.spinner("Rechne Splitting und gewöhnliche Simulation … (bei vielen Spuren und Teilchen bis zu einer halben Minute)"):
    live = _live(c, a, kind, n, seed, step)
split, plain, exact = live["split"], live["plain"], live["exact"]

st.markdown("---")
st.markdown("## 🔎 Ein seltener Verlust, zwei Verfahren")
st.caption(
    f"{c} Spuren, Angebot {a:g} Erlang, Dauer {kind_label(kind)}, {C.fmt_int(n)} Teilchen je Stufe, Stufenabstand {step}. Die gewöhnliche Simulation bekommt etwa dasselbe "
    f"Ereignisbudget ({C.fmt_int(split.events)} Ereignisse des Splittings, begrenzt auf höchstens {C.fmt_int(2 * C.PLAIN_ARRIVALS_MAX)})."
)
r1 = st.columns(3)
r1[0].metric("Exakter Verlust (Erlang B)", C.fmt_sci(exact), help="Gilt für jede Verteilung der Dauer mit gleichem Mittel.")
r1[1].metric("Splitting (Schätzung)", C.fmt_sci(split.estimate) if split.estimate > 0 else "kein Treffer",
             help="Null, wenn auf einer Stufe kein Teilchen die nächste erreicht hat." if split.estimate == 0 else None)
r1[2].metric("Gewöhnliche Simulation (gleiches Budget)", C.fmt_sci(plain.blocking()) if plain.lost > 0 else "kein Verlust gesehen",
             help=f"{C.fmt_int(plain.arrivals)} Ankünfte, davon {plain.lost} abgewiesen.")
r2 = st.columns(3)
r2[0].metric("Splitting gegenüber exakt", C.fmt_ratio(split.estimate / exact) if split.estimate > 0 else "–", help="1 = erwartungstreu für diesen einen Lauf (mit Streuung).")
r2[1].metric("Ereignisse des Splittings", C.fmt_int(split.events))
r2[2].metric("Ereignisse der gewöhnlichen Simulation für ±10 %", C.fmt_sci(live["plain_events_needed"], 0),
             help="Aus Var ≈ 1/(n·B): 2·(1 − B)/(B·0.01) Ereignisse (je Ankunft eine Ankunft und ein Abgang).")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Stufenwahrscheinlichkeiten: Schätzung gegen exakt**")
    st.plotly_chart(build_stage_chart(split.levels, split.stage_p, live["exact_stage"]), width="stretch",
                    key=f"stage_{c}_{a}_{kind}_{n}_{step}_{seed}")
with col_b:
    st.markdown("**Wie viele Wurzeln überleben? (Entartung)**")
    st.plotly_chart(build_roots_chart(split.levels, split.roots, n), width="stretch", key=f"roots_{c}_{a}_{kind}_{n}_{step}_{seed}")
if split.estimate == 0:
    st.warning(
        f"Der Lauf ist an Übergang {split.died_at} (zu Stufe {split.levels[split.died_at]}) gestorben: Kein Teilchen hat die nächste Stufe erreicht, die Schätzung ist null. "
        "Mehr Teilchen oder ein kleinerer Stufenabstand helfen."
    )
else:
    st.info(
        f"Splitting schätzt **{C.fmt_sci(split.estimate)}** (exakt {C.fmt_sci(exact)}, Verhältnis {C.fmt_ratio(split.estimate / exact)}) mit {C.fmt_int(split.events)} Ereignissen. "
        f"Auf der letzten Stufe stammen die {C.fmt_int(split.successes[-1])} überlebenden Teilchen von nur {C.fmt_roots(split.roots[-1])} "
        f"(von {C.fmt_int(n)})."
    )
st.caption(
    "Ein einzelner Lauf ist eine Stichprobe: Bei seltenem Verlust streut sie um Zehntel bis Vielfache des Werts. Die Studien unten wiederholen jedes Verfahren 16-mal "
    "(Angebot 3 Erlang)."
)

st.markdown("---")
st.subheader("📐 Wie genau ist Splitting? Streuung und Verzerrung")
st.markdown(
    f"Je 16 Läufe pro Zelle bei Angebot {C.STUDY_A:g} Erlang, Dauer {kind_label(study_kind)}. Die Seltenheit steigt mit der Zahl der Spuren: von 8·10⁻⁴ bei 10 Spuren "
    f"auf 4·10⁻²⁰ bei 30. Links: **relative Streuung** eines Laufs, rechts: **Mittel / exakt** (1 = erwartungstreu)."
)
col_c, col_d = st.columns(2)
with col_c:
    st.plotly_chart(build_relsd_chart(pre, study_kind), width="stretch", key=f"relsd_{study_kind}")
with col_d:
    st.plotly_chart(build_bias_chart(pre, study_kind), width="stretch", key=f"bias_{study_kind}")
header = "| Spuren | exakter Verlust | " + " | ".join(f"{C.fmt_int(k)} Teilchen" for k in C.STUDY_N) + " | Wurzeln auf der letzten Stufe (4.000) |\n|---|---|" + "---|" * len(C.STUDY_N) + "---|\n"
body = ""
for cc in C.STUDY_C:
    cells = [study_cell(pre, cc, k, study_kind) for k in C.STUDY_N]
    body += (f"| {cc} | {C.fmt_sci(cells[0]['exact'])} | " + " | ".join(f"{cell_bias(x):.2f} (±{100 * cell_rel_sd(x):.0f} %)" for x in cells)
             + f" | {cells[-1]['roots'][-1]:.1f} |\n")
st.markdown(header + body)
st.caption("Zelle = Mittel / exakt (relative Streuung eines Laufs). Die Streuung selbst ist aus 16 Läufen geschätzt und bei schweren Schwänzen unsicher.")
cb = study_cell(pre, study_c, max(C.STUDY_N), study_kind)
st.info(
    f"Bei {study_c} Spuren (Verlust {C.fmt_sci(cb['exact'])}) und {C.fmt_int(max(C.STUDY_N))} Teilchen liegt das Mittel der 16 Läufe bei {cell_bias(cb):.2f} des exakten Werts, "
    f"ein einzelner Lauf streut um {100 * cell_rel_sd(cb):.0f} %; auf der letzten Stufe bleiben im Mittel {cb['roots'][-1]:.1f} von {C.fmt_int(max(C.STUDY_N))} Wurzeln."
)

st.markdown("---")
st.subheader("🔬 Was spart Splitting gegenüber gewöhnlicher Simulation?")
st.markdown(
    "Ereignisse, die für eine relative Streuung von 10 % nötig wären: gewöhnliche Simulation (Formel) gegen Splitting (aus der Streuung der 16 Läufe hochgerechnet). "
    "Wo die Streuung über 100 % liegt, sind die Splitting-Werte nur Größenordnungen."
)
st.plotly_chart(build_effort_chart(pre, study_kind), width="stretch", key=f"effort_{study_kind}")
rows = []
for cc in C.STUDY_C:
    cell = study_cell(pre, cc, max(C.STUDY_N), study_kind)
    plain_needed = F.plain_events_needed(cell["exact"], C.TARGET_REL_SD)
    eff = effort_for_target(cell)
    ratio = plain_needed / eff
    ratio_text = f"{ratio:.1f}" if ratio < 1000 else C.fmt_sci(ratio, 0)
    rows.append(f"| {cc} | {C.fmt_sci(cell['exact'])} | {C.fmt_sci(plain_needed, 0)} | {C.fmt_sci(eff, 0)} | {ratio_text} |")
st.markdown("| Spuren | exakter Verlust | gewöhnlich (Ereignisse) | Splitting, 4.000 Teilchen (Ereignisse) | Verhältnis |\n|---|---|---|---|---|\n" + "\n".join(rows))
plain_rows = []
for pc in C.STUDY_PLAIN_C:
    p1, p2 = plain_cell(pre, pc, C.STUDY_PLAIN_BUDGETS[0]), plain_cell(pre, pc, C.STUDY_PLAIN_BUDGETS[1])
    plain_rows.append(f"| {pc} | {C.fmt_sci(p1['exact'])} | {p1['zeros']} von {p1['reps']} | {p2['zeros']} von {p2['reps']} |")
st.markdown("**Gewöhnliche Simulation: Läufe ohne einen einzigen Verlust**\n\n| Spuren | exakter Verlust | 400.000 Ereignisse | 4.000.000 Ereignisse |\n|---|---|---|---|\n" + "\n".join(plain_rows))
st.caption(
    "Die Formel für die gewöhnliche Simulation ist eine Untergrenze: Abgewiesene Lkw kommen in Gruppen (ein Besuch von „alle Spuren belegt“ weist oft mehrere "
    "Ankünfte ab), die gemessene Varianz der Verlustzahl liegt bei 10 Spuren beim 1.5- bis 1.8-Fachen des Poisson-Werts."
)
c10 = study_cell(pre, 10, max(C.STUDY_N), study_kind)
c15 = study_cell(pre, 15, max(C.STUDY_N), study_kind)
st.info(
    f"Bei 15 Spuren (Verlust {C.fmt_sci(c15['exact'])}) bräuchte die gewöhnliche Simulation {C.fmt_sci(F.plain_events_needed(c15['exact']), 0)} Ereignisse für ±10 %, "
    f"Splitting etwa {C.fmt_sci(effort_for_target(c15), 0)}. Bei 10 Spuren (Verlust {C.fmt_sci(c10['exact'])}) gibt es keinen nennenswerten Gewinn."
)

st.markdown("---")
st.subheader("🔬 Wie dicht sollen die Stufen liegen?")
st.markdown(
    f"{C.STUDY_STEP_C} Spuren, {C.fmt_int(C.STUDY_STEP_N)} Teilchen, exponentielle Dauer, je 16 Läufe: Stufenabstand 1 heißt jede belegte Spur ist eine Stufe, 5 jede fünfte. "
    "Weniger Stufen sparen Ereignisse, aber jede Stufenwahrscheinlichkeit wird kleiner."
)
st.plotly_chart(build_steps_chart(pre), width="stretch", key="steps")
srows = []
for s in C.STUDY_STEPS:
    cell = step_cell(pre, s)
    srows.append(f"| {s} | {len(cell['levels'])} | {C.fmt_int(round(cell_mean_events(cell)))} | {cell['zeros']} von {cell['reps']} | "
                 f"{cell_bias(cell):.2f} |")
st.markdown("| Stufenabstand | Stufen | Ereignisse je Lauf | Läufe ohne Treffer | Mittel / exakt |\n|---|---|---|---|---|\n" + "\n".join(srows))
st.info("Dichte Stufen (Abstand 1) sind am verlässlichsten; je gröber, desto mehr Läufe sterben an einer Stufe, die kein Teilchen übersteht.")

st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Zahl der Belegten beschreibt den Weg zum Ereignis** | Hier ist die Stufenfunktion offensichtlich. Bei Netzen oder Prioritäten ist sie nicht vorgegeben, und eine schlechte Wahl macht Splitting wertlos. | kein Folgestück |
| **Splitting ist das richtige Verfahren** | Importance Sampling (Raten umkehren) kommt ohne Entartung der Ahnenreihen aus, braucht aber ein passendes Maß; hier nicht gerechnet. | kein Folgestück |
| **Dauer exponentiell, fest oder gleichverteilt** | Bei schweren Schwänzen der Dauer ändern sich Stufenwahrscheinlichkeiten und Streuung; die Formel für den Verlust bleibt, die Schätzung nicht. | **[M/G/1, Kingman-Näherung](https://sebastianhanisch-mg1-kingman-demo.streamlit.app/)** |
| **Alle Lkw gleich wichtig** | Bei Prioritäten gibt es je Klasse einen Verlust, das Ereignis hängt vom Zustand beider Klassen ab. | **[Prioritätsklassen](https://sebastianhanisch-priority-queue-demo.streamlit.app/)** |
| **Konstante Ankunftsrate** | Bei Wellen ist der seltene Verlust ein Spitzenereignis; der Zyklus „bis leer“ gibt es nicht mehr. | **[Zeitvariable Ankünfte](https://sebastianhanisch-time-varying-arrivals-demo.streamlit.app/)** |
| **Ein Gate** | In Netzen läuft der Verlust in die nächste Station; die Stufenfunktion hat mehrere Dimensionen. | **[Jackson-Netze](https://sebastianhanisch-jackson-network-demo.streamlit.app/)** |
"""
)
st.caption(
    "Verwandt im Portfolio: [markov-queue-demo](https://sebastianhanisch-markov-queue-demo.streamlit.app/) (Zusatzstück: die Zeit bis zum ersten Verlust, bis 20 Spuren exakt aus der Kette, wo die Simulation sie nie erlebt), [erlang-b-demo](https://sebastianhanisch-erlang-b-demo.streamlit.app/) (Stück 8: der Verlust, Erlang B, und seine Unempfindlichkeit), "
    "[output-analysis-demo](https://sebastianhanisch-output-analysis-demo.streamlit.app/) (Stück 2: Wiederholungen, Streuung und Konfidenzintervalle), "
    "[mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/) (Stück 1: der Aufwand für Genauigkeit bei starker Auslastung) und die "
    "Rettungsdienst-Demo [ems-demo](https://sebastianhanisch-ems-demo.streamlit.app/) (Verlustsystem als Hypercube-Modell)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Ereignis.** Erlang-Verlustsystem: $c$ Spuren, Poisson-Ankünfte mit Angebot $a$, mittlere Dauer 1, wer bei $c$ Belegten ankommt, geht verloren. Verlust
$B = \pi_c = \dfrac{a^c/c!}{\sum_{j \le c} a^j/j!}$ (PASTA, für jede Dauer).

**Regenerative Zerlegung.** Zyklus: Ankunft in ein leeres Gate bis das Gate wieder leer ist, $E[\text{Zyklus}] = 1/(a\pi_0)$. Dann
$$B = \frac{P(\text{Zyklus erreicht } c) \cdot h}{E[\text{Zyklus}]}, \qquad h = E[\text{Zeit mit } c \text{ Belegten} \mid \text{erreicht}].$$

**Stufen.** Mit Stufen $1 = \ell_0 < \ell_1 < \dots < \ell_m = c$ (belegte Spuren) ist $P(\text{erreicht } c) = \prod_i p_i$, $p_i = P(\ell_{i+1} \text{ vor leer} \mid \ell_i)$. Für
exponentielle Dauer gilt (Spielerruin der Geburts-Sterbe-Kette mit Geburtsrate $a$, Sterberate $j$)
$$p_i = \frac{S(\ell_i)}{S(\ell_{i+1})}, \qquad S(m) = \sum_{j=0}^{m-1} \frac{j!}{a^j}, \qquad h = \frac{a^{c-1}}{c!}\,S(c).$$

**Fixed-Effort-Splitting.** Je Stufe $N$ Teilchen aus den Zuständen, die die Stufe erreicht haben (mit Zurücklegen), $\hat p_i$ = Anteil der Erfolge;
$\hat B = \prod \hat p_i \cdot \hat h / \hat E[\text{Zyklus}]$. Ein Teilchen ist der volle Zustand (Abgangszeiten der Belegten), daher gilt das Verfahren für jede Dauer.
**Entartung:** die Teilchen einer Stufe stammen von wenigen Wurzeln; die Varianz wächst mit der Zahl der Stufen und der Abhängigkeit der Teilchen.

**Gewöhnliche Simulation.** Der Anteil verlorener Ankünfte hat relative Varianz $\approx 1/(nB)$, also $n \approx 100/B$ Ankünfte für $\pm 10\,\%$.

Implementiert in `spl_formulas.py` (Erlang B, Spielerruin, Zerlegung), `spl_simulation.py` (Teilchen, Stufen, Splitting, gewöhnliche Simulation), `spl_evaluation.py`
(Live-Lauf, Studienzellen), `generate_precomputed.py` (vorgerechnete Studie).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Warteschlangentheorie: M/M/1 bis Surrogat](https://sebastianhanisch.net/konzepte-warteschlangentheorie.html)."
)
