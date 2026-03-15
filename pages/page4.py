import dash
from dash import html

dash.register_page(__name__,path="/page-4", name = "Analysis Page IV")

layout = html.Div([
    html.H1("This is Page 4"),
    html.P("Welcome to the side page content.")
])