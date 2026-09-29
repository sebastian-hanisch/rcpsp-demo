"""Instanz-Generator: Erzeugung, Determinismus, Kollaps-Eigenschaften; Auswertung: Kennzahlen, Sweep, die zwei
Experimente dieses Stücks (Kapazität, Vorrangdichte), Timing-Messreihe."""

import numpy as np
import pytest

import rcpsp_constants as C
import rcpsp_evaluation as ev
import rcpsp_scenario as S


# --- Instanz --------------------------------------------------------------------------------------------------


def test_instance_shape_and_bounds():
    inst = S.generate(5, 4, 3, capacity=2, density=0.2)
    assert inst.n_jobs == 5 and inst.m_resources == 4 and inst.n == 20
    assert inst.duration.shape == (20,) and inst.demand.shape == (20, 4)
    assert inst.duration.min() >= C.P_MIN and inst.duration.max() <= C.P_MAX
    assert np.all(inst.capacity == 2)


def test_instance_is_deterministic_and_seed_dependent():
    a, b, c = S.generate(5, 4, 3), S.generate(5, 4, 3), S.generate(5, 4, 4)
    assert np.array_equal(a.duration, b.duration) and a.precedence == b.precedence
    assert not np.array_equal(a.duration, c.duration)


def test_zero_density_gives_only_the_chain_precedence():
    inst = S.generate(5, 4, 3, density=0.0)
    assert len(inst.precedence) == 5 * 3   # (m_resources-1) Kettenkanten je Kette


def test_capacity_one_gives_unit_demand_on_exactly_one_resource_per_activity():
    inst = S.generate(4, 3, 2, capacity=1)
    for i in range(inst.n):
        assert inst.demand[i].sum() == 1


def test_precedence_graph_is_always_acyclic():
    for density in (0.0, 0.2, 0.6):
        inst = S.generate(6, 4, 9, density=density)
        indeg = {i: 0 for i in range(inst.n)}
        adj = {i: [] for i in range(inst.n)}
        for p, s in inst.precedence:
            adj[p].append(s)
            indeg[s] += 1
        queue = [i for i in range(inst.n) if indeg[i] == 0]
        visited = 0
        while queue:
            u = queue.pop()
            visited += 1
            for v in adj[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    queue.append(v)
        assert visited == inst.n


# --- Analyse --------------------------------------------------------------------------------------------------


def test_analysis_fields_are_consistent():
    a = ev.analyse(ev.Settings(n_jobs=10, m_resources=4))
    assert a.optimal is None   # 40 Aktivitäten > EXACT_MAX_N


def test_analysis_respects_small_n_cp_sat_gegenprobe():
    a = ev.analyse(ev.Settings(n_jobs=2, m_resources=3))
    assert a.optimal is not None and a.optimal_proven


def test_analysis_is_deterministic_given_the_chain_seed():
    from dataclasses import replace
    s = ev.Settings(n_jobs=5, m_resources=4, seed=1, chain_seed=0)
    a, b, c = ev.analyse(s), ev.analyse(s), ev.analyse(replace(s, chain_seed=1))
    assert a.gap_random == pytest.approx(b.gap_random)
    assert a.gap_random != pytest.approx(c.gap_random)


def test_gap_spt_can_be_negative():
    """LFT ist keine bewiesen optimale Regel - Stichprobe belegt einen echten Gegenfall (wie Stück 7-9)."""
    a = ev.analyse(ev.Settings(n_jobs=3, m_resources=5, seed=15, capacity=1, density=0.0))
    assert a.gap_spt < 0.0


# --- Sweep und Messreihe -------------------------------------------------------------------------------------


def test_run_config_counts_runs_and_aggregates():
    r = ev.run_config(ev.Settings(n_jobs=5, m_resources=4), chains=2)
    assert r["n_runs"] == len(C.SWEEP_SEEDS) * 2


def test_sweep_values_labels_and_ordering():
    assert set(ev.SWEEP_VALUES) == set(ev.SWEEP_LABELS)
    rows = ev.sweep("n_jobs", ev.Settings(), (3, 7))
    assert [r["value"] for r in rows] == [3, 7]


def test_capacity_sweep_shows_cmax_never_increasing():
    rows = ev.capacity_sweep()
    cmaxes = [r["lft_cmax"] for r in rows]
    assert all(cmaxes[i] >= cmaxes[i + 1] - 1e-6 for i in range(len(cmaxes) - 1))


def test_density_sweep_shows_cmax_never_decreasing():
    rows = ev.density_sweep()
    cmaxes = [r["lft_cmax"] for r in rows]
    assert all(cmaxes[i] <= cmaxes[i + 1] + 1e-6 for i in range(len(cmaxes) - 1))


def test_timing_sweep_stays_fast():
    rows = ev.timing_sweep()
    large = rows[-1]
    assert large["exact_seconds"] < 5.0 and large["sgs_seconds"] < 1.0
