"""Konstanten der Demo zu seltenen Ereignissen (Multilevel-Splitting): Regler, Voreinstellungen, Studien-Achsen. Zeiteinheit der Rechnung ist die
mittlere Abfertigungsdauer (= 1)."""


def fmt_int(n):
    """Ganzzahl mit Punkt als Tausendertrenner (10000 -> 10.000)."""
    return f"{n:,}".replace(",", ".")


def fmt_pct(x, digits=0):
    """Anteil als Prozent mit Leerzeichen (0.086 -> "9 %", mit digits=1 "8.6 %")."""
    return f"{x:.{digits}%}".replace("%", " %")


def fmt_sci(x, digits=1):
    """Kleine Zahl in Zehnerpotenz-Schreibweise mit Dezimalpunkt (5.46e-07 -> "5.5·10⁻⁷")."""
    if x == 0:
        return "0"
    mantissa, exponent = f"{x:.{digits}e}".split("e")
    e = int(exponent)
    sup = str(abs(e)).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
    return f"{mantissa}·10{'⁻' if e < 0 else ''}{sup}"


def fmt_ratio(x):
    """Verhältnis Schätzung/exakt: zwei Dezimalstellen, bei Werten unter 0.01 in Zehnerpotenz-Schreibweise (0.0043 -> "4.3·10⁻³")."""
    return f"{x:.2f}" if x >= 0.01 else fmt_sci(x)


def fmt_roots(k):
    """Zahl der Wurzeln als Satzteil: 1 -> "einer einzigen Wurzel", sonst "k verschiedenen Wurzeln"."""
    return "einer einzigen Wurzel" if k == 1 else f"{k} verschiedenen Wurzeln"


C_MIN, C_MAX, C_STEP, DEFAULT_C = 5, 30, 5, 15       # Zahl der Spuren (Verlustsystem ohne Warteraum, Stück 8)
A_OPTIONS = (2.0, 3.0, 5.0, 8.0)                      # Angebot a in Erlang (mittlere Dauer 1)
DEFAULT_A = 3.0
N_OPTIONS = (250, 1000, 2000, 4000)                   # Teilchen je Stufe (live; 250, 1000, 4000 gibt es auch in der Studie)
DEFAULT_N = 1000
STEP_OPTIONS = (1, 2, 3, 5)                           # Stufenabstand (jede step-te belegte Spur ist eine Stufe)
DEFAULT_STEP = 1
KINDS = ("exp", "det", "unif")                        # Verteilung der Abfertigungsdauer (Mittel 1)
KIND_LABELS = {"exp": "exponentiell", "det": "fest", "unif": "gleichverteilt (0 bis 2)"}
DEFAULT_KIND = "exp"
SEED_MAX = 999999
DEFAULT_SEED = 35

PLAIN_ARRIVALS_MIN, PLAIN_ARRIVALS_MAX = 50_000, 3_000_000     # Ankünfte der gewöhnlichen Simulation im Live-Lauf (gleiches Ereignisbudget, begrenzt)
TARGET_REL_SD = 0.10                                   # Genauigkeitsziel für den Aufwandsvergleich (±10 %)

# Vorgerechnete Studie (generate_precomputed.py)
STUDY_A = 3.0
STUDY_C = (10, 15, 20, 25, 30)
STUDY_N = (250, 1000, 4000)
STUDY_KINDS = ("exp", "det")
STUDY_REPS = 16                                        # unabhängige Wiederholungen je Zelle
STUDY_STEP_C, STUDY_STEP_N = 20, 2000                  # Stufenabstand-Studie: Spuren und Teilchen
STUDY_STEPS = (1, 2, 3, 5, 8)
STUDY_PLAIN_BUDGETS = (400_000, 4_000_000)             # Ereignisbudgets der gewöhnlichen Simulation
STUDY_PLAIN_C = (10, 15, 20)

PRESET_ORDER = ("Mäßig selten (10 Spuren)", "Selten (15 Spuren)", "Sehr selten (20 Spuren)", "Zu selten (30 Spuren)")


def _preset(c=DEFAULT_C, a=DEFAULT_A, n=DEFAULT_N, step=DEFAULT_STEP, kind=DEFAULT_KIND):
    return {"c": c, "a": a, "n": n, "step": step, "kind": kind, "seed": DEFAULT_SEED}


PRESETS = {
    "Mäßig selten (10 Spuren)": _preset(c=10, n=1000),
    "Selten (15 Spuren)": _preset(n=4000),
    "Sehr selten (20 Spuren)": _preset(c=20, n=4000),
    "Zu selten (30 Spuren)": _preset(c=30, n=1000),
}
# Zahlen aus der vorgerechneten Studie (Angebot 3 Erlang, exponentielle Dauer, je 16 Läufe); tests/test_claims.py rechnet jede nach
PRESET_HELP = {
    "Mäßig selten (10 Spuren)": "Verlust 8.1·10⁻⁴: Splitting (1000 Teilchen) trifft ihn im Mittel auf 2 % (Streuung 7 % je Lauf), aber auch die gewöhnliche Simulation sieht ihn (0 von 16 Läufen ohne Verlust): hier ist Splitting nicht nennenswert billiger.",
    "Selten (15 Spuren)": "Verlust 5.5·10⁻⁷: Splitting (4000 Teilchen) liegt im Mittel bei 0.94 des Werts (Streuung 17 %), die gewöhnliche Simulation mit 400 000 Ereignissen sieht in 13 von 16 Läufen keinen einzigen Verlust.",
    "Sehr selten (20 Spuren)": "Verlust 7.1·10⁻¹¹: die gewöhnliche Simulation sieht in allen 16 Läufen nichts, auch mit 4 Mio. Ereignissen; Splitting (4000 Teilchen) liegt im Mittel bei 0.79 des Werts, mit 41 % Streuung je Lauf.",
    "Zu selten (30 Spuren)": "Verlust 3.9·10⁻²⁰: Splitting (1000 Teilchen) streut um 277 % je Lauf; von 1000 Wurzeln bleiben auf der letzten Stufe im Mittel 2.2 übrig, die Schätzung ist unzuverlässig.",
}
