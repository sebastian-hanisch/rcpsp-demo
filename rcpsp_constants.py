"""Konstanten der RCPSP-Demo: Regler, Messreihen-Seeds. Kein Vehikel-Umschalter (bewusste Abweichung vom
Linien-Muster, siehe README) - das wachsende Beispiel ist die Verallgemeinerung des Modells selbst (Kapazität
und Vorrangdichte als Regler), nicht ein zweites Szenario."""

N_JOBS_MIN, N_JOBS_MAX, DEFAULT_N_JOBS = 2, 10, 5
M_RESOURCES_MIN, M_RESOURCES_MAX, DEFAULT_M_RESOURCES = 2, 6, 4
SEED_MAX = 999999
DEFAULT_SEED = 1
SWEEP_SEEDS = tuple(range(100000, 100005))

# Bearbeitungszeiten
P_MIN, P_MAX = 1, 20

# Kapazität je Ressource: bei 1 kollabiert jede Ressource auf eine Job-Shop-Maschine.
CAPACITY_MIN, CAPACITY_MAX, DEFAULT_CAPACITY = 1, 4, 1

# Zusätzliche Vorrangdichte (Kanten zwischen Aktivitäten VERSCHIEDENER Ketten, über die reine Kette pro
# "Auftrag" hinaus): bei 0 kollabiert der Vorranggraph auf reine Ketten (Job-Shop-Auftragsreihenfolge).
DENSITY_MIN, DENSITY_MAX, DEFAULT_DENSITY = 0.0, 0.6, 0.0
DENSITY_STEP = 0.1

# CP-SAT exakte Gegenprobe (AddCumulative statt AddCircuit - technisch neu für diese Linie, siehe README).
# Deutlich schneller als das Job-Shop-Kreis-Modell bei vergleichbarer Größe (gemessen, siehe README).
EXACT_MAX_N = 20
EXACT_TIME_LIMIT_SECONDS = 15.0


def _preset(n_jobs=DEFAULT_N_JOBS, m_resources=DEFAULT_M_RESOURCES, capacity=DEFAULT_CAPACITY, density=DEFAULT_DENSITY):
    return {"n_jobs": n_jobs, "m_resources": m_resources, "seed": DEFAULT_SEED, "capacity": capacity, "density": density}


PRESETS = {
    "Standardfall (Voreinstellung)": _preset(),
    "Job-Shop-Äquivalent": _preset(capacity=1, density=0.0),
    "Hohe Kapazität, dicht vernetzt": _preset(capacity=CAPACITY_MAX, density=DENSITY_MAX),
    "Kleine Instanz (Handrechnung)": _preset(n_jobs=2, m_resources=3),
    "Große Instanz (Skalierung)": _preset(n_jobs=N_JOBS_MAX, m_resources=M_RESOURCES_MAX),
}
# Werte in PRESET_HELP nach der Messreihe (rcpsp_evaluation.run_config) final eingetragen.
PRESET_HELP = {
    "Standardfall (Voreinstellung)": f"{DEFAULT_N_JOBS} Ketten über {DEFAULT_M_RESOURCES} Ressourcen, Kapazität {DEFAULT_CAPACITY}: LFT (Latest Finish Time) misst sich gegen SPT, FIFO und Zufall.",
    "Job-Shop-Äquivalent": "Kapazität 1 überall + keine zusätzliche Vorrangdichte: strukturell EXAKT das Job-Shop-Modell aus Stück 8-10 dieser Linie.",
    "Hohe Kapazität, dicht vernetzt": "Mehrere Aktivitäten teilen sich jede Ressource gleichzeitig UND es gibt viele Vorrangkanten quer über die Ketten hinweg - die volle Verallgemeinerung.",
    "Kleine Instanz (Handrechnung)": "6 Aktivitäten: klein genug, um den kritischen Pfad von Hand nachzuvollziehen.",
    "Große Instanz (Skalierung)": f"{N_JOBS_MAX} Ketten über {M_RESOURCES_MAX} Ressourcen: die serielle Konstruktion bleibt schnell, CP-SAT wird spürbar teurer.",
}
