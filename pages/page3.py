import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dash import State

dash.register_page(__name__, path="/page-3", name="Policy Simulator")

# ── Design tokens  ────────────────────────────

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

# ── Temporary dropdown values  ────────────────────────

REGIONS = ["All Regions", "North", "North-East", "East", "West", "Central"]

TIMES_OF_DAY = [
    "Morning Peak (6am–9am)",
    "Off-Peak (9am–5pm)",
    "Evening Peak (5pm–8pm)",
    "Night (8pm–12am)",
]

# ── Layout helpers  ────────────────────────────────────────────

def section_label(text):
    return html.P(text, style={
        "fontSize": "10px",
        "fontWeight": "600",
        "letterSpacing": "0.1em",
        "textTransform": "uppercase",
        "color": C["secondary"],
        "fontFamily": FONT_MONO,
        "margin": "0 0 6px 0",
    })


def card(title, subtitle, children):
    return html.Div([
        html.Div([
            html.H3(title, style={
                "margin": 0,
                "fontSize": "15px",
                "fontWeight": "600",
                "color": C["text"],
                "fontFamily": FONT_SANS,
            }),
            html.P(subtitle, style={
                "margin": "3px 0 0",
                "fontSize": "12px",
                "color": C["secondary"],
                "fontFamily": FONT_SANS,
            }),
        ], style={
            "marginBottom": "20px",
            "paddingBottom": "16px",
            "borderBottom": f"1px solid {C['border_light']}",
        }),
        *children,
    ], style={
        "background": C["surface"],
        "border": f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding": "24px 28px",
        "marginBottom": "20px",
    })


# ── Figure builder ──────────────────────────

def build_cost_benefit_figure(cost, benefit):
    fig = go.Figure([
        go.Bar(
            x=["Cost", "Benefit"],
            y=[cost, benefit],
            marker_color=[C["accent_mid"], C["accent"]],
            text=[round(cost,1), round(benefit,1)],
            textposition="outside",
            textfont=dict(size=11, family=FONT_MONO),
        )
    ])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_SANS, color=C["text"]),
        margin=dict(l=32, r=16, t=16, b=32),
        height=220,
        yaxis=dict(title="Score", gridcolor=C["border_light"]),
    )

    return fig


# ── Layout ───────────────────────────────────────

layout = html.Div([

    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap",
    ),

    # Header
    html.Div([
        html.H1("Policy Simulator", style={
            "margin": 0,
            "fontSize": "20px",
            "fontWeight": "600",
        }),
        html.P(
            "Generate proposed transfer rules and evaluate cost-benefit tradeoffs by demographic and travel conditions",
            style={"margin": "4px 0 0", "fontSize": "13px", "color": C["secondary"]},
        ),
    ], style={
        "marginBottom": "28px",
        "paddingBottom": "20px",
        "borderBottom": f"1px solid {C['border']}",
    }),

    # ── Main card ─────────────────────────────────────
    card(
        "Policy Input Controls",
        "Define commuter characteristics and travel conditions",
        [

            # Inputs row
            html.Div([

                html.Div([
                    section_label("Age"),
                    dcc.Input(
                        id="sim-age",
                        type="number",
                        placeholder="Enter age",
                        style={"width": "140px", "fontSize": "13px"},
                    ),
                ]),

                html.Div([
                    section_label("Region"),
                    dcc.Dropdown(
                        id="sim-region",
                        options=[{"label": r, "value": r} for r in REGIONS],
                        value="All Regions",
                        clearable=False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                ]),

                html.Div([
                    section_label("Time of Day"),
                    dcc.Dropdown(
                        id="sim-time",
                        options=[{"label": t, "value": t} for t in TIMES_OF_DAY],
                        placeholder="Select time",
                        style={"width": "220px", "fontSize": "13px"},
                    ),
                ]),
                html.Div([
                    html.Button(
                        "Let's Go!",
                        id="sim-submit",
                        n_clicks=0,
                        style={
                        "background": C["accent"],
                        "color": "white",
                        "border": "none",
                        "padding": "10px 18px",
                        "borderRadius": "6px",
                        "fontSize": "13px",
                        "fontWeight": "600",
                        "cursor": "pointer",
                        "marginTop": "18px",
                        }
                    )
                ])

            ], style={
                "display": "flex",
                "gap": "32px",
                "flexWrap": "wrap",
                "padding": "14px 18px",
                "background": C["bg"],
                "borderRadius": "6px",
                "border": f"1px solid {C['border']}",
                "marginBottom": "20px",
            }),

            # Output row
            html.Div([

                # Rules
                html.Div([
                    section_label("Proposed Rules"),
                    html.Ul(id="sim-rules"),
                ], style={
                    "flex": "1",
                    "background": C["surface"],
                    "border": f"1px solid {C['border']}",
                    "borderRadius": "8px",
                    "padding": "16px 18px",
                }),

                # Chart
                html.Div([
                    section_label("Cost vs Benefit"),
                    dcc.Graph(
                        id="sim-chart",
                        config={"displayModeBar": False},
                        style={"height": "240px"},
                    ),
                ], style={
                    "width": "280px",
                    "background": C["surface"],
                    "border": f"1px solid {C['border']}",
                    "borderRadius": "8px",
                    "padding": "16px 18px",
                }),

            ], style={"display": "flex", "gap": "20px"}),

        ],
    ),

], style={
    "background": C["bg"],
    "minHeight": "100vh",
    "padding": "36px 48px",
    "fontFamily": FONT_SANS,
    "maxWidth": "1100px",
    "margin": "0 auto",
})


# ── Callback ───────────────────────────────────
@callback(
    Output("sim-rules", "children"),
    Output("sim-chart", "figure"),
    Input("sim-submit", "n_clicks"),
    State("sim-age", "value"),
    State("sim-region", "value"),
    State("sim-time", "value"),
    prevent_initial_call=True,
)
def update_simulation(n_clicks, age, region, time):

    if not age or not time:
        return [], go.Figure()

    rules = []

    # ── Rule logic (aligned with project framing)
    if age >= 65:
        rules.append("Extend transfer window to 60 minutes for elderly commuters")

    if region != "Central":
        rules.append("Increase transfer window in less connected regions")

    if "Peak" in time:
        rules.append("Reduce transfer window slightly to manage congestion")
    else:
        rules.append("Extend transfer window during off-peak hours")

    # ── Cost-benefit logic (placeholder)
    cost = 30 + (age * 0.1)
    benefit = 50 + (10 if "Off-Peak" in time else -5)

    fig = build_cost_benefit_figure(cost, benefit)

    return [html.Li(r) for r in rules], fig