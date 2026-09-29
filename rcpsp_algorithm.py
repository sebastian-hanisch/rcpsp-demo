"""RCPSP (Resource-Constrained Project Scheduling Problem) - der wachsende Endpunkt dieser Linie: verallgemeinert
das GESAMTE Job-Shop-Modell (Stück 8-10) selbst, statt eine neue Regel oder ein neues Verfahren einzuführen.
Job Shop ist der Spezialfall Kapazität=1 auf jeder Ressource + reine Kettenvorrang pro Auftrag (per Test
belegt: RCPSP-Optimum == unabhängiges Job-Shop-Kreis-Modell-Optimum in diesem Fall, siehe tests/).

Drei Bausteine:
1. **CPM-Schranken** (`cpm_bounds`): Vorwärts-/Rückwärtslauf über den Vorranggraphen OHNE Ressourcen (klassische
   Netzplantechnik) - liefert früheste/späteste Start-/Endzeiten je Aktivität, Grundlage jeder Prioritätsregel.
2. **Serielle Schedule-Generation-Scheme (SSGS)** mit Prioritätsregel (`serial_sgs`): die RCPSP-Verallgemeinerung
   von Giffler-Thompson (Stück 8) - baut EINEN zulässigen Zeitplan, indem bei jedem Schritt unter den bereits
   zulässigen (alle Vorgänger fertig) Aktivitäten die mit der höchsten Priorität gewählt und zum frühesten
   ressourcenzulässigen Zeitpunkt eingeplant wird. **LFT** (Latest Finish Time, Kolisch 1995 - WebSearch-
   verifiziert als eine der besten klassischen Prioritätsregeln) ist die Hauptregel; SPT (Wiedersehen mit der
   Wurzel dieser Linie) die falsche Regel hier.
3. **CP-SAT über `AddCumulative`** (`solve_exact`) - technisch NEU für diese Linie (Stück 6-10 nutzten
   `AddCircuit` für Maschinenreihenfolgen; hier ist die Frage nicht "welche Reihenfolge auf einer Kapazität-1-
   Ressource", sondern "wie viele Aktivitäten dürfen eine Kapazität->1-Ressource gleichzeitig belegen" - genau
   das Standardwerkzeug für kumulative Ressourcen)."""

import os
from dataclasses import dataclass

import numpy as np
from ortools.sat.python import cp_model

NUM_SEARCH_WORKERS = min(8, os.cpu_count() or 1)  # NIE hart auf eine Zahl setzen - siehe project memory


@dataclass
class Result:
    start: np.ndarray          # (n,): Startzeit je Aktivität
    end: np.ndarray            # (n,): Fertigstellung je Aktivität
    cmax: float
    resource_finish: np.ndarray  # (m_resources,): späteste Fertigstellung einer Aktivität, die diese Ressource nutzt


# --- CPM-Schranken (ressourcenfrei) -----------------------------------------------------------------------------


def _topo_order(n, precedence):
    indeg = {i: 0 for i in range(n)}
    adj = {i: [] for i in range(n)}
    for p, s in precedence:
        adj[p].append(s)
        indeg[s] += 1
    queue = [i for i in range(n) if indeg[i] == 0]
    order = []
    while queue:
        u = queue.pop()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)
    if len(order) != n:
        raise ValueError("Vorranggraph hat einen Zyklus")
    return order


def cpm_bounds(n, duration, precedence, horizon=None):
    """Klassische Netzplantechnik (Critical Path Method) OHNE Ressourcen: früheste Start-/Endzeit (ES/EF) per
    Vorwärtslauf, späteste Start-/Endzeit (LS/LF) per Rückwärtslauf ab einem Horizont. Grundlage für die
    LFT/SPT-Prioritätsregeln und für den Kollaps-Test gegen Job Shop (dort entspricht das exakt Head/Tail)."""
    succ = {i: [] for i in range(n)}
    pred = {i: [] for i in range(n)}
    for p, s in precedence:
        succ[p].append(s)
        pred[s].append(p)
    order = _topo_order(n, precedence)
    es = np.zeros(n, dtype=np.int64)
    for i in order:
        es[i] = max([es[p] + duration[p] for p in pred[i]], default=0)
    ef = es + duration
    if horizon is None:
        horizon = int(ef.max())
    lf = np.full(n, horizon, dtype=np.int64)
    for i in reversed(order):
        if succ[i]:
            lf[i] = min(lf[s] - duration[s] for s in succ[i])
    ls = lf - duration
    return es, ef, ls, lf


# --- Serielle Schedule-Generation-Scheme mit Prioritätsregel ------------------------------------------------------


def lft_priority(lf):
    """Latest Finish Time (Kolisch 1995) - kleinerer Wert (früher fällig) heißt höhere Priorität."""
    return lambda i: lf[i]


def spt_priority(duration):
    return lambda i: duration[i]


def fifo_priority(i):
    return i


def random_priority(n, rng):
    order = rng.permutation(n)
    rank = {i: r for r, i in enumerate(order)}
    return lambda i: rank[i]


def serial_sgs(n, m_resources, duration, demand, capacity, precedence, priority):
    """Baut EINEN zulässigen Zeitplan: bei jedem Schritt unter den bereits zulässigen Aktivitäten (alle
    Vorgänger fertig) die mit der höchsten Priorität wählen, zum frühesten ressourcenzulässigen Zeitpunkt
    einplanen (ein Zeitfenster ist zulässig, wenn JEDE benötigte Ressource an JEDEM Zeitpunkt im Fenster genug
    freie Kapazität hat)."""
    pred = {i: [] for i in range(n)}
    succ = {i: [] for i in range(n)}
    for p, s in precedence:
        pred[s].append(p)
        succ[p].append(s)

    horizon = int(duration.sum()) + 1
    profile = np.tile(capacity, (horizon, 1)).astype(np.int64)

    start = np.full(n, -1, dtype=np.int64)
    scheduled = set()
    remaining_pred = {i: len(pred[i]) for i in range(n)}
    eligible = [i for i in range(n) if remaining_pred[i] == 0]

    def earliest_feasible_start(i, t_min):
        d = int(duration[i])
        if d == 0:
            return t_min
        t = t_min
        while True:
            window = profile[t:t + d]
            if window.shape[0] == d and np.all(window >= demand[i]):
                return t
            t += 1
            if t + d > horizon:
                raise RuntimeError("Horizont zu klein - sollte bei duration.sum()+1 nie passieren")

    while len(scheduled) < n:
        cand = [i for i in eligible if i not in scheduled]
        i = min(cand, key=priority)
        t_min = max([start[p] + duration[p] for p in pred[i]], default=0)
        t = earliest_feasible_start(i, t_min)
        start[i] = t
        profile[t:t + duration[i]] -= demand[i]
        scheduled.add(i)
        for s in succ[i]:
            remaining_pred[s] -= 1
            if remaining_pred[s] == 0:
                eligible.append(s)

    end = start + duration
    resource_finish = np.zeros(m_resources)
    for k in range(m_resources):
        users = np.where(demand[:, k] > 0)[0]
        if len(users):
            resource_finish[k] = end[users].max()
    return Result(start, end, float(end.max()), resource_finish)


# --- CP-SAT (exakte Gegenprobe über AddCumulative) -----------------------------------------------------------------


def solve_exact(n, m_resources, duration, demand, capacity, precedence, time_limit_seconds=15.0):
    """Ein `NewIntervalVar` je Aktivität, `AddCumulative` je Ressource - anders als das Job-Shop-Kreis-Modell
    (Stück 6-10) keine explizite Reihenfolge-Entscheidung nötig, CP-SAT verwaltet die Kapazitätsbelegung über
    die Zeit selbst."""
    horizon = int(duration.sum()) + 1
    model = cp_model.CpModel()
    start = {}
    end = {}
    intervals = {}
    for i in range(n):
        d = int(duration[i])
        start[i] = model.NewIntVar(0, horizon, f"s{i}")
        end[i] = model.NewIntVar(0, horizon, f"e{i}")
        model.Add(end[i] == start[i] + d)
        intervals[i] = model.NewIntervalVar(start[i], d, end[i], f"iv{i}")
    for p, s in precedence:
        model.Add(start[s] >= end[p])
    for k in range(m_resources):
        ivs = [intervals[i] for i in range(n) if demand[i, k] > 0]
        dems = [int(demand[i, k]) for i in range(n) if demand[i, k] > 0]
        if ivs:
            model.AddCumulative(ivs, dems, int(capacity[k]))

    cmax = model.NewIntVar(0, horizon, "cmax")
    model.AddMaxEquality(cmax, list(end.values()))
    model.Minimize(cmax)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = NUM_SEARCH_WORKERS
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, False

    start_arr = np.array([solver.Value(start[i]) for i in range(n)], dtype=np.int64)
    end_arr = start_arr + duration
    resource_finish = np.zeros(m_resources)
    for k in range(m_resources):
        users = np.where(demand[:, k] > 0)[0]
        if len(users):
            resource_finish[k] = end_arr[users].max()
    result = Result(start_arr, end_arr, float(solver.Value(cmax)), resource_finish)
    return result, status == cp_model.OPTIMAL
