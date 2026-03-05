import dash
from dash import html

dash.register_page(__name__,path="/page-1", name = "Analysis Page")

layout = html.Div([
    html.H1("This is Page 1"),
    html.P("Welcome to the side page content.")
])