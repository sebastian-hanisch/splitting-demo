import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class ScriptedRng:
    """Liefert vorgegebene Werte statt Zufall (Mini-Instanzen von Hand gerechnet). `expovariate(rate)` ignoriert die Rate und gibt der
    Reihe nach die Werte zurück, `uniform()` ebenso aus einer eigenen Liste."""

    def __init__(self, exp_values=(), uniform_values=()):
        self.exp_values, self.uniform_values = list(exp_values), list(uniform_values)
        self.n_exp = self.n_uniform = 0

    def expovariate(self, rate):
        v = self.exp_values[self.n_exp]
        self.n_exp += 1
        return v

    def uniform(self):
        v = self.uniform_values[self.n_uniform]
        self.n_uniform += 1
        return v


@pytest.fixture
def advance_mini():
    """Zwei Spuren (c = 2), Angebot a = 1 (Rate 1). Teilchen: eine belegte Spur mit Abgang bei 5.0, Uhr 0.0; Ziel Stufe 2. Zwischenankunft 1.0
    (Skript), Dauer des Ankömmlings 3.0: Ankunft bei 1.0 bei einer Belegten → zwei Belegte = Ziel erreicht, Erfolg bei Uhr 1.0 mit Abgängen
    [4.0, 5.0]; Zeit bei c = 0 (die Stufe wurde gerade erst erreicht)."""
    return ScriptedRng(exp_values=[1.0]), ScriptedRng(exp_values=[3.0])
