import dash
import os
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dash import State
from models.functions import get_marginal_at_45


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

csv_path_regional = os.path.join(current_dir, "..", "data", "welfare_results_regional.csv")
df_region = pd.read_csv((csv_path_regional))

csv_path_welfare = os.path.join(current_dir, "..", "data", "welfare_results.csv")
df_welfare = pd.read_csv(csv_path_welfare)


unique_specs = df['spec'].unique()
unique_patron = df['patron'].unique()
sorted_regions = sorted(df_region['region_value'].unique())
unique_region =  ['All Planning Areas'] + sorted_regions
unique_description = df_spec_info['description']

SPEC_OPTIONS = [{'label': str(val).capitalize(), 'value': val} for val in unique_specs]
PATRON_OPTIONS = [{'label': str(val).capitalize(), 'value': val} for val in unique_patron]
REGION_OPTIONS = [{'label': str(val).title(), 'value': val} for val in unique_region]
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

def info_box(title, children):
    return html.Div([
        html.Div(title, style={
            "fontSize": "12px",
            "fontWeight": "700",
            "letterSpacing": "0.04em",
            "textTransform": "uppercase",
            "color": C["accent"],
            "fontFamily": FONT_MONO,
            "marginBottom": "8px",
        }),
        html.Div(children, style={
            "fontSize": "13px",
            "color": C["secondary"],
            "fontFamily": FONT_SANS,
            "lineHeight": "1.6",
        }),
    ], style={
        "background": C["accent_soft"],
        "border": f"1px solid {C['border']}",
        "borderLeft": f"4px solid {C['accent']}",
        "borderRadius": "8px",
        "padding": "14px 16px",
        "marginBottom": "18px",
    })

def stat_card(label, value, color=C["text"]):
    return html.Div([
        html.P(label, style={
            "fontSize": "10px",
            "fontWeight": "600",
            "color": C["secondary"],
            "textTransform": "uppercase",
            "margin": "0 0 4px 0",
            "fontFamily": FONT_MONO
        }),
        html.H3(f"{value:,.0f}", style={
            "fontSize": "18px",
            "fontWeight": "700",
            "color": color,
            "margin": 0,
            "fontFamily": FONT_SANS
        })
    ], style={
        "flex": "1",
        "padding": "12px 16px",
        "background": C["surface"],
        "border": f"1px solid {C['border_light']}",
        "borderRadius": "6px",
        "textAlign": "center"
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

    info_box(
            "How to use this simulator",
            [
                html.Div(["1. "] + [html.Strong("Input")] + [" your choices of patron, model specification and planning area."]),
                html.Div(["2. "] + [html.Strong("Select a transfer window")] + [" to compare against the"] + [html.Strong(" current 45 minute window.")]),
                html.Div(["3. "] + [html.Strong("Click compare")] + [" to simulate and compare different scenario."]),
                html.Div(["4. Click the"] + [html.Strong(" Let's Go button")] + [" to start analysing!"]),
            ]
        ),

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
                
                html.Div([
                     section_label("Planning Area"),
                     dcc.Dropdown(
                         id="sim-region",
                         options=REGION_OPTIONS,
                         value = unique_region[0] if len(unique_region) > 0 else None,
                         style={"width": "180px", "fontSize": "13px"},
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

            # slider 1
            html.Div([
                section_label("Transfer Window (minutes)"),
                    dcc.Slider(
                        id="sim-window-bench",
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

            # -- compare checkbox --     
            html.Div([
                dcc.Checklist(
                    id="compare-toggle",
                    options=[{"label": "Compare", "value": "on"}],
                    value=[],
                    style={"fontSize": "14px", "fontWeight": "600", "color": C["accent"]}
                )
            ], style={"marginBottom": "20px"}),

            # --- Comparison Input Row ---
            html.Div(id="compare-input-row", children=[
                section_label("Comparison inputs"),
                html.Div([
                    html.Div([
                    section_label("Patron Category"),
                    dcc.Dropdown(
                        id="sim-patron-B",
                        options = PATRON_OPTIONS,
                        value=unique_patron[0] if len(unique_patron) > 0 else None,
                        clearable = False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                ]),

                html.Div([
                    section_label("Model Specification"),
                    dcc.Dropdown(
                        id="sim-spec-B",
                        options=SPEC_OPTIONS,
                        value=unique_specs[0] if len(unique_specs) > 0 else None,
                        clearable=False,
                        style={"width": "180px", "fontSize": "13px"},
                    ),
                ]),
                
                html.Div([
                     section_label("Planning Area"),
                     dcc.Dropdown(
                         id="sim-region-B",
                         options=REGION_OPTIONS,
                         value = unique_region[0] if len(unique_region) > 0 else None,
                         style={"width": "180px", "fontSize": "13px"},
                     ),
                 ]),
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
                html.Div([
                    section_label("Transfer Window (minutes)"),
                        dcc.Slider(
                            id="sim-window-hypo",
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
                })
            ], style={"display": "none", "padding": "20px", "background": C["accent_soft"], "borderRadius": "8px", "marginBottom": "20px"}),
           
            
            # ── Output row (All three columns inside ONE flex container) ──\
            html.Div(id="simulation-output-wrapper", style={"marginTop": "20px"}),
                ] # Closes card() children list
                ), # Closes card() component
            ], style={
                "background": C["bg"],
                "minHeight": "100vh",
                "padding": "36px 48px",
                "fontFamily": FONT_SANS,
                "maxWidth": "1100px",
                "margin": "0 auto",
            }),


# ── Callback ───────────────────────────────────
@callback(
    Output("compare-input-row", "style"),
    Input("compare-toggle", "value"),
)
def toggle_compare_inputs(toggle_value):
    if "on" in toggle_value:
        return {"display": "block", "padding": "20px", "background": C["accent_soft"], "borderRadius": "8px", "marginBottom": "20px"}
    return {"display": "none"}
@callback(
    Output("simulation-output-wrapper", "children"),
    Input("sim-submit", "n_clicks"),
    State("compare-toggle", "value"),
    # Scenario A States
    State("sim-patron", "value"), State("sim-spec", "value"), 
    State("sim-region", "value"), State("sim-window-bench", "value"),
    # Scenario B States
    State("sim-patron-B", "value"), State("sim-spec-B", "value"), 
    State("sim-region-B", "value"), State("sim-window-hypo", "value"),
    prevent_initial_call=True,
)




def update_simulation(n_clicks,compare_on, p_a, s_a, r_a, b_a, p_b, s_b, r_b, h_a):
     #creating elbow plot
    df_welfare_filtered = df_welfare[df_welfare['spec'] == s_a]
    elbow_fig = go.Figure()
    for patron in unique_patron:
            p_data = df_welfare_filtered[df_welfare_filtered['patron'] == patron]
            elbow_fig.add_trace(go.Scatter(
                x=p_data['window_mins'],
                y=p_data['wrongly_split_pct'],
                name=patron,
                mode='lines+markers',
                line=dict(width=3),
                marker=dict(size=6)
            ))

    elbow_fig.update_layout(
            title="Wrongly Split % by Transfer Window",
            xaxis_title="Window (mins)",
            yaxis_title="Wrongly Split (%)",
            font=dict(family=FONT_SANS, size=11),
            margin=dict(l=40, r=20, t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True, 
                gridcolor=C["border_light"], 
                gridwidth=1,
                dtick=5 
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor=C["border_light"], 
                gridwidth=1
            ),
            legend=dict(orientation="h", yanchor="bottom", y=0.9, xanchor="right", x=1),
            hovermode="x unified"
        )
    def render_analysis(patron, spec, region, bench, title_label):
        # --- 1. Initialize variables with defaults ---
        fig_pie = go.Figure()
        fig_pie_2 = go.Figure()
        region_fig = go.Figure()
        char_img = ""
        description_text = ""

        # Basic safety check
        if not patron or not spec:
            return fig_pie, char_img, description_text

        # --- 2. Image Logic ---
        CHAR_MAP = {
            "Student": "/assets/standup_stacey.png",
            "Adult": "/assets/movein_martin.png",
            "Senior Citizen": "/assets/giveway_glenda.png",
            "Overall": "/assets/mrt_picture.png" 
        }
        img_path = CHAR_MAP.get(patron, CHAR_MAP["Overall"])
        char_img = html.Img(src=img_path, style={"width": "150px", "height": "180px", "objectFit": "contain"})

        # --- 3. Description Logic ---
        MODEL_DESCRIPTIONS = df_spec_info.set_index('spec')['description'].to_dict()
        description_text = MODEL_DESCRIPTIONS.get(spec, "No description available.")

        # --- 4. Chart Logic (Where 'fig' is defined) ---
        #filtered_df = df[(df['patron'] == patron) & (df['spec'] == spec)]
        #if bench > 45:
        #    pie_df = filtered_df[(filtered_df['window_to'] <= bench) & (filtered_df['window_from'] >= 45)]
        #    total_benefit = pie_df['marginal_cost_n'].sum()
        #    total_cost = pie_df['marginal_benefit_n'].sum()
        #else:
        #    pie_df = filtered_df[(filtered_df['window_to'] >= bench) & (filtered_df['window_from'] <= 45)]
        #    total_benefit = pie_df['marginal_benefit_n'].sum()
        #    total_cost = pie_df['marginal_cost_n'].sum()
        filtered_df = get_marginal_at_45(patron, spec,bench)
        total_benefit = filtered_df['marginal_benefit_n']
        total_cost = filtered_df['marginal_cost_n']

        if (total_benefit != 0) or (total_cost != 0):
            #create pie chart
            if patron == "Overall":
                seniors_benefit = get_marginal_at_45('Senior Citizen', spec, bench)['marginal_benefit_n']
                seniors_cost = get_marginal_at_45('Senior Citizen', spec, bench)['marginal_cost_n']
                adults_benefit = get_marginal_at_45('Adult', spec, bench)['marginal_benefit_n']
                adults_cost = get_marginal_at_45('Adult', spec, bench)['marginal_cost_n']
                students_benefit = get_marginal_at_45('Student', spec, bench)['marginal_benefit_n']
                students_cost = get_marginal_at_45('Student', spec, bench)['marginal_cost_n']
                overall_benefit = total_benefit
                overall_cost = total_cost
                if total_benefit != 0:
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['Student', 'Adult','Senior'],
                        values=[abs(students_benefit), abs(adults_benefit), abs(seniors_benefit)],
                        hole=.3, 
                        marker_colors=[C["accent"], C["accent_mid"]],
                        textinfo='label+percent',
                        insidetextorientation='radial'
                    )])
                else:
                    fig_pie.add_annotation(text="No commuters correctly classified", showarrow=False, font_size=12)

                if total_cost != 0:
                    fig_pie_2 = go.Figure(data=[go.Pie(
                        labels=['Student', 'Adult','Senior'],
                        values=[abs(students_cost), abs(adults_cost), abs(seniors_cost)],
                        hole=.3, 
                        marker_colors=[C["accent"], C["accent_mid"]],
                        textinfo='label+percent',
                        insidetextorientation='radial'
                    )])
                else:
                    fig_pie_2.add_annotation(text="No commuters wrongly classified", showarrow=False, font_size=12)

            else:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Correctly Classified'],
                    values=[abs(total_benefit)],
                    hole=.3, 
                    marker_colors=[C["accent"], C["accent_mid"]],
                    textinfo='label+percent',
                    insidetextorientation='radial'
                )])

                fig_pie_2 = go.Figure(data=[go.Pie(
                    labels=['Wrongly Classified'],
                    values=[abs(total_cost)],
                    hole=.3, 
                    marker_colors=[C["accent"], C["accent_mid"]],
                    textinfo='label+percent',
                    insidetextorientation='radial'
                )])

            fig_pie.update_layout(
                height=240,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family=FONT_SANS)
            )
            fig_pie_2.update_layout(
                height=240,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family=FONT_SANS)
            )
        else:
            fig_pie = go.Figure()
            fig_pie.add_annotation(text="No data for this range", showarrow=False, font_size=12)
            fig_pie.update_layout(
                height=240, 
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), # Hide axis lines
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            fig_pie_2 = go.Figure()
            fig_pie_2.add_annotation(text="No data for this range", showarrow=False, font_size=12)
            fig_pie_2.update_layout(
                height=240, 
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        
        if patron == 'Overall' and ((total_benefit != 0) or (total_cost != 0)):
                stats_layout = html.Div([
                    stat_card("Seniors", seniors_benefit),
                    stat_card("Adults", adults_benefit),
                    stat_card("Students", students_benefit),
                    stat_card("Total", overall_benefit, color=C["accent"])
                ], style={"display": "flex", "gap": "12px", "marginTop": "16px"})

                stats_layout_2 = html.Div([
                    stat_card("Seniors", seniors_cost),
                    stat_card("Adults", adults_cost),
                    stat_card("Students", students_cost),
                    stat_card("Total", overall_cost, color=C["accent"])
                ], style={"display": "flex", "gap": "12px", "marginTop": "16px"})
        else:
                stats_layout = html.Div([
                    stat_card(patron, total_benefit)
                ], style={"display": "flex", "gap": "12px", "marginTop": "16px"})

                stats_layout_2 = html.Div([
                    stat_card(patron, total_cost)
                ], style={"display": "flex", "gap": "12px", "marginTop": "16px"})



        # regional analysis
        df_region_filtered = df_region[(df_region['spec'] == spec) & (df_region['window_mins'] == bench)]
        if patron != 'Overall':
            df_region_filtered = df_region_filtered[df_region_filtered['patron'] == patron]
        if region != "All regions":
            df_region_filtered = df_region_filtered[df_region_filtered['region_value']==region]
        wrongly_split = df_region_filtered['wrongly_split_n'].sum()
        wrongly_merged = df_region_filtered['wrongly_merged_n'].sum()
        region_fig = go.Figure(data=[
            go.Bar(
                name='Wrongly Split',
                x=['Wrongly Split'],
                y=[wrongly_split],
                text=[f"<b>{wrongly_split:,.0f}</b>"], 
                textposition='auto',
                marker_color="#2563eb"  
            ),
            go.Bar(
                name='Wrongly Merged',
                x=['Wrongly Merged'],
                y=[wrongly_merged],
                text=[f"<b>{wrongly_merged:,.0f}</b>"],
                textposition='auto',
                marker_color="#93c5fd"  
            )
        ])

        region_fig.update_layout(
            barmode='group', 
            title="Analysis of Classification Errors",
            font=dict(family=FONT_SANS, size=12),
            margin=dict(l=40, r=20, t=40, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=0.95, xanchor="right", x=1)
        )

       


        # Creating text for analysis
        base_desc = MODEL_DESCRIPTIONS.get(spec, "No description available.")
        description_text = html.Div([
            # Main Description from CSV
            html.P(base_desc, style={"marginBottom": "12px", "fontWeight": "500"}),
            
            # Add dynamic "Policy Summary" text
            html.Div([
                html.P([
                    html.B("Impacted Commuters: "), 
                    f"{total_benefit + total_cost:,.0f} individuals"
                ]),

                html.P([
                    f"By looking at the analysis, changing the transfer window from 45 minutes to {bench} minutes will result in {total_benefit:,.0f} change in correctly classified commuters and {total_cost:,.0f} change in wrongly classified commuters."
                ])
            ], style={
                "fontSize": "12px", 
                "padding": "10px", 
                "background": C["accent_soft"], 
                "borderRadius": "6px",
                "borderLeft": f"4px solid {C['accent']}"
            })
        ])

        return html.Div([
            html.H3(f"Scenario {title_label}", style={
                "textAlign": "center", "color": C["accent"], "fontSize": "18px", "marginBottom": "20px"
            }),
            
            # Section 1: Correctly Merged
            section_label("Correctly Merged Impact"),
            dcc.Graph(figure=fig_pie, config={"displayModeBar": False}),
            stats_layout,
            
            html.Hr(style={"margin": "25px 0", "borderTop": f"1px solid {C['border']}"}),
            
            # Section 2: Wrongly Merged
            section_label("Wrongly Merged Impact"),
            dcc.Graph(figure=fig_pie_2, config={"displayModeBar": False}),
            stats_layout_2,

            html.Hr(style={"margin": "25px 0", "borderTop": f"1px solid {C['border']}"}),
            
            # Section 3: Regional Error Analysis
            section_label("Regional Error Distribution"),
            dcc.Graph(figure=region_fig, config={"displayModeBar": False}),

            # Section 4: Character Profile & Text
            html.Div([
                html.Div(char_img, style={"flex": "0 0 150px"}),
                html.Div(description_text, style={"flex": "1", "marginLeft": "15px"})
            ], style={"display": "flex", "alignItems": "flex-start", "marginTop": "20px"}),




        ], style={
            "flex": "1", 
            "padding": "24px", 
            "background": "white", 
            "borderRadius": "12px", 
            "border": f"1px solid {C['border']}",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"
        })

    b_a = int(b_a)
    if "on" in compare_on:
        h_a = int(h_a)
        # Side-by-side view
        output_view = html.Div([
            render_analysis(p_a, s_a, r_a, b_a, "A"),
            render_analysis(p_b, s_b, r_b, h_a, "B")
        ], style={"display": "flex", "gap": "20px"})
    else:
        # Single view
        output_view = render_analysis(p_a, s_a, r_a, b_a, "Analysis")
    #return fig_pie, stats_layout, char_img, fig_pie_2, stats_layout_2,region_fig, description_text
    return html.Div([output_view,
                     html.Div([
                        html.Div([
                            dcc.Graph(figure=elbow_fig, config={"displayModeBar": False})
                        ], style={"flex": "0 0 60%", "paddingRight": "20px"}),
                        html.Div([
                            html.H4("Analysis of Classification Errors", 
                                    style={"color": C["accent"], "fontSize": "16px", "marginBottom": "12px"}),
                            html.P([
                                "This elbow plot illustrates the trade-off between transfer window duration and classification accuracy. ",
                                "The ", html.B("Wrongly Split %"), " represent commuters whose single journey is incorrectly identified as two separate trips."
                            ], style={"fontSize": "13px", "lineHeight": "1.6", "color": C["secondary"]}),
                            
                            html.P([
                                "As the window increases, we observe a diminishing rate of return in error reduction. ",
                                f"For the current ({s_a}) model, the steepest drop occurs before the 45-minute mark, suggesting that extending the window beyond this point yields marginal improvements for most patron groups."
                            ], style={"fontSize": "13px", "lineHeight": "1.6", "color": C["secondary"], "marginTop": "10px"}),

                            html.P([
                                "Analysing the elbow plot, most of the patron groups experience the sharpest change at the 25 minute window", html.B(" except for the elderly.")," For the elderly, the optimal window would be at ",
                                html.B("30 Minutes "), " which is still well below the current window of 45 minutes. This suggests that the existing transfer window is sufficiently forgiving and you might consider ",
                                html.B("decreasing "), "the transfer window."
                                ], style={"fontSize": "13px", "lineHeight": "1.6", "color": C["secondary"], "marginTop": "10px"}),

                        ], style={"flex": "1", "padding": "10px", "borderLeft": f"1px solid {C['border']}"})
                    ], style={"display": "flex", "alignItems": "flex-start", "marginTop": "20px"})
                    ])

