# temporary based on what claude tells me to include; for compatibility between frontend and backend
# feel free to remove/edit/change etc 

"""
callbacks/predictions.py — Backend Integration Layer
======================================================
Steps to integrate ML model:
  1. Add trained model file to the models/ folder (e.g., models/my_model.pkl)
  2. Load it below in the LOAD MODEL section
  3. Fill in the predict() callback with your logic
  4. Uncomment the import in app.py:
       from callbacks import predictions

This callback listens for a button click in the UI,
reads the user's input, runs it through your model,
and writes the result back to the frontend.
"""

from dash import Input, Output, State, callback
# import joblib            # ← Uncomment for sklearn models
# import torch             # ← Uncomment for PyTorch models
# import tensorflow as tf  # ← Uncomment for TensorFlow models
import json


# ─────────────────────────────────────────────
# LOAD MODEL (runs once at startup)
# ─────────────────────────────────────────────
# model = joblib.load("models/your_model.pkl")     # sklearn example
# model = torch.load("models/your_model.pt")       # PyTorch example
# model = tf.keras.models.load_model("models/...")  # TensorFlow example


# ─────────────────────────────────────────────
# PREDICTION CALLBACK
# ─────────────────────────────────────────────
@callback(
    Output("model-output", "children"),
    Output("output-graph",  "children"),
    Input("run-btn",        "n_clicks"),
    State("user-input",     "value"),
    State("upload-data",    "contents"),
    prevent_initial_call=True
)
def run_prediction(n_clicks, user_input, file_contents):

    if not user_input and not file_contents:
        from dash import html
        return html.P("Please provide input before running.", style={"color": "#888"}), None

    # ── YOUR MODEL LOGIC GOES HERE ────────────────────
    #
    # Example (replace with your real code):
    #
    #   processed = preprocess(user_input)
    #   prediction = model.predict([processed])[0]
    #   confidence = model.predict_proba([processed]).max()
    #
    # ─────────────────────────────────────────────────

    # ── PLACEHOLDER RESPONSE (delete when real model is wired up) ──
    from dash import html
    import plotly.graph_objects as go
    from dash import dcc

    placeholder_result = f"Received input: {str(user_input)[:100]}..."

    output_display = html.Div([
        html.P("✅ Model ran successfully (placeholder)", style={
            "color": "#00FFB2", "fontFamily": "Space Mono", "fontWeight": "700"
        }),
        html.P(placeholder_result, style={
            "color": "#aaa", "fontFamily": "DM Sans", "fontSize": "0.9rem"
        }),
        html.Hr(style={"borderColor": "#222"}),
        html.P("Replace this with your model's actual output.",
               style={"color": "#555", "fontFamily": "DM Sans", "fontSize": "0.8rem"})
    ])

    fig = go.Figure(go.Bar(
        x=["Class A", "Class B", "Class C"],
        y=[0.6, 0.3, 0.1],
        marker_color=["#00FFB2", "#00cc8e", "#009966"]
    ))
    fig.update_layout(
        title="Prediction Confidence (Placeholder)",
        paper_bgcolor="#111", plot_bgcolor="#111",
        font=dict(color="#aaa", family="DM Sans"),
        margin=dict(t=40, b=20, l=20, r=20)
    )
    graph_display = dcc.Graph(figure=fig, style={"height": "250px"})

    return output_display, graph_display
