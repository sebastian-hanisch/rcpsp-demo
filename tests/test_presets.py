"""Presets: Vollständigkeit, gültige Werte, Permalink-Konstanten."""

import rcpsp_constants as C
import rcpsp_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 5
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]


def test_preset_values_are_valid_and_match_the_setting_specs():
    for preset in C.PRESETS.values():
        assert C.N_JOBS_MIN <= preset["n_jobs"] <= C.N_JOBS_MAX
        assert C.M_RESOURCES_MIN <= preset["m_resources"] <= C.M_RESOURCES_MAX
        assert C.CAPACITY_MIN <= preset["capacity"] <= C.CAPACITY_MAX
        assert C.DENSITY_MIN <= preset["density"] <= C.DENSITY_MAX
        for key, state_key in P.PRESET_KEYS.items():
            P.SETTING_SPECS[state_key].caster(preset[key])


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Standardfall (Voreinstellung)"]
    assert p["n_jobs"] == C.DEFAULT_N_JOBS and p["m_resources"] == C.DEFAULT_M_RESOURCES
    assert p["seed"] == C.DEFAULT_SEED and p["capacity"] == C.DEFAULT_CAPACITY and p["density"] == C.DEFAULT_DENSITY


def test_job_shop_equivalent_preset_has_capacity_one_and_zero_density():
    p = C.PRESETS["Job-Shop-Äquivalent"]
    assert p["capacity"] == 1 and p["density"] == 0.0


def test_bounds_and_snapping_constants():
    assert P.bounds("n_jobs_slider") == (C.N_JOBS_MIN, C.N_JOBS_MAX)
    assert P.bounds("m_resources_slider") == (C.M_RESOURCES_MIN, C.M_RESOURCES_MAX)
    assert P.bounds("seed_input") == (0, C.SEED_MAX)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)
