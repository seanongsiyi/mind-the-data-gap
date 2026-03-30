import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from pathlib import Path

# ── Load delay simulation data ────────────────────────────────────────────────
DELAY_SIM_CSV_PATH = Path('data/delay_sim_results.csv')
if DELAY_SIM_CSV_PATH.exists():
    DELAY_SIM_DF = pd.read_csv(DELAY_SIM_CSV_PATH)
else:
    DELAY_SIM_DF = None

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


# ── Query helper function ────────────────────────────────────────────────────
def query_delay_sim(
    delay_mins:      int,
    bus_window:      int,
    classifier_type: str,
    patron:          str = 'all',
    df:              pd.DataFrame = None
):
    """Query delay simulation results for given parameters."""
    if df is None:
        df = DELAY_SIM_DF
    
    if df is None:
        raise ValueError("Delay simulation data not loaded. Missing data/delay_sim_results.csv")

    valid_delays  = [0, 5, 10, 15, 20]
    valid_windows = list(range(35, 65, 5))
    valid_specs   = ['baseline', 'lenient', 'strict']

    if delay_mins      not in valid_delays:  raise ValueError(f"delay_mins must be one of {valid_delays}")
    if bus_window      not in valid_windows: raise ValueError(f"bus_window must be one of {valid_windows}")
    if classifier_type not in valid_specs:   raise ValueError(f"classifier_type must be one of {valid_specs}")

    sub = df[
        (df['delay_mins']      == delay_mins)  &
        (df['bus_window_mins'] == bus_window)  &
        (df['spec']            == classifier_type)
    ].copy()

    if sub.empty:
        raise ValueError("No data found for given parameters")

    if patron == 'all':
        main_row = sub[sub['breakdown_type'] == 'overall'].iloc[0]
    else:
        patron_rows = sub[sub['breakdown_type'] == 'patron']
        if patron not in patron_rows['breakdown_value'].values:
            raise ValueError(f"Patron '{patron}' not found. Available: {patron_rows['breakdown_value'].tolist()}")
        main_row = patron_rows[patron_rows['breakdown_value'] == patron].iloc[0]

    classifier_journeys = int(main_row['classifier_journeys']) if not pd.isna(main_row['classifier_journeys']) else None
    window_journeys     = int(main_row['window_journeys'])     if not pd.isna(main_row['window_journeys'])     else None
    journey_difference  = (window_journeys - classifier_journeys) if (window_journeys and classifier_journeys) else None

    def get_breakdown(breakdown_type, col_name):
        return (
            sub[sub['breakdown_type'] == breakdown_type][[
                'breakdown_value', 'n_pairs', 'n_cards',
                'classifier_journeys', 'window_journeys',
                'wrongly_split_pairs',       'wrongly_merged_pairs',
                'wrongly_split_pair_pct',     'wrongly_merged_pair_pct',
                'wrongly_split_pct_all', 'wrongly_merged_pct_all',
            ]]
            .rename(columns={'breakdown_value': col_name})
            .sort_values('wrongly_split_pair_pct', ascending=False)
            .reset_index(drop=True)
        )

    return {
        'spec':                classifier_type,
        'delay_mins':          delay_mins,
        'bus_window_mins':     bus_window,
        'patron':              patron,
        'classifier_journeys': classifier_journeys,
        'window_journeys':     window_journeys,
        'journey_difference':  journey_difference,
        'wrongly_split_n':     int(main_row['wrongly_split_pairs']),
        'wrongly_merged_n':    int(main_row['wrongly_merged_pairs']),
        'wrongly_split_pct':   float(main_row['wrongly_split_pair_pct']),
        'wrongly_merged_pct':  float(main_row['wrongly_merged_pair_pct']),
        'by_patron':           get_breakdown('patron',          'patron'),
        'by_dest_region':      get_breakdown('dest_region',     'dest_region'),
        'by_orig_region':      get_breakdown('orig_region',     'orig_region'),
        'by_hour':             get_breakdown('next_entry_hour', 'hour'),
    }


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
# Expected shape: DataFrame with columns [region, planning_area, wrongly_split_n, wrongly_split_pct]
def get_placeholder_map_data(region=None, planning_area=None):
    meta = get_planning_area_metadata().copy()

    # Deterministic synthetic values so the demo remains stable across refreshes.
    # wrongly_split_n: number of genuine transfers broken under this delay
    meta["wrongly_split_n"] = meta["planning_area_raw"].apply(
        lambda x: 150 + (sum(ord(ch) for ch in x) % 800)
    )
    # wrongly_split_pct: percentage of all genuine transfers in this region
    meta["wrongly_split_pct"] = meta["planning_area_raw"].apply(
        lambda x: 5 + ((sum(ord(ch) for ch in x) % 25))
    )

    if region and region != "All Regions":
        meta = meta[meta["region"] == region]

    if planning_area and planning_area != "All Planning Areas":
        meta = meta[meta["planning_area"] == planning_area]

    return meta


def get_real_bar_data(delay_duration=None, transfer_window=45, region=None, planning_area=None, time_of_day=None):
    """Get real bar data from delay simulation results (percentages)."""
    if DELAY_SIM_DF is None:
        raise ValueError("Delay simulation data not loaded. Missing data/delay_sim_results.csv")
    
    # Parse delay_duration string to minutes (e.g. "10 minutes" -> 10)
    if delay_duration:
        try:
            delay_mins = int(delay_duration.split()[0])
        except (ValueError, IndexError):
            delay_mins = 10
    else:
        delay_mins = 10
    
    result = query_delay_sim(
        delay_mins=delay_mins,
        bus_window=transfer_window,
        classifier_type='baseline',
        patron='all'
    )
    
    wrongly_split_pct = result['wrongly_split_pct']
    wrongly_merged_pct = result['wrongly_merged_pct']
    
    df = pd.DataFrame({
        'metric': ['True transfers broken (%)', 'False transfers created (%)'],
        'count': [wrongly_split_pct, wrongly_merged_pct],
    })
    
    order = ['True transfers broken (%)', 'False transfers created (%)']
    df['metric'] = pd.Categorical(df['metric'], categories=order, ordered=True)
    df = df.sort_values('metric')
    
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
            color="wrongly_split_pct",
            labels={"wrongly_split_pct": "% of genuine transfers broken"},
            color_continuous_scale=[
                "#eaf2ff",
                "#bfd6ff",
                "#7faeff",
                "#1a56db"
            ],
            mapbox_style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=9.7
        )
        fig.update_traces(
            marker_line_width=0.5,
            marker_line_color="grey",
            showscale=False,
        )

        fig.update_traces(
            customdata=df_all[["planning_area", "region", "wrongly_split_n", "wrongly_split_pct"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Region: %{customdata[1]}<br>"
                "Transfers broken: %{customdata[2]}<br>"
                "% of transfers: %{customdata[3]}%<extra></extra>"
            ),
            marker_line_width=0.5,
            marker_line_color="grey",
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
                    marker_line_width=0.5,
                    marker_line_color="grey",
                    customdata=df_other[["planning_area", "region", "wrongly_split_n", "wrongly_split_pct"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Region: %{customdata[1]}<br>"
                        "Transfers broken: %{customdata[2]}<br>"
                        "% of transfers: %{customdata[3]}%<extra></extra>"
                    ),
                )
            )

        fig.add_trace(
            go.Choroplethmapbox(
                geojson=sg_geojson,
                locations=df_selected["planning_area_raw"],
                z=df_selected["wrongly_split_pct"],
                featureidkey="properties.PLN_AREA_N",
                colorscale=[
                    [0.0, "#eaf2ff"],
                    [0.33, "#bfd6ff"],
                    [0.66, "#7faeff"],
                    [1.0, "#1a56db"],
                ],
                zmin=df_all["wrongly_split_pct"].min(),
                zmax=df_all["wrongly_split_pct"].max(),
                showscale=False,
                marker_line_width=0.5,
                marker_line_color="grey",
                customdata=df_selected[["planning_area", "region", "wrongly_split_n", "wrongly_split_pct"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Region: %{customdata[1]}<br>"
                    "Transfers broken: %{customdata[2]}<br>"
                    "% of transfers: %{customdata[3]}%<extra></extra>"
                ),
            )
        )

    if not has_filter:
        fig.update_traces(
            hovertemplate=
            "<b>%{customdata[0]}</b><br>"
            "Region: %{customdata[1]}<br>"
            "Transfers broken: %{customdata[2]}<br>"
            "% of transfers: %{customdata[3]}%<extra></extra>"
        )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=9.7,
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
    Builds the Wrongly Split vs Wrongly Merged tradeoff bar chart.
    Shows the cost and benefit of the selected transfer window (as percentages).
    """
    df = get_real_bar_data(delay_duration, transfer_window, region, planning_area, time_of_day)
    max_count = df["count"].max()

    fig = go.Figure([
        go.Bar(
            x=df["metric"],
            y=df["count"],
            marker_color=["#dc2626", "#f59e0b"],  # Red for split errors (bad), amber for merge tradeoff
            text=[f"{v:.2f}%" for v in df["count"]],
            textposition="outside",
            textfont=dict(size=11, family=FONT_MONO),
            cliponaxis=False,
        )
    ])

    fig.update_layout(
        **{**PLOTLY_LAYOUT, "margin": dict(l=32, r=16, t=40, b=32)},
        xaxis=dict(**AXIS_STYLE),
        yaxis=dict(**AXIS_STYLE, title="Percentage (%)", range=[0, max_count * 1.18]),
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
        "Genuine transfers broken by delays, shown as % of all transfers in each region",
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
                        section_label("Tradeoff Analysis"),
                        dcc.Graph(
                            id="p4-bar-figure",
                            figure=build_bar_figure(),
                            config={"displayModeBar": False},
                            style={"height": "220px"},
                        ),
                        # Debug info
                        html.Div(id="p4-debug-info", style={
                            "fontSize": "11px",
                            "fontFamily": FONT_MONO,
                            "background": "#f3f4f6",
                            "padding": "8px 12px",
                            "borderRadius": "4px",
                            "color": "#374151",
                            "marginTop": "8px",
                            "lineHeight": "1.5",
                        }),
                    ], style={
                        "background":   C["surface"],
                        "border":       f"1px solid {C['border']}",
                        "borderRadius": "8px",
                        "padding":      "16px 18px",
                    }),

                ], style={"width": "260px", "display": "flex", "flexDirection": "column"}),

            ], style={"display": "flex", "gap": "20px", "alignItems": "flex-start"}),

            html.P(
                "The map shows the percentage of genuine transfers incorrectly broken under the current delay conditions. "
                "Use the slider to see how extending the transfer window rescues these broken transfers. "
                "The tradeoff panel shows the cost: wrongly linked transfers (false discounts) created by too-lenient windows.",
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
    Output("p4-debug-info", "children"),
    Input("p4-region-dropdown", "value"),
    Input("p4-planning-area-dropdown", "value"),
    Input("p4-time-dropdown", "value"),
    Input("p4-delay-dropdown", "value"),
    Input("p4-transfer-window-slider", "value"),
)
def update_figures(region, planning_area, time_of_day, delay_duration, transfer_window):
    map_fig = build_map_figure(region, time_of_day, delay_duration, transfer_window, planning_area)
    bar_fig = build_bar_figure(region, time_of_day, delay_duration, transfer_window, planning_area)
    
    # Get debug info from the query
    debug_text = ""
    if DELAY_SIM_DF is None:
        debug_text = "CSV not loaded"
    elif delay_duration is None:
        debug_text = "Select a delay duration"
    else:
        try:
            delay_mins = int(delay_duration.split()[0])
            result = query_delay_sim(
                delay_mins=delay_mins,
                bus_window=transfer_window,
                classifier_type='baseline',
                patron='all'
            )
            debug_text = (
                f"Delay: {result['delay_mins']}min | "
                f"Window: {result['bus_window_mins']}min | "
                f"Wrongly Split: {result['wrongly_split_pct']:.2f}% | "
                f"Wrongly Merged: {result['wrongly_merged_pct']:.2f}%"
            )
        except Exception as e:
            debug_text = f"Error: {str(e)}"
    
    return map_fig, bar_fig, debug_text

