"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Randwerte, gestorbener Lauf, Würfel-Knopf, Permalink-Grenzen, Abschnitte, Footer."""

import random
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import spl_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=900)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_default_run_has_no_exception_and_shows_the_exact_value():
    at = _run()
    _ok(at)
    assert _metric(at, "Exakter Verlust (Erlang B)") == "5.5·10⁻⁷"                          # B(15, 3)
    assert _metric(at, "Gewöhnliche Simulation (gleiches Budget)") == "1.2·10⁻⁵"            # drei Verluste in 252 754 Ankünften (Zufall und Gruppenbildung)
    assert _metric(at, "Ereignisse der gewöhnlichen Simulation für ±10 %") == "4·10⁸"
    assert int(_metric(at, "Ereignisse des Splittings").replace(".", "")) > 0


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert (at.session_state["c_slider"], at.session_state["n_select"], at.session_state["a_select"]) == (p["c"], p["n"], p["a"])
    assert at.metric


def test_a_dying_run_shows_a_warning_and_no_estimate():
    at = _run(c_slider=30, a_select=2.0, n_select=250, step_select=5)
    _ok(at)
    assert _metric(at, "Splitting (Schätzung)") == "kein Treffer"
    assert any("gestorben" in w.value for w in at.warning)
    assert _metric(at, "Splitting gegenüber exakt") == "–"
    assert not _run().warning                                                                  # der Standardlauf stirbt nicht


@pytest.mark.parametrize("kw", [dict(c_slider=5, a_select=8.0, n_select=250), dict(c_slider=10, kind_select="det", step_select=3),
                                 dict(c_slider=15, kind_select="unif", n_select=2000, a_select=5.0), dict(c_slider=25, n_select=250, step_select=2),
                                 dict(c_slider=5, a_select=2.0, n_select=250, step_select=5)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_dice_button_changes_the_seed_and_the_simulated_run(monkeypatch):
    """Der Würfel zieht sonst einen unseeded Zufalls-Seed; deshalb ist der gewürfelte Seed im Test fest, und verglichen werden die Daten
    des Diagramms der Stufenwahrscheinlichkeiten (nicht eine gerundete Kennzahl)."""
    monkeypatch.setattr(random, "randint", lambda a, b: 508145)
    at = _run(c_slider=10, n_select=250)
    old_seed, old = at.session_state["seed_input"], at.get("plotly_chart")[0].proto.spec
    next(b for b in at.button if b.label == "🎲 Neuen Lauf würfeln").click().run()
    _ok(at)
    assert at.session_state["seed_input"] == 508145 != old_seed and at.get("plotly_chart")[0].proto.spec != old


def test_permalink_values_are_clamped_and_snapped():
    at = AppTest.from_file(APP, default_timeout=900)
    at.query_params["c"] = "12"
    at.query_params["a"] = "4"
    at.query_params["n"] = "700"
    at.query_params["step"] = "4"
    at.query_params["kind"] = "det"
    at.run()
    _ok(at)
    assert at.session_state["c_slider"] == 10 and at.session_state["a_select"] == 3.0 and at.session_state["n_select"] == 1000
    assert at.session_state["step_select"] == 3 and at.session_state["kind_select"] == "det"


def test_permalink_ignores_garbage_and_unknown_kinds():
    at = AppTest.from_file(APP, default_timeout=900)
    at.query_params["a"] = "viel"
    at.query_params["kind"] = "lognormal"
    at.query_params["n"] = "nan"
    at.run()
    _ok(at)
    assert at.session_state["a_select"] == C.DEFAULT_A and at.session_state["kind_select"] == C.DEFAULT_KIND and at.session_state["n_select"] == C.DEFAULT_N


def test_charts_sections_and_limits_table_are_present():
    at = _run()
    _ok(at)
    assert len(at.get("plotly_chart")) == 6
    headers = [s.value for s in at.subheader]
    for part in ("Wie genau ist Splitting", "Was spart Splitting", "Wie dicht sollen die Stufen liegen", "Wo die Annahmen enden"):
        assert any(part in h for h in headers), part
    table = next(m.value for m in at.markdown if "Wer setzt an" in m.value)
    for name in ("Importance Sampling", "Kingman", "Prioritätsklassen", "Jackson-Netze", "Zeitvariable Ankünfte"):
        assert name in table
    assert "geplant" not in table      # die Linie wird erst vollständig veröffentlicht, kein Status-Zusatz


def test_study_tables_are_complete():
    at = _run()
    acc = next(m.value for m in at.markdown if m.value.startswith("| Spuren | exakter Verlust | 250 Teilchen"))
    for c in C.STUDY_C:
        assert f"| {c} |" in acc
    plain = next(m.value for m in at.markdown if "Läufe ohne einen einzigen Verlust" in m.value)
    assert "| 15 | 5.5·10⁻⁷ | 13 von 16 | 5 von 16 |" in plain and "| 20 | 7.1·10⁻¹¹ | 16 von 16 | 16 von 16 |" in plain
    steps = next(m.value for m in at.markdown if m.value.startswith("| Stufenabstand |"))
    for s in C.STUDY_STEPS:
        assert f"| {s} |" in steps


def test_unknown_kind_in_the_study_sections_falls_back_to_exponential():
    """Die Studie kennt nur exponentielle und feste Dauer; bei gleichverteilter Dauer zeigen die Studien-Abschnitte die exponentiellen Zellen."""
    at = _run(kind_select="unif", c_slider=10, n_select=250)
    _ok(at)
    assert at.metric


def test_seed_control_uses_the_portfolio_wording():
    at = _run()
    assert [n.label for n in at.number_input] == ["Zufalls-Seed"]


def test_related_demos_are_linked_and_footer_is_present():
    at = _run()
    text = " ".join(c.value for c in at.caption)
    for name in ("erlang-b-demo", "output-analysis-demo", "mm1-queue-demo", "ems-demo"):
        assert name in text
    assert "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in text


def test_no_sentence_wide_comma_replacement_in_the_app_source():
    """Regressionsschutz: `.replace(",", ".")` auf einem ganzen (verketteten) Satz macht aus Kommas im Fließtext Punkte; Tausender nur über `fmt_int`."""
    source = Path(APP).read_text(encoding="utf-8")
    assert '.replace(",", ".")' not in source
