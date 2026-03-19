import dash
from dash import html

dash.register_page(__name__,path="/page-3", name = "Delay Simulation")

layout = html.Div([
    html.H1("Delay Simulatioin"),
    html.P("Delay Conditions:")
])