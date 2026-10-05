"""Orakel-Tests (Kampagne E3): Stufenwahrscheinlichkeiten, Zeit bei c, Zykluslänge und Erlang B gegen eine unabhängige Rechnung in exakten Brüchen
(lineare Gleichungssysteme der Geburts-Sterbe-Kette der Belegten, Gauß-Elimination mit `fractions.Fraction`, nicht die Spielerruin-Formel der Demo);
Unverzerrtheit des Splitting-Schätzers über feste Zufalls-Seeds mit z-Band statt Gleichheit; Randfälle (kleinste Spurenzahl, grobe Stufen)."""

import math
from fractions import Fraction

import pytest

import spl_constants as C
import spl_formulas as F
import spl_simulation as S


# ---------------------------------------------------------------- Orakel: Kette der Belegten in exakten Brüchen

def _solve(matrix, rhs):
    """Lineares System A x = b mit Fraction-Gauß-Elimination (Pivotsuche auf Nicht-Null)."""
    n = len(rhs)
    m = [row[:] + [b] for row, b in zip(matrix, rhs)]
    for col in range(n):
        piv = next(r for r in range(col, n) if m[r][col] != 0)
        m[col], m[piv] = m[piv], m[col]
        m[col] = [v / m[col][col] for v in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col]
                m[r] = [x - f * y for x, y in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


def _chain_system(c, a, cost):
    """Unbekannte x_1 … x_c (x_0 = 0 absorbiert): x_k = cost_k + (a·x_{k+1} + k·x_{k−1}) / (a + k)
    für k < c, bei k = c nur Abgänge (Ankünfte gehen verloren): x_c = cost_c + x_{c−1}. Gibt Matrix und rechte Seite zurück."""
    mat = [[Fraction(0)] * c for _ in range(c)]
    rhs = []
    for k in range(1, c + 1):
        row = mat[k - 1]
        row[k - 1] = Fraction(1)
        if k < c:
            up, down = a / (a + k), Fraction(k) / (a + k)
            row[k] -= up
            if k > 1:
                row[k - 2] -= down
        elif k > 1:
            row[k - 2] -= 1
        rhs.append(cost(k))
    return mat, rhs


def _hit_probability(lo, hi, a):
    """P(von lo Belegten hi erreichen, bevor das Gate leer ist) als lineares System (h_0 = 0, h_hi = 1), unabhängig von S(lo)/S(hi)."""
    a = Fraction(a)
    n = hi - 1                                     # Unbekannte h_1 … h_{hi−1}
    mat = [[Fraction(0)] * n for _ in range(n)]
    rhs = [Fraction(0)] * n
    for k in range(1, hi):
        mat[k - 1][k - 1] = a + k
        if k + 1 < hi:
            mat[k - 1][k] -= a
        else:
            rhs[k - 1] += a                        # h_hi = 1
        if k > 1:
            mat[k - 1][k - 2] -= k
    return _solve(mat, rhs)[lo - 1]


def _busy_period_and_time_at_c(c, a):
    """(E[Busy Period ab einer Belegten], E[Zeit mit c Belegten bis leer ab einer Belegten]) aus je einem linearen System."""
    a = Fraction(a)
    mat, rhs = _chain_system(c, a, lambda k: 1 / (a + k) if k < c else Fraction(1, c))
    busy = _solve(mat, rhs)[0]
    mat, rhs = _chain_system(c, a, lambda k: Fraction(0) if k < c else Fraction(1, c))
    return busy, _solve(mat, rhs)[0]


def _erlang_b_exact(c, a):
    a = Fraction(a)
    return (a ** c / math.factorial(c)) / sum(a ** j / math.factorial(j) for j in range(c + 1))


A_GRID = (Fraction(1, 2), Fraction(2), Fraction(3), Fraction(5), Fraction(8))


def test_oracle_itself_on_a_hand_example():
    """c = 2, a = 1 von Hand: Erlang B = (1/2)/(1 + 1 + 1/2) = 1/5; P(1 → 2 vor leer) = 1/2; aus t_1 = 1/2 + t_2/2, t_2 = 1/2 + t_1 folgt
    Busy Period 3/2 (Zykluslänge 5/2); aus u_1 = u_2/2, u_2 = 1/2 + u_1 folgt Zeit bei 2 gleich 1/2; Verlust 1/2 : 5/2 = 1/5."""
    assert _erlang_b_exact(2, 1) == Fraction(1, 5)
    assert _hit_probability(1, 2, 1) == Fraction(1, 2)
    assert _busy_period_and_time_at_c(2, 1) == (Fraction(3, 2), Fraction(1, 2))


# ---------------------------------------------------------------- Formeln: exakt gegen die Bruchrechnung

@pytest.mark.parametrize("a", A_GRID)
def test_stage_probabilities_match_the_exact_linear_system(a):
    for hi in (2, 3, 6, 11):
        for lo in range(1, hi):
            exact = _hit_probability(lo, hi, a)
            assert F.stage_probability(lo, hi, float(a)) == pytest.approx(float(exact), rel=1e-12), (lo, hi, a)


@pytest.mark.parametrize("c", (5, 8, 15, 30))
def test_loss_cycle_time_at_c_and_reach_match_the_exact_chain(c):
    a = Fraction(3)
    busy, at_c = _busy_period_and_time_at_c(c, a)
    cycle = 1 / a + busy
    assert F.erlang_b(c, 3.0) == pytest.approx(float(_erlang_b_exact(c, a)), rel=1e-12)
    assert at_c / cycle == _erlang_b_exact(c, a)                                # zwei Rechenwege, exakt gleich
    assert F.expected_cycle_length(c, 3.0) == pytest.approx(float(cycle), rel=1e-12)
    assert F.expected_busy_period(c, 3.0) == pytest.approx(float(busy), rel=1e-12)
    reach = _hit_probability(1, c, a)
    assert F.reach_probability(c, 3.0) == pytest.approx(float(reach), rel=1e-12)
    assert F.expected_time_at_c(c, 3.0) * F.reach_probability(c, 3.0) == pytest.approx(float(at_c), rel=1e-12)


def test_product_of_stage_probabilities_is_the_reach_probability():
    """Π p(levels[i] → levels[i+1]) gilt für jede Stufenfolge (Markov-Eigenschaft), hier mit exakten Brüchen für Schrittweite 1, 2, 3 und 5."""
    c, a = 15, Fraction(3)
    for step in (1, 2, 3, 5):
        levels = S.default_levels(c, step)
        prod = Fraction(1)
        for lo, hi in zip(levels[:-1], levels[1:]):
            prod *= _hit_probability(lo, hi, a)
        assert prod == _hit_probability(1, c, a)


# ---------------------------------------------------------------- Splitting: Unverzerrtheit mit z-Band

def _z_of_mean(values, exact):
    n = len(values)
    mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
    return (mean - exact) / (sd / math.sqrt(n))


@pytest.mark.parametrize("kind", C.KINDS)
@pytest.mark.parametrize("c, a", [(5, 3.0), (6, 2.0)])
def test_splitting_estimate_is_unbiased_for_every_distribution(kind, c, a):
    """Erlang B gilt für jede Dauer mit Mittel 1. 24 Läufe mit festen Zufalls-Seeds, N = 150: das Mittel liegt im z-Band (|z| < 4)."""
    exact = float(_erlang_b_exact(c, Fraction(a)))
    ests = [S.splitting_estimate(c, a, kind, 150, 1000 + 31 * r).estimate for r in range(24)]
    assert abs(_z_of_mean(ests, exact)) < 4.0


def test_stage_probabilities_are_unbiased_against_the_exact_values():
    """Mittel von p̂ je Übergang über 40 Läufe gegen die exakte Bruchrechnung, z-Band je Übergang (exponentielle Dauer, c = 6, a = 2, N = 100)."""
    c, a = 6, Fraction(2)
    runs = [S.splitting_estimate(c, 2.0, "exp", 100, 5000 + 13 * r) for r in range(40)]
    levels = runs[0].levels
    for i, (lo, hi) in enumerate(zip(levels[:-1], levels[1:])):
        exact = float(_hit_probability(lo, hi, a))
        assert abs(_z_of_mean([r.stage_p[i] for r in runs], exact)) < 4.0, (lo, hi)


@pytest.mark.parametrize("kind", ("exp", "det"))
def test_final_stage_time_and_cycle_match_the_exact_chain(kind):
    """Zeit bei c (nur exponentiell exakt) und Zykluslänge (für jede Dauer, Insensitivität) gegen die Bruchrechnung, z-Band über 24 Läufe."""
    c, a = 5, Fraction(3)
    busy, at_c = _busy_period_and_time_at_c(c, a)
    runs = [S.splitting_estimate(c, 3.0, kind, 200, 300 + 7 * r) for r in range(24)]
    assert abs(_z_of_mean([r.cycle for r in runs], float(1 / a + busy))) < 4.0
    if kind == "exp":
        h = float(at_c / _hit_probability(1, c, a))
        assert abs(_z_of_mean([r.time_at_c for r in runs], h)) < 4.0


# ---------------------------------------------------------------- Randfälle

def test_smallest_lane_count_and_coarse_levels():
    """c = C_MIN = 5: Stufen 1 … 5; Schrittweite 5 und größer liefert nur [1, 5] (eine Stufe, p̂ gegen die exakte Wahrscheinlichkeit)."""
    assert C.C_MIN == 5 and S.default_levels(C.C_MIN) == [1, 2, 3, 4, 5]
    for step in C.STEP_OPTIONS:
        levels = S.default_levels(C.C_MIN, step)
        assert levels[0] == 1 and levels[-1] == C.C_MIN and levels == sorted(set(levels))
    assert S.default_levels(C.C_MIN, 5) == [1, 5] == S.default_levels(C.C_MIN, 99)
    exact = float(_hit_probability(1, 5, Fraction(3)))
    ps = [S.splitting_estimate(C.C_MIN, 3.0, "exp", 200, 77 + r, step=5).stage_p[0] for r in range(30)]
    assert abs(_z_of_mean(ps, exact)) < 4.0


def test_levels_cover_every_allowed_setting():
    for c in range(C.C_MIN, C.C_MAX + 1, C.C_STEP):
        for step in C.STEP_OPTIONS:
            levels = S.default_levels(c, step)
            assert levels[0] == 1 and levels[-1] == c and all(b > a for a, b in zip(levels, levels[1:]))


def test_rare_event_at_the_largest_lane_count_stays_in_bounds():
    """c = 30, a = 3 (B ≈ 4·10⁻²⁰): kleine Läufe liefern entweder 0 mit `died_at` oder einen Wert > 0; Wahrscheinlichkeiten bleiben in [0, 1]."""
    r = S.splitting_estimate(C.C_MAX, 3.0, "exp", 60, 3)
    assert 0.0 <= r.estimate < 1e-5 and all(0.0 <= p <= 1.0 for p in r.stage_p)
    assert (r.died_at == 0) == (r.estimate > 0.0)
