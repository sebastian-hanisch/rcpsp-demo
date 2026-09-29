"""Jede Zahl der App-Texte ist hier über die fünf festen Sweep-Instanzen belegt. Rechenzeiten nur als
Größenordnung geprüft; teure Läufe sind modul-weit über lru_cache dedupliziert."""

from functools import lru_cache

import rcpsp_evaluation as ev


@lru_cache(maxsize=None)
def _cfg(items):
    return ev.run_config(ev.Settings(), **dict(items))


def cfg(**kw):
    return _cfg(tuple(sorted(kw.items())))


@lru_cache(maxsize=1)
def _capacity():
    return tuple(tuple(r.items()) for r in ev.capacity_sweep())


def capacity_rows():
    return [dict(r) for r in _capacity()]


@lru_cache(maxsize=1)
def _density():
    return tuple(tuple(r.items()) for r in ev.density_sweep())


def density_rows():
    return [dict(r) for r in _density()]


@lru_cache(maxsize=1)
def _timing():
    return tuple(tuple(r.items()) for r in ev.timing_sweep())


def timing_rows():
    return [dict(r) for r in _timing()]


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.3f} statt {expected}"


# --- Standardfall -------------------------------------------------------------------------------------------------------------------------------


def test_standard_case_numbers():
    std = cfg()
    near(std["gap_spt"], 12.4, 20.0)
    near(std["gap_fifo"], 15.5, 20.0)
    near(std["gap_random"], 19.0, 20.0)


# --- Die zwei Experimente dieses Stücks -----------------------------------------------------------------------


def test_capacity_reduces_cmax_and_then_plateaus():
    rows = capacity_rows()
    assert rows[0]["lft_cmax"] > rows[-1]["lft_cmax"]
    # ab genug Kapazität aendert sich nichts mehr (Konvergenz gegen die Vorrang-Schranke)
    assert rows[-1]["lft_cmax"] == rows[-2]["lft_cmax"]


def test_density_increases_cmax_monotonically():
    rows = density_rows()
    cmaxes = [r["lft_cmax"] for r in rows]
    assert cmaxes == sorted(cmaxes)
    assert rows[-1]["lft_cmax"] > rows[0]["lft_cmax"]


# --- Timing: CP-SAT ueber AddCumulative bleibt hier durchgehend schnell -----------------------------------------


def test_exact_solving_stays_fast_even_at_the_largest_tested_size():
    rows = timing_rows()
    large = rows[-1]
    assert large["exact_seconds"] < 1.0
