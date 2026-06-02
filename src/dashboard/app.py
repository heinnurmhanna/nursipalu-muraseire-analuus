import math
import os

import pandas as pd
import dash
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output

from transform.schema import query_df

from typing import List, Tuple

app = dash.Dash(__name__, title="Nursipalu müraseire")
server = app.server  # exposed for main.py


def _fmt_db(v) -> str:
    return f"{v:.1f} dB" if v is not None and not math.isnan(v) else "–"


def _kpi_card(title: str, value: str) -> html.Div:
    return html.Div(
        style={
            "border": "1px solid #ddd", "borderRadius": "8px",
            "padding": "1rem", "minWidth": "180px", "textAlign": "center",
        },
        children=[
            html.H3(value, style={"margin": 0}),
            html.P(title, style={"margin": 0, "color": "#555"}),
        ],
    )

def _planned_noise_color(level):
    if level is None or str(level).lower() in ["nan", "none", ""]:
        return "rgba(233,236,239,0.25)"

    value = str(level).strip().lower()

    color_map = {
        "absent": "rgba(233,236,239,0.35)",
        
        "madal": "rgba(223,240,216,0.60)",
        "low": "rgba(223,240,216,0.60)",

        "keskmine": "rgba(255,243,205,0.65)",
        "medium": "rgba(255,243,205,0.65)",
        "average": "rgba(255,243,205,0.65)",

        "kõrge": "rgba(255,229,180,0.70)",
        "korge": "rgba(255,229,180,0.70)",
        "high": "rgba(255,229,180,0.70)",

        "väga kõrge": "rgba(248,215,218,0.75)",
        "vaga kõrge": "rgba(248,215,218,0.75)",
        "vaga korge": "rgba(248,215,218,0.75)",
        "very high": "rgba(248,215,218,0.75)",
        "very_high": "rgba(248,215,218,0.75)",
    }

    return color_map.get(value, "rgba(233,236,239,0.25)")


def _wind_direction_to_compass(degrees):
    if degrees is None or math.isnan(degrees):
        return None

    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int((degrees + 22.5) // 45) % 8
    return directions[index]


def _noise_class(avg_db, n):
    if n < 5:
        return 0
    if avg_db < 45:
        return 1
    if avg_db < 50:
        return 2
    if avg_db < 55:
        return 3
    if avg_db < 60:
        return 4
    if avg_db < 65:
        return 5
    return 6


Span = Tuple[pd.Timestamp, pd.Timestamp, str]


_SCHEDULE_LEVEL_COLOR = {
    # ABSENT tähendab: müra puudub
    "absent": "#dce9f7",

    "low": "#dff0d8",
    "madal": "#dff0d8",

    "average": "#fff9c4",
    "medium": "#fff9c4",
    "keskmine": "#fff9c4",

    "high": "#ffe5b4",
    "kõrge": "#ffe5b4",
    "korge": "#ffe5b4",

    "very_high": "#f8d7da",
    "very high": "#f8d7da",
    "väga kõrge": "#f8d7da",
    "vaga kõrge": "#f8d7da",
    "vaga korge": "#f8d7da",
}

_NO_ACTIVITY_COLOR = "#eeeeee"
_SCHEDULE_FALLBACK_COLOR = "#f0f0f0"


def _schedule_level_color(level) -> str:
    """Tagastab planned_noise_level väärtusele vastava taustavärvi."""
    if level is None or (isinstance(level, float) and math.isnan(level)):
        return _SCHEDULE_FALLBACK_COLOR

    return _SCHEDULE_LEVEL_COLOR.get(
        str(level).strip().lower(),
        _SCHEDULE_FALLBACK_COLOR,
    )


def _merge_schedule_spans(spans: List[Span]) -> List[Span]:
    """
    Ühendab järjestikused või kattuvad sama värviga perioodid.
    See vähendab vrect-ide arvu ja teeb Plotly joonise kiiremaks.
    """
    if not spans:
        return []

    spans = sorted(spans, key=lambda s: s[0])
    merged = [spans[0]]

    for start, end, color in spans[1:]:
        prev_start, prev_end, prev_color = merged[-1]

        if color == prev_color and start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end), prev_color)
        else:
            merged.append((start, end, color))

    return merged


def _schedule_spans_from_schedule(
    schedule_df: pd.DataFrame,
    t_min: pd.Timestamp,
    t_max: pd.Timestamp,
) -> List[Span]:
    """
    Loob taustaperioodid schedule tabeli põhjal.
    Kui mitu tegevust kattuvad, valib kõrgema mürataseme prioriteedi:
    VERY_HIGH > HIGH > AVERAGE > LOW > ABSENT.
    """
    if schedule_df is None or schedule_df.empty:
        return []

    required_cols = {
        "activity_start_utc",
        "activity_end_utc",
        "planned_noise_level",
    }

    if not required_cols.issubset(schedule_df.columns):
        return []

    sched = schedule_df.copy()
    sched["start"] = pd.to_datetime(sched["activity_start_utc"], errors="coerce")
    sched["end"] = pd.to_datetime(sched["activity_end_utc"], errors="coerce")
    sched = sched.dropna(subset=["start", "end", "planned_noise_level"])

    sched = sched[
        (sched["end"] >= t_min) &
        (sched["start"] <= t_max)
    ].copy()

    if sched.empty:
        return []

    sched["start"] = sched["start"].clip(lower=t_min)
    sched["end"] = sched["end"].clip(upper=t_max)

    priority = {
        "absent": 0,
        "low": 1,
        "madal": 1,
        "average": 2,
        "medium": 2,
        "keskmine": 2,
        "high": 3,
        "kõrge": 3,
        "korge": 3,
        "very_high": 4,
        "very high": 4,
        "väga kõrge": 4,
        "vaga kõrge": 4,
        "vaga korge": 4,
    }

    # Kõik algus- ja lõpuhetked, mille vahel tase ei muutu.
    breakpoints = sorted(
        set([t_min, t_max])
        | set(sched["start"].tolist())
        | set(sched["end"].tolist())
    )

    spans = []

    for start, end in zip(breakpoints[:-1], breakpoints[1:]):
        if start >= end:
            continue

        active = sched[
            (sched["start"] < end) &
            (sched["end"] > start)
        ].copy()

        if active.empty:
            continue

        active["level_key"] = (
            active["planned_noise_level"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        active["priority"] = active["level_key"].map(priority).fillna(-1)

        selected = active.sort_values("priority", ascending=False).iloc[0]
        color = _schedule_level_color(selected["planned_noise_level"])

        spans.append((start, end, color))

    return _merge_schedule_spans(spans)

def _no_activity_spans_from_schedule(
    schedule_df: pd.DataFrame,
    t_min: pd.Timestamp,
    t_max: pd.Timestamp,
) -> List[Span]:
    """
    Loob taustaperioodid ajale, kus schedule tabelis ei ole ühtegi planeeritud tegevust.
    See ei ole sama mis ABSENT: ABSENT tähendab planned_noise_level väärtust "müra puudub".
    """
    if t_min is None or t_max is None or pd.isna(t_min) or pd.isna(t_max):
        return []

    if schedule_df is None or schedule_df.empty:
        return [(t_min, t_max, _NO_ACTIVITY_COLOR)]

    required_cols = {
        "activity_start_utc",
        "activity_end_utc",
    }

    if not required_cols.issubset(schedule_df.columns):
        return [(t_min, t_max, _NO_ACTIVITY_COLOR)]

    sched = schedule_df.copy()
    sched["start"] = pd.to_datetime(sched["activity_start_utc"], errors="coerce")
    sched["end"] = pd.to_datetime(sched["activity_end_utc"], errors="coerce")
    sched = sched.dropna(subset=["start", "end"])

    sched = sched[
        (sched["end"] >= t_min) &
        (sched["start"] <= t_max)
    ].copy()

    if sched.empty:
        return [(t_min, t_max, _NO_ACTIVITY_COLOR)]

    sched["start"] = sched["start"].clip(lower=t_min)
    sched["end"] = sched["end"].clip(upper=t_max)

    activity_spans = sorted(
        [(row["start"], row["end"]) for _, row in sched.iterrows()],
        key=lambda s: s[0],
    )

    merged_activity_spans = []

    for start, end in activity_spans:
        if not merged_activity_spans:
            merged_activity_spans.append((start, end))
            continue

        prev_start, prev_end = merged_activity_spans[-1]

        if start <= prev_end:
            merged_activity_spans[-1] = (prev_start, max(prev_end, end))
        else:
            merged_activity_spans.append((start, end))

    no_activity_spans = []
    cursor = t_min

    for start, end in merged_activity_spans:
        if start > cursor:
            no_activity_spans.append((cursor, start, _NO_ACTIVITY_COLOR))

        cursor = max(cursor, end)

    if cursor < t_max:
        no_activity_spans.append((cursor, t_max, _NO_ACTIVITY_COLOR))

    return no_activity_spans


def _schedule_spans_from_merged(merged_df: pd.DataFrame) -> List[Span]:
    """
    Varuvariant: kui schedule tabeli ridu pole, loob taustaperioodid merged vaatest.
    See ei ole põhiallikas, sest merged on tunnipõhine koondvaade.
    """
    if merged_df is None or merged_df.empty:
        return []

    required_cols = {
        "timestamp_utc",
        "has_scheduled_activity",
        "planned_noise_level",
    }

    if not required_cols.issubset(merged_df.columns):
        return []

    bucket = pd.Timedelta(hours=1)

    act = merged_df[
        merged_df["has_scheduled_activity"].astype(str).str.lower()
        .isin(["true", "1", "yes"])
    ].copy()

    if act.empty:
        return []

    spans = []
    for _, row in act.iterrows():
        start = pd.to_datetime(row["timestamp_utc"], errors="coerce")
        if pd.isna(start):
            continue

        spans.append((
            start,
            start + bucket,
            _schedule_level_color(row.get("planned_noise_level")),
        ))

    return spans


def build_schedule_noise_activity_figure(
    merged_df: pd.DataFrame,
    schedule_df: pd.DataFrame | None = None,
) -> go.Figure:
    """
    Uus lisajoonis:
    mõõdetud LAeq + planeeritud mürakategooriad schedule tabeli alusel.

    NB! ABSENT tähendab planned_noise_level veerus: müra puudub.
    """
    fig = go.Figure()

    if merged_df is None or merged_df.empty:
        fig.update_layout(title="Andmed puuduvad")
        return fig

    if schedule_df is None:
        schedule_df = pd.DataFrame()

    t_min = pd.to_datetime(merged_df["timestamp_utc"].min())
    t_max = pd.to_datetime(merged_df["timestamp_utc"].max())

    schedule_spans = _schedule_spans_from_schedule(schedule_df, t_min, t_max)
    no_activity_spans = _no_activity_spans_from_schedule(schedule_df, t_min, t_max)

    # Taustaks lisame ka perioodid, kus planeeritud tegevusi ei ole.
    spans = []
    spans.extend(no_activity_spans)
    spans.extend(schedule_spans)

    # Kui schedule tabelist ei õnnestu perioode saada, kasuta varuvariandina merged vaadet.
    if not schedule_spans:
        spans.extend(_schedule_spans_from_merged(merged_df))

    spans = _merge_schedule_spans(spans)

    for start, end, color in spans:
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor=color,
            layer="below",
            line_width=0,
        )

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(merged_df["timestamp_utc"]),
        y=merged_df["laeq_db"],
        mode="lines",
        name="Mõõdetud müratase LAeq",
        line=dict(color="#2196F3", width=2),
        showlegend=False,
    ))

    fig.add_hline(
        y=65,
        line_dash="dash",
        line_color="#555555",
        line_width=2,
        annotation_text="Ld = 65 dB",
        annotation_position="top right",
    )

    legend_items = [
    ("Müra puudub", "#dce9f7"),
    ("Madal", "#dff0d8"),
    ("Keskmine", "#fff9c4"),
    ("Kõrge", "#ffe5b4"),
    ("Väga kõrge", "#f8d7da"),
    
    ("Planeeritud tegevusi ei ole", _NO_ACTIVITY_COLOR),
    ]

    for label, color in legend_items:
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=12, color=color, symbol="square"),
            name=label,
            showlegend=True,
        ))

    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        line=dict(color="#555555", width=2, dash="dash"),
        name="Ld = 65 dB",
        showlegend=False,
    ))

    fig.update_layout(
        xaxis_title="Aeg (UTC)",
        yaxis_title="Müratase LAeq (dB)",
        legend_title="Planeeritud mürakategooria",
        legend=dict(
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top",
        ),
        margin=dict(r=260),
    )

    return fig

app.layout = html.Div(
    style={"fontFamily": "sans-serif", "maxWidth": "1300px", "margin": "0 auto", "padding": "1rem"},
    children=[
        html.H1("Nursipalu müraseire"),
        html.P(
            "Mürataseme, harjutusgraafiku ja ilmaandmete ajapõhine võrdlus.",
            style={"color": "#555"},
        ),

        html.Div([
            html.Label("Ajavahemik:"),
            dcc.DatePickerRange(
                id="date-range",
                display_format="YYYY-MM-DD",
                style={"marginLeft": "0.5rem"},
            ),
        ], style={"marginBottom": "1.5rem"}),

        html.Div(id="kpi-cards", style={"display": "flex", "flexWrap": "wrap", "gap": "1rem", "marginBottom": "1.5rem"}),

        html.H2("Müratase ajas koos harjutuste ja tuulekiirusega"),
        dcc.Graph(id="noise-timeline"),

        html.H2("Müraseirejaama mõõdetud müratase ja Nursipalu harjutusvälja planeeritud mürakategooriad"),
        dcc.Graph(id="spec-noise-activity"),

        html.H2("Mõõdetud müratase ja planeeritud mürakategooriad schedule tabeli põhjal"),
        dcc.Graph(id="schedule-noise-activity"),

        html.H2("Mõõdetud müratase tuulesuuna ja tuulekiiruse järgi"),
        dcc.Graph(id="spec-wind-heatmap"),        

        html.H2("Keskmine müratase: tegevusega vs. tegevuseta"),
        dcc.Graph(id="noise-by-activity"),

        html.H2("Tipptaseme sündmused ja planeeritud tegevused"),
        dcc.Graph(id="peak-events"),

        html.H2("Tuulekiiruse ja -suuna seos planeeritud tegevuste ning müratasemega"),
        dcc.Graph(id="wind-noise-scatter"),
    ],
)


@app.callback(
    Output("kpi-cards", "children"),
    Output("noise-timeline", "figure"),
    Output("spec-noise-activity", "figure"),
    Output("schedule-noise-activity", "figure"),
    Output("spec-wind-heatmap", "figure"),
    Output("noise-by-activity", "figure"),
    Output("peak-events", "figure"),
    Output("wind-noise-scatter", "figure"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_charts(start_date, end_date):
    where = "WHERE 1=1"
    if start_date:
        where += f" AND timestamp_utc >= '{start_date}'"
    if end_date:
        where += f" AND timestamp_utc <= '{end_date} 23:59:59'"

    df = query_df(f"SELECT * FROM merged {where} ORDER BY timestamp_utc")

    schedule_where = "WHERE 1=1"

    if start_date:
        schedule_where += f" AND activity_end_utc >= '{start_date}'"

    if end_date:
        schedule_where += f" AND activity_start_utc <= '{end_date} 23:59:59'"

    schedule_df = query_df(
        f"""
        SELECT
            activity_start_utc,
            activity_end_utc,
            planned_noise_level
        FROM schedule
        {schedule_where}
        ORDER BY activity_start_utc
        """
    )

    empty_fig = go.Figure().update_layout(title="Andmed puuduvad")

    if df.empty:
        return (
            [html.P("Andmed puuduvad")],
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
        )

    with_act = df[df["has_scheduled_activity"] == True]
    without_act = df[df["has_scheduled_activity"] == False]

    # Energetic average helper: 10*log10(mean(10^(L/10)))
    def leq_avg(series):
        s = series.dropna()
        if s.empty:
            return float("nan")
        return 10 * math.log10(s.apply(lambda x: 10 ** (x / 10)).mean())

    avg_laeq_with    = leq_avg(with_act["laeq_db"])
    avg_laeq_without = leq_avg(without_act["laeq_db"])
    avg_lceq_with    = leq_avg(with_act["lceq_db"])
    avg_lceq_without = leq_avg(without_act["lceq_db"])
    peak_rate = (df["peak_event"] == True).sum() / max(len(df), 1) * 100
    activity_hours = int((df["has_scheduled_activity"] == True).sum())

    # Mürataseme tõusu kattuvus planeeritud tegevustega
    noise_rise_threshold = 60
    noise_rise_df = df[df["laeq_db"] >= noise_rise_threshold]

    if len(noise_rise_df) > 0:
        overlap_pct = (
            noise_rise_df["has_scheduled_activity"]
            .astype(str)
            .str.lower()
            .isin(["true", "1", "yes"])
            .sum() / len(noise_rise_df) * 100
        )
    else:
        overlap_pct = 0

    kpis = [
        _kpi_card("LAeq tegevusega", _fmt_db(avg_laeq_with)),
        _kpi_card("LAeq tegevuseta", _fmt_db(avg_laeq_without)),
        _kpi_card("LCeq tegevusega", _fmt_db(avg_lceq_with)),
        _kpi_card("LCeq tegevuseta", _fmt_db(avg_lceq_without)),
        _kpi_card("Planeeritud tegevuse tunnid", str(activity_hours)),
        _kpi_card("Tipptaseme tunnid", f"{peak_rate:.0f}%"),
        _kpi_card("Müratõusude kattuvus tegevustega",f"{overlap_pct:.0f}%"),
    ]

    # --- Chart 1: noise timeline (LAeq, LCeq, LZeq) ---
    fig_timeline = go.Figure()

    for col, label, color in [
        ("laeq_db", "LAeq", "#2196F3"),
        ("lceq_db", "LCeq", "#FF9800"),
        ("lzeq_db", "LZeq", "#9C27B0"),
    ]:
        if col in df.columns:
            fig_timeline.add_trace(go.Scatter(
                x=df["timestamp_utc"],
                y=df[col],
                mode="lines",
                name=label,
                line=dict(color=color),
            ))

    # Lisa tuulekiirus samale graafikule paremale Y-teljele
    if "wind_speed_ms" in df.columns:
        fig_timeline.add_trace(go.Scatter(
            x=df["timestamp_utc"],
            y=df["wind_speed_ms"],
            mode="lines",
            name="Tuulekiirus (m/s)",
            yaxis="y2",
            line=dict(color="#4CAF50", dash="dot"),
        ))

    # Shade scheduled-activity periods
    activity_df = df[
        df["has_scheduled_activity"].astype(str).str.lower().isin(["true", "1", "yes"])
    ].copy()

    print("Scheduled activity rows:", len(activity_df))

    # Lisa legendi kirje planeeritud harjutuse jaoks
    if not activity_df.empty:
        fig_timeline.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                size=12,
                color="rgba(244,67,54,0.35)",
                symbol="square",
            ),
            name="Planeeritud harjutus",
            showlegend=True,
        ))

    # Lisa punased taustaalad
    for _, row in activity_df.iterrows():
        start = pd.to_datetime(row["timestamp_utc"])
        end = start + pd.Timedelta(hours=1)

        fig_timeline.add_vrect(
            x0=start,
            x1=end,
            fillcolor="rgba(244,67,54,0.35)",
            layer="below",
            line_width=0,
        )

    fig_timeline.update_layout(
        xaxis_title="Aeg (UTC)",
        yaxis=dict(
            title="Müratase (dB)",
        ),
        yaxis2=dict(
            title="Tuulekiirus (m/s)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(
            title="Mõõt",
            x=1.08,
            y=1,
            xanchor="left",
            yanchor="top",
        ),
        margin=dict(r=260),
    )

    # --- Chart 2: bar — activity vs non-activity for all three metrics ---
    bar_data = []
    for col, label in [("laeq_db", "LAeq"), ("lceq_db", "LCeq"), ("lzeq_db", "LZeq")]:
        if col not in df.columns:
            continue
        bar_data.append({"Mõõt": label, "Periood": "Tegevusega",  "dB": leq_avg(with_act[col])})
        bar_data.append({"Mõõt": label, "Periood": "Tegevuseta", "dB": leq_avg(without_act[col])})

    bar_df = pd.DataFrame(bar_data).dropna(subset=["dB"])
    fig_bar = px.bar(
        bar_df, x="Mõõt", y="dB", color="Periood", barmode="group",
        labels={"dB": "Energeetiline keskmine (dB)"},
        color_discrete_map={"Tegevusega": "#F44336", "Tegevuseta": "#2196F3"},
    )

    # --- Chart 3: peak events timeline ---
    fig_peaks = go.Figure()
    fig_peaks.add_trace(go.Scatter(
        x=df["timestamp_utc"], y=df["lc_peak_db"],
        mode="lines", name="LCpeak", line=dict(color="#FF9800"),
    ))
    fig_peaks.add_trace(go.Scatter(
        x=df["timestamp_utc"], y=df["lz_peak_db"],
        mode="lines", name="LZpeak", line=dict(color="#9C27B0"),
    ))
    peak_rows = df[df["peak_event"] == True]
    fig_peaks.add_trace(go.Scatter(
        x=peak_rows["timestamp_utc"],
        y=peak_rows["lc_peak_db"],
        mode="markers", name="Tipptaseme sündmus",
        marker=dict(color="red", size=8, symbol="circle"),
    ))
    fig_peaks.update_layout(xaxis_title="Aeg (UTC)", yaxis_title="dB")

    # --- Chart 4: wind speed vs LAeq, with weather/activity context ---
    scatter_df = df.dropna(subset=["wind_speed_ms", "laeq_db"]).copy()

    # Tee väärtused loetavamaks
    scatter_df["Planeeritud tegevus"] = scatter_df["has_scheduled_activity"].map({
        True: "Jah",
        False: "Ei",
    })

    scatter_df["Tuulesuund"] = scatter_df["downwind_category"].map({
        "downwind": "Allatuult",
        "crosswind": "Külgtuul",
        "upwind": "Vastutuul",
    }).fillna(scatter_df["downwind_category"])

    fig_scatter = px.scatter(
        scatter_df,
        x="wind_speed_ms",
        y="laeq_db",
        color="Tuulesuund",
        symbol="Planeeritud tegevus",
        trendline="ols",
        labels={
            "wind_speed_ms": "Tuulekiirus (m/s)",
            "laeq_db": "LAeq müratase (dB)",
            "Tuulesuund": "Tuulesuund",
            "Planeeritud tegevus": "Planeeritud tegevus",
        },
        hover_data={
            "timestamp_utc": True,
            "wind_speed_ms": ":.1f",
            "laeq_db": ":.1f",
            "Tuulesuund": True,
            "Planeeritud tegevus": True,
        },
        color_discrete_map={
            "Allatuult": "#F44336",
            "Külgtuul": "#FF9800",
            "Vastutuul": "#2196F3",
        },
        opacity=0.75,
    )

    fig_scatter.update_traces(marker=dict(size=9))

    fig_scatter.update_layout(
        xaxis_title="Tuulekiirus (m/s)",
        yaxis_title="LAeq müratase (dB)",
        legend_title="Tuulesuund / tegevus",
        margin=dict(r=220),
    )

    # --- New spec visual 1: LAeq + planned noise categories + 65 dB threshold ---
    
    fig_spec_noise_activity = go.Figure()

    fig_schedule_noise_activity = build_schedule_noise_activity_figure(
        df,
        schedule_df,
    )

    # Filtreerib välja read, kus on planeeritud tegevus.
    # Väärtused teisendatakse tekstiks, et töötaks nii True, "true", "1" kui ka "yes" korral.
    activity_spec_df = df[
        df["has_scheduled_activity"].astype(str).str.lower().isin(["true", "1", "yes"])
    ].copy()

    # Lisab graafikule planeeritud tegevuste perioodid taustavärvina.
    for _, row in activity_spec_df.iterrows():
        start = pd.to_datetime(row["timestamp_utc"])
        end = start + pd.Timedelta(hours=1)
        planned_level = row.get("planned_noise_level", None)

        fig_spec_noise_activity.add_vrect(
            x0=start,
            x1=end,
            fillcolor=_planned_noise_color(planned_level),
            layer="below",
            line_width=0,
        )

    # Lisab mõõdetud mürataseme joone.
    fig_spec_noise_activity.add_trace(go.Scatter(
        x=df["timestamp_utc"],
        y=df["laeq_db"],
        mode="lines",
        name="Mõõdetud müratase LAeq",
        line=dict(color="#2196F3", width=2),
    ))

    # Lisab 65 dB võrdluspiiri.
    fig_spec_noise_activity.add_hline(
        y=65,
        line_dash="dash",
        line_color="#555555",
        line_width=2,
        annotation_text="Ld = 65 dB",
        annotation_position="top right",
    )

    # Lisab legendi
    for label, color in [
        ("Madal", "#DFF0D8"),
        ("Keskmine", "#FFF3CD"),
        ("Kõrge", "#FFE5B4"),
        ("Väga kõrge", "#F8D7DA"),
        ("Müra puudub", "#E9ECEF")
    ]:
        fig_spec_noise_activity.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(size=12, color=color, symbol="square"),
            name=label,
            showlegend=True,
        ))

    fig_spec_noise_activity.update_layout(
        xaxis_title="Aeg (UTC)",
        yaxis_title="Müratase LAeq (dB)",
        legend_title="Mõõt / Müra kategooria",
        legend=dict(
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top",
        ),
        margin=dict(r=260),
    )

    # --- New spec visual 2: heatmap wind direction / wind speed vs LAeq ---
    noise_col = "laeq_db"

    # Leiame tuulesuuna veeru.
    if "wind_direction" in df.columns:
        wind_dir_col = "wind_direction"
    elif "wind_direction_deg" in df.columns:
        wind_dir_col = "wind_direction_deg"
    elif "wind_direction_10m" in df.columns:
        wind_dir_col = "wind_direction_10m"
    else:
        wind_dir_col = None

    # Leiame tuulekiiruse veeru.
    if "wind_speed" in df.columns:
        wind_speed_col = "wind_speed"
    elif "wind_speed_ms" in df.columns:
        wind_speed_col = "wind_speed_ms"
    elif "wind_speed_10m" in df.columns:
        wind_speed_col = "wind_speed_10m"
    else:
        wind_speed_col = None

    # Kui tuuleandmeid pole, kuvame tühja graafiku teatega.
    if wind_dir_col is None or wind_speed_col is None:
        fig_spec_wind_heatmap = go.Figure()
        fig_spec_wind_heatmap.update_layout(
            title="Tuuleandmed puuduvad",
            xaxis_title="Tuulekiirus",
            yaxis_title="Tuulesuund",
        )
    else:
        # Jätame alles ainult read, kus LAeq, tuulekiirus ja tuulesuund on olemas.
        heatmap_df = df.dropna(subset=[noise_col, wind_speed_col, wind_dir_col]).copy()

        heatmap_df["wind_direction_compass"] = heatmap_df[wind_dir_col].apply(_wind_direction_to_compass)

        # Jagame tuulekiiruse etteantud vahemikesse.
        heatmap_df["wind_speed_bin"] = pd.cut(
            heatmap_df[wind_speed_col],
            bins=[0, 2, 4, 6, 8, float("inf")],
            labels=["0–2 m/s", "2–4 m/s", "4–6 m/s", "6–8 m/s", "> 8 m/s"],
            right=False,
        )

        grouped = (
            heatmap_df
            .dropna(subset=["wind_direction_compass", "wind_speed_bin"])
            .groupby(["wind_direction_compass", "wind_speed_bin"], observed=False)
            .agg(
                avg_noise=(noise_col, "mean"),
                n=(noise_col, "count"),
            )
            .reset_index()
        )

        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        speed_bins = ["0–2 m/s", "2–4 m/s", "4–6 m/s", "6–8 m/s", "> 8 m/s"]

        z = []
        text = []

        for direction in directions:
            z_row = []
            text_row = []

            for speed_bin in speed_bins:
                row = grouped[
                    (grouped["wind_direction_compass"] == direction)
                    & (grouped["wind_speed_bin"].astype(str) == speed_bin)
                ]

                if row.empty:
                    z_row.append(0)
                    text_row.append("Andmed<br>puuduvad")
                else:
                    avg_noise = float(row["avg_noise"].iloc[0])
                    n = int(row["n"].iloc[0])

                    z_row.append(_noise_class(avg_noise, n))
                    text_row.append(f"{avg_noise:.1f}<br>n = {n}")

            z.append(z_row)
            text.append(text_row)

        colorscale = [
            [0.00, "#E9ECEF"],
            [0.16, "#E9ECEF"],
            [0.17, "#A8D99B"],
            [0.32, "#A8D99B"],
            [0.33, "#C5E1A5"],
            [0.48, "#C5E1A5"],
            [0.49, "#F3E27A"],
            [0.64, "#F3E27A"],
            [0.65, "#F8C96B"],
            [0.80, "#F8C96B"],
            [0.81, "#F79A3E"],
            [0.92, "#F79A3E"],
            [0.93, "#EF5350"],
            [1.00, "#EF5350"],
        ]

        fig_spec_wind_heatmap = go.Figure(data=go.Heatmap(
            z=z,
            x=speed_bins,
            y=directions,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=12),
            colorscale=colorscale,
            zmin=0,
            zmax=6,
            hovertemplate=(
                "Tuulesuund: %{y}<br>"
                "Tuulekiirus: %{x}<br>"
                "Keskmine LAeq / n:<br>%{text}"
                "<extra></extra>"
            ),
            colorbar=dict(
                title="Keskmine LAeq",
                tickvals=[0, 1, 2, 3, 4, 5, 6],
                ticktext=["n < 5", "<45", "45–50", "50–55", "55–60", "60–65", ">65"],
            ),
        ))

        fig_spec_wind_heatmap.update_layout(
            xaxis_title="Tuulekiirus",
            yaxis_title="Tuulesuund",
            yaxis=dict(categoryorder="array", categoryarray=directions),
            margin=dict(r=160),
        )

    return (
        kpis,
        fig_timeline,
        fig_spec_noise_activity,
        fig_schedule_noise_activity,
        fig_spec_wind_heatmap,
        fig_bar,
        fig_peaks,
        fig_scatter,
    )

if __name__ == "__main__":
    from transform.schema import init_schema
    init_schema()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("DASH_PORT", "8050")))
