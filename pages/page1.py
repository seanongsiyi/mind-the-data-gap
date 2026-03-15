import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np

dash.register_page(__name__, path="/page-1", name="Visualisation Suite")

# ── Dummy Data ────────────────────────────────────────────────────────────────

np.random.seed(42)
n = 1200

commuter_types = np.random.choice(["Adult", "Student", "Senior"], size=n, p=[0.55, 0.30, 0.15])
time_of_day    = np.random.choice(["Morning Peak", "Off-Peak", "Evening Peak"], size=n, p=[0.35, 0.35, 0.30])

transfer_times = []
for ct, tod in zip(commuter_types, time_of_day):
    base  = {"Adult": 6, "Student": 8, "Senior": 12}[ct]
    noise = {"Morning Peak": 3, "Off-Peak": 2, "Evening Peak": 4}[tod]
    transfer_times.append(max(1, np.random.normal(base, noise)))

df = pd.DataFrame({
    "commuter_type": commuter_types,
    "time_of_day":   time_of_day,
    "transfer_time": transfer_times,
})

stations = [
    "Jurong East", "Raffles Place", "City Hall", "Dhoby Ghaut",
    "Outram Park", "Bugis", "Lavender", "Paya Lebar",
    "Tampines", "Bedok", "Toa Payoh", "Ang Mo Kio",
]
np.random.seed(7)
transfer_counts = np.random.randint(200, 2000, size=(len(stations), len(stations)))
np.fill_diagonal(transfer_counts, 0)
transfer_counts = (transfer_counts + transfer_counts.T) // 2

dow     = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ts_data = []
for d in dow:
    for h in range(24):
        peak = 1.0
        if d in ["Mon", "Tue", "Wed", "Thu", "Fri"]:
            if 7 <= h <= 9:             peak = 1.8
            elif 17 <= h <= 19:         peak = 1.6
            elif 22 <= h or h <= 5:     peak = 0.5
        else:
            if 10 <= h <= 14:           peak = 1.3
            elif 22 <= h or h <= 6:     peak = 0.4
        ts_data.append({
            "day":  d,
            "hour": h,
            "avg_transfer_time": round(max(2, np.random.normal(7 * peak, 1.2)), 2),
        })
df_ts = pd.DataFrame(ts_data)

# ── Design tokens ─────────────────────────────────────────────────────────────

C = {
    "bg":           "#f8f9fb",
    "surface":      "#ffffff",
    "border":       "#e2e5ec",
    "border_light": "#edf0f4",
    "accent":       "#1a56db",
    "accent_soft":  "#eff4ff",
    "text":         "#111827",
    "secondary":    "#6b7280",
    "Adult":        "#1a56db",
    "Student":      "#0e9f6e",
    "Senior":       "#d97706",
    "Morning Peak": "#e02424",
    "Off-Peak":     "#1a56db",
    "Evening Peak": "#d97706",
}

FONT_SANS = "'Inter', 'Helvetica Neue', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Mono', monospace"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_SANS, color=C["text"], size=12),
    margin=dict(l=48, r=24, t=24, b=48),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=C["border"],
        borderwidth=1,
        font=dict(size=12),
    ),
)

AXIS_STYLE = dict(
    gridcolor=C["border_light"],
    linecolor=C["border"],
    zerolinecolor=C["border"],
    tickfont=dict(size=11, color=C["secondary"]),
)

# ── Chart builders ────────────────────────────────────────────────────────────

def build_histogram(commuter_filter, tod_filter):
    filtered = df.copy()
    if commuter_filter:
        filtered = filtered[filtered["commuter_type"].isin(commuter_filter)]
    if tod_filter:
        filtered = filtered[filtered["time_of_day"].isin(tod_filter)]

    fig = go.Figure()
    for ct in (commuter_filter or ["Adult", "Student", "Senior"]):
        sub = filtered[filtered["commuter_type"] == ct]["transfer_time"]
        if len(sub) == 0:
            continue
        fig.add_trace(go.Histogram(
            x=sub, name=ct, opacity=0.7,
            marker_color=C.get(ct, C["accent"]),
            xbins=dict(size=1),
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="overlay",
        xaxis=dict(**AXIS_STYLE, title="Transfer Time (min)"),
        yaxis=dict(**AXIS_STYLE, title="Count"),
    )
    return fig


def build_heatmap():
    fig = go.Figure(go.Heatmap(
        z=transfer_counts,
        x=stations,
        y=stations,
        colorscale=[
            [0.0, "#eff4ff"],
            [0.5, "#76a9fa"],
            [1.0, "#1a56db"],
        ],
        showscale=True,
        hoverongaps=False,
        colorbar=dict(
            outlinewidth=0,
            tickfont=dict(size=11, color=C["secondary"]),
        ),
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(**AXIS_STYLE, tickangle=-40),
        yaxis=dict(**AXIS_STYLE),
    )
    return fig


def build_timeseries(selected_days):
    days  = selected_days or dow
    pivot = df_ts[df_ts["day"].isin(days)].groupby("hour")["avg_transfer_time"].mean().reset_index()

    fig = go.Figure()
    for band_start, band_end, label in [(7, 9, "AM Peak"), (17, 19, "PM Peak")]:
        fig.add_vrect(
            x0=band_start, x1=band_end,
            fillcolor=C["accent"], opacity=0.05,
            layer="below", line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation_font=dict(size=11, color=C["secondary"]),
        )
    fig.add_trace(go.Scatter(
        x=pivot["hour"],
        y=pivot["avg_transfer_time"],
        mode="lines+markers",
        line=dict(color=C["accent"], width=2, shape="spline"),
        marker=dict(size=5, color=C["accent"],
                    line=dict(color="#ffffff", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(26,86,219,0.06)",
        name="Avg Transfer Time",
    ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(
            **AXIS_STYLE,
            title="Hour of Day",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)],
        ),
        yaxis=dict(**AXIS_STYLE, title="Avg Transfer Time (min)"),
    )
    return fig


# ── Layout helpers ────────────────────────────────────────────────────────────

def section_label(text):
    return html.P(text, style={
        "fontSize":      "10px",
        "fontWeight":    "600",
        "letterSpacing": "0.1em",
        "textTransform": "uppercase",
        "color":         C["secondary"],
        "fontFamily":    FONT_MONO,
        "margin":        "0 0 8px 0",
    })


def filter_bar(children):
    return html.Div(children, style={
        "display":      "flex",
        "flexWrap":     "wrap",
        "gap":          "32px",
        "padding":      "14px 18px",
        "background":   C["bg"],
        "borderRadius": "6px",
        "border":       f"1px solid {C['border']}",
        "marginBottom": "20px",
    })


def card(title, subtitle, children):
    return html.Div([
        html.Div([
            html.H3(title, style={
                "margin":     0,
                "fontSize":   "15px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT_SANS,
            }),
            html.P(subtitle, style={
                "margin":     "3px 0 0",
                "fontSize":   "12px",
                "color":      C["secondary"],
                "fontFamily": FONT_SANS,
            }),
        ], style={
            "marginBottom": "20px",
            "paddingBottom": "16px",
            "borderBottom": f"1px solid {C['border_light']}",
        }),
        *children,
    ], style={
        "background":   C["surface"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding":      "24px 28px",
        "marginBottom": "20px",
    })


# ── Page layout ───────────────────────────────────────────────────────────────

layout = html.Div([

    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap",
    ),

    # Page header
    html.Div([
        html.Div([
            html.H1("Visualisation Suite", style={
                "margin":     0,
                "fontSize":   "20px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT_SANS,
            }),
            html.P(
                "Journey pattern analysis — Singapore public transport transfer data",
                style={
                    "margin":     "4px 0 0",
                    "fontSize":   "13px",
                    "color":      C["secondary"],
                    "fontFamily": FONT_SANS,
                },
            ),
        ]),
        html.Div("DUMMY DATA", style={
            "fontSize":      "10px",
            "fontWeight":    "600",
            "letterSpacing": "0.08em",
            "color":         C["accent"],
            "background":    C["accent_soft"],
            "padding":       "4px 10px",
            "borderRadius":  "4px",
            "fontFamily":    FONT_MONO,
            "alignSelf":     "flex-start",
        }),
    ], style={
        "display":        "flex",
        "justifyContent": "space-between",
        "alignItems":     "flex-start",
        "marginBottom":   "28px",
        "paddingBottom":  "20px",
        "borderBottom":   f"1px solid {C['border']}",
    }),

    # ── 1. Transfer Time Distributions ────────────────────────────────────────
    card(
        "Transfer Time Distributions",
        "Time intervals between consecutive taps, segmented by commuter type and period",
        [
            filter_bar([
                html.Div([
                    section_label("Commuter Type"),
                    dcc.Checklist(
                        id="filter-commuter",
                        options=[{"label": f"  {c}", "value": c}
                                 for c in ["Adult", "Student", "Senior"]],
                        value=["Adult", "Student", "Senior"],
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
                html.Div([
                    section_label("Time of Day"),
                    dcc.Checklist(
                        id="filter-tod",
                        options=[{"label": f"  {t}", "value": t}
                                 for t in ["Morning Peak", "Off-Peak", "Evening Peak"]],
                        value=["Morning Peak", "Off-Peak", "Evening Peak"],
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
            ]),
            dcc.Graph(id="hist-chart", config={"displayModeBar": False},
                      style={"height": "360px"}),
            html.P(
                "Overlapping distributions reveal whether transfer times follow expected patterns "
                "and identify natural breakpoints that justify different transfer windows.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ),

    # ── 2. Spatial Transfer Analysis ──────────────────────────────────────────
    card(
        "Spatial Transfer Analysis",
        "Transfer volumes between interchange stations — identifies high-traffic pairs",
        [
            dcc.Graph(id="heatmap-chart", figure=build_heatmap(),
                      config={"displayModeBar": False}, style={"height": "480px"}),
            html.P(
                "Higher-intensity cells indicate station pairs with elevated transfer volumes, "
                "where extended transfer windows may be warranted due to distance or congestion.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ),

    # ── 3. Temporal Pattern Detection ─────────────────────────────────────────
    card(
        "Temporal Pattern Detection",
        "Average transfer completion time by hour of day — shaded bands indicate peak periods",
        [
            filter_bar([
                html.Div([
                    section_label("Day of Week"),
                    dcc.Checklist(
                        id="filter-dow",
                        options=[{"label": f"  {d}", "value": d} for d in dow],
                        value=dow,
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
            ]),
            dcc.Graph(id="ts-chart", config={"displayModeBar": False},
                      style={"height": "360px"}),
            html.P(
                "Systematic hourly patterns inform dynamic transfer window adjustments. "
                "Shaded regions denote AM and PM peak periods.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ),

], style={
    "background":  C["bg"],
    "minHeight":   "100vh",
    "padding":     "36px 48px",
    "fontFamily":  FONT_SANS,
    "color":       C["text"],
    "maxWidth":    "1100px",
    "margin":      "0 auto",
})


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("hist-chart", "figure"),
    Input("filter-commuter", "value"),
    Input("filter-tod", "value"),
)
def update_histogram(commuter_filter, tod_filter):
    return build_histogram(commuter_filter, tod_filter)


@callback(
    Output("ts-chart", "figure"),
    Input("filter-dow", "value"),
)
def update_timeseries(selected_days):
    return build_timeseries(selected_days)