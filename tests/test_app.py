"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt, Randwerte, Würfel-Knopf, Permalink-Grenzen,
Experimente auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import rcpsp_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(rcpsp_step=1, **state):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if rcpsp_step != 1:
        at.select_slider(key="rcpsp_step").set_value(rcpsp_step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m.value for m in at.metric if m.label == label)


def test_default_run_has_no_exception_and_shows_the_measured_default():
    at = _run()
    _ok(at)
    assert _metric(at, "LFT (Cmax)") == "75"
    assert _metric(at, "SPT (Wurzel dieser Linie!)") == "+49.3 %"
    assert any("LFT ist" in s.value for s in at.success)


def test_capacity_and_density_sliders_actually_change_the_main_metric():
    """Kein Vehikel-Umschalter hier (siehe README) - aber DIESELBE Disziplin gilt für die beiden neuen Regler:
    sie müssen die Hauptkennzahl ändern, nicht nur eine Zusatzbox."""
    at_low = _run(n_jobs_slider=5, seed_input=1, capacity_slider=1, density_slider=0.0)
    at_high = _run(n_jobs_slider=5, seed_input=1, capacity_slider=4, density_slider=0.4)
    _ok(at_low)
    _ok(at_high)
    assert _metric(at_low, "LFT (Cmax)") != _metric(at_high, "LFT (Cmax)")


def test_negative_gap_is_shown_honestly_not_as_a_broken_sign():
    """Regressionsschutz für einen echten Fund (wie Stück 7-9): n_jobs=3, m=5, Kapazität 1, Seed 15 - SPT
    schlägt LFT sogar ohne zusätzliche Vorrangdichte."""
    at = _run(n_jobs_slider=3, m_resources_slider=5, seed_input=15, capacity_slider=1, density_slider=0.0)
    _ok(at)
    spt_metric = _metric(at, "SPT (Wurzel dieser Linie!)")
    assert "+-" not in spt_metric and spt_metric.startswith("-")
    assert any("schneidet hier sogar schlechter ab" in w.value for w in at.warning)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["n_jobs_slider"] == p["n_jobs"] and at.session_state["capacity_slider"] == p["capacity"]
    assert at.metric


@pytest.mark.parametrize("step", [1, 2, 3])
def test_every_step_runs(step):
    at = _run(n_jobs_slider=5, rcpsp_step=step)
    _ok(at)
    assert at.session_state["rcpsp_step"] == step


def test_step_two_has_the_upto_slider_defaulting_to_all_activities():
    at = _run(n_jobs_slider=3, m_resources_slider=3, rcpsp_step=2)
    _ok(at)
    sl = next(s for s in at.slider if s.key == "rcpsp_upto")
    assert sl.value == sl.max == 9


def test_exact_limit_is_respected_in_the_metric():
    at = _run(n_jobs_slider=4, m_resources_slider=5)   # 20 Aktivitaeten == EXACT_MAX_N
    _ok(at)
    proven_metric = next((m for m in at.metric if m.label == "CP-SAT (exakte Gegenprobe)"), None)
    timeout_metric = next((m for m in at.metric if m.label == "CP-SAT" and m.value == "Zeitlimit erreicht"), None)
    assert proven_metric is not None or timeout_metric is not None
    at2 = _run(n_jobs_slider=5, m_resources_slider=5)   # 25 Aktivitaeten > EXACT_MAX_N
    _ok(at2)
    assert "erst ab n" in _metric(at2, "CP-SAT")


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


@pytest.mark.parametrize("kw", [dict(n_jobs_slider=C.N_JOBS_MIN), dict(n_jobs_slider=C.N_JOBS_MAX),
                                 dict(m_resources_slider=C.M_RESOURCES_MIN), dict(m_resources_slider=C.M_RESOURCES_MAX),
                                 dict(capacity_slider=C.CAPACITY_MIN), dict(capacity_slider=C.CAPACITY_MAX),
                                 dict(density_slider=C.DENSITY_MIN), dict(density_slider=C.DENSITY_MAX)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_permalink_values_are_clamped():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["njobs"] = "9999"
    at.query_params["mres"] = "9999"
    at.query_params["cap"] = "9999"
    at.query_params["dens"] = "9999"
    at.run()
    _ok(at)
    assert at.session_state["n_jobs_slider"] == C.N_JOBS_MAX and at.session_state["m_resources_slider"] == C.M_RESOURCES_MAX
    assert at.session_state["capacity_slider"] == C.CAPACITY_MAX and at.session_state["density_slider"] == C.DENSITY_MAX


@pytest.mark.parametrize("param", ["n_jobs", "m_resources"])
def test_sweeps_run_on_demand(param):
    at = _run(n_jobs_slider=5)
    at.selectbox(key="sweep_select").set_value(param).run()
    next(b for b in at.button if b.key == "sweep_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


def test_experiments_run_on_demand():
    at = _run(n_jobs_slider=5)
    for key, flag in (("cap_start", "cap_on"), ("dens_start", "dens_on"), ("timing_start", "timing_on")):
        next(b for b in at.button if b.key == key).click().run()
        _ok(at)
        assert at.session_state[flag]


def test_footer_and_grenzen_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Nur erneuerbare Ressourcen" in m.value for m in at.markdown)
