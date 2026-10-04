"""Plotly-Abbildungen der Splitting-Demo: Stufenwahrscheinlichkeiten (Schätzung gegen exakt), Überleben der Wurzeln, Streuung und Verzerrung über die
Seltenheit, Aufwand gegen gewöhnliche Simulation, Stufenabstand. Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

import plotly.graph_objects as go

import spl_constants as C
import spl_evaluation as E
import spl_formulas as F

SPLIT_COLOR = "#f58518"
EXACT_COLOR = "#4c78a8"
PLAIN_COLOR = "#9d9d9d"
N_COLORS = {250: "#9ecae9", 1000: "#4c78a8", 4000: "#1f3d63"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.25, top=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=top, b=10), legend=dict(orientation="h", y=legend_y),
                      plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def kind_label(kind):
    return C.KIND_LABELS[kind]


def build_stage_chart(levels, p_hat, p_exact):
    """Wahrscheinlichkeit, von einer Stufe zur nächsten zu kommen, bevor das Gate leer ist: Schätzung des Laufs (Punkte) gegen exakte
    Spielerruin-Werte (Linie, exponentielle Dauer); x = Zielstufe."""
    xs = levels[1:len(p_hat) + 1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=p_exact[:len(xs)], mode="lines", line=dict(color=EXACT_COLOR, width=2.5), name="exakt (exponentielle Dauer)"))
    fig.add_trace(go.Scatter(x=xs, y=p_hat, mode="markers", marker=dict(color=SPLIT_COLOR, size=8), name="Schätzung dieses Laufs"))
    fig.update_xaxes(title_text="Zielstufe (belegte Spuren)", dtick=max(1, len(xs) // 12))
    fig.update_yaxes(title_text="P(Zielstufe vor leerem Gate)", range=[0, 1.02])
    return _base(fig, 340)


def build_roots_chart(levels, roots, n):
    """Verschiedene Wurzeln (Teilchen der ersten Stufe, aus denen die überlebenden Teilchen hervorgingen) je Stufe: die Entartung der Ahnenreihen."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=levels[:len(roots)], y=roots, mode="lines+markers", line=dict(color=SPLIT_COLOR, width=2.5), name="verschiedene Wurzeln"))
    fig.add_hline(y=n, line=dict(color=PLAIN_COLOR, dash="dash"), annotation_text=f"Start: {C.fmt_int(n)} Teilchen")
    fig.update_xaxes(title_text="Stufe (belegte Spuren)", dtick=max(1, len(levels) // 12))
    fig.update_yaxes(title_text="verschiedene Wurzeln (logarithmisch)", type="log", rangemode="tozero")
    return _base(fig, 340)


def build_relsd_chart(pre, kind):
    """Relative Standardabweichung eines Splitting-Laufs (je 16 Läufe) über die Zahl der Spuren (= Seltenheit), je Teilchenzahl."""
    fig = go.Figure()
    for n in C.STUDY_N:
        xs, ys = [], []
        for c in C.STUDY_C:
            sd = E.cell_rel_sd(E.study_cell(pre, c, n, kind))
            if sd == sd:
                xs.append(c)
                ys.append(100 * sd)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=N_COLORS[n], width=2.5), name=f"{C.fmt_int(n)} Teilchen je Stufe"))
    fig.add_hline(y=100, line=dict(color=PLAIN_COLOR, dash="dash"), annotation_text="100 %")
    fig.update_xaxes(title_text="Spuren c (Verlust sinkt von 10⁻³ auf 10⁻²⁰)", tickvals=list(C.STUDY_C))
    fig.update_yaxes(title_text="relative Streuung eines Laufs (%, logarithmisch)", type="log", ticksuffix=" %")
    return _base(fig, 340)


def build_bias_chart(pre, kind):
    """Mittel der 16 Schätzwerte geteilt durch den exakten Wert über die Zahl der Spuren (1 = erwartungstreu); graue Punkte: die einzelnen Läufe
    mit 4000 Teilchen (Läufe ohne Treffer fehlen auf der logarithmischen Achse)."""
    fig = go.Figure()
    xs, ys = [], []
    for c in C.STUDY_C:
        cell = E.study_cell(pre, c, max(C.STUDY_N), kind)
        for est in cell["estimates"]:
            if est > 0:
                xs.append(c)
                ys.append(est / cell["exact"])
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", marker=dict(color=PLAIN_COLOR, size=6, opacity=0.5),
                             name=f"einzelne Läufe ({C.fmt_int(max(C.STUDY_N))} Teilchen)"))
    for n in C.STUDY_N:
        cx, cy = [], []
        for c in C.STUDY_C:
            b = E.cell_bias(E.study_cell(pre, c, n, kind))
            if b > 0:
                cx.append(c)
                cy.append(b)
        fig.add_trace(go.Scatter(x=cx, y=cy, mode="lines+markers", line=dict(color=N_COLORS[n], width=2.5), name=f"Mittel, {C.fmt_int(n)} Teilchen"))
    fig.add_hline(y=1, line=dict(color="#e45756", dash="dash"))
    fig.update_xaxes(title_text="Spuren c", tickvals=list(C.STUDY_C))
    fig.update_yaxes(title_text="Schätzwert / exakter Wert (logarithmisch)", type="log")
    return _base(fig, 340, legend_y=-0.35)


def build_effort_chart(pre, kind):
    """Ereignisse für eine relative Standardabweichung von 10 %: gewöhnliche Simulation (Formel) gegen Splitting (aus der Streuung der Läufe
    hochgerechnet), logarithmisch. Splitting-Werte bei Streuung über 100 % sind Größenordnungen."""
    cs = [c for c in C.STUDY_C]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cs, y=[F.plain_events_needed(F.erlang_b(c, C.STUDY_A), C.TARGET_REL_SD) for c in cs], mode="lines+markers",
                             line=dict(color=PLAIN_COLOR, width=2.5, dash="dash"), name="gewöhnliche Simulation"))
    for n in (1000, 4000):
        ys = [E.effort_for_target(E.study_cell(pre, c, n, kind)) for c in cs]
        fig.add_trace(go.Scatter(x=cs, y=ys, mode="lines+markers", line=dict(color=N_COLORS[n], width=2.5), name=f"Splitting, {C.fmt_int(n)} Teilchen"))
    fig.update_xaxes(title_text="Spuren c", tickvals=cs)
    fig.update_yaxes(title_text="Ereignisse für ±10 % (logarithmisch)", type="log")
    return _base(fig, 340)


def build_steps_chart(pre):
    """Stufenabstand (20 Spuren, 2000 Teilchen, exponentiell, je 16 Läufe): Läufe ohne Treffer (Balken) und Mittel/exakt (Linie, rechts)."""
    steps = list(C.STUDY_STEPS)
    cells = [E.step_cell(pre, s) for s in steps]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(s) for s in steps], y=[c["zeros"] for c in cells], marker_color=PLAIN_COLOR, name="Läufe ohne Treffer (von 16)"))
    fig.add_trace(go.Scatter(x=[str(s) for s in steps], y=[E.cell_bias(c) if E.cell_bias(c) > 0 else None for c in cells], mode="lines+markers",
                             line=dict(color=SPLIT_COLOR, width=2.5), name="Mittel / exakt (rechts)", yaxis="y2"))
    fig.update_layout(yaxis2=dict(title="Mittel / exakt", overlaying="y", side="right", rangemode="tozero", fixedrange=True))
    fig.update_xaxes(title_text="Stufenabstand (jede so-vielte belegte Spur ist eine Stufe)")
    fig.update_yaxes(title_text="Läufe ohne Treffer", range=[0, 16.5])
    return _base(fig, 340)
