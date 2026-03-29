import dash
from dash import html, dcc, Input, Output, callback, State
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.functions import get_welfare_summary, get_marginal_summary

dash.register_page(__name__, path="/page-3-welfare", name="Policy Simulator Welfare")

# ── Design tokens ─────────────────────────────────────────────────────────────

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
    "red":          "#ef4444",
    "green":        "#22c55e",
}

FONT_SANS = "'Inter', 'Helvetica Neue', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Mono', monospace"

PATRON_OPTIONS = ["Adult", "Student", "Senior Citizen"]
SPEC_OPTIONS   = ["baseline", "strict", "lenient"]
WINDOW_OPTIONS = list(range(20, 56, 5))  # 20,25,...,55

# ── Layout helpers ────────────────────────────────────────────────────────────

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


def stat_tile(label, value, sublabel=None, highlight=None):
    border_color = C["red"] if highlight == "red" else C["green"] if highlight == "green" else C["border"]
    return html.Div([
        html.P(label, style={
            "fontSize": "10px",
            "fontWeight": "600",
            "letterSpacing": "0.08em",
            "textTransform": "uppercase",
            "color": C["secondary"],
            "fontFamily": FONT_MONO,
            "margin": "0 0 6px 0",
        }),
        html.P(value, style={
            "fontSize": "22px",
            "fontWeight": "700",
            "color": C["text"],
            "fontFamily": FONT_MONO,
            "margin": "0",
            "lineHeight": "1",
        }),
        html.P(sublabel or "", style={
            "fontSize": "11px",
            "color": C["secondary"],
            "fontFamily": FONT_SANS,
            "margin": "4px 0 0",
        }),
    ], style={
        "background": C["surface"],
        "border": f"1.5px solid {border_color}",
        "borderRadius": "8px",
        "padding": "14px 18px",
        "flex": "1",
        "minWidth": "140px",
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


# ── Figure builders ───────────────────────────────────────────────────────────

def build_welfare_chart(split_n, merge_n, split_cond, merge_cond):
    fig = go.Figure([
        go.Bar(
            x=["Split Error (n)", "Merge Error (n)"],
            y=[split_n, merge_n],
            marker_color=[C["accent_mid"], C["red"]],
            text=[f"{int(split_n):,}", f"{int(merge_n):,}"],
            textposition="outside",
            textfont=dict(size=11, family=FONT_MONO),
            name="Count",
            yaxis="y1",
        ),
    ])
    fig.update_layout(
        title=dict(text="Window Performance vs Classifier", font=dict(size=13, family=FONT_SANS)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_SANS, color=C["text"]),
        margin=dict(l=32, r=16, t=40, b=32),
        height=260,
        yaxis=dict(gridcolor=C["border_light"], title="Count"),
        showlegend=False,
    )
    return fig


def build_marginal_chart(benefit_n, cost_n, window_from, window_to):
    fig = go.Figure([
        go.Bar(
            x=["Marginal Benefit", "Marginal Cost"],
            y=[benefit_n, cost_n],
            marker_color=[C["green"], C["red"]],
            text=[f"{int(benefit_n):,}", f"{int(cost_n):,}"],
            textposition="outside",
            textfont=dict(size=11, family=FONT_MONO),
        )
    ])
    fig.update_layout(
        title=dict(
            text=f"Marginal Effect: {window_from} → {window_to} min",
            font=dict(size=13, family=FONT_SANS)
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_SANS, color=C["text"]),
        margin=dict(l=32, r=16, t=40, b=32),
        height=260,
        yaxis=dict(gridcolor=C["border_light"], title="Pairs"),
    )
    return fig


# ── Layout ────────────────────────────────────────────────────────────────────

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
            "Evaluate transfer window policy tradeoffs by patron category and classifier specification",
            style={"margin": "4px 0 0", "fontSize": "13px", "color": C["secondary"]},
        ),
    ], style={
        "marginBottom": "28px",
        "paddingBottom": "20px",
        "borderBottom": f"1px solid {C['border']}",
    }),

    # ── Input card ────────────────────────────────────────────────────────────
    card(
        "Policy Input Controls",
        "Select patron category and classifier spec, then drag the slider to explore window sizes",
        [
            # dropdowns row
            html.Div([

                html.Div([
                    section_label("Patron Category"),
                    dcc.Dropdown(
                        id="sim-patron",
                        options=[{"label": p, "value": p} for p in PATRON_OPTIONS],
                        value="Adult",
                        clearable=False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                ]),

                html.Div([
                    section_label("Classifier Spec"),
                    dcc.Dropdown(
                        id="sim-spec",
                        options=[{"label": s, "value": s} for s in SPEC_OPTIONS],
                        value="baseline",
                        clearable=False,
                        style={"width": "160px", "fontSize": "13px"},
                    ),
                ]),

            ], style={
                "display": "flex",
                "gap": "32px",
                "flexWrap": "wrap",
                "marginBottom": "24px",
            }),

            # slider
            html.Div([
                section_label("Transfer Window (minutes)"),
                dcc.Slider(
                    id="sim-window",
                    min=20,
                    max=55,
                    step=5,
                    value=35,
                    marks={w: {"label": str(w), "style": {"fontSize": "12px", "fontFamily": FONT_MONO}} for w in WINDOW_OPTIONS},
                    tooltip={"placement": "bottom", "always_visible": True},
                    updatemode="drag",   # fires as slider moves
                ),
            ], style={
                "padding": "14px 18px",
                "background": C["bg"],
                "borderRadius": "6px",
                "border": f"1px solid {C['border']}",
            }),
        ],
    ),

    # ── Results card ──────────────────────────────────────────────────────────
    card(
        "Welfare Summary",
        "Performance of selected window against the classifier ground truth",
        [
            # stat tiles
            html.Div(id="sim-stats", style={
                "display": "flex",
                "gap": "12px",
                "flexWrap": "wrap",
                "marginBottom": "24px",
            }),

            # two charts
            html.Div([
                html.Div([
                    dcc.Graph(
                        id="sim-welfare-chart",
                        config={"displayModeBar": False},
                    ),
                ], style={"flex": "1"}),

                html.Div([
                    dcc.Graph(
                        id="sim-marginal-chart",
                        config={"displayModeBar": False},
                    ),
                ], style={"flex": "1"}),

            ], style={"display": "flex", "gap": "20px"}),
        ],
    ),

], style={
    "background": C["bg"],
    "minHeight": "100vh",
    "padding": "36px 48px",
    "fontFamily": FONT_SANS,
    "maxWidth": "1200px",
    "margin": "0 auto",
})


# ── Callback ──────────────────────────────────────────────────────────────────

@callback(
    Output("sim-stats",          "children"),
    Output("sim-welfare-chart",  "figure"),
    Output("sim-marginal-chart", "figure"),
    Input("sim-patron", "value"),
    Input("sim-spec",   "value"),
    Input("sim-window", "value"),
)
def update_simulation(patron, spec, window):

    # ── welfare summary ───────────────────────────────────────────────────────
    ws = get_welfare_summary(patron, window, spec)

    if isinstance(ws, str):
        empty = go.Figure()
        return [html.P(ws, style={"color": C["red"]})], empty, empty

    stats = [
        stat_tile(
            "Classifier Transfers",
            f"{int(ws['classifier_transfer_n']):,}",
            "pairs classifier says are transfers",
        ),
        stat_tile(
            "Classifier New Journeys",
            f"{int(ws['classifier_new_journey_n']):,}",
            "pairs classifier says are new journeys",
        ),
        stat_tile(
            "Split Error",
            f"{int(ws['split_error_n']):,}",
            f"{ws['split_error_cond_pct']:.2f}% of classifier transfers",
            highlight="red",
        ),
        stat_tile(
            "Merge Error",
            f"{int(ws['merge_error_n']):,}",
            f"{ws['merge_error_cond_pct']:.2f}% of classifier new journeys",
            highlight="red",
        ),
    ]

    welfare_fig = build_welfare_chart(
        ws['split_error_n'],
        ws['merge_error_n'],
        ws['split_error_cond_pct'],
        ws['merge_error_cond_pct'],
    )

    # ── marginal summary ──────────────────────────────────────────────────────
    if window < 55:
        mg = get_marginal_summary(patron, spec, window)
        if isinstance(mg, str):
            marginal_fig = go.Figure()
        else:
            marginal_fig = build_marginal_chart(
                mg['marginal_benefit_n'],
                mg['marginal_cost_n'],
                window,
                window + 5,
            )
    else:
        marginal_fig = go.Figure()
        marginal_fig.add_annotation(
            text="No marginal data — 55 min is the largest window",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=12, color=C["secondary"], family=FONT_SANS),
        )
        marginal_fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=260,
            margin=dict(l=32, r=16, t=40, b=32),
        )

    return stats, welfare_fig, marginal_fig