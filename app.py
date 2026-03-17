import dash
from dash import Dash, html, dcc, Input, Output, callback

app = Dash(__name__, use_pages=True)

app.layout = html.Div([

    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ),

    # ── Top header bar ────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span("MIND THE", style={
                "fontWeight": "700",
                "color": "#1a56db",
                "letterSpacing": "0.05em",
            }),
            html.Span(" DATA GAP", style={
                "fontWeight": "700",
                "color": "#111827",
                "letterSpacing": "0.05em",
            }),
        ], style={"fontSize": "18px", "fontFamily": "'Inter', sans-serif"}),

        html.P(
            "Evaluating Public Transfer Rules in Singapore",
            style={
                "margin": 0,
                "fontSize": "13px",
                "color": "#6b7280",
                "fontFamily": "'Inter', sans-serif",
            },
        ),
    ], style={
        "background":    "#ffffff",
        "borderBottom":  "1px solid #e2e5ec",
        "padding":       "16px 48px",
        "display":       "flex",
        "alignItems":    "center",
        "gap":           "32px",
    }),

    # ── Navigation tabs ───────────────────────────────────────────────────────
    html.Div([
        dcc.Tabs(
            id="nav-tabs",
            value="/",
            children=[
                dcc.Tab(
                    label=page["name"],
                    value=page["relative_path"],
                    style={
                        "padding":       "10px 20px",
                        "fontSize":      "13px",
                        "fontWeight":    "500",
                        "fontFamily":    "'Inter', sans-serif",
                        "color":         "#6b7280",
                        "border":        "none",
                        "borderBottom":  "2px solid transparent",
                        "background":    "transparent",
                        "cursor":        "pointer",
                    },
                    selected_style={
                        "padding":       "10px 20px",
                        "fontSize":      "13px",
                        "fontWeight":    "600",
                        "fontFamily":    "'Inter', sans-serif",
                        "color":         "#1a56db",
                        "border":        "none",
                        "borderBottom":  "2px solid #1a56db",
                        "background":    "transparent",
                        "cursor":        "pointer",
                    },
                )
                for page in dash.page_registry.values()
            ],
            style={
                "borderBottom": "1px solid #e2e5ec",
                "background":   "#ffffff",
            },
        ),
    ], style={"paddingLeft": "36px", "background": "#ffffff"}),

    # ── URL sync (hidden) ─────────────────────────────────────────────────────
    dcc.Location(id="url", refresh="callback-nav"),

    # ── Page content ──────────────────────────────────────────────────────────
    html.Div(
        dash.page_container,
        style={"background": "#f8f9fb", "minHeight": "calc(100vh - 110px)"},
    ),

], style={
    "margin":     0,
    "padding":    0,
    "background": "#f8f9fb",
    "fontFamily": "'Inter', sans-serif",
})


# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("url", "pathname"),
    Input("nav-tabs", "value"),
    prevent_initial_call=True,
)
def update_url(tab_value):
    return tab_value


@callback(
    Output("nav-tabs", "value"),
    Input("url", "pathname"),
)
def update_active_tab(pathname):
    return pathname

<<<<<<< HEAD
=======

>>>>>>> 5935f954d240c7ace57594bab51b29d0f2dabecc
if __name__ == "__main__":
    app.run(debug=True)