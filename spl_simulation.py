"""Gewöhnliche Simulation und Multilevel-Splitting (Fixed Effort, regenerativ) für den Verlust des Erlang-Systems: c Spuren ohne Warteraum,
Angebot a, mittlere Dauer 1, beliebige Verteilung der Dauer (exponentiell, fest, gleichverteilt).

**Splitting.** Ein Zyklus beginnt mit einer Ankunft in ein leeres Gate und endet, wenn das Gate wieder leer ist. Die Stufen sind Zahlen
belegter Spuren (`levels`, standardmäßig 1, 2, …, c). Stufe 1: N frische Teilchen. Von Stufe `lo` zu `hi`: N Teilchen werden aus den Zuständen gezogen, die
`lo` erreicht haben (mit Zurücklegen), und laufen, bis sie `hi` erreichen (Erfolg, Zustand wird gespeichert) oder das Gate leer wird (Misserfolg);
p̂ = Erfolge/N. Ein Teilchen ist der volle Zustand (Abgangszeiten der Belegten), daher gilt das Verfahren auch für nicht-exponentielle Dauer. Von der
letzten Stufe läuft jedes Teilchen bis zum Leerwerden und misst die Zeit mit c Belegten. Verlust = Π p̂ · mittlere Zeit bei c / E[Zykluslänge];
E[Zykluslänge] = 1/a + mittlere Busy Period (gewöhnliche Simulation, N Zyklen). Die Wurzel (`root`) jedes Teilchens ist der Index des
Stufe-1-Teilchens, aus dem es hervorging; wie viele verschiedene Wurzeln überleben, misst die Entartung der Ahnenreihen.

Aufbau nach Einheiten: `draw_service`, `advance` (ein Teilchen bis zur Zielstufe oder bis leer), `run_stage` (eine Stufe), `busy_period_mean`,
`splitting_estimate` (ganzes Verfahren), `plain_estimate` (gewöhnliche Simulation). Zufall nur über übergebene `SplitMix64`-Ströme."""

import heapq
import math
from dataclasses import dataclass, field

_MASK = (1 << 64) - 1


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def uniform(self):
        """Gleichverteilt auf [0, 1) mit 53 Bit."""
        return (self.next() >> 11) * (1.0 / (1 << 53))

    def expovariate(self, rate):
        """Exponentiell mit Mittel 1/rate (Inversion; 1 − u liegt in (0, 1], der Logarithmus ist endlich)."""
        return -math.log(1.0 - self.uniform()) / rate


def streams(seed):
    """Die drei Zufallsströme eines Laufs: Zwischenankunft, Abfertigungsdauer, Auswahl der Teilchen."""
    return SplitMix64(seed), SplitMix64(seed + 7_777_777), SplitMix64(seed + 15_555_555)


def draw_service(kind, rng):
    """Eine Abfertigungsdauer mit Mittel 1: `exp` exponentiell, `det` fest 1, `unif` gleichverteilt auf (0, 2)."""
    if kind == "exp":
        return rng.expovariate(1.0)
    if kind == "det":
        return 1.0
    if kind == "unif":
        return 2.0 * rng.uniform()
    raise ValueError(f"unbekannte Verteilung: {kind}")


@dataclass
class Advance:
    """Ergebnis von `advance`: Erfolg (Zielstufe erreicht) oder Misserfolg (Gate leer), Uhr, Zustand, Zeit mit c Belegten, Ereignisse."""
    success: bool
    clock: float
    busy: list
    time_at_c: float
    events: int


def advance(clock, busy, target, c, a, kind, gap_rng, svc_rng):
    """Ein Teilchen (Uhr, Heap der Abgangszeiten der Belegten) laufen lassen, bis `target` Belegte erreicht sind (Erfolg) oder das Gate leer ist
    (Misserfolg). Gemessen wird die Zeit mit allen c Belegten (Ankünfte bei c Belegten gehen verloren und ändern nichts). Der übergebene Zustand
    wird nicht verändert (Kopie)."""
    busy = list(busy)
    time_at_c = 0.0
    events = 0
    while True:
        t_arr = clock + gap_rng.expovariate(a)
        while busy and busy[0] < t_arr:
            t_dep = heapq.heappop(busy)
            if len(busy) + 1 == c:
                time_at_c += t_dep - clock
            clock = t_dep
            events += 1
            if not busy:
                return Advance(False, clock, busy, time_at_c, events)
        if len(busy) == c:
            time_at_c += t_arr - clock
        clock = t_arr
        events += 1
        if len(busy) < c:
            heapq.heappush(busy, clock + draw_service(kind, svc_rng))
            if len(busy) == target:
                return Advance(True, clock, busy, time_at_c, events)


def run_stage(states, lo_to_hi, n, c, a, kind, gap_rng, svc_rng, pick_rng):
    """Eine Stufe: `n` Teilchen aus `states` (Liste aus (Uhr, Heap, Wurzel)) ziehen und bis `lo_to_hi` laufen lassen.
    Gibt (Erfolge, neue Zustände, Ereignisse) zurück."""
    new_states, events = [], 0
    for _ in range(n):
        clock, busy, root = states[int(pick_rng.uniform() * len(states))]
        res = advance(clock, busy, lo_to_hi, c, a, kind, gap_rng, svc_rng)
        events += res.events
        if res.success:
            new_states.append((res.clock, res.busy, root))
    return len(new_states), new_states, events


def busy_period_mean(n, c, a, kind, gap_rng, svc_rng):
    """Mittlere Busy Period aus `n` Zyklen (Start mit einer frischen Ankunft in ein leeres Gate); gibt (Mittel, Ereignisse) zurück."""
    total, events = 0.0, 0
    for _ in range(n):
        res = advance(0.0, [draw_service(kind, svc_rng)], c + 1, c, a, kind, gap_rng, svc_rng)   # Stufe c + 1 gibt es nicht: bis leer
        total += res.clock
        events += res.events
    return total / n, events


def default_levels(c, step=1):
    """Stufen 1, 1 + step, 1 + 2·step, …, c (die letzte immer c)."""
    levels = list(range(1, c, step))
    if levels[0] != 1:
        levels = [1] + levels
    if levels[-1] != c:
        levels.append(c)
    return levels


@dataclass
class SplitResult:
    c: int
    a: float
    kind: str
    n: int
    levels: list                    # Stufen 1 … c
    stage_p: list                   # p̂ je Übergang levels[i] → levels[i + 1]
    successes: list                 # Erfolge je Übergang (von n)
    roots: list                     # verschiedene Wurzeln unter den Teilchen je Stufe (Länge len(levels))
    time_at_c: float                # mittlere Zeit mit c Belegten je Teilchen der letzten Stufe (0, wenn keines ankam)
    cycle: float                    # geschätzte E[Zykluslänge]
    events: int
    estimate: float                 # geschätzter Verlust (0, wenn eine Stufe kein Teilchen durchbrachte)
    died_at: int = 0                # Übergang (1-basiert), an dem kein Teilchen mehr durchkam; 0 = nie
    reach: float = field(default=0.0)   # Π p̂ = geschätzte Wahrscheinlichkeit, dass ein Zyklus c erreicht


def splitting_estimate(c, a, kind, n, seed, step=1, rngs=None):
    """Multilevel-Splitting (Fixed Effort) für den Verlust: siehe Modulbeschreibung."""
    gap_rng, svc_rng, pick_rng = rngs if rngs is not None else streams(seed)
    levels = default_levels(c, step)
    states = [(0.0, [draw_service(kind, svc_rng)], i) for i in range(n)]
    events, reach = 0, 1.0
    stage_p, successes, roots = [], [], [n]
    for lo, hi in zip(levels[:-1], levels[1:]):
        succ, states, ev = run_stage(states, hi, n, c, a, kind, gap_rng, svc_rng, pick_rng)
        events += ev
        stage_p.append(succ / n)
        successes.append(succ)
        roots.append(len({s[2] for s in states}))
        if succ == 0:
            reach = 0.0
            return SplitResult(c, a, kind, n, levels, stage_p, successes, roots, 0.0, float("nan"), events, 0.0,
                               died_at=len(stage_p), reach=0.0)
        reach *= succ / n
    total = 0.0
    for clock, busy, _ in states:
        res = advance(clock, busy, c + 1, c, a, kind, gap_rng, svc_rng)
        total += res.time_at_c
        events += res.events
    time_at_c = total / len(states)
    bp, ev = busy_period_mean(n, c, a, kind, gap_rng, svc_rng)
    events += ev
    cycle = 1.0 / a + bp
    return SplitResult(c, a, kind, n, levels, stage_p, successes, roots, time_at_c, cycle, events, reach * time_at_c / cycle, reach=reach)


@dataclass
class PlainResult:
    c: int
    a: float
    kind: str
    arrivals: int
    lost: int
    events: int

    def blocking(self):
        return self.lost / self.arrivals if self.arrivals else float("nan")


def plain_estimate(c, a, kind, arrivals, seed, rngs=None):
    """Gewöhnliche Simulation des Verlustsystems über `arrivals` Ankünfte (Start leer, keine Einschwingphase; bei seltenem Verlust bedeutungslos)."""
    gap_rng, svc_rng, _ = rngs if rngs is not None else streams(seed)
    busy, lost, events, t = [], 0, 0, 0.0
    for _ in range(arrivals):
        t += gap_rng.expovariate(a)
        while busy and busy[0] <= t:
            heapq.heappop(busy)
            events += 1
        events += 1
        if len(busy) < c:
            heapq.heappush(busy, t + draw_service(kind, svc_rng))
        else:
            lost += 1
    return PlainResult(c, a, kind, arrivals, lost, events)
