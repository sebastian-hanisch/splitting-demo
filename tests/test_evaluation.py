"""Auswertung: Live-Lauf, Zusammenfassung von Läufen, Zellen-Kennzahlen von Hand, Vollständigkeit der vorgerechneten Datei."""

import pytest

import spl_constants as C
import spl_evaluation as E
import spl_formulas as F
from spl_simulation import SplitResult


def fake_run(estimate, events, roots=(100, 50, 20), stage_p=(0.5, 0.4)):
    return SplitResult(c=3, a=3.0, kind="exp", n=100, levels=[1, 2, 3], stage_p=list(stage_p), successes=[50, 40], roots=list(roots), time_at_c=0.1,
                       cycle=2.0, events=events, estimate=estimate)


def test_mean_and_sd_by_hand():
    assert E.mean_and_sd([1.0, 3.0]) == (2.0, pytest.approx(2 ** 0.5)) and E.mean_and_sd([5.0]) == (5.0, 0.0)


def test_cell_figures_by_hand():
    """Schätzwerte 1.0 / 3.0 bei exaktem Wert 1.0 und 100 / 300 Ereignissen: Mittel/exakt 2, relative Streuung √2/2, Aufwand für ±10 %: 200·(0.7071/0.1)²."""
    cell = E.summarize_split_runs(3, 100, "exp", [fake_run(1.0, 100), fake_run(3.0, 300)], a=3.0)
    cell["exact"] = 1.0
    assert E.cell_mean(cell) == 2.0 and E.cell_bias(cell) == 2.0 and E.cell_rel_sd(cell) == pytest.approx(0.5 * 2 ** 0.5)
    assert E.cell_mean_events(cell) == 200.0 and E.effort_for_target(cell) == pytest.approx(200 * (0.5 * 2 ** 0.5 / 0.1) ** 2)


def test_summary_pads_died_runs_with_zero():
    died = SplitResult(c=3, a=3.0, kind="exp", n=100, levels=[1, 2, 3], stage_p=[0.5, 0.0], successes=[50, 0], roots=[100, 50, 0], time_at_c=0.0,
                       cycle=float("nan"), events=10, estimate=0.0, died_at=2)
    cell = E.summarize_split_runs(3, 100, "exp", [fake_run(1.0, 100), died], a=3.0)
    assert cell["zeros"] == 1 and cell["roots"] == [100.0, 50.0, 10.0] and cell["stage_p"] == pytest.approx([0.5, 0.2]) and cell["reps"] == 2
    assert cell["exact"] == pytest.approx(F.erlang_b(3, 3.0))


def test_relative_sd_is_nan_when_every_run_found_nothing():
    cell = E.summarize_split_runs(3, 100, "exp", [fake_run(0.0, 10), fake_run(0.0, 20)], a=3.0)
    assert E.cell_rel_sd(cell) != E.cell_rel_sd(cell) and E.effort_for_target(cell) != E.effort_for_target(cell)


def test_nearest_picks_the_closest_option_and_the_smaller_on_a_tie():
    assert E.nearest(C.STUDY_C, 5) == 10 and E.nearest(C.STUDY_C, 12) == 10 and E.nearest(C.STUDY_C, 13) == 15 and E.nearest(C.STUDY_C, 22) == 20
    assert E.nearest(C.STUDY_N, 2000) == 1000 and E.nearest(C.STUDY_N, 3000) == 4000


def test_live_report_structure_and_reference_values():
    r = E.live_report(8, 3.0, "exp", 300, seed=3)
    assert r["exact"] == pytest.approx(F.erlang_b(8, 3.0)) and len(r["exact_stage"]) == len(r["split"].stage_p) == 7
    assert r["plain"].arrivals == max(C.PLAIN_ARRIVALS_MIN, r["split"].events // 2)
    assert r["plain_events_needed"] == pytest.approx(F.plain_events_needed(r["exact"], C.TARGET_REL_SD))


def test_live_report_caps_the_plain_budget_and_follows_the_stage_list():
    r = E.live_report(10, 3.0, "det", 200, seed=1, step=3)
    assert r["split"].levels == [1, 4, 7, 10] and len(r["exact_stage"]) == 3
    assert r["exact_stage"][0] == pytest.approx(F.stage_probability(1, 4, 3.0))
    assert C.PLAIN_ARRIVALS_MIN <= r["plain"].arrivals <= C.PLAIN_ARRIVALS_MAX


def test_study_cell_run_small_structure():
    cell = E.study_cell_run(6, 200, "exp", 3, seed=5)
    assert cell["reps"] == 3 and len(cell["estimates"]) == len(cell["events"]) == 3 and len(cell["levels"]) == 6 and len(cell["roots"]) == 6
    assert cell["roots"][0] == 200 and cell["exact"] == pytest.approx(F.erlang_b(6, 3.0))
    plain = E.plain_cell_run(6, 20_000, "exp", 3, seed=5)
    assert plain["reps"] == 3 and len(plain["estimates"]) == 3 and plain["budget"] == 20_000


def test_precomputed_file_is_complete():
    pre = E.load_precomputed()
    assert {(x["c"], x["n"], x["kind"]) for x in pre["study"]} == {(c, n, k) for c in C.STUDY_C for n in C.STUDY_N for k in C.STUDY_KINDS}
    assert {(x["c"], x["budget"]) for x in pre["plain"]} == {(c, b) for c in C.STUDY_PLAIN_C for b in C.STUDY_PLAIN_BUDGETS}
    assert [x["step"] for x in pre["steps"]] == list(C.STUDY_STEPS) and pre["study_reps"] == C.STUDY_REPS and pre["study_a"] == C.STUDY_A
    for x in pre["study"] + pre["steps"]:
        assert x["reps"] == C.STUDY_REPS and len(x["estimates"]) == C.STUDY_REPS and x["exact"] == pytest.approx(F.erlang_b(x["c"], C.STUDY_A))
    for x in pre["plain"]:
        assert x["reps"] == C.STUDY_REPS and x["exact"] == pytest.approx(F.erlang_b(x["c"], C.STUDY_A))


def test_lookups_and_missing_cells():
    pre = E.load_precomputed()
    assert E.study_cell(pre, 15, 1000, "exp")["c"] == 15 and E.plain_cell(pre, 10, 400_000)["c"] == 10 and E.step_cell(pre, 3)["step"] == 3
    for call in (lambda: E.study_cell(pre, 16, 1000, "exp"), lambda: E.plain_cell(pre, 10, 5), lambda: E.step_cell(pre, 4)):
        with pytest.raises(KeyError):
            call()
