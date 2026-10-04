"""Formeln: Erlang B, Spielerruin-Stufenwahrscheinlichkeiten (von Hand und gegen ein lineares System), regenerative Zerlegung (der Verlust ergibt sich
aus Zyklus-Größen), Aufwand der gewöhnlichen Simulation."""

import math

import numpy as np
import pytest

import spl_formulas as F


def test_erlang_b_by_hand():
    assert F.erlang_b(1, 1.0) == pytest.approx(0.5) and F.erlang_b(2, 1.0) == pytest.approx(0.2)
    assert F.erlang_b(3, 2.0) == pytest.approx((8 / 6) / (1 + 2 + 2 + 8 / 6))
    assert F.erlang_b(10, 3.0) == pytest.approx(8.1038808585e-4, rel=1e-8)


def test_ruin_weight_by_hand():
    """S(m) = Σ_{j<m} j!/a^j: für a = 2: S(1) = 1, S(2) = 1 + 1/2, S(3) = 1 + 1/2 + 2/4, S(4) = 1 + 1/2 + 2/4 + 6/8."""
    assert [F.ruin_weight(m, 2.0) for m in (1, 2, 3, 4)] == pytest.approx([1.0, 1.5, 2.0, 2.75])


def test_stage_probability_by_hand_and_bounds():
    """Von einer Belegten zu zwei vor leer (c ≥ 2): a/(a + 1) – die Ankunft kommt vor dem Abgang; für a = 3 sind das 0.75."""
    assert F.stage_probability(1, 2, 3.0) == pytest.approx(0.75)
    assert F.stage_probability(2, 3, 2.0) == pytest.approx(1.5 / 2.0)               # S(2)/S(3)
    for lo, hi in ((1, 5), (3, 4), (2, 9)):
        assert 0 < F.stage_probability(lo, hi, 3.0) < 1
    with pytest.raises(ValueError):
        F.stage_probability(3, 3, 2.0)


def test_stage_probabilities_multiply_across_stages():
    """Spielerruin: P_lo(hi vor leer) = Π der Einzelstufen (Markov-Eigenschaft)."""
    a = 3.0
    chain = math.prod(F.stage_probability(i, i + 1, a) for i in range(1, 8))
    assert F.stage_probability(1, 8, a) == pytest.approx(chain, rel=1e-12)
    assert F.reach_probability(8, a) == pytest.approx(chain, rel=1e-12)


def test_stage_probabilities_against_a_linear_solve():
    """Unabhängige Gegenprobe: Erreichwahrscheinlichkeit der Geburts-Sterbe-Kette (Geburt a, Tod j) als lineares System h_j = (a h_{j+1} + j h_{j−1})/(a + j)."""
    a, c = 2.5, 6
    n = c + 1
    m = np.zeros((n, n))
    rhs = np.zeros(n)
    m[0, 0] = 1.0                                           # h_0 = 0 (leer)
    m[c, c] = 1.0
    rhs[c] = 1.0                                            # h_c = 1 (Ziel erreicht)
    for j in range(1, c):
        m[j, j] = a + j
        m[j, j + 1] = -a
        m[j, j - 1] = -j
    h = np.linalg.solve(m, rhs)
    for j in range(1, c):
        assert F.ruin_weight(j, a) / F.ruin_weight(c, a) == pytest.approx(h[j], rel=1e-10)


def test_regenerative_decomposition_reproduces_erlang_b():
    """π_c = P(erreicht c) · h / E[Zyklus] ergibt Erlang B (drei Größen aus dem Spielerruin, E[Zyklus] = 1/(a π_0))."""
    for c, a in ((5, 2.0), (10, 3.0), (20, 3.0), (25, 8.0)):
        got = F.reach_probability(c, a) * F.expected_time_at_c(c, a) / F.expected_cycle_length(c, a)
        assert got == pytest.approx(F.erlang_b(c, a), rel=1e-10), (c, a)


def test_cycle_and_busy_period_by_hand():
    """c = 1, a = 1: π_0 = 1/2, E[Zyklus] = 2, Busy Period = 1 (eine Abfertigung, Mittel 1)."""
    assert F.idle_probability(1, 1.0) == pytest.approx(0.5) and F.expected_cycle_length(1, 1.0) == pytest.approx(2.0)
    assert F.expected_busy_period(1, 1.0) == pytest.approx(1.0)
    assert F.expected_time_at_c(1, 1.0) == pytest.approx(1.0)                        # eine Belegte, c = 1: Zeit bis zum Leerwerden = eine Dauer


def test_plain_effort_formula():
    """Für ±10 % braucht die gewöhnliche Simulation etwa 100/B Ankünfte (genau (1 − B)/(B·0.01))."""
    assert F.plain_arrivals_needed(0.01) == pytest.approx(9900.0) and F.plain_events_needed(0.01) == pytest.approx(19800.0)
    assert F.plain_arrivals_needed(1e-6) == pytest.approx(1e8, rel=1e-4)
    assert F.plain_arrivals_needed(0.01, 0.5) == pytest.approx(396.0)
    assert F.plain_arrivals_needed(1e-9) > F.plain_arrivals_needed(1e-6) * 900


def test_invalid_input_is_rejected():
    with pytest.raises(ValueError):
        F.erlang_b(-1, 1.0)
