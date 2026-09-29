"""Plotly-Abbildungen der RCPSP-Demo: Aktivitätsübersicht, Ressourcen-Gantt (eine ZEILE JE KAPAZITÄTS-SLOT -
neu für diese Linie, weil eine Ressource jetzt MEHRERE Aktivitäten gleichzeitig tragen kann; Slot-Zuweisung per
gieriger Intervallfärbung, da jede Aktivität hier genau 1 Einheit einer Ressource braucht), Ressourcen-Endzeit-
Vergleich, Sweeps. Achsen sind gesperrt (fixedrange). Ein Plotly-Trace JE ZEILE (siehe
[[feedback_plotly_many_traces_per_category_shrinks_bars]])."""

import plotly.graph_objects as go

RESOURCE_COLORS = ["#4c78a8", "#54a24b", "#e45756", "#f58518", "#b279a2", "#9c755f"]
JOB_COLORS = ["#4c78a8", "#54a24b", "#e45756", "#f58518", "#b279a2", "#9c755f", "#ff9da6", "#9d755d", "#bab0ac", "#eeca3b"]
SPT_COLOR = "#e45756"
FIFO_COLOR = "#f58518"
RANDOM_COLOR = "#7f7f7f"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _job_color(j):
    return JOB_COLORS[j % len(JOB_COLORS)]


def build_activities_chart(routing, duration, n_jobs, m_resources):
    """Ein gestapelter Balken je Kette - jedes Segment ist eine Aktivität in ihrer Kettenposition, eingefärbt
    nach der PRIMÄREN Ressource."""
    fig = go.Figure()
    for pos in range(m_resources):
        xs, ys, colors, hover = [], [], [], []
        for j in range(n_jobs):
            k = int(routing[j, pos])
            i = j * m_resources + pos
            xs.append(j)
            ys.append(int(duration[i]))
            colors.append(RESOURCE_COLORS[k % len(RESOURCE_COLORS)])
            hover.append(f"Kette {j}, Position {pos + 1}: Ressource {k + 1}, Dauer {duration[i]}")
        fig.add_trace(go.Bar(x=xs, y=ys, marker_color=colors, hovertext=hover, hoverinfo="text", showlegend=False))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Kette")
    fig.update_yaxes(title_text="Bearbeitungszeit (gestapelt über alle Aktivitäten)")
    return _base(fig, 280)


def _assign_slots(users, start, end, capacity_k):
    """Gierige Intervallfärbung: jede Aktivität (Bedarf genau 1) bekommt den ERSTEN Slot, dessen letzte
    Aktivität bereits fertig ist, sonst einen neuen Slot - Anzahl Slots ist bei einem zulässigen Zeitplan nie
    größer als die Kapazität."""
    users_sorted = sorted(users, key=lambda i: start[i])
    slot_free_at = []  # slot_free_at[s] = Zeitpunkt, ab dem Slot s wieder frei ist
    slot_of = {}
    for i in users_sorted:
        placed = False
        for s in range(len(slot_free_at)):
            if slot_free_at[s] <= start[i]:
                slot_free_at[s] = end[i]
                slot_of[i] = s
                placed = True
                break
        if not placed:
            slot_of[i] = len(slot_free_at)
            slot_free_at.append(end[i])
    return slot_of, max(1, len(slot_free_at))


def build_resource_gantt(routing, n_jobs, m_resources, demand, start, end, capacity):
    """EINE ZEILE JE (RESSOURCE, KAPAZITÄTS-SLOT) - bei Kapazität 1 identisch zum Ein-Zeile-je-Maschine-Gantt
    aus Stück 6-10, bei Kapazität >1 zeigt jede zusätzliche Zeile eine parallele Belegung."""
    n = len(start)
    fig = go.Figure()
    rows = []
    row_traces = []
    for k in range(m_resources):
        users = [i for i in range(n) if demand[i, k] > 0]
        if not users:
            continue
        slot_of, n_slots = _assign_slots(users, start, end, capacity[k])
        for s in range(n_slots):
            row_label = f"Ressource {k + 1}" if n_slots == 1 else f"Ressource {k + 1} · Slot {s + 1}"
            rows.append(row_label)
            ops = [i for i in users if slot_of[i] == s]
            ops.sort(key=lambda i: start[i])
            xs = [float(end[i] - start[i]) for i in ops]
            bases = [float(start[i]) for i in ops]
            colors = [_job_color(i // m_resources) for i in ops]
            customdata = [i // m_resources for i in ops]
            row_traces.append((row_label, xs, bases, colors, customdata))
    for row_label, xs, bases, colors, customdata in row_traces:
        fig.add_trace(go.Bar(x=xs, y=[row_label] * len(xs), base=bases, orientation="h", width=0.6,
                              marker=dict(color=colors, line=dict(width=1, color="white")),
                              customdata=customdata, showlegend=False, hovertemplate="Kette %{customdata}<br>Dauer %{x}<extra></extra>"))
    fig.update_xaxes(title_text="Zeit")
    fig.update_yaxes(categoryorder="array", categoryarray=rows, autorange="reversed")
    return _base(fig, max(160, 32 * max(1, len(rows))))


def build_resource_finish_comparison(lft_finish, spt_finish):
    m = len(lft_finish)
    resources = [f"R{k + 1}" for k in range(m)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=resources, y=lft_finish.tolist(), name="LFT", marker_color=RESOURCE_COLORS[0]))
    fig.add_trace(go.Bar(x=resources, y=spt_finish.tolist(), name="SPT", marker_color=SPT_COLOR))
    fig.add_hline(y=float(lft_finish.max()), line=dict(color=RESOURCE_COLORS[0], width=1.5, dash="dot"))
    fig.add_hline(y=float(spt_finish.max()), line=dict(color=SPT_COLOR, width=1.5, dash="dot"))
    fig.update_xaxes(title_text="Ressource")
    fig.update_yaxes(title_text="Fertigstellung der letzten nutzenden Aktivität")
    fig.update_layout(barmode="group")
    return _base(fig, 320)


def build_sweep(rows, param_label, value_key="value",
                 y_keys=(("gap_spt", "LFT gegen SPT", SPT_COLOR), ("gap_fifo", "LFT gegen FIFO", FIFO_COLOR), ("gap_random", "LFT gegen Zufall", RANDOM_COLOR))):
    xs = [r[value_key] for r in rows]
    fig = go.Figure()
    for key, name, color in y_keys:
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in rows], mode="lines+markers", line=dict(color=color, width=2.5), name=name))
    fig.update_xaxes(title_text=param_label)
    fig.update_yaxes(title_text="Abstand zu LFT (%)")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 360)


def build_capacity_sweep(rows):
    xs = [r["value"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["lft_cmax"] for r in rows], mode="lines+markers", line=dict(color=RESOURCE_COLORS[0], width=2.5), name="Cmax (LFT)"))
    fig.update_xaxes(title_text="Kapazität je Ressource", dtick=1)
    fig.update_yaxes(title_text="Cmax (Mittel über 5 Instanzen)")
    return _base(fig, 320)


def build_density_sweep(rows):
    xs = [r["value"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["lft_cmax"] for r in rows], mode="lines+markers", line=dict(color=FIFO_COLOR, width=2.5), name="Cmax (LFT)"))
    fig.update_xaxes(title_text="Zusätzliche Vorrangdichte")
    fig.update_yaxes(title_text="Cmax (Mittel über 5 Instanzen)")
    return _base(fig, 320)


def build_timing(rows):
    xs = [r["value"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["exact_seconds"] * 1000 for r in rows], mode="lines+markers", line=dict(color=SPT_COLOR, width=2.5), name="CP-SAT (AddCumulative)"))
    fig.add_trace(go.Scatter(x=xs, y=[r["sgs_seconds"] * 1000 for r in rows], mode="lines+markers", line=dict(color=RESOURCE_COLORS[0], width=2.5), name="Serielle Konstruktion (polynomiell)"))
    fig.update_xaxes(title_text="Aktivitäten")
    fig.update_yaxes(title_text="Rechenzeit (ms)", type="log")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 340)
