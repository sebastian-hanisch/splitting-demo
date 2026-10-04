"""Formeln zum Verlustsystem mit seltenem Verlust und zur Zerlegung für Multilevel-Splitting: c Spuren ohne Warteraum, Ankünfte Poisson mit
Angebot a (Erlang, mittlere Abfertigungsdauer 1), wer bei c Belegten ankommt, geht verloren.

**Verlust** B = Erlang B(c, a) (gilt für jede Verteilung der Dauer, Stück 8), Rekursion B_j = a·B_{j−1}/(j + a·B_{j−1}).

**Regenerative Zerlegung** (für exponentielle Dauer exakt, Referenz der Tests): Ein Zyklus beginnt, wenn das Gate leer wird, und endet beim
nächsten Leerwerden. Es gilt π_c = E[Zeit mit c Belegten je Zyklus] / E[Zykluslänge], E[Zykluslänge] = 1/(a·π_0), und
E[Zeit bei c je Zyklus] = P(Zyklus erreicht c) · h mit h = E[Zeit bei c | erreicht].

**Stufenwahrscheinlichkeiten** (Geburts-Sterbe-Kette der Belegten, Geburtsrate a, Sterberate j): P_lo(erreicht hi vor leer) = S(lo)/S(hi) mit
S(m) = Σ_{j=0}^{m−1} j!/a^j (Spielerruin). Damit P(Zyklus erreicht c) = 1/S(c) (Start bei einer Belegten) und h = π_c/(a·π_0·P)
= (a^{c−1}/c!)·S(c)."""

import math


def erlang_b(c, a):
    """Erlang-B-Verlustwahrscheinlichkeit über die stabile Rekursion B_j = a·B_{j−1}/(j + a·B_{j−1})."""
    if c < 0 or a < 0:
        raise ValueError("c und a müssen nicht negativ sein")
    b = 1.0
    for j in range(1, c + 1):
        b = a * b / (j + a * b)
    return b


def ruin_weight(m, a):
    """S(m) = Σ_{j=0}^{m−1} j!/a^j (Spielerruin der Belegten-Kette; S(1) = 1)."""
    total, term = 0.0, 1.0
    for j in range(m):
        if j > 0:
            term *= j / a
        total += term
    return total


def stage_probability(lo, hi, a):
    """P(von `lo` Belegten `hi` Belegte erreichen, bevor das Gate leer ist) bei exponentieller Dauer: S(lo)/S(hi)."""
    if not 1 <= lo < hi:
        raise ValueError("1 ≤ lo < hi erwartet")
    return ruin_weight(lo, a) / ruin_weight(hi, a)


def reach_probability(c, a):
    """P(ein Zyklus erreicht c Belegte) bei exponentieller Dauer, Start bei einer Belegten: 1/S(c)."""
    return 1.0 / ruin_weight(c, a)


def idle_probability(c, a):
    """π_0 des Verlustsystems (exponentiell): 1/Σ_{j≤c} a^j/j!."""
    return 1.0 / sum(a ** j / math.factorial(j) for j in range(c + 1))


def expected_cycle_length(c, a):
    """E[Zykluslänge] = 1/(a·π_0) (Leerlauf 1/a plus Busy Period); gilt für jede Dauer mit Mittel 1 (Insensitivität)."""
    return 1.0 / (a * idle_probability(c, a))


def expected_busy_period(c, a):
    """E[Busy Period] = E[Zykluslänge] − 1/a."""
    return expected_cycle_length(c, a) - 1.0 / a


def expected_time_at_c(c, a):
    """h = E[Zeit mit c Belegten bis zum Leerwerden | Gate erreicht c] bei exponentieller Dauer: (a^{c−1}/c!)·S(c)."""
    return a ** (c - 1) / math.factorial(c) * ruin_weight(c, a)


def plain_arrivals_needed(b, rel_sd=0.10):
    """Ankünfte, die die gewöhnliche Simulation für die relative Standardabweichung `rel_sd` braucht: Var ≈ 1/(n·B), also n = 1/(B·rel_sd²)."""
    return (1.0 - b) / (b * rel_sd ** 2)


def plain_events_needed(b, rel_sd=0.10):
    """Dasselbe in Ereignissen (je Ankunft eine Ankunft und ein Abgang): 2·n."""
    return 2.0 * plain_arrivals_needed(b, rel_sd)
