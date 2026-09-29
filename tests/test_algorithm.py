"""rcpsp_algorithm: CP-SAT (AddCumulative) gegen ein UNABHÄNGIGES Job-Shop-Kreis-Modell (AddCircuit) im
Kollaps-Fall (Kapazität=1, reine Kette) - der zentrale Beweis-Check dieses Stücks: RCPSP verallgemeinert Job
Shop strukturell, nicht nur behauptet. CPM-Schranken per Handrechnung, serielle Konstruktion gegen CP-SAT-
Optimum, Zulässigkeits-Zertifikat (Vorrang + Kapazität zu jedem Zeitpunkt)."""

import numpy as np
import pytest
from ortools.sat.python import cp_model

import rcpsp_algorithm as A
import rcpsp_scenario as S


def _independent_job_shop_optimum(n_jobs, m, routing, proc, time_limit_seconds=10):
    """Kreis-Modell (AddCircuit) je Maschine - strukturell UNABHÄNGIG von rcpsp_algorithm.solve_exact
    (AddCumulative), wie in job-shop-demo/shifting-bottleneck-demo/job-shop-tabu-demo."""
    model = cp_model.CpModel()
    start = {}
    end = {}
    for j in range(n_jobs):
        for pos in range(m):
            start[j, pos] = model.NewIntVar(0, int(proc.sum()) + 1, f"s{j}_{pos}")
            end[j, pos] = model.NewIntVar(0, int(proc.sum()) + 1, f"e{j}_{pos}")
            model.Add(end[j, pos] == start[j, pos] + int(proc[j, pos]))
            if pos > 0:
                model.Add(start[j, pos] >= end[j, pos - 1])
    ops_per_machine = [[] for _ in range(m)]
    for j in range(n_jobs):
        for pos in range(m):
            ops_per_machine[routing[j, pos]].append((j, pos))
    for k in range(m):
        ops = ops_per_machine[k]
        arcs = []
        for idx, (j, pos) in enumerate(ops):
            arcs.append((0, idx + 1, model.NewBoolVar(f"a0_{k}_{idx}")))
            arcs.append((idx + 1, 0, model.NewBoolVar(f"a{k}_{idx}_0")))
        for i1, (j1, p1) in enumerate(ops):
            for i2, (j2, p2) in enumerate(ops):
                if i1 == i2:
                    continue
                lit = model.NewBoolVar(f"a{k}_{i1}_{i2}")
                arcs.append((i1 + 1, i2 + 1, lit))
                model.Add(start[j2, p2] >= end[j1, p1]).OnlyEnforceIf(lit)
        model.AddCircuit(arcs)
    cmax = model.NewIntVar(0, int(proc.sum()) + 1, "cmax")
    model.AddMaxEquality(cmax, list(end.values()))
    model.Minimize(cmax)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 4
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, False
    return solver.Value(cmax), status == cp_model.OPTIMAL


@pytest.mark.parametrize("n_jobs,m", [(2, 2), (3, 2), (3, 3), (4, 3)])
def test_capacity_one_pure_chain_collapses_to_job_shop_optimum(n_jobs, m):
    """Der zentrale Beweis-Check dieses Stücks: RCPSP mit Kapazität=1 überall und OHNE zusätzliche
    Vorrangdichte ist strukturell IDENTISCH zu Job Shop - dasselbe Optimum, per zwei UNABHÄNGIGEN CP-SAT-
    Modellen (AddCumulative gegen AddCircuit) bestätigt."""
    for seed in range(3):
        inst = S.generate(n_jobs, m, seed * 10 + n_jobs + m, capacity=1, density=0.0)
        result, proven = A.solve_exact(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, time_limit_seconds=10)
        assert proven
        proc = inst.duration.reshape(n_jobs, m)
        js_opt, js_proven = _independent_job_shop_optimum(n_jobs, m, inst.routing, proc, time_limit_seconds=10)
        assert js_proven
        assert result.cmax == pytest.approx(js_opt, abs=1e-6)


def test_cpm_bounds_on_a_hand_picked_chain():
    """3 Aktivitäten in einer Kette (Dauer 5, 3, 4): ES/EF/LS/LF von Hand nachvollziehbar."""
    n = 3
    duration = np.array([5, 3, 4])
    precedence = [(0, 1), (1, 2)]
    es, ef, ls, lf = A.cpm_bounds(n, duration, precedence)
    assert list(es) == [0, 5, 8]
    assert list(ef) == [5, 8, 12]
    assert list(lf) == [5, 8, 12]   # eine einzige Kette: kein Puffer irgendwo
    assert list(ls) == [0, 5, 8]


def test_cpm_bounds_gives_slack_on_a_parallel_branch():
    """Aktivität 0 (Dauer 10) und Aktivität 1 (Dauer 2) laufen PARALLEL, beide münden in Aktivität 2 - Aktivität
    1 hat 8 Einheiten Puffer."""
    n = 3
    duration = np.array([10, 2, 3])
    precedence = [(0, 2), (1, 2)]
    es, ef, ls, lf = A.cpm_bounds(n, duration, precedence)
    assert es[2] == 10 and ef[2] == 13
    assert ls[1] - es[1] == 8   # Puffer von Aktivität 1


def test_serial_sgs_produces_a_precedence_and_capacity_feasible_schedule():
    inst = S.generate(6, 3, 5, capacity=2, density=0.3)
    es, ef, ls, lf = A.cpm_bounds(inst.n, inst.duration, inst.precedence)
    result = A.serial_sgs(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, A.lft_priority(lf))
    for p, s in inst.precedence:
        assert result.start[s] >= result.end[p] - 1e-9
    horizon = int(result.end.max()) + 1
    for k in range(inst.m_resources):
        usage = np.zeros(horizon)
        for i in range(inst.n):
            if inst.demand[i, k] > 0:
                usage[int(result.start[i]):int(result.end[i])] += inst.demand[i, k]
        assert np.all(usage <= inst.capacity[k])


def test_serial_sgs_never_beats_the_cp_sat_optimum():
    for seed in range(3):
        inst = S.generate(6, 3, seed, capacity=2, density=0.2)
        es, ef, ls, lf = A.cpm_bounds(inst.n, inst.duration, inst.precedence)
        result = A.serial_sgs(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, A.lft_priority(lf))
        opt, proven = A.solve_exact(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, time_limit_seconds=10)
        assert proven
        assert result.cmax >= opt.cmax - 1e-6


def test_lft_priority_prefers_the_activity_with_the_earliest_deadline():
    lf = np.array([10, 3, 7])
    priority = A.lft_priority(lf)
    assert priority(1) < priority(2) < priority(0)


def test_spt_priority_is_the_duration_itself():
    duration = np.array([5, 2, 9])
    priority = A.spt_priority(duration)
    assert priority(1) < priority(0) < priority(2)


def test_lft_beats_spt_on_a_hand_picked_instance():
    """Zwei Ketten, zwei Ressourcen. Kette 0 hat insgesamt viel Arbeit (spät fällig auf Ressource 0), Kette 1
    wenig - SPT stellt fälschlich die kurze Kette konsequent voran, LFT erkennt die Dringlichkeit über die
    CPM-Schranken."""
    routing = np.array([[0, 1], [1, 0]])
    proc = np.array([[8, 8], [1, 1]])
    n_jobs, m = 2, 2
    duration = proc.flatten()
    demand = np.zeros((4, 2), dtype=np.int64)
    precedence = []
    for j in range(n_jobs):
        for pos in range(m):
            i = j * m + pos
            demand[i, routing[j, pos]] = 1
            if pos > 0:
                precedence.append((j * m + pos - 1, i))
    capacity = np.ones(2, dtype=np.int64)
    es, ef, ls, lf = A.cpm_bounds(4, duration, precedence)
    lft = A.serial_sgs(4, m, duration, demand, capacity, precedence, A.lft_priority(lf))
    spt = A.serial_sgs(4, m, duration, demand, capacity, precedence, A.spt_priority(duration))
    assert lft.cmax <= spt.cmax


def test_lft_can_lose_to_spt_on_a_specific_instance():
    """Regressionsschutz für einen echten, gefundenen Fund (wie in Stück 7-9): LFT ist eine sehr gute, aber
    KEINE bewiesen optimale Regel - n_jobs=3, m=5, Kapazität=1, Seed 15 zeigt SPT klar vorn."""
    inst = S.generate(3, 5, 15, capacity=1, density=0.0)
    es, ef, ls, lf = A.cpm_bounds(inst.n, inst.duration, inst.precedence)
    lft = A.serial_sgs(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, A.lft_priority(lf))
    spt = A.serial_sgs(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, A.spt_priority(inst.duration))
    assert spt.cmax < lft.cmax


def test_more_capacity_never_increases_the_lft_makespan():
    """Mehr Kapazität kann nur mehr Parallelität ERLAUBEN, nie weniger - Cmax darf mit steigender Kapazität nie
    wachsen (bei sonst gleicher Instanz)."""
    prev_cmax = None
    for cap in range(1, 5):
        inst = S.generate(5, 4, 7, capacity=cap, density=0.2)
        es, ef, ls, lf = A.cpm_bounds(inst.n, inst.duration, inst.precedence)
        result = A.serial_sgs(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, A.lft_priority(lf))
        if prev_cmax is not None:
            assert result.cmax <= prev_cmax + 1e-6
        prev_cmax = result.cmax


def test_demand_never_exceeds_capacity_by_construction():
    """Der Instanz-Generator MUSS sicherstellen, dass keine Aktivität mehr als die Kapazität ihrer Ressource
    braucht - sonst wäre die Instanz von vornherein unlösbar (echter Fund beim Bau, siehe Scratch-Verifikation)."""
    for cap in (1, 2, 3, 4):
        inst = S.generate(6, 4, 3, capacity=cap, density=0.3)
        for k in range(inst.m_resources):
            assert np.all(inst.demand[:, k] <= inst.capacity[k])
