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

# Normalise region names to uppercase to match geojson PLN_AREA_N
df_region["orig_region"] = df_region["orig_region"].str.upper().str.strip()
df_region["dest_region"] = df_region["dest_region"].str.upper().str.strip()

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
    "20-59":        "#e02424",
    "60+":          "#d97706",
    "7-19":         "#7e3af2",
}

AGE_COLORS = {
    "20-59": "#e02424",
    "60+":   "#d97706",
    "7-19":  "#7e3af2",
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

def build_timeseries(age_filter):
    groups   = age_filter or df_time["age_group"].unique().tolist()
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
            name=grp,
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
    groups   = age_filter or df_time["age_group"].unique().tolist()
    filtered = df_time[df_time["age_group"].isin(groups)]

    fig = go.Figure()
    for grp in groups:
        sub = filtered[filtered["age_group"] == grp].sort_values("hour_of_day")
        fig.add_trace(go.Bar(
            x=sub["hour_of_day"],
            y=sub["count"],
            name=grp,
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


def build_map_figure(origin, hour_filter):
    filtered = df_region.copy()

    if hour_filter:
        filtered = filtered[filtered["hour_of_day"].isin(hour_filter)]

    if origin:
        filtered = filtered[filtered["orig_region"] == origin]
        agg = filtered.groupby("dest_region")["count"].sum().reset_index()
        agg.columns = ["region", "count"]
        # Also include the origin itself with 0 so it renders on map
        origin_row = pd.DataFrame([{"region": origin, "count": 0}])
        agg = pd.concat([agg, origin_row], ignore_index=True).drop_duplicates("region")
    else:
        # No origin selected: show total outbound volume per region
        agg = filtered.groupby("orig_region")["count"].sum().reset_index()
        agg.columns = ["region", "count"]

    fig = px.choropleth_mapbox(
        agg,
        geojson=geojson,
        locations="region",
        featureidkey="properties.PLN_AREA_N",
        color="count",
        color_continuous_scale=[
            [0.0, "#eff4ff"],
            [0.5, "#76a9fa"],
            [1.0, "#1a56db"],
        ],
        mapbox_style="carto-positron",
        zoom=10,
        center={"lat": 1.3521, "lon": 103.8198},
        opacity=0.7,
        hover_name="region",
        hover_data={"count": True, "region": False},
        labels={"count": "Transfer Volume"},
    )

    # Highlight selected origin region in red outline
    if origin:
        origin_geom = [f for f in geojson["features"]
                       if f["properties"]["PLN_AREA_N"] == origin]
        if origin_geom:
            fig.add_trace(go.Choroplethmapbox(
                geojson={"type": "FeatureCollection", "features": origin_geom},
                locations=[origin],
                featureidkey="properties.PLN_AREA_N",
                z=[1],
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker=dict(line=dict(color="#e02424", width=2)),
                hoverinfo="skip",
                name="Selected Origin",
            ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(
            title="Volume",
            tickfont=dict(size=11, color=C["secondary"]),
            outlinewidth=0,
        ),
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


# ── Derive filter options ─────────────────────────────────────────────────────

age_groups   = sorted(df_time["age_group"].unique().tolist())
all_hours    = sorted(df_region["hour_of_day"].unique().tolist())
all_regions  = sorted(df_region["orig_region"].unique().tolist())

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
    ], style={
        "display":       "flex",
        "alignItems":    "flex-start",
        "marginBottom":  "28px",
        "paddingBottom": "20px",
        "borderBottom":  f"1px solid {C['border']}",
    }),

    # ── 1. Avg Transfer Time by Hour ──────────────────────────────────────────
    card(
        "Average Transfer Time by Hour",
        "Mean transfer completion time per hour of day, segmented by age group",
        [
            filter_bar([
                html.Div([
                    section_label("Age Group"),
                    dcc.Checklist(
                        id="filter-age-ts",
                        options=[{"label": f"  {a}", "value": a} for a in age_groups],
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
    ),

    # ── 2. Transfer Volume by Hour ────────────────────────────────────────────
    card(
        "Transfer Volume by Hour",
        "Total number of transfers per hour, stacked by age group",
        [
            filter_bar([
                html.Div([
                    section_label("Age Group"),
                    dcc.Checklist(
                        id="filter-age-bar",
                        options=[{"label": f"  {a}", "value": a} for a in age_groups],
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
    ),

    # ── 3. Spatial Transfer Map ───────────────────────────────────────────────
    card(
        "Spatial Transfer Analysis",
        "Transfer volumes from a selected origin region across Singapore — select an origin to explore flows",
        [
            filter_bar([
                html.Div([
                    section_label("Origin Region"),
                    dcc.Dropdown(
                        id="filter-origin",
                        options=[{"label": r.title(), "value": r} for r in all_regions],
                        value=None,
                        multi=False,
                        placeholder="All regions (total outbound volume)",
                        style={"minWidth": "280px", "fontSize": "13px"},
                    ),
                ]),
                html.Div([
                    section_label("Hour of Day"),
                    dcc.Dropdown(
                        id="filter-hour",
                        options=[{"label": f"{h:02d}:00", "value": h} for h in all_hours],
                        value=None,
                        multi=True,
                        placeholder="All hours",
                        style={"minWidth": "260px", "fontSize": "13px"},
                    ),
                ]),
            ]),
            dcc.Graph(id="map-chart", config={"displayModeBar": False},
                      style={"height": "560px", "borderRadius": "8px", "overflow": "hidden"}),
            html.P(
                "Select an origin region to see where transfers flow. "
                "The selected origin is outlined in red. "
                "Darker shading indicates higher transfer volume to that destination.",
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
    Output("map-chart", "figure"),
    Input("filter-origin", "value"),
    Input("filter-hour", "value"),
)
def update_map(origin, hour_filter):
    return build_map_figure(origin, hour_filter)