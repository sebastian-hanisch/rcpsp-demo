"""RCPSP - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Elftes und letztes Stück der Konzepte-Linie "Klassische Scheduling-Theorie", der wachsende Endpunkt: statt
einer neuen Regel oder eines neuen Verfahrens verallgemeinert dieses Stück das GESAMTE Job-Shop-Modell (Stück
8-10) selbst - Ressourcen statt nur Maschinen (Kapazität ≥ 1 statt nur 1), allgemeiner Vorranggraph statt nur
Ketten pro Auftrag. Job Shop ist strukturell der Spezialfall Kapazität=1 + reine Kette (per Test belegt).
LFT (Latest Finish Time, Kolisch 1995) ist die Hauptregel; CP-SAT löst über `AddCumulative` exakt. Siehe README.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import rcpsp_constants as C
from rcpsp_evaluation import Settings, SWEEP_LABELS, analyse, capacity_sweep, density_sweep, sweep, timing_sweep
from rcpsp_presets import apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sync_query_params
from rcpsp_visualization import build_activities_chart, build_capacity_sweep, build_density_sweep, build_resource_finish_comparison, build_resource_gantt, build_sweep, build_timing

st.set_page_config(page_title="RCPSP – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _capacity_sweep(base):
    return capacity_sweep(base)


@st.cache_data(show_spinner=False)
def _density_sweep(base):
    return density_sweep(base)


@st.cache_data(show_spinner=False)
def _timing():
    return timing_sweep()


def _fmt_int(x):
    return f"{int(round(x)):,}".replace(",", ".")


def _fmt_pct(x):
    """Vorzeichen-korrekt: `+49.3 %` (Vergleichsregel schlechter als LFT) oder `-x %` (LFT ist keine bewiesen
    optimale Regel - kann auf einzelnen Instanzen auch verlieren, siehe 🚧)."""
    return f"{x:+.1f} %"


st.title("🏗️ RCPSP – der wachsende Endpunkt dieser Linie")
st.markdown(
    r"""
**Elftes und letztes Stück dieser Linie.** Statt einer neuen Regel oder eines neuen Verfahrens wird hier das
GESAMTE Job-Shop-Modell (Stück 8-10) selbst verallgemeinert: **Ressourcen** statt nur Maschinen (eine Ressource
kann mehrere Aktivitäten GLEICHZEITIG tragen, bis zu ihrer Kapazität) und ein **allgemeiner Vorranggraph** statt
nur einer festen Kette pro Auftrag. Job Shop ist der Spezialfall Kapazität = 1 überall + reine Kette - strukturell
identisch, nicht nur ähnlich (per Test belegt). **LFT** (Latest Finish Time, Kolisch 1995) baut einen Zeitplan
Schritt für Schritt; **CP-SAT** löst über `AddCumulative` exakt - neu für diese Linie (Stück 6-10 nutzten
`AddCircuit` für Maschinenreihenfolgen).
"""
)
st.caption(
    "Elftes Stück der Konzepte-Linie „Klassische Scheduling-Theorie“ - der wachsende Endpunkt. KEIN Vehikel-"
    "Umschalter hier (bewusste Abweichung vom Linien-Muster): das wachsende Beispiel sind die Regler "
    "„Ressourcenkapazität“ und „Vorrangdichte“ selbst, siehe README."
)

with st.expander("So funktioniert die serielle Konstruktion mit LFT", expanded=True):
    st.markdown(
        r"""
1. **CPM-Schranken berechnen.** Ohne Ressourcen: früheste/späteste Start- und Endzeit je Aktivität (klassische
   Netzplantechnik, Vorwärts- und Rückwärtslauf über den Vorranggraphen).
2. **Zulässige Aktivitäten bestimmen.** Alle, deren Vorgänger bereits eingeplant sind.
3. **Per Priorität wählen.** LFT: die Aktivität mit der frühesten spätest-zulässigen Fertigstellung zuerst.
4. **Zum frühesten zulässigen Zeitpunkt einplanen.** Der früheste Zeitpunkt, an dem JEDE benötigte Ressource an
   JEDEM Zeitpunkt der Dauer genug freie Kapazität hat.
5. **Wiederholen**, bis alle Aktivitäten eingeplant sind.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_names = list(C.PRESETS.keys())
cols = st.columns(len(preset_names))
for col, name in zip(cols, preset_names):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name], key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_jobs = st.slider("Ketten", *bounds("n_jobs_slider"), key="n_jobs_slider",
                        help="Jede Kette ist eine Folge von Aktivitäten (wie ein Auftrag im Job Shop).")
    m_resources = st.slider("Ressourcen", *bounds("m_resources_slider"), key="m_resources_slider",
                             help="Jede Kettenposition braucht ihre PRIMÄRE Ressource - wie eine Maschine im Job Shop.")
    capacity = st.slider("Kapazität je Ressource", *bounds("capacity_slider"), key="capacity_slider",
                          help="Bei 1 kollabiert jede Ressource auf eine Job-Shop-Maschine (nur eine Aktivität gleichzeitig).")
    density = st.slider("Zusätzliche Vorrangdichte", *bounds("density_slider"), key="density_slider", step=C.DENSITY_STEP, format="%.1f",
                         help="Bei 0 kollabiert der Vorranggraph auf reine Ketten (Job-Shop-Auftragsreihenfolge).")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Seed für Dauern, Routing und Vorrangkanten.")

sync_query_params({"n_jobs_slider": int(n_jobs), "m_resources_slider": int(m_resources), "seed_input": int(seed),
                    "capacity_slider": int(capacity), "density_slider": float(density)})

settings = Settings(int(n_jobs), int(m_resources), int(seed), capacity=int(capacity), density=float(density))
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst = a.inst
data_key = settings

# --- RCPSP in Aktion --------------------------------------------------------------------------------------------

st.markdown("## 🎯 RCPSP in Aktion")
STEP_LABELS = {1: "1 · Aktivitäten", 2: "2 · Einplanen", 3: "3 · Ergebnis"}
if "rcpsp_step" not in st.session_state or st.session_state.get("rcpsp_step_owner") != data_key:
    st.session_state["rcpsp_step"] = 1
    st.session_state["rcpsp_step_owner"] = data_key
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="rcpsp_step", format_func=lambda s: STEP_LABELS[s])

total_activities = inst.n
if step == 2:
    it_col, _ = st.columns([5, 2])
    with it_col:
        upto = st.slider("Eingeplante Aktivitäten", 1, total_activities, value=total_activities, key="rcpsp_upto")
else:
    upto = total_activities

view_slot = st.empty()
with view_slot.container():
    if step == 1:
        st.markdown(f"**{n_jobs} Ketten, unsortiert** (gestapelt in Kettenposition, Farbe nach primärer Ressource)")
        st.plotly_chart(build_activities_chart(inst.routing, inst.duration, int(n_jobs), int(m_resources)), width="stretch", key="s1_activities")
    elif step == 2:
        order = sorted(range(total_activities), key=lambda i: a.lft.end[i])[:upto]
        mask = set(order)
        start_masked = a.lft.start.copy()
        end_masked = a.lft.end.copy()
        for i in range(total_activities):
            if i not in mask:
                start_masked[i] = -1e9
                end_masked[i] = -1e9
        st.markdown(f"**LFT-Zeitplan nach {upto} von {total_activities} eingeplanten Aktivitäten** (Farbe nach Kette)")
        visible_demand = inst.demand.copy()
        for i in range(total_activities):
            if i not in mask:
                visible_demand[i] = 0
        st.plotly_chart(build_resource_gantt(inst.routing, int(n_jobs), int(m_resources), visible_demand, start_masked, end_masked, inst.capacity), width="stretch", key=f"s2_sched_{upto}")
    else:
        st.markdown("**Fertigstellung je Ressource: LFT gegen SPT**")
        st.plotly_chart(build_resource_finish_comparison(a.lft.resource_finish, a.spt.resource_finish), width="stretch", key="s3_finish")

if step == 1:
    st.caption(f"Bearbeitungszeiten zwischen {int(inst.duration.min())} und {int(inst.duration.max())} Minuten (Seed {seed}). Jede Kette hat eine eigene Ressourcenreihenfolge.")
elif step == 2:
    st.caption(f"Jede Zeile ist eine Ressource (bei Kapazität >1 mehrere Zeilen für parallele Slots), jeder Balken eine Aktivität, Farbe = Kette.")
else:
    st.caption(f"LFT: Cmax {_fmt_int(a.lft.cmax)}. SPT: {_fmt_int(a.spt.cmax)} (Differenz {_fmt_pct(a.gap_spt)}). Die gestrichelten Linien markieren jeweils die höchste Last (= Cmax).")

st.markdown("---")

# --- Ergebnis -------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was die Prioritätsregel bringt")
st.caption("**Abstand:** Cmax einer Regel gegenüber LFT in Prozent - kann negativ werden, LFT ist keine bewiesen optimale Regel.")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("LFT (Cmax)", _fmt_int(a.lft.cmax), help="Die Zielgröße: Projektdauer mit der Latest-Finish-Time-Regel.")
m2.metric("SPT (Wurzel dieser Linie!)", _fmt_pct(a.gap_spt), delta_color="off", help="SPT war für Stück 1 dieser Linie beweisbar optimal - hier, im RCPSP mit Cmax-Ziel, schneidet es häufig schlecht ab.")
m3.metric("FIFO (naiv)", _fmt_pct(a.gap_fifo), delta_color="off", help="Keine Prioritätsinformation - Aktivitäten in ID-Reihenfolge.")
m4.metric(f"Zufällige Priorität (Mittel über {a.random_runs})", _fmt_pct(a.gap_random), delta_color="off")
if a.optimal is not None and a.optimal_proven:
    m5.metric("CP-SAT (exakte Gegenprobe)", "trifft LFT exakt" if a.lft_matches_optimum else f"{a.lft_ratio_to_optimum:.3f}× Optimum", delta_color="off",
              help="OR-Tools CP-SAT hat diese Instanz über AddCumulative bewiesen exakt gelöst.")
elif a.optimal is not None:
    m5.metric("CP-SAT", "Zeitlimit erreicht", delta_color="off")
else:
    m5.metric("CP-SAT", f"erst ab n ≤ {C.EXACT_MAX_N}", delta_color="off")

if a.gap_spt < 0 or a.gap_fifo < 0 or a.gap_random < 0:
    candidates = [("SPT", a.gap_spt), ("FIFO", a.gap_fifo), ("eine zufällige Priorität", a.gap_random)]
    worse_than, worst_gap = min(candidates, key=lambda c: c[1])
    st.warning(f"⚠️ LFT schneidet hier sogar schlechter ab als {worse_than}: {abs(worst_gap):.1f} % mehr. Kein Fehler - LFT ist eine sehr gute, aber keine bewiesen optimale Regel (anders als SPT für die Wurzel Stück 1 dieser Linie).")
else:
    st.success(f"✅ LFT ist {a.gap_spt:.1f} % besser als SPT, {a.gap_fifo:.1f} % besser als FIFO und {a.gap_random:.1f} % besser als eine zufällige Priorität.")

st.markdown("---")

# --- Sweeps --------------------------------------------------------------------------------------------------------

st.subheader("📐 Wie stark hängt der Vorsprung von der Instanz ab?")
sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda k: SWEEP_LABELS[k], key="sweep_select")
if st.button("Sweep über 5 feste Instanzen berechnen (dauert wenige Sekunden)", key="sweep_start"):
    st.session_state["sweep_done"] = st.session_state.get("sweep_done", set()) | {sweep_param}
if sweep_param in st.session_state.get("sweep_done", set()):
    rows_sweep = _sweep(sweep_param, Settings())
    st.plotly_chart(build_sweep(rows_sweep, SWEEP_LABELS[sweep_param]), width="stretch", key="sweep_chart")
    st.caption("Mittel über 5 feste Instanzen (Seeds 100000–100004) mit je 3 Ketten-Seeds für die Vergleichspriorität.")

st.markdown("---")

# --- Experimente -----------------------------------------------------------------------------------------------

st.subheader("🔬 Wie stark hilft mehr Ressourcenkapazität?")
if st.button("Kapazität 1 bis 4 durchfahren (dauert wenige Sekunden)", key="cap_start"):
    st.session_state["cap_on"] = True
if st.session_state.get("cap_on"):
    rows_c = _capacity_sweep(Settings())
    st.plotly_chart(build_capacity_sweep(rows_c), width="stretch", key="cap_chart")
    st.caption("Mehr Kapazität erlaubt mehr Parallelität - Cmax fällt, konvergiert aber gegen die reine Vorrang-Schranke (CPM ohne Ressourcen), sobald genug Kapazität da ist.")

st.markdown("---")

st.subheader("🔬 Wie teuer ist zusätzlicher Vorrang?")
if st.button("Vorrangdichte 0 bis 0,6 durchfahren (dauert wenige Sekunden)", key="dens_start"):
    st.session_state["dens_on"] = True
if st.session_state.get("dens_on"):
    rows_d = _density_sweep(Settings())
    st.plotly_chart(build_density_sweep(rows_d), width="stretch", key="dens_chart")
    st.caption("Mehr Vorrangkanten schränken die mögliche Parallelität ein - Cmax wächst.")

st.markdown("---")

st.subheader("🔬 Wie teuer ist eine exakte Lösung wirklich?")
if st.button("Rechenzeit über mehrere Größen messen (dauert etwa 1 Sekunde)", key="timing_start"):
    st.session_state["timing_on"] = True
if st.session_state.get("timing_on"):
    rows_t = _timing()
    st.plotly_chart(build_timing(rows_t), width="stretch", key="timing_chart")
    last = rows_t[-1]
    st.caption(f"Bei {last['value']} Aktivitäten braucht CP-SAT (AddCumulative) {last['exact_seconds']*1000:.1f} ms, die serielle Konstruktion {last['sgs_seconds']*1000:.3f} ms - AddCumulative bleibt hier deutlich schneller als das Kreis-Modell (AddCircuit) aus Stück 6-10 bei vergleichbarer Größe.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Jede Aktivität braucht genau eine Ressource, Bedarf 1** | Aktivitäten, die MEHRERE Ressourcen gleichzeitig brauchen (z. B. Werkzeug UND Facharbeiter), sind hier nicht modelliert. | Kein direkter Nachfolger in dieser Linie |
| **Nur erneuerbare Ressourcen** | Ein Budget oder Materialverbrauch (nicht-erneuerbare Ressource, einmal verbraucht) braucht ein anderes Modell. | Kreuzverweis: Exakte-Suche-Linie |
| **Eine feste Dauer je Aktivität** | Multi-Mode-RCPSP erlaubt mehrere Dauer/Ressourcen-Kombinationen je Aktivität (schneller = mehr Ressourcen). | Kein direkter Nachfolger in dieser Linie |
| **LFT ist eine sehr gute, aber keine bewiesen optimale Regel** | Auf einzelnen Instanzen kann LFT schlechter abschneiden als SPT/FIFO/Zufall (siehe Warnmeldung oben). | Kein direkter Nachfolger in dieser Linie |
"""
)
st.caption(
    "Elftes und letztes Stück der Linie „Klassische Scheduling-Theorie“ - der wachsende Endpunkt. Job Shop "
    "(Stück 8-10) ist der Spezialfall Kapazität=1 + reine Kette, per Test belegt (siehe README)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem** (RCPSP, $C_{\max}$): $n$ Aktivitäten mit Dauer $d_i$, einem Vorranggraphen (beliebige DAG, nicht nur
Ketten) und $K$ erneuerbaren Ressourcen mit Kapazität $c_k$; Aktivität $i$ braucht $r_{ik}$ Einheiten von
Ressource $k$ WÄHREND ihrer gesamten Dauer. Gesucht: Startzeiten $S_i$, die Vorrang UND zu jedem Zeitpunkt
$\sum_{i: S_i \le t < S_i+d_i} r_{ik} \le c_k$ für jede Ressource $k$ einhalten und $C_{\max} = \max_i (S_i+d_i)$
minimieren - stark NP-schwer, Verallgemeinerung von Job Shop ($K=m$, $c_k=1$, reine Ketten).

**CPM-Schranken.** $ES_i$/$EF_i$ (frühester Start/Ende) per Vorwärtslauf, $LS_i$/$LF_i$ (spätester Start/Ende
bei gegebenem Horizont) per Rückwärtslauf über den Vorranggraphen OHNE Ressourcen.

**LFT** (Kolisch 1995): Priorität $= LF_i$ - kleinerer Wert (früher fällig) zuerst.

**CP-SAT-Modell** (`solve_exact`): ein `NewIntervalVar` je Aktivität, `AddCumulative(intervals_k, demands_k,
c_k)` je Ressource $k$ - im Gegensatz zum Kreis-Modell (Stück 6-10) keine explizite Reihenfolge-Entscheidung
nötig.

Implementiert in `rcpsp_algorithm.py` (CPM, serielle Konstruktion, Prioritätsregeln, CP-SAT),
`rcpsp_scenario.py` (Instanz-Generator mit Kapazitäts-/Vorrangdichte-Reglern), `rcpsp_evaluation.py`
(Kennzahlen, Sweep, Kapazitäts-/Vorrang-Experimente, Timing-Messreihe).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
