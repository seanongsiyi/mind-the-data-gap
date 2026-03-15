import dash
from dash import html

dash.register_page(__name__,path="/page-2", name = "Analysis Page II")

layout = html.Div([
    html.H1("This is Page 2"),
    html.P("Welcome to the side page content.")
])