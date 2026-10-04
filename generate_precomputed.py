"""Rechnet die teure Studie vor (Build-Zeit, nicht in der App): `python generate_precomputed.py [Prozesse]` schreibt
`precomputed_sweep.json`.

  study  Spurzahl × Teilchen je Stufe × Verteilung der Dauer: je 16 Splitting-Läufe (Angebot 3 Erlang); Schätzwerte, Ereignisse, Wurzeln je Stufe
  plain  gewöhnliche Simulation mit zwei Ereignisbudgets (400 000 und 4 000 000), je 16 Läufe
  steps  Stufenabstand 1, 2, 3, 5, 8 bei 20 Spuren und 2000 Teilchen, je 16 Läufe"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import spl_constants as C
from spl_evaluation import PRECOMPUTED_PATH, summarize_split_runs
from spl_formulas import erlang_b
from spl_simulation import plain_estimate, splitting_estimate


def _split_task(args):
    key, c, n, kind, step, seed = args
    return key, splitting_estimate(c, C.STUDY_A, kind, n, seed, step=step)


def _plain_task(args):
    key, c, budget, kind, seed = args
    return key, plain_estimate(c, C.STUDY_A, kind, budget // 2, seed)


def main(workers):
    t0 = time.time()
    jobs, idx = [], 0
    for c in C.STUDY_C:
        for n in C.STUDY_N:
            for kind in C.STUDY_KINDS:
                for r in range(C.STUDY_REPS):
                    jobs.append((("study", c, n, kind, 1), c, n, kind, 1, 10_000 + 97 * idx + 1000 * r))
                idx += 1
    for step in C.STUDY_STEPS:
        for r in range(C.STUDY_REPS):
            jobs.append((("steps", C.STUDY_STEP_C, C.STUDY_STEP_N, "exp", step), C.STUDY_STEP_C, C.STUDY_STEP_N, "exp", step,
                         50_000 + 97 * step + 1000 * r))
    plain_jobs = []
    for c in C.STUDY_PLAIN_C:
        for budget in C.STUDY_PLAIN_BUDGETS:
            for r in range(C.STUDY_REPS):
                plain_jobs.append(((c, budget), c, budget, "exp", 90_000 + 97 * c + 1000 * r))
    jobs.sort(key=lambda j: -(j[1] * j[2]))              # größte Aufträge zuerst, damit die Prozesse gleichmäßig auslasten
    with ProcessPoolExecutor(max_workers=workers) as ex:
        split_out = list(ex.map(_split_task, jobs, chunksize=1))
        plain_out = list(ex.map(_plain_task, plain_jobs, chunksize=1))
    groups = {}
    for key, res in split_out:
        groups.setdefault(key, []).append(res)
    study, steps = [], []
    for (which, c, n, kind, step), runs in groups.items():
        cell = summarize_split_runs(c, n, kind, runs, C.STUDY_A, step)
        (study if which == "study" else steps).append(cell)
    study.sort(key=lambda x: (x["c"], x["n"], x["kind"]))
    steps.sort(key=lambda x: x["step"])
    pgroups = {}
    for key, res in plain_out:
        pgroups.setdefault(key, []).append(res)
    plain = []
    for (c, budget), runs in sorted(pgroups.items()):
        est = [r.blocking() for r in runs]
        plain.append({"c": c, "budget": budget, "kind": "exp", "reps": len(runs), "estimates": est, "zeros": sum(1 for e in est if e == 0.0),
                      "exact": erlang_b(c, C.STUDY_A)})
    out = {"study_a": C.STUDY_A, "study_reps": C.STUDY_REPS, "study": study, "plain": plain, "steps": steps}
    Path(PRECOMPUTED_PATH).write_text(json.dumps(out), encoding="utf-8")
    print(f"fertig in {time.time() - t0:.0f} s -> {PRECOMPUTED_PATH}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else min(6, os.cpu_count() or 1))
