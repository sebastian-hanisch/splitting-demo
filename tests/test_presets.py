"""Presets: Vollständigkeit, gültige Werte, Permalink-Konstanten."""

import pytest

import spl_constants as C
import spl_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER) and len(C.PRESETS) == 4
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]


def test_preset_values_are_valid_and_match_the_setting_specs():
    for preset in C.PRESETS.values():
        assert C.C_MIN <= preset["c"] <= C.C_MAX and P.snap_c(preset["c"]) == preset["c"]
        assert preset["a"] in C.A_OPTIONS and preset["n"] in C.N_OPTIONS and preset["step"] in C.STEP_OPTIONS and preset["kind"] in C.KINDS
        for key, state_key in P.PRESET_KEYS.items():
            P.SETTING_SPECS[state_key].caster(preset[key])


def test_preset_names_state_the_values_they_set():
    assert [C.PRESETS[n]["c"] for n in C.PRESET_ORDER] == [10, 15, 20, 30]
    assert [C.PRESETS[n]["n"] for n in C.PRESET_ORDER] == [1000, 4000, 4000, 1000]


def test_default_settings():
    assert (C.DEFAULT_C, C.DEFAULT_A, C.DEFAULT_N, C.DEFAULT_STEP, C.DEFAULT_KIND) == (15, 3.0, 1000, 1, "exp")
    assert all(C.PRESETS[n]["a"] == C.STUDY_A for n in C.PRESET_ORDER)          # die Presets liegen auf dem Angebot der Studie


def test_bounds_and_url_params():
    assert P.bounds("seed_input") == (0, C.SEED_MAX) and P.bounds("c_slider") == (5, 30)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


@pytest.mark.parametrize("key,value,expected", [("a_select", 4.0, 3.0), ("a_select", 6.5, 5.0), ("a_select", 7.0, 8.0), ("a_select", 0.1, 2.0),
                                                ("n_select", 600, 250), ("n_select", 700, 1000), ("n_select", 3000, 2000), ("n_select", 99999, 4000),
                                                ("step_select", 4, 3), ("step_select", 9, 5)])
def test_option_regulators_snap_to_the_nearest_option(key, value, expected):
    assert P.snap_to_option(key, value) == expected


@pytest.mark.parametrize("value,expected", [(0, 5), (7, 5), (8, 10), (12, 10), (33, 30), (99, 30)])
def test_spuren_snap_to_the_step_inside_the_bounds(value, expected):
    assert P.snap_c(value) == expected


def test_formatters():
    assert C.fmt_int(150000) == "150.000" and C.fmt_pct(0.2) == "20 %" and C.fmt_pct(0.0898, 1) == "9.0 %"
    assert C.fmt_sci(5.46e-07) == "5.5·10⁻⁷" and C.fmt_sci(8.1e-4) == "8.1·10⁻⁴" and C.fmt_sci(0.0) == "0" and C.fmt_sci(3.0e22, 0) == "3·10²²"


def test_ratio_and_roots_formatters():
    assert C.fmt_ratio(0.78) == "0.78" and C.fmt_ratio(1.0) == "1.00" and C.fmt_ratio(0.0043) == "4.3·10⁻³" and C.fmt_ratio(0.01) == "0.01"
    assert C.fmt_roots(1) == "einer einzigen Wurzel" and C.fmt_roots(26) == "26 verschiedenen Wurzeln"
