"""JEDE Zahl aus README und App-Texten wird hier nachgerechnet: Formelwerte exakt, Studien-Zahlen aus der vorgerechneten Datei (Angebot 3 Erlang, je 16 Läufe je
Zelle, Splitting mit 250 / 1000 / 4000 Teilchen je Stufe). Die Datei ist fest; ändern sich die Zahlen nach einer neuen Rechnung, müssen README und Hilfetexte
nachgezogen werden."""

import pytest

import spl_constants as C
import spl_evaluation as E
import spl_formulas as F

PRE = E.load_precomputed()


def cell(c, n, kind="exp"):
    return E.study_cell(PRE, c, n, kind)


def pct(x):
    return round(100 * x)


def test_exact_losses_quoted_in_readme():
    """README (Angebot 3 Erlang): Verlust bei 10 / 15 / 20 / 25 / 30 Spuren 8.1·10⁻⁴ / 5.5·10⁻⁷ / 7.1·10⁻¹¹ / 2.7·10⁻¹⁵ / 3.9·10⁻²⁰."""
    assert [C.fmt_sci(F.erlang_b(c, 3.0)) for c in C.STUDY_C] == ["8.1·10⁻⁴", "5.5·10⁻⁷", "7.1·10⁻¹¹", "2.7·10⁻¹⁵", "3.9·10⁻²⁰"]
    assert C.fmt_sci(F.erlang_b(20, 3.0)).startswith("7.1") and round(1 / F.erlang_b(20, 3.0) / 1e9) == 14           # einer von 14 Milliarden


def test_plain_simulation_sees_nothing_when_it_is_rare():
    """README: Gewöhnliche Simulation, Läufe ohne einen einzigen Verlust von 16: bei 10 Spuren 0 / 0 (Budget 400 000 / 4 000 000 Ereignisse), bei 15 Spuren 13 / 5,
    bei 20 Spuren 16 / 16; Mittel/exakt bei 10 Spuren 1.02 / 1.00, bei 15 Spuren 2.29 / 1.26."""
    z = {(p["c"], p["budget"]): p["zeros"] for p in PRE["plain"]}
    assert z == {(10, 400_000): 0, (10, 4_000_000): 0, (15, 400_000): 13, (15, 4_000_000): 5, (20, 400_000): 16, (20, 4_000_000): 16}
    bias = {(p["c"], p["budget"]): E.cell_bias(p) for p in PRE["plain"]}
    assert [round(bias[k], 2) for k in ((10, 400_000), (10, 4_000_000), (15, 400_000), (15, 4_000_000))] == [1.02, 1.00, 2.29, 1.26]


def test_plain_losses_come_in_groups_so_the_poisson_formula_is_a_lower_bound():
    """README: Die Varianz der Verlustzahl der gewöhnlichen Simulation beträgt bei 10 Spuren das 1.5-fache (400 000 Ereignisse) bzw. 1.8-fache (4 000 000) des Poisson-
    Werts (= Mittel)."""
    out = []
    for p in PRE["plain"]:
        if p["c"] != 10:
            continue
        n = p["budget"] // 2
        counts = [round(e * n) for e in p["estimates"]]
        m, sd = E.mean_and_sd(counts)
        out.append(round(sd ** 2 / m, 1))
    assert out == [1.5, 1.8]


def test_splitting_is_unbiased_and_precise_at_moderate_rarity():
    """README (10 Spuren, Verlust 8.1·10⁻⁴): in allen sechs Zellen (3 Teilchenzahlen × exponentiell/fest) Mittel/exakt 0.95 bis 1.02, relative Streuung eines Laufs
    5 % bis 20 %."""
    cells = [cell(10, n, k) for n in C.STUDY_N for k in C.STUDY_KINDS]
    biases, sds = [E.cell_bias(x) for x in cells], [E.cell_rel_sd(x) for x in cells]
    assert (round(min(biases), 2), round(max(biases), 2)) == (0.95, 1.02) and (pct(min(sds)), pct(max(sds))) == (5, 20)


def test_more_particles_lower_the_spread_up_to_fifteen_lanes():
    """README: Bis 15 Spuren sinkt die Streuung mit der Teilchenzahl in allen vier Reihen (10 und 15 Spuren × exponentiell und fest); 15 Spuren exponentiell:
    85 / 58 / 17 % bei 250 / 1000 / 4000 Teilchen."""
    for c in (10, 15):
        for kind in C.STUDY_KINDS:
            sds = [E.cell_rel_sd(cell(c, n, kind)) for n in C.STUDY_N]
            assert sds[0] > sds[1] > sds[2], (c, kind)
    assert [pct(E.cell_rel_sd(cell(15, n))) for n in C.STUDY_N] == [85, 58, 17]


def test_splitting_at_fifteen_lanes_with_4000_particles():
    """README (Verlust 5.5·10⁻⁷): 4000 Teilchen: Mittel/exakt exponentiell 0.94 (Streuung 17 %), fest 1.00 (22 %); 250 Teilchen exponentiell 1.66."""
    assert (round(E.cell_bias(cell(15, 4000)), 2), pct(E.cell_rel_sd(cell(15, 4000)))) == (0.94, 17)
    assert (round(E.cell_bias(cell(15, 4000, "det")), 2), pct(E.cell_rel_sd(cell(15, 4000, "det")))) == (1.00, 22)
    assert round(E.cell_bias(cell(15, 250)), 2) == 1.66


def test_splitting_becomes_unreliable_for_very_rare_events():
    """README (4000 Teilchen): Mittel/exakt (Streuung) exponentiell bei 20 / 25 / 30 Spuren 0.79 (41 %) / 2.23 (281 %) / 0.61 (156 %), fest 0.84 (42 %) / 1.11 (116 %) /
    1.02 (131 %). Die Streuung steigt von 10 bis 25 Spuren (exponentiell 5 / 17 / 41 / 281 %)."""
    got = {(c, k): (round(E.cell_bias(cell(c, 4000, k)), 2), pct(E.cell_rel_sd(cell(c, 4000, k)))) for c in (20, 25, 30) for k in C.STUDY_KINDS}
    assert got == {(20, "exp"): (0.79, 41), (25, "exp"): (2.23, 281), (30, "exp"): (0.61, 156),
                   (20, "det"): (0.84, 42), (25, "det"): (1.11, 116), (30, "det"): (1.02, 131)}
    assert [pct(E.cell_rel_sd(cell(c, 4000))) for c in (10, 15, 20, 25)] == [5, 17, 41, 281]


def test_ancestor_lines_degenerate_with_rarity():
    """README: Verschiedene Wurzeln auf der letzten Stufe (von 4000 bzw. 1000 Teilchen, exponentiell) bei 10 / 15 / 20 / 25 / 30 Spuren: 400 / 119 / 36 / 12 / 5 (4000)
    und 104 / 29 / 10 / 3.5 / 2.2 (1000); bei 4000 Teilchen und 30 Spuren 0.13 % der Wurzeln."""
    assert [round(cell(c, 4000)["roots"][-1]) for c in C.STUDY_C] == [400, 119, 36, 12, 5]
    assert [round(cell(c, 1000)["roots"][-1], 1) for c in C.STUDY_C] == [103.6, 28.6, 9.7, 3.5, 2.2]
    assert round(100 * cell(30, 4000)["roots"][-1] / 4000, 2) == 0.13
    for c in C.STUDY_C:
        roots = cell(c, 1000)["roots"]
        assert roots[0] == 1000 and all(a >= b for a, b in zip(roots, roots[1:]))


def test_effort_comparison_quoted_in_readme():
    """README: Für ±10 % bräuchte die gewöhnliche Simulation bei 15 Spuren 3.7·10⁸ Ereignisse, Splitting (4000 Teilchen, exponentiell) 5.3·10⁶, also das 69-fache weniger
    (fest 56-fach); bei 20 Spuren 2.8·10¹² gegen 5.7·10⁷ (4.9·10⁴-fach, fest 7.2·10⁴); bei 10 Spuren nur das 1.1- bis 2.1-fache (alle sechs Zellen)."""
    ratio = lambda x: F.plain_events_needed(x["exact"]) / E.effort_for_target(x)
    assert C.fmt_sci(F.plain_events_needed(F.erlang_b(15, 3.0))) == "3.7·10⁸" and C.fmt_sci(E.effort_for_target(cell(15, 4000))) == "5.3·10⁶"
    assert (round(ratio(cell(15, 4000))), round(ratio(cell(15, 4000, "det")))) == (69, 56)
    assert C.fmt_sci(F.plain_events_needed(F.erlang_b(20, 3.0))) == "2.8·10¹²" and C.fmt_sci(E.effort_for_target(cell(20, 4000))) == "5.7·10⁷"
    assert (C.fmt_sci(ratio(cell(20, 4000)), 1), C.fmt_sci(ratio(cell(20, 4000, "det")), 1)) == ("4.9·10⁴", "7.2·10⁴")
    r10 = [ratio(cell(10, n, k)) for n in C.STUDY_N for k in C.STUDY_KINDS]
    assert (round(min(r10), 1), round(max(r10), 1)) == (1.1, 2.1)


def test_step_study_quoted_in_readme():
    """README (20 Spuren, 2000 Teilchen, exponentiell, 16 Läufe): Stufenabstand 1 / 2 / 3 / 5 / 8: Stufen 20 / 11 / 8 / 5 / 4, Läufe ohne Treffer 0 / 0 / 0 / 8 / 16,
    Mittel/exakt 1.09 / 1.47 / 0.48 / 0.71 / 0, Ereignisse je Lauf 1.67 / 1.16 / 0.92 / 0.46 / 0.21 Mio."""
    cells = [E.step_cell(PRE, s) for s in C.STUDY_STEPS]
    assert [len(x["levels"]) for x in cells] == [20, 11, 8, 5, 4] and [x["zeros"] for x in cells] == [0, 0, 0, 8, 16]
    assert [round(E.cell_bias(x), 2) for x in cells] == [1.09, 1.47, 0.48, 0.71, 0.0]
    assert [round(E.cell_mean_events(x) / 1e6, 2) for x in cells] == [1.67, 1.16, 0.92, 0.46, 0.21]
    ev = [E.cell_mean_events(x) for x in cells]
    assert all(a > b for a, b in zip(ev, ev[1:]))                      # größerer Abstand kostet weniger Ereignisse


def test_preset_help_numbers():
    """PRESET_HELP: jede Zahl aus den vier Texten (siehe spl_constants)."""
    h = C.PRESET_HELP
    t = h["Mäßig selten (10 Spuren)"]
    x = cell(10, 1000)
    assert "8.1·10⁻⁴" in t and f"{pct(E.cell_bias(x) - 1)} %" in t and f"{pct(E.cell_rel_sd(x))} %" in t and "0 von 16" in t
    t = h["Selten (15 Spuren)"]
    x = cell(15, 4000)
    assert "5.5·10⁻⁷" in t and f"{E.cell_bias(x):.2f}" in t and f"{pct(E.cell_rel_sd(x))} %" in t and "13 von 16" in t
    t = h["Sehr selten (20 Spuren)"]
    x = cell(20, 4000)
    assert "7.1·10⁻¹¹" in t and f"{E.cell_bias(x):.2f}" in t and f"{pct(E.cell_rel_sd(x))} %" in t and "16 Läufen" in t
    t = h["Zu selten (30 Spuren)"]
    x = cell(30, 1000)
    assert "3.9·10⁻²⁰" in t and f"{pct(E.cell_rel_sd(x))} %" in t and f"{x['roots'][-1]:.1f}" in t


def test_default_live_run_numbers():
    """README: Standardlauf (15 Spuren, Angebot 3, 1000 Teilchen, Seed 35): Splitting 4.3·10⁻⁷ (0.78 des exakten Werts) mit 505 508 Ereignissen, 26 Wurzeln auf
    der letzten Stufe (217 überlebende Teilchen); die gewöhnliche Simulation zählt 3 Verluste in 252 754 Ankünften (1.2·10⁻⁵, 22-fach zu hoch; erwartet 0.14)."""
    r = E.live_report(15, 3.0, "exp", 1000, 35)
    s, p = r["split"], r["plain"]
    assert C.fmt_sci(s.estimate) == "4.3·10⁻⁷" and round(s.estimate / r["exact"], 2) == 0.78 and s.events == 505_508
    assert (s.roots[-1], s.successes[-1]) == (26, 217) and (p.lost, p.arrivals) == (3, 252_754)
    assert C.fmt_sci(p.blocking()) == "1.2·10⁻⁵" and round(p.blocking() / r["exact"]) == 22 and round(p.arrivals * r["exact"], 2) == 0.14


def test_the_sign_of_the_bias_changes_for_very_rare_events():
    """README: Bei 20 Spuren und mehr liegt das Mittel aus 16 Läufen mal unter, mal über dem exakten Wert (Vorab-Messreihe 0.16, Studie 0.61 bei 4000 und 1.35 bei 1000 Teilchen
    für 30 Spuren exponentiell)."""
    biases = [E.cell_bias(cell(c, n, k)) for c in (20, 25, 30) for n in C.STUDY_N for k in C.STUDY_KINDS]
    assert any(b < 0.9 for b in biases) and any(b > 1.1 for b in biases)
    assert round(E.cell_bias(cell(30, 1000)), 2) == 1.35 and round(E.cell_bias(cell(30, 4000)), 2) == 0.61
