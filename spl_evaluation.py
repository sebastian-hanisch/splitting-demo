"""Auswertung: Live-Lauf (Splitting gegen gewöhnliche Simulation und die exakte Formel), Studienzellen (Wiederholungen: Verzerrung, Streuung, Aufwand,
Entartung der Ahnenreihen), Stufenabstand. Die teure Studie steht vorgerechnet in `precomputed_sweep.json` (Generator: generate_precomputed.py,
Laden: `load_precomputed`)."""

import json
import math
from pathlib import Path

import spl_constants as C
import spl_formulas as F
from spl_simulation import plain_estimate, splitting_estimate

PRECOMPUTED_PATH = Path(__file__).resolve().parent / "precomputed_sweep.json"


def exact_stage_probabilities(levels, a):
    """Exakte Stufenwahrscheinlichkeiten (exponentielle Dauer) für die Übergänge der Stufenliste."""
    return [F.stage_probability(lo, hi, a) for lo, hi in zip(levels[:-1], levels[1:])]


def live_report(c, a, kind, n, seed, step=1):
    """Ein Live-Lauf: Splitting (n Teilchen je Stufe) und gewöhnliche Simulation mit etwa gleichem Ereignisbudget (je Ankunft zwei Ereignisse,
    begrenzt), dazu die exakten Bezugswerte."""
    split = splitting_estimate(c, a, kind, n, seed, step=step)
    arrivals = min(C.PLAIN_ARRIVALS_MAX, max(C.PLAIN_ARRIVALS_MIN, split.events // 2))
    plain = plain_estimate(c, a, kind, arrivals, seed + 99)
    b = F.erlang_b(c, a)
    return {"split": split, "plain": plain, "exact": b, "exact_stage": exact_stage_probabilities(split.levels, a),
            "plain_arrivals_needed": F.plain_arrivals_needed(b, C.TARGET_REL_SD), "plain_events_needed": F.plain_events_needed(b, C.TARGET_REL_SD)}


def mean_and_sd(values):
    """Mittelwert und Stichproben-Standardabweichung (0.0 bei nur einem Wert)."""
    n = len(values)
    m = sum(values) / n
    if n < 2:
        return m, 0.0
    return m, math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1))


def summarize_split_runs(c, n, kind, runs, a=C.STUDY_A, step=1):
    """Eine Studienzelle aus den Läufen `runs` (SplitResult): Schätzwerte, Nullläufe, Ereignisse, mittlere Wurzeln je Stufe."""
    estimates = [r.estimate for r in runs]
    levels = runs[0].levels
    roots = [sum(r.roots[i] if i < len(r.roots) else 0 for r in runs) / len(runs) for i in range(len(levels))]
    stage = [sum(r.stage_p[i] if i < len(r.stage_p) else 0.0 for r in runs) / len(runs) for i in range(len(levels) - 1)]
    return {"c": c, "n": n, "kind": kind, "step": step, "reps": len(runs), "estimates": estimates, "zeros": sum(1 for e in estimates if e == 0.0),
            "events": [r.events for r in runs], "levels": levels, "roots": roots, "stage_p": stage, "exact": F.erlang_b(c, a)}


def study_cell_run(c, n, kind, reps, seed, step=1, a=C.STUDY_A):
    runs = [splitting_estimate(c, a, kind, n, seed + 1000 * r, step=step) for r in range(reps)]
    return summarize_split_runs(c, n, kind, runs, a, step)


def plain_cell_run(c, budget_events, kind, reps, seed, a=C.STUDY_A):
    """Gewöhnliche Simulation mit dem Ereignisbudget `budget_events` (je Ankunft zwei Ereignisse), `reps` Wiederholungen."""
    arrivals = budget_events // 2
    runs = [plain_estimate(c, a, kind, arrivals, seed + 1000 * r) for r in range(reps)]
    estimates = [r.blocking() for r in runs]
    return {"c": c, "budget": budget_events, "kind": kind, "reps": reps, "estimates": estimates, "zeros": sum(1 for e in estimates if e == 0.0),
            "exact": F.erlang_b(c, a)}


def cell_mean(cell):
    return sum(cell["estimates"]) / len(cell["estimates"])


def cell_bias(cell):
    """Mittel der Schätzwerte geteilt durch den exakten Wert (1 = erwartungstreu)."""
    return cell_mean(cell) / cell["exact"]


def cell_rel_sd(cell):
    """Relative Standardabweichung der Schätzwerte eines Laufs (sd/Mittel); nan, wenn das Mittel null ist."""
    m, sd = mean_and_sd(cell["estimates"])
    return sd / m if m > 0 else float("nan")


def cell_mean_events(cell):
    return sum(cell["events"]) / len(cell["events"])


def effort_for_target(cell, rel_sd=C.TARGET_REL_SD):
    """Ereignisse, die das Splitting dieser Zelle für die relative Standardabweichung `rel_sd` bräuchte: mittlere Ereignisse · (sd/rel_sd)²."""
    sd = cell_rel_sd(cell)
    return cell_mean_events(cell) * (sd / rel_sd) ** 2 if sd == sd else float("nan")


def load_precomputed():
    return json.loads(PRECOMPUTED_PATH.read_text(encoding="utf-8"))


def nearest(options, value):
    """Nächster Wert aus `options` (bei Gleichstand der kleinere)."""
    return min(options, key=lambda o: (abs(o - value), o))


def study_cell(pre, c, n, kind):
    for cell in pre["study"]:
        if cell["c"] == c and cell["n"] == n and cell["kind"] == kind:
            return cell
    raise KeyError((c, n, kind))


def plain_cell(pre, c, budget):
    for cell in pre["plain"]:
        if cell["c"] == c and cell["budget"] == budget:
            return cell
    raise KeyError((c, budget))


def step_cell(pre, step):
    for cell in pre["steps"]:
        if cell["step"] == step:
            return cell
    raise KeyError(step)
