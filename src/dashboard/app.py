import math
import os

import pandas as pd
import dash
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output

from transform.schema import query_df

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

        html.H2("Keskmine müratase: tegevusega vs. tegevuseta"),
        dcc.Graph(id="noise-by-activity"),

        html.H2("Tipptaseme sündmused ja planeeritud tegevused"),
        dcc.Graph(id="peak-events"),

        html.H2("Tuulekiirus ja -suund vs. müratase"),
        dcc.Graph(id="wind-noise-scatter"),
    ],
)


@app.callback(
    Output("kpi-cards", "children"),
    Output("noise-timeline", "figure"),
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



    empty_fig = go.Figure().update_layout(title="Andmed puuduvad")

    if df.empty:
        return [html.P("Andmed puuduvad")], empty_fig, empty_fig, empty_fig, empty_fig

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

    kpis = [
        _kpi_card("LAeq tegevusega", _fmt_db(avg_laeq_with)),
        _kpi_card("LAeq tegevuseta", _fmt_db(avg_laeq_without)),
        _kpi_card("LCeq tegevusega", _fmt_db(avg_lceq_with)),
        _kpi_card("LCeq tegevuseta", _fmt_db(avg_lceq_without)),
        _kpi_card("Tipptaseme tunnid", f"{peak_rate:.0f}%"),
        _kpi_card("Planeeritud tegevuse tunnid", str(activity_hours)),
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

    # --- Chart 4: scatter wind speed vs laeq, coloured by downwind category ---
    scatter_df = df.dropna(subset=["wind_speed_ms", "laeq_db"])
    fig_scatter = px.scatter(
        scatter_df,
        x="wind_speed_ms", y="laeq_db",
        color="downwind_category",
        symbol="has_scheduled_activity",
        labels={
            "wind_speed_ms": "Tuulekiirus (m/s)",
            "laeq_db": "LAeq (dB)",
            "downwind_category": "Tuulesuund",
            "has_scheduled_activity": "Planeeritud tegevus",
        },
        color_discrete_map={
            "downwind":  "#F44336",
            "crosswind": "#FF9800",
            "upwind":    "#2196F3",
        },
        opacity=0.7,
    )

    return kpis, fig_timeline, fig_bar, fig_peaks, fig_scatter


if __name__ == "__main__":
    from transform.schema import init_schema
    init_schema()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("DASH_PORT", "8050")))
