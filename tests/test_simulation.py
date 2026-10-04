"""Simulation: Einheiten von Hand (Verteilungen, advance, run_stage, Busy Period, Stufenliste, gewöhnliche Simulation), Splitting gegen die exakten Stufen-
wahrscheinlichkeiten und gegen Erlang B (exponentielle, feste und gleichverteilte Dauer), Invarianten, Reproduzierbarkeit."""

import pytest

import spl_constants as C
import spl_formulas as F
import spl_simulation as S
from conftest import ScriptedRng


# ---------------------------------------------------------------- Einheit: Verteilung der Dauer

def test_draw_service_by_hand():
    assert S.draw_service("det", ScriptedRng()) == 1.0
    assert S.draw_service("unif", ScriptedRng(uniform_values=[0.25])) == pytest.approx(0.5)
    assert S.draw_service("exp", ScriptedRng(exp_values=[0.7])) == 0.7
    with pytest.raises(ValueError):
        S.draw_service("zipf", ScriptedRng())


@pytest.mark.parametrize("kind", C.KINDS)
def test_every_distribution_has_mean_one(kind):
    rng = S.SplitMix64(7)
    n = 300_000
    assert sum(S.draw_service(kind, rng) for _ in range(n)) / n == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------- Einheit: advance

def test_advance_reaches_the_target_by_hand(advance_mini):
    """Siehe conftest: c = 2, Teilchen [5.0] bei Uhr 0, Ankunft bei 1.0 mit Dauer 3.0 → zwei Belegte (Ziel), Zustand [4.0, 5.0]."""
    gap, svc = advance_mini
    res = S.advance(0.0, [5.0], 2, 2, 1.0, "exp", gap, svc)
    assert res.success and res.clock == pytest.approx(1.0) and sorted(res.busy) == [4.0, 5.0] and res.time_at_c == 0.0 and res.events == 1


def test_advance_fails_when_the_gate_empties_by_hand():
    """c = 3, Teilchen [1.0] bei Uhr 0, nächste Ankunft erst bei 2.0: der Abgang bei 1.0 leert das Gate → Misserfolg bei Uhr 1.0."""
    res = S.advance(0.0, [1.0], 2, 3, 1.0, "exp", ScriptedRng(exp_values=[2.0]), ScriptedRng(exp_values=[]))
    assert not res.success and res.clock == 1.0 and res.busy == [] and res.events == 1 and res.time_at_c == 0.0


def test_advance_measures_the_time_with_all_lanes_busy_by_hand():
    """c = 2, Teilchen [2.0, 5.0] bei Uhr 1.0, Ziel 3 (unerreichbar → bis leer), Ankünfte bei 2.5 (Dauer 1.0 → Abgang 3.5) und danach 102.5.
    Zeit mit beiden Spuren belegt: 1.0 → 2.0 (1.0) und 2.5 → 3.5 (1.0), zusammen 2.0; vier Ereignisse (Abgang 2.0, Ankunft 2.5, Abgänge 3.5 und 5.0)."""
    res = S.advance(1.0, [2.0, 5.0], 3, 2, 1.0, "exp", ScriptedRng(exp_values=[1.5, 100.0]), ScriptedRng(exp_values=[1.0]))
    assert not res.success and res.clock == 5.0 and res.time_at_c == pytest.approx(2.0) and res.events == 4


def test_blocked_arrivals_do_not_change_the_state_but_count_as_time_at_c():
    """c = 1, Teilchen [4.0] bei Uhr 0: Ankünfte bei 1.0 und 2.0 gehen verloren (Gate voll), der Abgang bei 4.0 leert das Gate: Zeit bei c = 4.0."""
    res = S.advance(0.0, [4.0], 2, 1, 1.0, "exp", ScriptedRng(exp_values=[1.0, 1.0, 100.0]), ScriptedRng(exp_values=[]))
    assert not res.success and res.time_at_c == pytest.approx(4.0) and res.events == 3


def test_advance_does_not_modify_the_given_state():
    busy = [2.0, 5.0]
    S.advance(0.0, busy, 3, 2, 1.0, "exp", ScriptedRng(exp_values=[1.0, 100.0]), ScriptedRng(exp_values=[1.0]))
    assert busy == [2.0, 5.0]


# ---------------------------------------------------------------- Einheit: Stufe, Busy Period, Stufenliste

def test_run_stage_by_hand():
    """Zwei Teilchen aus demselben Zustand ([5.0] bei Uhr 0, Wurzel 0): beide ziehen die Zwischenankunft 1.0 und Dauer 3.0 → beide erreichen Stufe 2."""
    states = [(0.0, [5.0], 0)]
    gap, svc, pick = ScriptedRng(exp_values=[1.0, 1.0]), ScriptedRng(exp_values=[3.0, 3.0]), ScriptedRng(uniform_values=[0.0, 0.9])
    succ, new_states, events = S.run_stage(states, 2, 2, 2, 1.0, "exp", gap, svc, pick)
    assert succ == 2 and events == 2 and all(root == 0 and sorted(busy) == [4.0, 5.0] for _, busy, root in new_states)


def test_busy_period_mean_by_hand():
    """c = 1: Dauer 2.0, danach Ankunft erst bei 5.0 → Busy Period 2.0."""
    mean, events = S.busy_period_mean(1, 1, 1.0, "exp", ScriptedRng(exp_values=[5.0]), ScriptedRng(exp_values=[2.0]))
    assert mean == pytest.approx(2.0) and events == 1


@pytest.mark.parametrize("kind", C.KINDS)
def test_busy_period_matches_the_exact_value_for_every_distribution(kind):
    """E[Busy Period] = (1/π_0 − 1)/a gilt für jede Dauer mit Mittel 1 (Insensitivität)."""
    gap, svc, _ = S.streams(5)
    mean, _ = S.busy_period_mean(40_000, 5, 3.0, kind, gap, svc)
    assert mean == pytest.approx(F.expected_busy_period(5, 3.0), rel=0.04)


def test_default_levels_by_hand():
    assert S.default_levels(10) == list(range(1, 11)) and S.default_levels(10, 3) == [1, 4, 7, 10]
    assert S.default_levels(10, 4) == [1, 5, 9, 10] and S.default_levels(10, 20) == [1, 10] and S.default_levels(2) == [1, 2]


# ---------------------------------------------------------------- gewöhnliche Simulation

def test_plain_estimate_by_hand():
    """c = 1, Ankünfte bei 1.0 (Dauer 2.0, Abgang 3.0), 1.5 und 1.7 (beide verloren): Verlust 2/3, drei Ereignisse (der Abgang bei 3.0 liegt nach dem Lauf)."""
    res = S.plain_estimate(1, 1.0, "exp", 3, 0, rngs=(ScriptedRng(exp_values=[1.0, 0.5, 0.2]), ScriptedRng(exp_values=[2.0]), None))
    assert (res.arrivals, res.lost, res.events) == (3, 2, 3) and res.blocking() == pytest.approx(2 / 3)


def test_plain_estimate_matches_erlang_b_for_moderate_loss():
    res = S.plain_estimate(10, 8.0, "exp", 300_000, 11)
    assert res.blocking() == pytest.approx(F.erlang_b(10, 8.0), rel=0.04)
    assert res.arrivals <= res.events <= 2 * res.arrivals


def test_plain_estimate_sees_nothing_for_a_very_rare_event():
    """c = 20, a = 3: B = 7·10⁻¹¹; 200 000 Ankünfte zählen keinen einzigen Verlust."""
    assert S.plain_estimate(20, 3.0, "exp", 200_000, 3).lost == 0


# ---------------------------------------------------------------- Splitting gegen die exakte Referenz

def test_stage_probabilities_match_the_exact_gamblers_ruin_values():
    """Jede Stufenwahrscheinlichkeit gegen S(lo)/S(hi) (unabhängige Formel, in test_formulas gegen ein lineares System geprüft)."""
    r = S.splitting_estimate(6, 2.0, "exp", 20_000, 7)
    exact = [F.stage_probability(lo, hi, 2.0) for lo, hi in zip(r.levels[:-1], r.levels[1:])]
    assert r.stage_p == pytest.approx(exact, abs=0.02)


def test_stage_probabilities_with_coarser_levels_match_too():
    r = S.splitting_estimate(8, 2.0, "exp", 20_000, 7, step=3)
    assert r.levels == [1, 4, 7, 8]
    exact = [F.stage_probability(lo, hi, 2.0) for lo, hi in zip(r.levels[:-1], r.levels[1:])]
    assert r.stage_p == pytest.approx(exact, abs=0.02)


def test_final_stage_time_and_cycle_match_the_exact_values():
    r = S.splitting_estimate(5, 3.0, "exp", 20_000, 9)
    assert r.time_at_c == pytest.approx(F.expected_time_at_c(5, 3.0), rel=0.05)
    assert r.cycle == pytest.approx(F.expected_cycle_length(5, 3.0), rel=0.04)
    assert r.reach == pytest.approx(F.reach_probability(5, 3.0), rel=0.05)


@pytest.mark.parametrize("kind", C.KINDS)
def test_splitting_is_unbiased_for_every_distribution(kind):
    """Der Verlust (Erlang B, für jede Dauer gleich): Mittel aus 8 Läufen mit 1500 Teilchen je Stufe innerhalb von 8 % (c = 8, a = 3)."""
    exact = F.erlang_b(8, 3.0)
    ests = [S.splitting_estimate(8, 3.0, kind, 1500, 100 + 17 * r).estimate for r in range(8)]
    assert sum(ests) / len(ests) == pytest.approx(exact, rel=0.08)


def test_splitting_finds_what_plain_simulation_misses():
    """c = 15, a = 3: B = 5.5·10⁻⁷. Splitting (N = 1000) trifft den Wert auf einen Faktor 3, gewöhnliche Simulation mit gleichem Budget zählt keinen Verlust."""
    split = S.splitting_estimate(15, 3.0, "exp", 1000, 21)
    plain = S.plain_estimate(15, 3.0, "exp", split.events // 2, 21)
    assert F.erlang_b(15, 3.0) / 3 < split.estimate < F.erlang_b(15, 3.0) * 3 and plain.lost == 0


# ---------------------------------------------------------------- Invarianten

def test_result_invariants():
    r = S.splitting_estimate(10, 3.0, "exp", 800, 4)
    assert r.levels == list(range(1, 11)) and len(r.stage_p) == len(r.successes) == 9 and len(r.roots) == 10
    assert r.roots[0] == 800 and all(a >= b for a, b in zip(r.roots, r.roots[1:]))        # Wurzeln können nur verschwinden
    assert all(0 <= s <= 800 for s in r.successes) and all(abs(p - s / 800) < 1e-12 for p, s in zip(r.stage_p, r.successes))
    assert r.reach == pytest.approx(__import__("math").prod(r.stage_p)) and r.events > 0
    assert r.estimate == pytest.approx(r.reach * r.time_at_c / r.cycle)


def test_a_dying_run_returns_zero_and_says_where():
    """Bei winziger Last (a = 0.01) überlebt kein Teilchen die erste Stufe: Schätzwert 0, `died_at` = 1."""
    r = S.splitting_estimate(4, 0.01, "exp", 5, 1)
    assert r.estimate == 0.0 and r.died_at == 1 and r.reach == 0.0


def test_same_seed_same_result_and_different_seed_differs():
    a, b, c = (S.splitting_estimate(8, 3.0, "exp", 300, s) for s in (5, 5, 6))
    assert a == b and a.estimate != c.estimate
    assert S.plain_estimate(5, 3.0, "exp", 20_000, 5) == S.plain_estimate(5, 3.0, "exp", 20_000, 5)
