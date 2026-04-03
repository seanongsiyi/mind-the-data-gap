import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
import json

dash.register_page(__name__, path="/page-1", name="Visualisation Suite")

# ── Load Real Data ────────────────────────────────────────────────────────────

current_dir = os.path.dirname(__file__)

df_time   = pd.read_csv(os.path.join(current_dir, "..", "data", "trf_time_distribution.csv"))
df_region = pd.read_csv(os.path.join(current_dir, "..", "data", "trf_region_pair.csv"))

with open(os.path.join(current_dir, "..", "data", "singapore_planning_areas.geojson")) as f:
    geojson = json.load(f)

df_region["orig_region"] = df_region["orig_region"].str.upper().str.strip()
df_region["dest_region"] = df_region["dest_region"].str.upper().str.strip()

# ── Time bucket mapping ───────────────────────────────────────────────────────

def hour_to_bucket(hour):
    try:
        hour = int(hour)
    except (ValueError, TypeError):
        return None
    if   6  <= hour <= 8:  return "Morning Peak (6am–9am)"
    elif 9  <= hour <= 16: return "Off-Peak (9am–5pm)"
    elif 17 <= hour <= 19: return "Evening Peak (5pm–8pm)"
    elif 20 <= hour <= 23: return "Night (8pm–12am)"
    else: return None

df_region["time_bucket"] = df_region["hour_of_day"].apply(hour_to_bucket)

# ── Planning area metadata ────────────────────────────────────────────────────

def get_planning_area_metadata():
    rows = []
    for feature in geojson["features"]:
        props = feature["properties"]
        region = props["REGION_N"].replace(" REGION", "").title()
        planning_area_raw = props["PLN_AREA_N"]
        rows.append({
            "region":            region,
            "planning_area_raw": planning_area_raw,
            "planning_area":     planning_area_raw.title(),
        })
    return pd.DataFrame(rows).drop_duplicates().sort_values("planning_area")

pa_meta = get_planning_area_metadata()

def get_planning_areas_for_region(region):
    meta = pa_meta.copy()
    if region and region != "All Regions":
        meta = meta[meta["region"] == region]
    return ["All Planning Areas"] + meta["planning_area"].tolist()

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
    "muted":        "#9ca3af",
    "success":      "#0e9f6e",
    "warning":      "#d97706",
}

AGE_ORDER = ["7-19", "20-59", "60+"]

AGE_COLORS = {
    "7-19":  "#7e3af2",
    "20-59": "#e02424",
    "60+":   "#d97706",
}

AGE_LABELS = {
    "7-19":  "Student (7-19)",
    "20-59": "Adult (20-59)",
    "60+":   "Senior Citizen (60+)",
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

REGIONS = ["All Regions", "Central", "East", "North", "North-East", "West"]
TIMES_OF_DAY = [
    "Morning Peak (6am–9am)",
    "Off-Peak (9am–5pm)",
    "Evening Peak (5pm–8pm)",
    "Night (8pm–12am)",
]

# ── Derive filter options ─────────────────────────────────────────────────────

age_groups = [a for a in AGE_ORDER if a in df_time["age_group"].unique()]

# ── Stats helpers ─────────────────────────────────────────────────────────────

def compute_side_stats(region, planning_area, time_of_day):
    filtered = df_region.copy()

    if time_of_day:
        filtered = filtered[filtered["time_bucket"] == time_of_day]

    if planning_area and planning_area != "All Planning Areas":
        pa_raw = pa_meta.loc[
            pa_meta["planning_area"].str.strip().str.lower()
            == planning_area.strip().lower(),
            "planning_area_raw"
        ].values
        if len(pa_raw):
            filtered = filtered[filtered["dest_region"].isin(pa_raw)]
    elif region and region != "All Regions":
        valid_areas = pa_meta.loc[pa_meta["region"] == region, "planning_area_raw"].tolist()
        filtered = filtered[filtered["dest_region"].isin(valid_areas)]

    if filtered.empty:
        return {
            "total":        0,
            "busiest_hour": "N/A",
            "worst_age":    "N/A",
            "pct_of_daily": "N/A",
        }

    total       = int(filtered["count"].sum())
    daily_total = int(df_region["count"].sum())
    pct_of_daily = f"{total / daily_total * 100:.1f}%" if daily_total > 0 else "N/A"

    by_hour      = filtered.groupby("hour_of_day")["count"].sum()
    busiest_hour = int(by_hour.idxmax())
    busiest_hour_str = f"{busiest_hour:02d}:00"

    df_age_hour = df_time[df_time["hour_of_day"] == busiest_hour]
    if not df_age_hour.empty:
        worst_age_row = df_age_hour.loc[df_age_hour["avg_transfer_time_mins"].idxmax()]
        worst_age = AGE_LABELS.get(worst_age_row["age_group"], worst_age_row["age_group"])
    else:
        worst_age = "N/A"

    return {
        "total":        total,
        "busiest_hour": busiest_hour_str,
        "worst_age":    worst_age,
        "pct_of_daily": pct_of_daily,
    }

# ── Chart builders ────────────────────────────────────────────────────────────

def build_timeseries(age_filter):
    groups   = age_filter or age_groups
    groups   = [g for g in AGE_ORDER if g in groups]
    filtered = df_time[df_time["age_group"].isin(groups)]

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

    for grp in groups:
        sub = filtered[filtered["age_group"] == grp].sort_values("hour_of_day")
        fig.add_trace(go.Scatter(
            x=sub["hour_of_day"],
            y=sub["avg_transfer_time_mins"],
            mode="lines+markers",
            name=AGE_LABELS.get(grp, grp),
            line=dict(color=AGE_COLORS.get(grp, C["accent"]), width=2, shape="spline"),
            marker=dict(size=5, color=AGE_COLORS.get(grp, C["accent"]),
                        line=dict(color="#ffffff", width=1.5)),
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


def build_volume_bar(age_filter):
    groups   = age_filter or age_groups
    groups   = [g for g in AGE_ORDER if g in groups]
    filtered = df_time[df_time["age_group"].isin(groups)]

    fig = go.Figure()
    for grp in groups:
        sub = filtered[filtered["age_group"] == grp].sort_values("hour_of_day")
        fig.add_trace(go.Bar(
            x=sub["hour_of_day"],
            y=sub["count"],
            name=AGE_LABELS.get(grp, grp),
            marker_color=AGE_COLORS.get(grp, C["accent"]),
            opacity=0.85,
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="stack",
        xaxis=dict(
            **AXIS_STYLE,
            title="Hour of Day",
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)],
        ),
        yaxis=dict(**AXIS_STYLE, title="Transfer Count"),
    )
    return fig


def build_map_figure(region=None, planning_area=None, time_of_day=None):
    filtered = df_region.copy()

    if time_of_day:
        filtered = filtered[filtered["time_bucket"] == time_of_day]

    agg = filtered.groupby("dest_region")["count"].sum().reset_index()
    agg.columns = ["planning_area_raw", "count"]

    df_map = pa_meta[["planning_area_raw", "planning_area", "region"]].merge(
        agg, on="planning_area_raw", how="left"
    )
    df_map["count"]    = df_map["count"].fillna(0)
    df_map["has_data"] = df_map["count"] > 0

    has_filter = (region and region != "All Regions") or \
                 (planning_area and planning_area != "All Planning Areas")

    fig = go.Figure()

    if not has_filter:
        df_with_data = df_map[df_map["has_data"]].copy()
        df_no_data   = df_map[~df_map["has_data"]].copy()

        if not df_with_data.empty:
            fig = px.choropleth_mapbox(
                df_with_data,
                geojson=geojson,
                locations="planning_area_raw",
                featureidkey="properties.PLN_AREA_N",
                color="count",
                color_continuous_scale=[
                    [0.0, "#eff4ff"],
                    [0.5, "#76a9fa"],
                    [1.0, "#1a56db"],
                ],
                mapbox_style="carto-positron",
                center={"lat": 1.3521, "lon": 103.8198},
                zoom=9.7,
                labels={"count": "Transfer Volume"},
            )
            fig.update_traces(
                customdata=df_with_data[["planning_area", "region", "count"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Region: %{customdata[1]}<br>"
                    "Transfer Volume: %{customdata[2]:,}<extra></extra>"
                ),
                marker_line_width=0.5,
                marker_line_color="grey",
                showscale=False,
            )
            fig.update_layout(coloraxis_showscale=False)

        if not df_no_data.empty:
            fig.add_trace(go.Choroplethmapbox(
                geojson=geojson,
                locations=df_no_data["planning_area_raw"],
                z=[1] * len(df_no_data),
                featureidkey="properties.PLN_AREA_N",
                colorscale=[[0, "#9ca3af"], [1, "#9ca3af"]],
                showscale=False, name="",
                marker_line_width=0.5, marker_line_color="grey",
                customdata=df_no_data[["planning_area", "region"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Region: %{customdata[1]}<br>"
                    "No data<extra></extra>"
                ),
            ))
    else:
        if planning_area and planning_area != "All Planning Areas":
            selected_areas = set(pa_meta.loc[
                pa_meta["planning_area"].str.strip().str.lower()
                == planning_area.strip().lower(), "planning_area_raw"
            ])
        elif region and region != "All Regions":
            selected_areas = set(pa_meta.loc[pa_meta["region"] == region, "planning_area_raw"])
        else:
            selected_areas = set()

        df_map["is_selected"] = df_map["planning_area_raw"].isin(selected_areas)
        df_map["fill_value"]  = df_map["is_selected"].astype(int)

        fig.add_trace(go.Choroplethmapbox(
            geojson=geojson,
            locations=df_map["planning_area_raw"],
            z=df_map["fill_value"],
            featureidkey="properties.PLN_AREA_N",
            colorscale=[
                [0.0, "#e5e7eb"], [0.499, "#e5e7eb"],
                [0.5, "#1a56db"], [1.0,   "#1a56db"],
            ],
            zmin=0, zmax=1, showscale=False, name="",
            marker_line_width=0.5, marker_line_color="grey",
            customdata=df_map[["planning_area", "region", "count"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Region: %{customdata[1]}<br>"
                "Transfer Volume: %{customdata[2]:,}<extra></extra>"
            ),
        ))

    fig.update_layout(
        mapbox=dict(style="carto-positron", center={"lat": 1.3521, "lon": 103.8198}, zoom=9.7),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=480,
        hoverlabel=dict(bgcolor="white", font_size=13, font_family=FONT_SANS,
                        font_color="#1f2937", bordercolor="#d1d5db"),
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


def stat_card(label, value, sublabel=None, accent=None):
    accent = accent or C["accent"]
    return html.Div([
        html.Div(label, style={
            "fontSize":      "10px",
            "fontWeight":    "600",
            "letterSpacing": "0.08em",
            "textTransform": "uppercase",
            "color":         C["secondary"],
            "fontFamily":    FONT_MONO,
            "marginBottom":  "4px",
        }),
        html.Div(value, style={
            "fontSize":   "20px",
            "fontWeight": "700",
            "color":      accent,
            "fontFamily": FONT_SANS,
            "lineHeight": "1.2",
        }),
        html.Div(sublabel, style={
            "fontSize":  "11px",
            "color":     C["muted"],
            "fontFamily": FONT_SANS,
            "marginTop": "2px",
        }) if sublabel else None,
    ], style={
        "background":   C["bg"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "8px",
        "padding":      "12px 14px",
        "marginBottom": "8px",
    })


def info_box(title, children):
    return html.Div([
        html.Div(title, style={
            "fontSize":      "12px",
            "fontWeight":    "700",
            "letterSpacing": "0.04em",
            "textTransform": "uppercase",
            "color":         C["accent"],
            "fontFamily":    FONT_MONO,
            "marginBottom":  "8px",
        }),
        html.Div(children, style={
            "fontSize":   "13px",
            "color":      C["secondary"],
            "fontFamily": FONT_SANS,
            "lineHeight": "1.6",
        }),
    ], style={
        "background":   C["accent_soft"],
        "border":       f"1px solid {C['border']}",
        "borderLeft":   f"4px solid {C['accent']}",
        "borderRadius": "8px",
        "padding":      "14px 16px",
        "marginBottom": "18px",
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
                "Explore journey trends across demographics, regions, and time of day.",
                style={
                    "margin":     "4px 0 0",
                    "fontSize":   "13px",
                    "color":      C["secondary"],
                    "fontFamily": FONT_SANS,
                },
            ),
        ]),
    ], style={
        "display":       "flex",
        "alignItems":    "flex-start",
        "marginBottom":  "28px",
        "paddingBottom": "20px",
        "borderBottom":  f"1px solid {C['border']}",
    }),

    # ── How to use ────────────────────────────────────────────────────────────
    info_box(
        "About This Page",
        [
            html.Div(["1. ", html.Strong("Average Transfer Time by Hour"), " Compare how long each age group takes to complete a transfer across the day."]),
            html.Div(["2. ", html.Strong("Transfer Volume by Hour"), " See when transfers are most concentrated and which age groups contribute most."]),
            html.Div(["3. ", html.Strong("Spatial Transfer Analysis"), " Explore inbound transfer volumes across Singapore planning areas, filterable by region and time of day."]),
        ]
    ),

    # ── Jump to ───────────────────────────────────────────────────────────────
    html.Div([
        html.Span("Jump to: ", style={
            "fontWeight":  "600",
            "marginRight": "10px",
            "fontSize":    "13px",
            "fontFamily":  FONT_SANS,
            "color":       C["text"],
        }),
        html.A("Transfer Time", href="#chart-time",   style={"marginRight": "15px", "textDecoration": "none", "color": C["accent"], "fontSize": "13px"}),
        html.A("Volume",        href="#chart-volume", style={"marginRight": "15px", "textDecoration": "none", "color": C["accent"], "fontSize": "13px"}),
        html.A("Spatial Map",   href="#chart-map",    style={"textDecoration": "none", "color": C["accent"], "fontSize": "13px"}),
    ], style={"marginBottom": "24px"}),

    # ── 1. Avg Transfer Time by Hour ──────────────────────────────────────────
    html.Div(card(
        "Average Transfer Time by Hour",
        "Mean transfer completion time per hour of day, segmented by age group",
        [
            filter_bar([
                html.Div([
                    section_label("Age Group"),
                    dcc.Checklist(
                        id="filter-age-ts",
                        options=[{"label": f"  {AGE_LABELS.get(a, a)}", "value": a} for a in age_groups],
                        value=age_groups,
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
            ]),
            dcc.Graph(id="ts-chart", config={"displayModeBar": False},
                      style={"height": "360px"}),
            html.P(
                "Shaded bands indicate AM and PM peak periods. "
                "Compare age groups to identify where transfer windows may need adjustment.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ), id="chart-time"),

    # ── 2. Transfer Volume by Hour ────────────────────────────────────────────
    html.Div(card(
        "Transfer Volume by Hour",
        "Total number of transfers per hour, stacked by age group",
        [
            filter_bar([
                html.Div([
                    section_label("Age Group"),
                    dcc.Checklist(
                        id="filter-age-bar",
                        options=[{"label": f"  {AGE_LABELS.get(a, a)}", "value": a} for a in age_groups],
                        value=age_groups,
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
            ]),
            dcc.Graph(id="bar-chart", config={"displayModeBar": False},
                      style={"height": "360px"}),
            html.P(
                "Volume peaks during morning and evening rush hours. "
                "Stacking reveals the relative contribution of each age group across the day.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ), id="chart-volume"),

    # ── 3. Spatial Transfer Map ───────────────────────────────────────────────
    html.Div(card(
        "Spatial Transfer Analysis",
        "Transfer volumes to each planning area (filter by region, planning area, or time of day)",
        [
            html.Div([
                html.Div([
                    section_label("Region"),
                    dcc.Dropdown(
                        id="p1-region-dropdown",
                        options=[{"label": r, "value": r} for r in REGIONS],
                        value="All Regions",
                        clearable=False,
                        style={"fontSize": "13px", "width": "180px"},
                    ),
                ]),
                html.Div([
                    section_label("Planning Area (Town)"),
                    dcc.Dropdown(
                        id="p1-planning-area-dropdown",
                        options=[{"label": pa, "value": pa}
                                 for pa in get_planning_areas_for_region(None)],
                        value="All Planning Areas",
                        clearable=False,
                        style={"fontSize": "13px", "width": "200px"},
                    ),
                ]),
                html.Div([
                    section_label("Time of Day"),
                    dcc.Dropdown(
                        id="p1-time-dropdown",
                        options=[{"label": t, "value": t} for t in TIMES_OF_DAY],
                        placeholder="All times",
                        clearable=True,
                        style={"fontSize": "13px", "width": "220px"},
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

            html.Div([
                html.Div([
                    dcc.Graph(
                        id="map-chart",
                        config={"displayModeBar": False},
                        style={"height": "480px", "borderRadius": "8px", "overflow": "hidden"},
                    ),
                ], style={"flex": "1"}),

                html.Div(
                    id="p1-side-panel",
                    children=[],
                    style={
                        "width":         "220px",
                        "display":       "flex",
                        "flexDirection": "column",
                        "gap":           "0px",
                    },
                ),
            ], style={"display": "flex", "gap": "20px", "alignItems": "stretch"}),

            html.P(
                "Darker shading indicates higher inbound transfer volume. "
                "Select a region or planning area to highlight it. "
                ,
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ), id="chart-map"),

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
    Output("ts-chart", "figure"),
    Input("filter-age-ts", "value"),
)
def update_timeseries(age_filter):
    return build_timeseries(age_filter)


@callback(
    Output("bar-chart", "figure"),
    Input("filter-age-bar", "value"),
)
def update_bar(age_filter):
    return build_volume_bar(age_filter)


@callback(
    Output("p1-planning-area-dropdown", "options"),
    Output("p1-planning-area-dropdown", "value"),
    Input("p1-region-dropdown", "value"),
)
def update_planning_areas(region):
    planning_areas = get_planning_areas_for_region(region)
    options = [{"label": pa, "value": pa} for pa in planning_areas]
    return options, "All Planning Areas"


@callback(
    Output("map-chart",     "figure"),
    Output("p1-side-panel", "children"),
    Input("p1-region-dropdown",        "value"),
    Input("p1-planning-area-dropdown", "value"),
    Input("p1-time-dropdown",          "value"),
)
def update_map(region, planning_area, time_of_day):
    fig   = build_map_figure(region, planning_area, time_of_day)
    stats = compute_side_stats(region, planning_area, time_of_day)

    total_fmt = f"{stats['total']:,}" if isinstance(stats['total'], int) else stats['total']

    panel = [
        stat_card(
            "Total Transfers",
            total_fmt,
            f"{stats['pct_of_daily']} of daily total",
            accent=C["accent"],
        ),
        stat_card(
            "Busiest Hour",
            stats["busiest_hour"],
            "highest transfer volume",
            accent=C["success"],
        ),
        stat_card(
            "Slowest Age Group",
            stats["worst_age"],
            f"at {stats['busiest_hour']}",
            accent=C["warning"],
        ),
    ]

    return fig, panel