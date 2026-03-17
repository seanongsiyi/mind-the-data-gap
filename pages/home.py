import dash
from dash import html

dash.register_page(__name__, path="/", name="Home")

C = {
    "bg":          "#f8f9fb",
    "surface":     "#ffffff",
    "border":      "#e2e5ec",
    "accent":      "#1a56db",
    "accent_soft": "#eff4ff",
    "accent_mid":  "#76a9fa",
    "text":        "#111827",
    "secondary":   "#6b7280",
    "muted":       "#9ca3af",
}

FONT = "'Inter', 'Helvetica Neue', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Mono', monospace"

def stat_card(number, label):
    return html.Div([
        html.Div(number, style={
            "fontSize":   "28px",
            "fontWeight": "700",
            "color":      C["accent"],
            "fontFamily": FONT_MONO,
            "lineHeight": "1",
        }),
        html.Div(label, style={
            "fontSize":   "12px",
            "color":      C["secondary"],
            "marginTop":  "6px",
            "fontFamily": FONT,
            "lineHeight": "1.4",
        }),
    ], style={
        "background":   C["surface"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding":      "20px 24px",
        "flex":         "1",
        "minWidth":     "140px",
    })


def section_tag(text):
    return html.Span(text, style={
        "fontSize":      "10px",
        "fontWeight":    "600",
        "letterSpacing": "0.1em",
        "textTransform": "uppercase",
        "color":         C["accent"],
        "background":    C["accent_soft"],
        "padding":       "3px 8px",
        "borderRadius":  "4px",
        "fontFamily":    FONT_MONO,
    })


def team_pill(name, matric):
    return html.Div([
        html.Span(name, style={
            "fontSize":   "13px",
            "fontWeight": "500",
            "color":      C["text"],
            "fontFamily": FONT,
        }),
        html.Span(matric, style={
            "fontSize":   "11px",
            "color":      C["muted"],
            "fontFamily": FONT_MONO,
            "marginLeft": "6px",
        }),
    ], style={
        "padding":      "6px 12px",
        "background":   C["bg"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "6px",
        "display":      "inline-flex",
        "alignItems":   "center",
        "margin":       "4px",
    })


layout = html.Div([

    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap",
    ),

    # ── Hero ──────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            section_tag("DSE3101 · NUS"),
            html.H1([
                "Evaluating Public",
                html.Br(),
                "Transfer Rules in",
                html.Br(),
                html.Span("Singapore", style={"color": C["accent"]}),
            ], style={
                "fontSize":    "36px",
                "fontWeight":  "700",
                "color":       C["text"],
                "fontFamily":  FONT,
                "margin":      "16px 0 12px",
                "lineHeight":  "1.2",
            }),
            html.P(
                "Current transfer rules leave elderly and differently-abled commuters at a disadvantage. "
                "This project investigates how transfer windows can be made more equitable and efficient.",
                style={
                    "fontSize":   "14px",
                    "color":      C["secondary"],
                    "fontFamily": FONT,
                    "lineHeight": "1.7",
                    "maxWidth":   "480px",
                    "margin":     "0",
                },
            ),
        ], style={"flex": "1"}),

        # Transfer window quick-facts
        html.Div([
            html.Div("Current Transfer Windows", style={
                "fontSize":    "11px",
                "fontWeight":  "600",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color":       C["secondary"],
                "fontFamily":  FONT_MONO,
                "marginBottom": "12px",
            }),
            html.Div([
                html.Div([
                    html.Div("45 min", style={
                        "fontSize": "22px", "fontWeight": "700",
                        "color": C["accent"], "fontFamily": FONT_MONO,
                    }),
                    html.Div("Train → Bus / Bus → Bus", style={
                        "fontSize": "12px", "color": C["secondary"],
                        "fontFamily": FONT, "marginTop": "2px",
                    }),
                ], style={
                    "padding": "14px 18px",
                    "background": C["accent_soft"],
                    "borderRadius": "8px",
                    "marginBottom": "8px",
                    "borderLeft": f"3px solid {C['accent']}",
                }),
                html.Div([
                    html.Div("15 min", style={
                        "fontSize": "22px", "fontWeight": "700",
                        "color": "#0e9f6e", "fontFamily": FONT_MONO,
                    }),
                    html.Div("Train → Train", style={
                        "fontSize": "12px", "color": C["secondary"],
                        "fontFamily": FONT, "marginTop": "2px",
                    }),
                ], style={
                    "padding": "14px 18px",
                    "background": "#f0fdf4",
                    "borderRadius": "8px",
                    "borderLeft": "3px solid #0e9f6e",
                }),
            ]),
        ], style={
            "background":   C["surface"],
            "border":       f"1px solid {C['border']}",
            "borderRadius": "12px",
            "padding":      "24px",
            "minWidth":     "260px",
        }),

    ], style={
        "display":     "flex",
        "gap":         "40px",
        "alignItems":  "flex-start",
        "flexWrap":    "wrap",
        "marginBottom": "32px",
    }),

    # ── Stats row ─────────────────────────────────────────────────────────────
    html.Div([
        stat_card("45 min", "Current max transfer\nwindow for bus transfers"),
        stat_card("2 tiers", "Transfer rules across\ndifferent mode pairs"),
        stat_card("9", "Team members across\nfront and back end"),
        stat_card("Dynamic", "Proposed rule framework\nby demographic & region"),
    ], style={
        "display":      "flex",
        "gap":          "12px",
        "flexWrap":     "wrap",
        "marginBottom": "28px",
    }),

    # ── Project Overview ──────────────────────────────────────────────────────
    html.Div([
        html.Div([
            section_tag("Project Overview"),
            html.H2("About This Study", style={
                "fontSize":   "18px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT,
                "margin":     "12px 0 12px",
            }),
            html.P(
                "Current public transfer rules enforce a 45-minute window for train-bus and bus-bus "
                "transfers, and a 15-minute window for train-train transfers. These policies leave "
                "certain demographics — including the elderly and differently-abled — in inequitable "
                "situations where reduced mobility results in higher fares.",
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "0 0 12px"},
            ),
            html.P(
                "This project evaluates, from a policy standpoint, how public transfer rules can be "
                "optimised to enhance both equity and efficiency. It assesses demographic fairness of "
                "existing policies and proposes dynamic transfer rules that vary across demographics, "
                "regions, and time-of-day. A comprehensive cost-benefit analysis informs policy reforms "
                "that better balance commuter welfare with LTA's operational sustainability.",
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "0 0 12px"},
            ),
            html.P(
                "Beyond the core analysis, the project explores extensions including adapting transfer "
                "windows to real-time conditions such as service disruptions or weather-related delays, "
                "and a regional analysis tool that handles both emerging and declining neighbourhoods.",
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "0"},
            ),
        ], style={
            "background":   C["surface"],
            "border":       f"1px solid {C['border']}",
            "borderRadius": "10px",
            "padding":      "28px",
            "flex":         "3",
        }),

        # Key objectives
        html.Div([
            section_tag("Key Objectives"),
            html.H2("What We Aim To Do", style={
                "fontSize":   "18px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT,
                "margin":     "12px 0 16px",
            }),
            *[
                html.Div([
                    html.Div(str(i + 1), style={
                        "width":          "22px",
                        "height":         "22px",
                        "borderRadius":   "50%",
                        "background":     C["accent_soft"],
                        "color":          C["accent"],
                        "fontSize":       "11px",
                        "fontWeight":     "700",
                        "fontFamily":     FONT_MONO,
                        "display":        "flex",
                        "alignItems":     "center",
                        "justifyContent": "center",
                        "flexShrink":     "0",
                        "marginTop":      "1px",
                    }),
                    html.P(obj, style={
                        "fontSize":   "13px",
                        "color":      C["secondary"],
                        "fontFamily": FONT,
                        "lineHeight": "1.5",
                        "margin":     "0",
                    }),
                ], style={"display": "flex", "gap": "12px", "alignItems": "flex-start",
                          "marginBottom": "14px"})
                for i, obj in enumerate([
                    "Assess demographic fairness of existing 45-min and 15-min transfer windows.",
                    "Propose dynamic transfer rules varying by commuter type, region, and time-of-day.",
                    "Conduct cost-benefit analysis balancing commuter welfare and LTA sustainability.",
                    "Explore real-time adaptations for service disruptions and weather delays.",
                    "Develop a regional analysis tool for emerging and declining neighbourhoods.",
                ])
            ],
        ], style={
            "background":   C["surface"],
            "border":       f"1px solid {C['border']}",
            "borderRadius": "10px",
            "padding":      "28px",
            "flex":         "2",
        }),

    ], style={
        "display":      "flex",
        "gap":          "16px",
        "flexWrap":     "wrap",
        "marginBottom": "28px",
    }),

    # ── Team ──────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Div([
                section_tag("Front End"),
                html.Div([
                    team_pill("Christopher Goh", "A0272921E"),
                    team_pill("Keira Low", "A0283298M"),
                    team_pill("Neoh Jing Herng", "A0272508A"),
                    team_pill("Ryan Chong", "A0272778L"),
                    team_pill("Sean Ong", "A0271830J"),
                ], style={"marginTop": "10px"}),
            ], style={"marginBottom": "20px"}),
            html.Div([
                section_tag("Back End"),
                html.Div([
                    team_pill("Calista Wong", "A0283269R"),
                    team_pill("Jeslyn Tan", "A0282642A"),
                    team_pill("Koh Lin Kiat", "A0273180J"),
                    team_pill("Tan Shao Gjin", "A0281362H"),
                ], style={"marginTop": "10px"}),
            ]),
        ]),
    ], style={
        "background":   C["surface"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding":      "28px",
        "marginBottom": "28px",
    }),

], style={
    "background":  C["bg"],
    "minHeight":   "100vh",
    "padding":     "36px 48px",
    "fontFamily":  FONT,
    "color":       C["text"],
    "maxWidth":    "1100px",
    "margin":      "0 auto",
})
