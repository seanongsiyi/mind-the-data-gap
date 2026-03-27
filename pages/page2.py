import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from pathlib import Path

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

PLANNING_AREAS_GEOJSON_PATH = Path("data/singapore_planning_areas.geojson")

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


def load_planning_area_geojson():
    with open(PLANNING_AREAS_GEOJSON_PATH, "r") as f:
        return json.load(f)


def get_planning_area_metadata():
    sg_geojson = load_planning_area_geojson()
    rows = []

    for feature in sg_geojson["features"]:
        props = feature["properties"]
        region = props["REGION_N"].replace(" REGION", "").title()
        planning_area_raw = props["PLN_AREA_N"]
        rows.append(
            {
                "region": region,
                "planning_area_raw": planning_area_raw,
                "planning_area": planning_area_raw.title(),
            }
        )

    return pd.DataFrame(rows).drop_duplicates().sort_values("planning_area")


def get_planning_areas_for_region(region):
    """Get list of planning areas for a given region."""
    meta = get_planning_area_metadata()
    if region and region != "All Regions":
        meta = meta[meta["region"] == region]

    return ["All Planning Areas"] + meta["planning_area"].tolist()


# TODO: Replace with real filtered commuter data from backend.
# Expected shape: DataFrame with columns [region, planning_area, affected_commuters]
def get_placeholder_map_data(region=None, planning_area=None):
    meta = get_planning_area_metadata().copy()

    # Deterministic synthetic values so the demo remains stable across refreshes.
    meta["affected_commuters"] = meta["planning_area_raw"].apply(
        lambda x: 400 + (sum(ord(ch) for ch in x) % 1400)
    )

    if region and region != "All Regions":
        meta = meta[meta["region"] == region]

    if planning_area and planning_area != "All Planning Areas":
        meta = meta[meta["planning_area"] == planning_area]

    return meta


# TODO: Replace with real filtered commuter counts from backend.
# Expected shape: DataFrame with columns [category, count]
# category values: "In Window", "Out of Window"
def get_placeholder_bar_data(region=None, planning_area=None):
    source = get_placeholder_map_data(region, planning_area)
    total = int(source["affected_commuters"].sum()) if not source.empty else 0
    in_window = int(total * 0.68)
    out_of_window = total - in_window

    df = pd.DataFrame(
        {
            "category": ["In Window", "Out of Window"],
            "count": [in_window, out_of_window],
        }
    )

    order = ["In Window", "Out of Window"]
    df["category"] = pd.Categorical(df["category"], categories=order, ordered=True)
    df = df.sort_values("category")

    return df

# ── Figure builders ───────────────────────────────────────────────────────────

def build_map_figure(region=None, time_of_day=None, delay_duration=None, transfer_window=45, planning_area=None):
    """
    Builds the Singapore map figure.

    TODO: When backend is ready:
      1. Query filtered commuter data using (region, time_of_day, delay_duration, transfer_window, planning_area)
      2. Query filtered commuter data by planning area and join on PLN_AREA_N.
      3. Replace synthetic values with actual affected commuter counts.
    """
    sg_geojson = load_planning_area_geojson()
    df_all = get_placeholder_map_data()
    df_selected = get_placeholder_map_data(region, planning_area)

    if df_selected.empty:
        df_selected = df_all.copy()

    has_filter = (region and region != "All Regions") or (
        planning_area and planning_area != "All Planning Areas"
    )

    fig = go.Figure()

    if not has_filter:
        fig = px.choropleth_mapbox(
            df_all,
            geojson=sg_geojson,
            locations="planning_area_raw",
            featureidkey="properties.PLN_AREA_N",
            color="affected_commuters",
            labels={"affected_commuters": "Affected commuters"},
            color_continuous_scale=[
                "#eaf2ff",
                "#bfd6ff",
                "#7faeff",
                "#1a56db"
            ],
            mapbox_style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=10
        )

        fig.update_traces(
            customdata=df_all[["planning_area", "region", "affected_commuters"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Region: %{customdata[1]}<br>"
                "Affected commuters: %{customdata[2]}<extra></extra>"
            ),
        )

    else:
        selected_areas = set(df_selected["planning_area_raw"])
        df_other = df_all[~df_all["planning_area_raw"].isin(selected_areas)]

        if not df_other.empty:
            fig.add_trace(
                go.Choroplethmapbox(
                    geojson=sg_geojson,
                    locations=df_other["planning_area_raw"],
                    z=[1] * len(df_other),
                    featureidkey="properties.PLN_AREA_N",
                    colorscale=[[0, "#e5e7eb"], [1, "#e5e7eb"]],
                    showscale=False,
                    marker_line_color="#9ca3af",
                    marker_line_width=0.8,
                    customdata=df_other[["planning_area", "region", "affected_commuters"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Region: %{customdata[1]}<br>"
                        "Affected commuters: %{customdata[2]}<extra></extra>"
                    ),
                )
            )

        fig.add_trace(
            go.Choroplethmapbox(
                geojson=sg_geojson,
                locations=df_selected["planning_area_raw"],
                z=df_selected["affected_commuters"],
                featureidkey="properties.PLN_AREA_N",
                colorscale=[
                    [0.0, "#eaf2ff"],
                    [0.33, "#bfd6ff"],
                    [0.66, "#7faeff"],
                    [1.0, "#1a56db"],
                ],
                zmin=df_all["affected_commuters"].min(),
                zmax=df_all["affected_commuters"].max(),
                showscale=False,
                marker_line_color="#6b7280",
                marker_line_width=1.2,
                customdata=df_selected[["planning_area", "region", "affected_commuters"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Region: %{customdata[1]}<br>"
                    "Affected commuters: %{customdata[2]}<extra></extra>"
                ),
            )
        )

    if not has_filter:
        fig.update_traces(
            hovertemplate=
            "<b>%{customdata[0]}</b><br>"
            "Region: %{customdata[1]}<br>"
            "Affected commuters: %{customdata[2]}<extra></extra>"
        )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=10,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        hoverlabel=dict(
    bgcolor="white",
    font_size=16,
    font_family="Arial",
    font_color="#1f2937",
    bordercolor="#d1d5db"
)
    )
    return fig


def build_bar_figure(region=None, time_of_day=None, delay_duration=None, transfer_window=45, planning_area=None):
    """
    Builds the In Window vs Out of Window bar chart.

    TODO: When backend is ready, replace get_placeholder_bar_data() with
          a real query filtered by (region, time_of_day, delay_duration, transfer_window, planning_area).
    """
    df = get_placeholder_bar_data(region, planning_area)
    max_count = df["count"].max()

    fig = go.Figure([
        go.Bar(
            x=df["category"],
            y=df["count"],
            marker_color=[C["accent"], C["accent_mid"]],
            text=df["count"],
            textposition="outside",
            textfont=dict(size=11, family=FONT_MONO),
            cliponaxis = False,
        )
    ])

    fig.update_layout(
        **{**PLOTLY_LAYOUT, "margin": dict(l=32, r=16, t=40, b=32)},
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title="Commuters", range=[0, max_count * 1.18]),
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
                    section_label("Planning Area (Town)"),
                    dcc.Dropdown(
                        id="p4-planning-area-dropdown",
                        options=[],
                        value="All Planning Areas",
                        clearable=False,
                        style={"fontSize": "13px", "width": "200px"},
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
    Output("p4-planning-area-dropdown", "options"),
    Output("p4-planning-area-dropdown", "value"),
    Input("p4-region-dropdown", "value"),
)
def update_planning_areas(region):
    """Update planning area options based on selected region."""
    planning_areas = get_planning_areas_for_region(region)
    options = [{"label": pa, "value": pa} for pa in planning_areas]
    return options, "All Planning Areas"


@callback(
    Output("p4-map-figure", "figure"),
    Output("p4-bar-figure", "figure"),
    Input("p4-region-dropdown", "value"),
    Input("p4-planning-area-dropdown", "value"),
    Input("p4-time-dropdown", "value"),
    Input("p4-delay-dropdown", "value"),
    Input("p4-transfer-window-slider", "value"),
)
def update_figures(region, planning_area, time_of_day, delay_duration, transfer_window):
    map_fig = build_map_figure(region, time_of_day, delay_duration, transfer_window, planning_area)
    bar_fig = build_bar_figure(region, time_of_day, delay_duration, transfer_window, planning_area)
    return map_fig, bar_fig

