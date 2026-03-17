import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

dash.register_page(__name__, path="/page-4", name="Delay Simulation")

# ── Design tokens ───────────────────────────

C = {
    "bg":           "#f8f9fb",
    "surface":      "#ffffff",
    "border":       "#e2e5ec",
    "border_light": "#edf0f4",
    "accent":       "#1a56db",
    "accent_soft":  "#eff4ff",
    "accent_mid":   "#76a9fa",
    "text":         "#111827",
    "secondary":    "#6b7280",
    "muted":        "#9ca3af",
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


# ─────────────────────────────────────────────
# PLACEHOLDER DATA
# ─────────────────────────────────────────────

# TODO: Replace with actual region list from backend
REGIONS = ["All Regions", "North", "North-East", "East", "West", "Central"]

# TODO: Replace with actual time-of-day options from backend
TIMES_OF_DAY = [
    "Morning Peak (6am–9am)",
    "Off-Peak (9am–5pm)",
    "Evening Peak (5pm–8pm)",
    "Night (8pm–12am)",
]

# TODO: Replace with actual delay duration options from backend
DELAY_DURATIONS = ["5 minutes", "10 minutes", "15 minutes"]


# TODO: Replace with real filtered commuter data from backend.
# Expected shape: DataFrame with columns [region, affected_commuters, lat, lon]
def get_placeholder_map_data():
    return pd.DataFrame({
        "region":             ["North", "North-East", "East", "West", "Central"],
        "affected_commuters": [1200, 850, 960, 1100, 780],
        "lat":                [1.38, 1.36, 1.32, 1.34, 1.30],
        "lon":                [103.80, 103.87, 103.93, 103.75, 103.83],
    })


# TODO: Replace with real filtered commuter counts from backend.
# Expected shape: DataFrame with columns [category, count]
# category values: "In Window", "Out of Window"
def get_placeholder_bar_data():
    return pd.DataFrame({
        "category": ["In Window", "Out of Window"],
        "count":    [3200, 1800],
    })


# ── Figure builders ───────────────────────────────────────────────────────────

def build_map_figure(region=None, time_of_day=None, delay_duration=None, transfer_window=45):
    """
    Builds the Singapore map figure.

    TODO: When backend is ready:
      1. Query filtered commuter data using (region, time_of_day, delay_duration, transfer_window)
      2. Load real Singapore region GeoJSON from:
         https://data.gov.sg/dataset/master-plan-2019-region-boundary-no-sea
      3. Switch from Scattermapbox to px.choropleth_mapbox, colouring
         each region by its affected_commuters count.
    """
    df = get_placeholder_map_data()

    fig = go.Figure(go.Scattermapbox(
        lat=df["lat"],
        lon=df["lon"],
        mode="markers+text",
        marker=dict(size=32, color=C["accent"], opacity=0.6),
        text=df["region"],
        textposition="top center",
        customdata=df["affected_commuters"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Affected commuters: %{customdata}<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=10,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
    )
    return fig


def build_bar_figure(region=None, time_of_day=None, delay_duration=None, transfer_window=45):
    """
    Builds the In Window vs Out of Window bar chart.

    TODO: When backend is ready, replace get_placeholder_bar_data() with
          a real query filtered by (region, time_of_day, delay_duration, transfer_window).
    """
    df = get_placeholder_bar_data()

    fig = go.Figure([
        go.Bar(
            x=df["category"],
            y=df["count"],
            marker_color=[C["accent"], C["accent_mid"]],
            text=df["count"],
            textposition="outside",
            textfont=dict(size=11, family=FONT_MONO),
        )
    ])

    fig.update_layout(
        **{**PLOTLY_LAYOUT, "margin": dict(l=32, r=16, t=16, b=32)},
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title="Commuters"),
        height=200,
    )
    return fig


# ── Layout helpers ────────────────────────────────────

def section_label(text):
    return html.P(text, style={
        "fontSize":      "10px",
        "fontWeight":    "600",
        "letterSpacing": "0.1em",
        "textTransform": "uppercase",
        "color":         C["secondary"],
        "fontFamily":    FONT_MONO,
        "margin":        "0 0 6px 0",
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
            "marginBottom":  "20px",
            "paddingBottom": "16px",
            "borderBottom":  f"1px solid {C['border_light']}",
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
            html.H1("Delay Simulation", style={
                "margin":     0,
                "fontSize":   "20px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT_SANS,
            }),
            html.P(
                "Simulating transfer window sufficiency under varying delay conditions by region and time of day",
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

    # ── Main card: Map + Controls ─────────────────────────────────────────────
    card(
        "Regional Impact Map",
        "Commuters affected by delayed transfers, filterable by region, time of day, and delay duration",
        [
            # Filter row
            html.Div([
                html.Div([
                    section_label("Region"),
                    dcc.Dropdown(
                        id="p4-region-dropdown",
                        options=[{"label": r, "value": r} for r in REGIONS],
                        value="All Regions",
                        clearable=False,
                        style={"fontSize": "13px", "width": "180px"},
                    ),
                ]),
                html.Div([
                    section_label("Time of Day"),
                    dcc.Dropdown(
                        id="p4-time-dropdown",
                        options=[{"label": t, "value": t} for t in TIMES_OF_DAY],
                        placeholder="All times",
                        clearable=True,
                        style={"fontSize": "13px", "width": "220px"},
                    ),
                ]),
                html.Div([
                    section_label("Duration of Delay"),
                    dcc.Dropdown(
                        id="p4-delay-dropdown",
                        options=[{"label": d, "value": d} for d in DELAY_DURATIONS],
                        placeholder="All durations",
                        clearable=True,
                        style={"fontSize": "13px", "width": "160px"},
                    ),
                ]),
            ], style={
                "display":      "flex",
                "flexWrap":     "wrap",
                "gap":          "32px",
                "padding":      "14px 18px",
                "background":   C["bg"],
                "borderRadius": "6px",
                "border":       f"1px solid {C['border']}",
                "marginBottom": "20px",
            }),

            # Map + right panel
            html.Div([

                # Map
                html.Div(
                    dcc.Graph(
                        id="p4-map-figure",
                        figure=build_map_figure(),
                        config={"displayModeBar": False},
                        style={"height": "400px"},
                    ),
                    style={
                        "flex":         "1",
                        "borderRadius": "8px",
                        "overflow":     "hidden",
                        "border":       f"1px solid {C['border_light']}",
                    },
                ),

                # Right panel: slider + bar chart
                html.Div([

                    # Transfer window slider
                    html.Div([
                        section_label("Transfer Window (minutes)"),
                        dcc.Slider(
                            id="p4-transfer-window-slider",
                            min=30, max=60, step=5, value=45,
                            marks={
                                30: {"label": "30", "style": {"fontFamily": FONT_MONO, "fontSize": "11px"}},
                                45: {"label": "45", "style": {"fontFamily": FONT_MONO, "fontSize": "11px", "color": C["accent"]}},
                                60: {"label": "60", "style": {"fontFamily": FONT_MONO, "fontSize": "11px"}},
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ], style={
                        "background":   C["surface"],
                        "border":       f"1px solid {C['border']}",
                        "borderRadius": "8px",
                        "padding":      "16px 18px",
                        "marginBottom": "12px",
                    }),

                    # Bar chart
                    html.Div([
                        section_label("Commuters affected"),
                        dcc.Graph(
                            id="p4-bar-figure",
                            figure=build_bar_figure(),
                            config={"displayModeBar": False},
                            style={"height": "220px"},
                        ),
                    ], style={
                        "background":   C["surface"],
                        "border":       f"1px solid {C['border']}",
                        "borderRadius": "8px",
                        "padding":      "16px 18px",
                    }),

                ], style={"width": "260px", "display": "flex", "flexDirection": "column"}),

            ], style={"display": "flex", "gap": "20px", "alignItems": "flex-start"}),

            html.P(
                "Regions with higher affected commuter counts may benefit most from an extended transfer window. "
                "Use the slider to evaluate how different window sizes change the proportion of commuters impacted.",
                style={
                    "fontSize":   "12px",
                    "color":      C["secondary"],
                    "margin":     "16px 0 0",
                    "fontFamily": FONT_SANS,
                },
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
    Output("p4-map-figure", "figure"),
    Output("p4-bar-figure", "figure"),
    Input("p4-region-dropdown", "value"),
    Input("p4-time-dropdown", "value"),
    Input("p4-delay-dropdown", "value"),
    Input("p4-transfer-window-slider", "value"),
)
def update_figures(region, time_of_day, delay_duration, transfer_window):
    """
    Updates both figures when any filter or slider changes.

    TODO: When backend is ready, pass the filter values to your data
          query functions and feed real DataFrames into the figure builders.
    """
    map_fig = build_map_figure(region, time_of_day, delay_duration, transfer_window)
    bar_fig = build_bar_figure(region, time_of_day, delay_duration, transfer_window)
    return map_fig, bar_fig