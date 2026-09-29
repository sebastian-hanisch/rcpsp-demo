"""Instanz-Generator der RCPSP-Demo: `n_jobs` Ketten über `m_resources` Ressourcen (wie Job Shop, Stück 8-10),
aber mit zwei Reglern, die das Modell VERALLGEMEINERN statt ein zweites Vehikel zu sein (siehe README):
- `capacity`: Kapazität JEDER Ressource - bei 1 kollabiert jede Ressource auf eine Job-Shop-Maschine.
- `density`: zusätzliche Vorrangkanten ZWISCHEN verschiedenen Ketten - bei 0 kollabiert der Vorranggraph auf
  reine Ketten (Job-Shop-Auftragsreihenfolge). Kanten nur in aufsteigender Aktivitäts-ID, garantiert azyklisch."""

from dataclasses import dataclass

import numpy as np

import rcpsp_constants as C


@dataclass(frozen=True)
class Instance:
    n_jobs: int
    m_resources: int
    n: int                     # n_jobs * m_resources, Gesamtzahl Aktivitäten
    duration: np.ndarray       # (n,)
    demand: np.ndarray         # (n, m_resources)
    capacity: np.ndarray       # (m_resources,)
    precedence: tuple          # Liste (Vorgänger, Nachfolger), jeweils Aktivitäts-ID
    routing: np.ndarray        # (n_jobs, m_resources): PRIMÄRE Ressource je Kettenposition (wie Job-Shop-Routing)
    seed: int


def act_id(j, pos, m_resources):
    return j * m_resources + pos


def generate(n_jobs, m_resources, seed, capacity=C.DEFAULT_CAPACITY, density=C.DEFAULT_DENSITY, p_min=C.P_MIN, p_max=C.P_MAX):
    rng = np.random.default_rng(seed)
    n = n_jobs * m_resources
    routing = np.array([rng.permutation(m_resources) for _ in range(n_jobs)])
    proc = rng.integers(p_min, p_max + 1, size=(n_jobs, m_resources)).astype(np.int64)

    duration = np.zeros(n, dtype=np.int64)
    demand = np.zeros((n, m_resources), dtype=np.int64)
    precedence = []
    for j in range(n_jobs):
        for pos in range(m_resources):
            i = act_id(j, pos, m_resources)
            duration[i] = proc[j, pos]
            demand[i, routing[j, pos]] = 1
            if pos > 0:
                precedence.append((act_id(j, pos - 1, m_resources), i))

    existing = set(precedence)
    for i in range(1, n):
        j_owner = i // m_resources
        for i2 in range(i):
            if i2 // m_resources == j_owner:
                continue  # innerhalb derselben Kette schon durch die Vorrangkette abgedeckt
            if rng.random() < density:
                edge = (i2, i)
                if edge not in existing:
                    precedence.append(edge)
                    existing.add(edge)

    capacity_arr = np.full(m_resources, capacity, dtype=np.int64)
    return Instance(n_jobs, m_resources, n, duration, demand, capacity_arr, tuple(precedence), routing, seed)
