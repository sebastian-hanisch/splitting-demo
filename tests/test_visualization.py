"""Abbildungen: gesperrte Achsen, Zahl der Linien, Beschriftungen."""

import spl_constants as C
import spl_evaluation as E
import spl_formulas as F
import spl_visualization as V

PRE = E.load_precomputed()


def _locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def test_all_charts_lock_their_axes():
    live = E.live_report(8, 3.0, "exp", 200, seed=1)
    s = live["split"]
    figs = [V.build_stage_chart(s.levels, s.stage_p, live["exact_stage"]), V.build_roots_chart(s.levels, s.roots, 200), V.build_relsd_chart(PRE, "exp"),
            V.build_bias_chart(PRE, "exp"), V.build_effort_chart(PRE, "det"), V.build_steps_chart(PRE)]
    assert all(_locked(f) for f in figs)
    assert figs[5].layout.yaxis2.fixedrange                          # auch die rechte Achse ist gesperrt


def test_kind_labels():
    assert [V.kind_label(k) for k in C.KINDS] == ["exponentiell", "fest", "gleichverteilt (0 bis 2)"]


def test_stage_chart_plots_one_point_per_transition_against_the_target_level():
    fig = V.build_stage_chart([1, 2, 3, 4], [0.7, 0.6, 0.5], [0.75, 0.6, 0.48])
    assert list(fig.data[1].x) == [2, 3, 4] and list(fig.data[1].y) == [0.7, 0.6, 0.5]


def test_roots_chart_starts_at_the_particle_count():
    fig = V.build_roots_chart([1, 2, 3], [100, 40, 12], 100)
    assert list(fig.data[0].y) == [100, 40, 12]


def test_relsd_chart_has_one_line_per_particle_count_and_rising_spread_with_rarity():
    fig = V.build_relsd_chart(PRE, "exp")
    assert [t.name for t in fig.data] == [f"{C.fmt_int(n)} Teilchen je Stufe" for n in C.STUDY_N]
    ys = list(fig.data[-1].y)
    assert ys[0] < ys[1] < ys[2]                                     # 10, 15, 20 Spuren: je seltener, desto größer die Streuung


def test_bias_chart_has_run_dots_plus_one_line_per_particle_count_and_a_reference_at_one():
    fig = V.build_bias_chart(PRE, "exp")
    assert len(fig.data) == 1 + len(C.STUDY_N) and all(y > 0 for y in fig.data[0].y)
    assert any(s.y0 == 1 for s in fig.layout.shapes)


def test_effort_chart_compares_plain_and_splitting_on_the_same_axis():
    fig = V.build_effort_chart(PRE, "exp")
    assert [t.name for t in fig.data] == ["gewöhnliche Simulation", "Splitting, 1.000 Teilchen", "Splitting, 4.000 Teilchen"]
    assert list(fig.data[0].y) == [F.plain_events_needed(F.erlang_b(c, C.STUDY_A)) for c in C.STUDY_C]
    assert fig.data[0].y[-1] > fig.data[2].y[-1] > 0


def test_steps_chart_has_one_bar_per_step():
    fig = V.build_steps_chart(PRE)
    assert list(fig.data[0].x) == [str(s) for s in C.STUDY_STEPS] and list(fig.data[0].y)[-1] == 16
