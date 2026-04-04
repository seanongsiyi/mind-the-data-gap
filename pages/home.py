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
    "warning":     "#d97706",
    "warning_soft":"#fffbeb",
    "success":     "#0e9f6e",
    "success_soft":"#f0fdf4",
    "danger":      "#e02424",
    "danger_soft": "#fff5f5",
}

FONT = "'Inter', 'Helvetica Neue', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Mono', monospace"


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


def rule_badge(text, color, bg):
    return html.Span(text, style={
        "fontSize":      "9px",
        "fontWeight":    "600",
        "letterSpacing": "0.06em",
        "textTransform": "uppercase",
        "color":         color,
        "background":    bg,
        "padding":       "2px 7px",
        "borderRadius":  "4px",
        "fontFamily":    FONT_MONO,
        "whiteSpace":    "nowrap",
        "flexShrink":    "0",
    })


def rule_row(number, text, badge_text, badge_color, badge_bg, note=None):
    row_children = [
        html.Div([
            html.Span(f"{number:02d}", style={
                "fontSize":    "11px",
                "fontWeight":  "700",
                "color":       C["muted"],
                "fontFamily":  FONT_MONO,
                "marginRight": "12px",
                "flexShrink":  "0",
            }),
            html.Span(text, style={
                "fontSize":   "13px",
                "color":      C["secondary"],
                "fontFamily": FONT,
                "lineHeight": "1.5",
                "flex":       "1",
            }),
        ], style={"display": "flex", "alignItems": "flex-start", "flex": "1"}),
        rule_badge(badge_text, badge_color, badge_bg),
    ]

    rows = [html.Div(row_children, style={
        "display":        "flex",
        "alignItems":     "center",
        "gap":            "12px",
        "justifyContent": "space-between",
    })]

    if note:
        rows.append(html.Div([
            html.Span("↳ ", style={"color": C["muted"], "fontFamily": FONT_MONO}),
            html.Span(note, style={
                "fontSize":   "12px",
                "color":      C["muted"],
                "fontFamily": FONT,
                "fontStyle":  "italic",
                "lineHeight": "1.5",
            }),
        ], style={
            "marginTop":   "6px",
            "marginLeft":  "23px",
            "paddingLeft": "12px",
            "borderLeft":  f"2px solid {C['border']}",
        }))

    return html.Div(rows, style={
        "padding":      "12px 14px",
        "borderRadius": "6px",
        "border":       f"1px solid {C['border']}",
        "background":   C["bg"],
        "marginBottom": "8px",
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
                "fontSize":   "36px",
                "fontWeight": "700",
                "color":      C["text"],
                "fontFamily": FONT,
                "margin":     "16px 0 12px",
                "lineHeight": "1.2",
            }),
            html.P(
                "Current transfer rules leave some commuters at a disadvantage. "
                "This project investigates how the 45-minute bus transfer window can be made more equitable and efficient.",
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
            html.Div("Current Transfer Window", style={
                "fontSize":      "11px",
                "fontWeight":    "600",
                "letterSpacing": "0.08em",
                "textTransform": "uppercase",
                "color":         C["secondary"],
                "fontFamily":    FONT_MONO,
                "marginBottom":  "12px",
            }),
            html.Div([
                html.Div([
                    html.Div("45 min", style={
                        "fontSize":   "22px",
                        "fontWeight": "700",
                        "color":      C["accent"],
                        "fontFamily": FONT_MONO,
                    }),
                    html.Div("Train → Bus / Bus → Bus", style={
                        "fontSize":  "12px",
                        "color":     C["secondary"],
                        "fontFamily": FONT,
                        "marginTop": "2px",
                    }),
                ], style={
                    "padding":      "14px 18px",
                    "background":   C["accent_soft"],
                    "borderRadius": "8px",
                    "borderLeft":   f"3px solid {C['accent']}",
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
        "display":      "flex",
        "gap":          "40px",
        "alignItems":   "flex-start",
        "flexWrap":     "wrap",
        "marginBottom": "32px",
    }),

    # ── Transfer Rules ────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            section_tag("Transfer Rules"),
            html.H2("Journey & Transfer Rules", style={
                "fontSize":   "18px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT,
                "margin":     "12px 0 16px",
            }),
        ]),
        rule_row(
            1,
            "Maximum duration between first and last boarding within a journey is 2 hours. "
            "Card is rejected at fare gate if exceeded; $2 admin charge to exit at Passenger Service Centre. "
            "Applies to all card types including Concession cardholders.",
            "2 HR CAP",
            C["danger"], C["danger_soft"],
            note="Unmanned LRT stations: use intercom to contact Operations Control Centre for assistance.",
        ),
        rule_row(
            2,
            "A maximum of 5 transfers can be made within a single journey.",
            "MAX 5 XFERS",
            C["warning"], C["warning_soft"],
        ),
        rule_row(
            3,
            "Multiple train transfers are allowed with no additional boarding charges.",
            "TRAIN FREE",
            C["success"], C["success_soft"],
        ),
        rule_row(
            4,
            "Maximum 45 minutes before being charged for transfers between a train station and a bus, "
            "or between different bus services.",
            "45 MIN · BUS",
            C["warning"], C["warning_soft"],
        ),
        rule_row(
            5,
            "The current bus service must not be the same number as the immediately preceding bus service.",
            "NO SAME BUS",
            C["danger"], C["danger_soft"],
        ),
        rule_row(
            6,
            "No exit and re-entry at the same train station.",
            "NO RE-ENTRY",
            C["danger"], C["danger_soft"],
            note=(
                "Exceptions: Bukit Panjang, Newton, and Tampines MRT interchanges require tapping out "
                "and back in when transferring between lines."
            ),
        ),
    ], style={
        "background":   C["surface"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding":      "28px",
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
                "transfers. These policies leave certain demographics like the elderly "
                "in inequitable situations where reduced mobility results in higher fares.",
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "0 0 12px"},
            ),
            html.P(
                "This project evaluates, from a policy standpoint, how public transfer rules can be "
                "optimised to enhance both equity and efficiency. It assesses demographic fairness of "
                "the existing 45-minute transfer window and proposes dynamic transfer rules that vary "
                "across demographics, regions, and time-of-day. "
               ,
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "0 0 12px"},
            ),
            html.P(
                "Beyond the core analysis, the project explores extensions including adapting transfer "
                "windows to real-time conditions such as service disruptions or miscellaneous delays. "
                ,
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
                    "Assess demographic fairness of the existing 45-minute bus transfer window.",
                    "Propose dynamic transfer rules varying by commuter type, region, and time-of-day.",
                    "Explore real-time adaptations for service disruptions and miscellaneous delays.",
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

    # ── Definitions ─────────────────────────────────────────────────────────────

    html.Div([
        html.Div([
            section_tag("Definitions"),
            html.Div([
                html.B("Wrongly Split Transfers:"),
                html.P(
                "Journeys that are a single journey but split into 2 due to transfer window",
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "12px 0 12px"},
                ),
                html.B("Wrongly Merged Journeys:"),
                html.P(
                "Journeys that are separate journeys but merged into 1 under the transfer window",
                style={"fontSize": "13px", "color": C["secondary"], "fontFamily": FONT,
                       "lineHeight": "1.7", "margin": "12px 0 12px"},)

        ], style={"marginTop": "20px"})

    ], style={
        "background":   C["surface"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding":      "28px",
        "marginBottom": "28px",
    })
    ]),

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