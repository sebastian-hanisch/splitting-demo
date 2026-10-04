"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).
Alle Regler sind immer sichtbar - es gibt keinen ausblendbaren Regler (also auch kein KEPT-Muster)."""

import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import spl_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "c_slider": SettingSpec("c", int, C.DEFAULT_C, C.C_MIN, C.C_MAX),
    "a_select": SettingSpec("a", float, C.DEFAULT_A, C.A_OPTIONS[0], C.A_OPTIONS[-1]),
    "n_select": SettingSpec("n", int, C.DEFAULT_N, C.N_OPTIONS[0], C.N_OPTIONS[-1]),
    "step_select": SettingSpec("step", int, C.DEFAULT_STEP, C.STEP_OPTIONS[0], C.STEP_OPTIONS[-1]),
    "kind_select": SettingSpec("kind", str, C.DEFAULT_KIND),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"c": "c_slider", "a": "a_select", "n": "n_select", "step": "step_select", "kind": "kind_select", "seed": "seed_input"}
OPTIONS = {"a_select": C.A_OPTIONS, "n_select": C.N_OPTIONS, "step_select": C.STEP_OPTIONS}       # Regler, die nur feste Stufen kennen


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def snap_to_option(state_key, value):
    """Regler mit festen Stufen: ein Permalink-Wert dazwischen rastet auf die nächste Stufe ein (bei Gleichstand auf die kleinere)."""
    return min(OPTIONS[state_key], key=lambda o: (abs(o - value), o))


def snap_c(value):
    """Die Spurzahl rastet auf das nächste Vielfache der Schrittweite innerhalb der Grenzen ein."""
    snapped = round(value / C.C_STEP) * C.C_STEP
    return int(min(C.C_MAX, max(C.C_MIN, snapped)))


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if value != value:                     # NaN
                    continue
                if state_key == "kind_select":
                    if value not in C.KINDS:
                        continue
                else:
                    if spec.lo is not None:
                        value = max(spec.lo, value)
                    if spec.hi is not None:
                        value = min(spec.hi, value)
                    if state_key in OPTIONS:
                        value = snap_to_option(state_key, value)
                    if state_key == "c_slider":
                        value = snap_c(value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
