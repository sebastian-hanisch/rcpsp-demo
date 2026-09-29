"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Buttons (Standardmuster aus dem Demo-Portfolio).
Keine ausblendbaren Regler in diesem Stück (kein Vehikel-Umschalter, siehe README) - deshalb kein
seed_widget/KEPT-Muster nötig."""

import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import rcpsp_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_jobs_slider": SettingSpec("njobs", int, C.DEFAULT_N_JOBS, C.N_JOBS_MIN, C.N_JOBS_MAX),
    "m_resources_slider": SettingSpec("mres", int, C.DEFAULT_M_RESOURCES, C.M_RESOURCES_MIN, C.M_RESOURCES_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
    "capacity_slider": SettingSpec("cap", int, C.DEFAULT_CAPACITY, C.CAPACITY_MIN, C.CAPACITY_MAX),
    "density_slider": SettingSpec("dens", float, C.DEFAULT_DENSITY, C.DENSITY_MIN, C.DENSITY_MAX),
}
PRESET_KEYS = {"n_jobs": "n_jobs_slider", "m_resources": "m_resources_slider", "seed": "seed_input",
               "capacity": "capacity_slider", "density": "density_slider"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
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
