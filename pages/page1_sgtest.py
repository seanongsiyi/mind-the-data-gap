import sys
import os
import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.functions import get_trf_time_distribution, get_trf_pair_distribution, get_trf_temporal_pattern

dash.register_page(__name__, path="/page-1-test", name="Visualisation Suite test")

# ── Design tokens ─────────────────────────────────────────────────────────────

C = {
    "bg":             "#f8f9fb",
    "surface":        "#ffffff",
    "border":         "#e2e5ec",
    "border_light":   "#edf0f4",
    "accent":         "#1a56db",
    "accent_soft":    "#eff4ff",
    "text":           "#111827",
    "secondary":      "#6b7280",
    "7-19":           "#0e9f6e",
    "20-59":          "#1a56db",
    "60+":            "#d97706",
    "Adult":          "#1a56db",
    "Student":        "#0e9f6e",
    "Senior Citizen": "#d97706",
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

def build_histogram(age_group_filter, hour_filter):
    fig = go.Figure()
    groups = age_group_filter if age_group_filter else ["7-19", "20-59", "60+"]
    for ag in groups:
        df = get_trf_time_distribution(
            age_group=ag,
            hour=hour_filter if hour_filter != "All" else None
        )
        if df.empty:
            continue
        fig.add_trace(go.Bar(
            x=df['hour_of_day'],
            y=df['avg_transfer_time_mins'],
            name=ag,
            marker_color=C.get(ag, C["accent"]),
            opacity=0.85,
        ))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        barmode="group",
        xaxis=dict(**AXIS_STYLE, title="Hour of Day", tickvals=list(range(0, 24))),
        yaxis=dict(**AXIS_STYLE, title="Avg Transfer Time (min)"),
    )
    return fig


def build_heatmap():
    df = get_trf_pair_distribution()
    stations_orig = df['ORIG_STATION_NAME'].unique().tolist()
    stations_dest = df['DEST_STATION_NAME'].unique().tolist()
    all_stations  = sorted(set(stations_orig + stations_dest))
    matrix = pd.DataFrame(0, index=all_stations, columns=all_stations)
    for _, row in df.iterrows():
        matrix.loc[row['ORIG_STATION_NAME'], row['DEST_STATION_NAME']] = row['count']

    fig = go.Figure(go.Heatmap(
        z=matrix.values,
        x=matrix.columns.tolist(),
        y=matrix.index.tolist(),
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


def build_timeseries(patron_filter):
    fig = go.Figure()
    patrons = patron_filter if patron_filter else ["Adult", "Student", "Senior Citizen"]
    for patron in patrons:
        df = get_trf_temporal_pattern(patron=patron)
        if df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=df['hour_of_day'],
            y=df['avg_transfer_time_mins'],
            mode="lines+markers",
            name=patron,
            line=dict(color=C.get(patron, C["accent"]), width=2, shape="spline"),
            marker=dict(size=5, line=dict(color="#ffffff", width=1.5)),
        ))
    for band_start, band_end, label in [(7, 9, "AM Peak"), (17, 19, "PM Peak")]:
        fig.add_vrect(
            x0=band_start, x1=band_end,
            fillcolor=C["accent"], opacity=0.05,
            layer="below", line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation_font=dict(size=11, color=C["secondary"]),
        )
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
        "marginBottom":  "28px",
        "paddingBottom": "20px",
        "borderBottom":  f"1px solid {C['border']}",
    }),

    # ── 1. Transfer Time Distributions ────────────────────────────────────────
    card(
        "Transfer Time Distributions",
        "Average transfer time by age group and hour of day",
        [
            filter_bar([
                html.Div([
                    section_label("Age Group"),
                    dcc.Checklist(
                        id="vis-filter-age-group",
                        options=[{"label": f"  {a}", "value": a}
                                 for a in ["7-19", "20-59", "60+"]],
                        value=["7-19", "20-59", "60+"],
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
                html.Div([
                    section_label("Hour of Day"),
                    dcc.Dropdown(
                        id="vis-filter-hour",
                        options=[{"label": "All Hours", "value": "All"}] +
                                [{"label": f"{h:02d}:00", "value": h} for h in range(24)],
                        value="All",
                        clearable=False,
                        style={"width": "140px", "fontSize": "13px"},
                    ),
                ]),
            ]),
            dcc.Graph(id="vis-hist-chart", config={"displayModeBar": False},
                      style={"height": "360px"}),
            html.P(
                "Average transfer time per age group across hours of the day. "
                "Use the hour filter to isolate a specific time slot.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ),

    # ── 2. Spatial Transfer Analysis ──────────────────────────────────────────
    card(
        "Spatial Transfer Analysis",
        "Transfer volumes between station pairs — top 50 pairs by frequency",
        [
            dcc.Graph(id="vis-heatmap-chart", figure=build_heatmap(),
                      config={"displayModeBar": False}, style={"height": "520px"}),
            html.P(
                "Higher-intensity cells indicate station pairs with elevated transfer volumes. "
                "Only the top 50 most frequent transfer pairs are shown.",
                style={"fontSize": "12px", "color": C["secondary"],
                       "margin": "12px 0 0", "fontFamily": FONT_SANS},
            ),
        ],
    ),

    # ── 3. Temporal Pattern Detection ─────────────────────────────────────────
    card(
        "Temporal Pattern Detection",
        "Average transfer time by hour of day, segmented by patron type",
        [
            filter_bar([
                html.Div([
                    section_label("Patron Type"),
                    dcc.Checklist(
                        id="vis-filter-patron",
                        options=[{"label": f"  {p}", "value": p}
                                 for p in ["Adult", "Student", "Senior Citizen"]],
                        value=["Adult", "Student", "Senior Citizen"],
                        inline=True,
                        style={"color": C["text"], "fontSize": "13px", "fontFamily": FONT_SANS},
                        inputStyle={"marginRight": "5px", "accentColor": C["accent"]},
                    ),
                ]),
            ]),
            dcc.Graph(id="vis-ts-chart", config={"displayModeBar": False},
                      style={"height": "360px"}),
            html.P(
                "Shaded regions denote AM and PM peak periods. "
                "Each line represents a patron type's average transfer time profile across the day.",
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
    Output("vis-hist-chart", "figure"),
    Input("vis-filter-age-group", "value"),
    Input("vis-filter-hour", "value"),
)
def update_histogram(age_group_filter, hour_filter):
    return build_histogram(age_group_filter, hour_filter)


@callback(
    Output("vis-ts-chart", "figure"),
    Input("vis-filter-patron", "value"),
)
def update_timeseries(patron_filter):
    return build_timeseries(patron_filter)