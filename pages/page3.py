import dash
import os
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
current_dir = os.path.dirname(__file__)

csv_path = os.path.join(current_dir, "..", "data", "welfare_marginal.csv")
df = pd.read_csv(csv_path)

csv_path_spec_info = os.path.join(current_dir, "..", "data", "spec_info.csv")
df_spec_info = pd.read_csv(csv_path_spec_info)


unique_specs = df['spec'].unique()
unique_patron = df['patron'].unique()
unique_description = df_spec_info['description']

SPEC_OPTIONS = [{'label': str(val).capitalize(), 'value': val} for val in unique_specs]
PATRON_OPTIONS = [{'label': str(val).capitalize(), 'value': val} for val in unique_patron]
WINDOW_OPTIONS = list(range(20, 56, 5))  # 20,25,...,55
MODEL_DESCRIPTIONS = df_spec_info.set_index('spec')['description'].to_dict()



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
                    section_label("Patron Category"),
                    dcc.Dropdown(
                        id="sim-patron",
                        options = PATRON_OPTIONS,
                        value=unique_patron[0] if len(unique_patron) > 0 else None,
                        clearable = False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                ]),

                html.Div([
                    section_label("Model Specification"),
                    dcc.Dropdown(
                        id="sim-spec",
                        options=SPEC_OPTIONS,
                        value=unique_specs[0] if len(unique_specs) > 0 else None,
                        clearable=False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                ]),
                
                # html.Div([
                #     section_label("Time of Day"),
                #     dcc.Dropdown(
                #         id="sim-time",
                #         options=[{"label": t, "value": t} for t in TIMES_OF_DAY],
                #         value = "Morning Peak (6am–9am)",
                #         style={"width": "220px", "fontSize": "13px"},
                #     ),
                # ]),
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
            # slider 1
            html.Div([
                section_label("Transfer Window (minutes) Benchmark"),
                    dcc.Slider(
                        id="sim-window",
                        min=20,
                        max=55,
                        step=5,
                        value=45,
                        marks={w: {"label": str(w), "style": {"fontSize": "12px", "fontFamily": FONT_MONO}} for w in WINDOW_OPTIONS},
                        tooltip={"placement": "bottom"},
                        updatemode="drag",
                    ),
                ], style={
                    "padding": "14px 18px",
                    "background": C["bg"],
                    "borderRadius": "6px",
                    "border": f"1px solid {C['border']}",
                    "marginBottom": "20px", 
                }),
            # slider 2
            html.Div([
                section_label("Transfer Window (minutes) Hypothetical"),
                    dcc.Slider(
                        id="sim-window",
                        min=20,
                        max=55,
                        step=5,
                        value=45,
                        marks={w: {"label": str(w), "style": {"fontSize": "12px", "fontFamily": FONT_MONO}} for w in WINDOW_OPTIONS},
                        tooltip={"placement": "bottom"},
                        updatemode="drag",
                    ),
                ], style={
                    "padding": "14px 18px",
                    "background": C["bg"],
                    "borderRadius": "6px",
                    "border": f"1px solid {C['border']}",
                    "marginBottom": "20px", 
                }),
            
            # ── Output row (All three columns inside ONE flex container) ──
            html.Div([

                # Column 1: Specification Detail
                html.Div([
                    section_label("Specification Detail"),
                    html.Div(id="model-description-text", style={
                        "fontSize": "13px",
                        "color": C["secondary"],
                        "lineHeight": "1.5",
                        "fontFamily": FONT_SANS
                    })
                ], style={
                    "flex": "1", 
                    "background": C["surface"],
                    "border": f"1px solid {C['border']}",
                    "borderRadius": "8px",
                    "padding": "16px 18px",
                }),

                # Column 2: Rules & Chart
                html.Div([
                    # Chart input here 
                    html.Div([
                        section_label("Cost vs Benefit"),
                        dcc.Graph(
                            id="sim-chart",
                            config={"displayModeBar": False},
                            style={"height": "240px"},
                        ),
                    ]),
                ], style={
                    "flex": "1.5",
                    "background": C["surface"],
                    "border": f"1px solid {C['border']}",
                    "borderRadius": "8px",
                    "padding": "16px 18px",
                }),

                # Column 3: Commuter Profile
                html.Div([
                    section_label("Commuter Profile"),
                    html.Div(id="character-display", style={
                        "width": "180px", 
                        "height": "200px", 
                        "display": "flex", 
                        "alignItems": "center", 
                        "justifyContent": "center",
                        "background": "#fff",
                        "borderRadius": "12px",
                        "border": f"1px solid {C['border']}"
                    })
                ], style={"flex": "0 0 auto"}),

            ], style={
                "display": "flex", 
                "gap": "20px", 
                "alignItems": "stretch" # Keeps all cards the same height
            }),
        ] # Closes card() children list
    ), # Closes card() component
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

    Output("sim-chart", "figure"),
    Output("character-display","children"),
    Output("model-description-text", "children"),
    Input("sim-submit", "n_clicks"),
    State("sim-patron", "value"),
    State("sim-spec", "value"),
    prevent_initial_call=True,
)


def update_simulation(n_clicks, patron, spec):
    # --- 1. Initialize variables with defaults ---
    fig = go.Figure()  # Pre-define fig so it always exists
    char_img = ""
    description_text = ""

    # Basic safety check
    if not patron or not spec:
        return fig, char_img, description_text

    # --- 2. Image Logic ---
    CHAR_MAP = {
        "Student": "/assets/standup_stacey.png",
        "Adult": "/assets/movein_martin.png",
        "Senior Citizen": "/assets/giveway_glenda.png",
        "Overall": "/assets/mrt_picture.png" # current picture is bad can replace
    }
    img_path = CHAR_MAP.get(patron, CHAR_MAP["Overall"])
    char_img = html.Img(src=img_path, style={"width": "150px", "height": "180px", "objectFit": "contain"})

    # --- 3. Description Logic ---
    MODEL_DESCRIPTIONS = df_spec_info.set_index('spec')['description'].to_dict()
    description_text = MODEL_DESCRIPTIONS.get(spec, "No description available.")

    # --- 4. Chart Logic (Where 'fig' is defined) ---
    # Example: filtering your dataframe
    # Make sure 'df' is your welfare_marginal dataframe
    filtered_df = df[(df['patron'] == patron) & (df['spec'] == spec)]
    
    if not filtered_df.empty:
        # Create your bar chart here
        fig = go.Figure(data=[
            go.Bar(name='Benefit', x=['Impact'], y=[filtered_df['marginal_benefit_n'].sum()]),
            go.Bar(name='Cost', x=['Impact'], y=[filtered_df['marginal_cost_n'].sum()])
        ])
        fig.update_layout(barmode='group', height=240, margin=dict(l=20, r=20, t=20, b=20))
    else:
        # If no data is found, fig remains the empty object created at the top
        pass

    return fig, char_img, description_text




# def update_simulation(n_clicks, age, region, time):

#     if not age or not time:
#         return [], go.Figure()

#     rules = []

#     CHAR_MAP = {
#     "senior": "/assets/giveway_glenda.png",
#     "peak":   "/assets/movein_martin.png",
#     "default": "/assets/standup_stacey.png"
#     }
#     if age == "Youth":
#         img_path = CHAR_MAP["default"]
#     elif age == "Adult":
#         img_path = CHAR_MAP["peak"]
#     else:
#         img_path = CHAR_MAP["senior"]
#     char_img = html.Img(src=img_path, style={"width": "150px", "height": "180px"})
#     # ── Rule logic (aligned with project framing)
#     if age == "Senior":
#         rules.append("Extend transfer window to 60 minutes for elderly commuters")

#     if region != "Central":
#         rules.append("Increase transfer window in less connected regions")

#     if "Peak" in time:
#         rules.append("Reduce transfer window slightly to manage congestion")
#     else:
#         rules.append("Extend transfer window during off-peak hours")

#     # ── Cost-benefit logic (placeholder)
#     age_dict = {"Youth":2,"Adult":1,"Senior":5}
#     age_cost = age_dict[age]
#     cost = 30 + (age_cost * 0.1)
#     benefit = 50 + (10 if "Off-Peak" in time else -5)

#     fig = build_cost_benefit_figure(cost, benefit)

#   return [html.Li(r) for r in rules], fig, char_img