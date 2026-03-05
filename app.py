import dash
from dash import Dash, html, dcc, Input, Output, callback

app = Dash(__name__, use_pages = True)
app.layout = html.Div([
    dcc.Location(id="url", refresh = "callback-nav"),
    html.H1("My MIND THE DATA GAP Dashboard", style = {'textAlign': 'centre'}),
    dcc.Tabs(id="nav-tabs", value ="/", children = [
        dcc.Tab(label=page["name"],value=page["relative_path"])
        for page in dash.page_registry.values()
    ]),
    dash.page_container
])

#callback to sync URL with selected tab
@callback(
    Output("url","pathname"),
    Input("nav-tabs","value")
)
def update_url(tab_value):
    return tab_value
@callback(
    Output("nav-tabs","value"),
    Input("url","pathname")
)
def update_active_tab(pathname):
    return pathname

if __name__ == "__main__":
    app.run(debug=True)