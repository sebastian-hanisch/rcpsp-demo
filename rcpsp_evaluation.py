"""Auswertung der RCPSP-Demo: LFT (Kolisch 1995) gegen SPT (Wurzel dieser Linie - hier die falsche Regel),
FIFO, Zufall, gegen CP-SAT als exakte Gegenprobe (nur kleine n), und die zwei Experimente, die das wachsende
Beispiel dieses Stücks ausmachen - was bringt mehr Ressourcenkapazität, was kostet mehr Vorrang."""

import time
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import rcpsp_algorithm as A
import rcpsp_constants as C
import rcpsp_scenario as S


@dataclass(frozen=True)
class Settings:
    n_jobs: int = C.DEFAULT_N_JOBS
    m_resources: int = C.DEFAULT_M_RESOURCES
    seed: int = C.DEFAULT_SEED
    capacity: int = C.DEFAULT_CAPACITY
    density: float = C.DEFAULT_DENSITY
    chain_seed: int = 0


@lru_cache(maxsize=512)
def instance(n_jobs, m_resources, seed, capacity, density):
    return S.generate(n_jobs, m_resources, seed, capacity=capacity, density=density)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    lft: object                 # Hauptregel: Latest Finish Time (Kolisch 1995)
    spt: object                 # falsche Regel hier - obwohl SPT die Wurzel dieser Linie ist!
    fifo: object
    random_mean: float
    random_runs: int
    optimal: object             # None, wenn n > EXACT_MAX_N
    optimal_proven: bool

    @property
    def gap_spt(self):
        return _gap(self.spt.cmax, self.lft.cmax)

    @property
    def gap_fifo(self):
        return _gap(self.fifo.cmax, self.lft.cmax)

    @property
    def gap_random(self):
        return _gap(self.random_mean, self.lft.cmax)

    @property
    def lft_matches_optimum(self):
        return self.optimal is not None and abs(self.lft.cmax - self.optimal.cmax) < 1e-6

    @property
    def lft_ratio_to_optimum(self):
        return None if self.optimal is None or self.optimal.cmax <= 1e-9 else self.lft.cmax / self.optimal.cmax


def _gap(value, baseline):
    if baseline <= 1e-9:
        return 0.0 if value <= 1e-9 else float(value)
    return 100.0 * (value - baseline) / baseline


def analyse(settings, random_draws=20):
    inst = instance(settings.n_jobs, settings.m_resources, settings.seed, settings.capacity, settings.density)
    n, m = inst.n, inst.m_resources
    es, ef, ls, lf = A.cpm_bounds(n, inst.duration, inst.precedence)

    def ev(priority):
        return A.serial_sgs(n, m, inst.duration, inst.demand, inst.capacity, inst.precedence, priority)

    lft = ev(A.lft_priority(lf))
    spt = ev(A.spt_priority(inst.duration))
    fifo = ev(A.fifo_priority)
    rng = np.random.default_rng(settings.chain_seed)
    random_totals = [ev(A.random_priority(n, rng)).cmax for _ in range(random_draws)]
    optimal, proven = (A.solve_exact(n, m, inst.duration, inst.demand, inst.capacity, inst.precedence, C.EXACT_TIME_LIMIT_SECONDS)
                        if n <= C.EXACT_MAX_N else (None, False))
    return Analysis(settings, inst, lft, spt, fifo, float(np.mean(random_totals)), random_draws, optimal, proven)


# --- Sweeps und Tabellen -----------------------------------------------------------------------------------------------------------------------


def _mean(rows, key):
    return float(np.mean([r[key] for r in rows]))


def run_config(base, seeds=C.SWEEP_SEEDS, chains=3, **changes):
    s0 = replace(base, **changes)
    rows = []
    for seed in seeds:
        for ch in range(chains):
            a = analyse(replace(s0, seed=seed, chain_seed=ch))
            rows.append({"gap_spt": a.gap_spt, "gap_fifo": a.gap_fifo, "gap_random": a.gap_random})
    out = {k: _mean(rows, k) for k in rows[0]}
    out["n_runs"] = len(rows)
    return out


SWEEP_VALUES = {"n_jobs": (2, 3, 5, 7, 10), "m_resources": (2, 3, 4, 5, 6)}
SWEEP_LABELS = {"n_jobs": "Ketten", "m_resources": "Ressourcen"}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]


def capacity_sweep(base=Settings(), capacities=range(C.CAPACITY_MIN, C.CAPACITY_MAX + 1)):
    """Das erste Experiment dieses Stücks: wie stark hilft mehr Ressourcenkapazität? Mehr Kapazität erlaubt mehr
    Parallelität - Cmax sollte fallen, konvergiert aber gegen die reine Vorrang-Schranke (CPM ohne Ressourcen)."""
    rows = []
    for cap in capacities:
        r = run_config(base, capacity=cap)
        rows.append({"value": cap, "gap_spt": r["gap_spt"]})
        # zusätzlich der rohe LFT-Cmax-Mittelwert, nicht nur der Abstand zu SPT
        cmaxes = []
        for seed in C.SWEEP_SEEDS:
            a = analyse(replace(base, seed=seed, capacity=cap))
            cmaxes.append(a.lft.cmax)
        rows[-1]["lft_cmax"] = float(np.mean(cmaxes))
    return rows


def density_sweep(base=Settings(), densities=(0.0, 0.1, 0.2, 0.3, 0.4, 0.6)):
    """Das zweite Experiment: wie teuer ist zusätzlicher Vorrang? Mehr Vorrangkanten schränken die mögliche
    Parallelität ein - Cmax sollte wachsen."""
    rows = []
    for dens in densities:
        cmaxes = []
        for seed in C.SWEEP_SEEDS:
            a = analyse(replace(base, seed=seed, density=dens))
            cmaxes.append(a.lft.cmax)
        rows.append({"value": dens, "lft_cmax": float(np.mean(cmaxes))})
    return rows


def timing_sweep(n_jobs_values=(2, 3, 4, 5, 7, 10), m_resources=C.DEFAULT_M_RESOURCES, seed=C.DEFAULT_SEED):
    """Gemessene Rechenzeit: CP-SAT (`AddCumulative`, im schlimmsten Fall exponentiell) gegen die serielle
    Konstruktion (polynomiell)."""
    rows = []
    for n_jobs in n_jobs_values:
        inst = instance(n_jobs, m_resources, seed, C.DEFAULT_CAPACITY, C.DEFAULT_DENSITY)
        t0 = time.perf_counter()
        A.solve_exact(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, C.EXACT_TIME_LIMIT_SECONDS)
        t_exact = time.perf_counter() - t0
        es, ef, ls, lf = A.cpm_bounds(inst.n, inst.duration, inst.precedence)
        t0 = time.perf_counter()
        for _ in range(50):
            A.serial_sgs(inst.n, inst.m_resources, inst.duration, inst.demand, inst.capacity, inst.precedence, A.lft_priority(lf))
        t_sgs = (time.perf_counter() - t0) / 50
        rows.append({"value": inst.n, "exact_seconds": t_exact, "sgs_seconds": t_sgs})
    return rows
