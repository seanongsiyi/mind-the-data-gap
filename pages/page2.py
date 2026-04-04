import dash
from dash import dcc, html, Input, Output, callback, State, no_update
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import json
from pathlib import Path

# ── Load delay simulation data ────────────────────────────────────────────────

# ── Load / prepare delay simulation data ─────────────────────────────────────

INPUT_PATH = Path("data/final_delays.csv")
OUTPUT_PATH = Path("data/final_cleaned_delay_sim_results.csv")


def hour_to_bucket(hour):
    if pd.isna(hour):
        return None

    try:
        hour = int(hour)
    except (ValueError, TypeError):
        return None

    if 6 <= hour <= 8:
        return "Morning Peak (6am–9am)"
    elif 9 <= hour <= 16:
        return "Off-Peak (9am–5pm)"
    elif 17 <= hour <= 19:
        return "Evening Peak (5pm–8pm)"
    elif 20 <= hour <= 23:
        return "Night (8pm–12am)"
    else:
        return None


def prepare_delay_sim_csv():
    if not INPUT_PATH.exists():
        print(f"Raw CSV not found: {INPUT_PATH}")
        return

    df = pd.read_csv(INPUT_PATH, low_memory=False)

    df["time_bucket"] = None

    mask = df["breakdown_type"] == "hour_x_dest_region"
    df.loc[mask, "time_bucket"] = df.loc[mask, "breakdown_value"].apply(hour_to_bucket)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Prepared cleaned CSV: {OUTPUT_PATH}")


prepare_delay_sim_csv()

DELAY_SIM_CSV_PATH = OUTPUT_PATH
if DELAY_SIM_CSV_PATH.exists():
    DELAY_SIM_DF = pd.read_csv(DELAY_SIM_CSV_PATH, low_memory=False)
else:
    DELAY_SIM_DF = None


dash.register_page(__name__, path="/page-4", name="Delay Simulator")

# ── Design tokens ───────────────────────────

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

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_SANS, color=C["text"], size=12),
    margin=dict(l=48, r=24, t=24, b=48),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor=C["border"],
        borderwidth=1,
        font=dict(size=12),
    ),
)

AXIS_STYLE = dict(
    gridcolor=C["border_light"],
    linecolor=C["border"],
    zerolinecolor=C["border"],
    tickfont=dict(size=11, color=C["secondary"]),
)


# ─────────────────────────────────────────────
# PLACEHOLDER DATA
# ─────────────────────────────────────────────

PLANNING_AREAS_GEOJSON_PATH = Path("data/singapore_planning_areas.geojson")

# TODO: Replace with actual region list from backend
REGIONS = ["All Regions", "North", "North-East", "East", "West", "Central"]

# TODO: Replace with actual time-of-day options from backend
TIMES_OF_DAY = [
    "Morning Peak (6am–9am)",
    "Off-Peak (9am–5pm)",
    "Evening Peak (5pm–8pm)",
    "Night (8pm–12am)",
]


# TODO: Replace with actual delay duration options from backend
DELAY_DURATIONS = ["0 minutes", "5 minutes", "10 minutes", "15 minutes", "20 minutes"]


def load_planning_area_geojson():
    with open(PLANNING_AREAS_GEOJSON_PATH, "r") as f:
        return json.load(f)


# ── Query helper function ────────────────────────────────────────────────────
def query_delay_sim(
    delay_mins:      int,
    bus_window:      int,
    classifier_type: str,
    patron:          str = 'all',
    time_bucket: str = None,
    df:              pd.DataFrame = None
):
    """Query delay simulation results for given parameters."""
    if df is None:
        df = DELAY_SIM_DF
    
    if df is None:
        raise ValueError("Delay simulation data not loaded. Missing data/delay_sim_results.csv")

    valid_delays  = [0, 5, 10, 15, 20]
    valid_windows = list(range(30, 65, 5))
    valid_specs   = ['baseline', 'lenient', 'strict']

    if delay_mins      not in valid_delays:  raise ValueError(f"delay_mins must be one of {valid_delays}")
    if bus_window      not in valid_windows: raise ValueError(f"bus_window must be one of {valid_windows}")
    if classifier_type not in valid_specs:   raise ValueError(f"classifier_type must be one of {valid_specs}")

    sub = df[
        (df['delay_mins']      == delay_mins)  &
        (df['bus_window_mins'] == bus_window)  &
        (df['spec']            == classifier_type)
    ].copy()
    
    if time_bucket:
        sub = sub[sub["time_bucket"] == time_bucket]

    if sub.empty:
        raise ValueError("No data found for given parameters")

    if patron == 'all':
        main_row = sub[sub['breakdown_type'] == 'overall'].iloc[0]
    else:
        patron_rows = sub[sub['breakdown_type'] == 'patron']
        if patron not in patron_rows['breakdown_value'].values:
            raise ValueError(f"Patron '{patron}' not found. Available: {patron_rows['breakdown_value'].tolist()}")
        main_row = patron_rows[patron_rows['breakdown_value'] == patron].iloc[0]

    classifier_journeys = int(main_row['classifier_journeys']) if not pd.isna(main_row['classifier_journeys']) else None
    window_journeys     = int(main_row['window_journeys'])     if not pd.isna(main_row['window_journeys'])     else None
    journey_difference  = (window_journeys - classifier_journeys) if (window_journeys and classifier_journeys) else None

    # Calculate True Positives (correctly kept transfers) and True Negatives (correctly split separate journeys)
    ground_truth_transfer_n = int(main_row['ground_truth_transfer_n']) if not pd.isna(main_row['ground_truth_transfer_n']) else 0
    ground_truth_new_journey_n = int(main_row['ground_truth_new_journey_n']) if not pd.isna(main_row['ground_truth_new_journey_n']) else 0
    wrongly_split_n = int(main_row['wrongly_split_n'])
    wrongly_merged_n = int(main_row['wrongly_merged_n'])
    correctly_kept_n = ground_truth_transfer_n - wrongly_split_n
    correctly_kept_pct = (correctly_kept_n / ground_truth_transfer_n * 100) if ground_truth_transfer_n > 0 else 0.0
    correctly_split_n = ground_truth_new_journey_n - wrongly_merged_n
    correctly_split_pct = (correctly_split_n / ground_truth_new_journey_n * 100) if ground_truth_new_journey_n > 0 else 0.0

    def get_breakdown(breakdown_type, col_name):
        cols = [
            'breakdown_value', 'n_pairs', 'n_cards',
            'classifier_journeys', 'window_journeys',
            'ground_truth_transfer_n', 'ground_truth_new_journey_n',
            'wrongly_split_n', 'wrongly_merged_n',
            'wrongly_split_pct', 'wrongly_merged_pct',
            'wrongly_split_pct_all', 'wrongly_merged_pct_all',
        ]

        if 'dest_region' in sub.columns and col_name != 'dest_region':
            cols.append('dest_region')

        if 'time_bucket' in sub.columns:
            cols.append('time_bucket')
            
        return (
            sub[sub['breakdown_type'] == breakdown_type][cols]
            .rename(columns={'breakdown_value': col_name})
            .sort_values('wrongly_split_pct', ascending=False)
            .reset_index(drop=True)
        )

    return {
        'spec':                classifier_type,
        'delay_mins':          delay_mins,
        'bus_window_mins':     bus_window,
        'patron':              patron,
        'classifier_journeys': classifier_journeys,
        'window_journeys':     window_journeys,
        'journey_difference':  journey_difference,
        'correctly_kept_n':    correctly_kept_n,
        'correctly_kept_pct':  correctly_kept_pct,
        'correctly_split_n':   correctly_split_n,
        'correctly_split_pct': correctly_split_pct,
        'wrongly_split_n':     wrongly_split_n,
        'wrongly_merged_n':    wrongly_merged_n,
        'wrongly_split_pct':   float(main_row['wrongly_split_pct']),
        'wrongly_merged_pct':  float(main_row['wrongly_merged_pct']),
        'by_patron':           get_breakdown('patron',          'patron'),
        'by_dest_region':      get_breakdown('dest_region',     'dest_region'),
        'by_orig_region':      get_breakdown('orig_region',     'orig_region'),
        'by_hour':             get_breakdown('next_entry_hour', 'hour'),
        'by_hour_x_region': get_breakdown('hour_x_dest_region', 'hour'),
    }


def get_planning_area_metadata():
    sg_geojson = load_planning_area_geojson()
    rows = []

    for feature in sg_geojson["features"]:
        props = feature["properties"]
        region = props["REGION_N"].replace(" REGION", "").title()
        planning_area_raw = props["PLN_AREA_N"]
        rows.append(
            {
                "region": region,
                "planning_area_raw": planning_area_raw,
                "planning_area": planning_area_raw.title(),
            }
        )

    return pd.DataFrame(rows).drop_duplicates().sort_values("planning_area")


def get_planning_areas_for_region(region):
    """Get list of planning areas for a given region."""
    meta = get_planning_area_metadata()
    if region and region != "All Regions":
        meta = meta[meta["region"] == region]

    return ["All Planning Areas"] + meta["planning_area"].tolist()


# ── Real map data helper using simulation results ────────────────────────────
def get_real_map_data(
    region=None,
    planning_area=None,
    delay_duration=None,
    transfer_window=45,
    classifier_type="baseline",
    time_of_day=None  # Ignored for now; TODO: implement time-of-day filtering
):
    """
    Get real map data from delay simulation CSV using destination geography.
    
    This function:
    1. Filters simulation data by delay_mins, bus_window_mins, and spec
    2. Extracts destination-region (planning area) level data
    3. Joins with planning area metadata from GeoJSON
    4. Includes all planning areas; marks missing data areas with has_data=False
    5. Applies region/planning_area filters
    
    Args:
        region: Selected region filter (or "All Regions")
        planning_area: Selected planning area filter (or "All Planning Areas")
        delay_duration: String like "10 minutes" (parsed to int)
        transfer_window: int, window in minutes (default 45)
        classifier_type: "baseline", "lenient", or "strict"
        time_of_day: Currently ignored; no time filtering on map
    
    Returns:
        DataFrame with columns: region, planning_area_raw, planning_area, wrongly_split_n, wrongly_split_pct, has_data
    """
    if DELAY_SIM_DF is None:
        raise ValueError("Delay simulation data not loaded. Missing data/delay_sim_results.csv")
    
    # Parse delay_duration string to minutes (e.g., "10 minutes" -> 10)
    # Default to 0 if no delay_duration filter selected
    if delay_duration:
        try:
            delay_mins = int(delay_duration.split()[0])
        except (ValueError, IndexError):
            delay_mins = 0
    else:
        delay_mins = 0
    
    # Load planning area metadata (all areas)
    meta = get_planning_area_metadata().copy()
    
    # Filter to destination region breakdown rows with matching parameters
    df_dest_region = DELAY_SIM_DF[
        (DELAY_SIM_DF['breakdown_type'] == 'dest_region') &
        (DELAY_SIM_DF['delay_mins'] == delay_mins) &
        (DELAY_SIM_DF['bus_window_mins'] == transfer_window) &
        (DELAY_SIM_DF['spec'] == classifier_type)
    ].copy()
    
    # Rename breakdown_value to planning_area_raw
    if not df_dest_region.empty:
        df_dest_region = df_dest_region.rename(columns={'breakdown_value': 'planning_area_raw'})
        df_dest_region = df_dest_region[['planning_area_raw', 'wrongly_split_n', 'wrongly_split_pct']].copy()
        df_dest_region = df_dest_region.rename(columns={
            'wrongly_split_n': 'wrongly_split_n',
            'wrongly_split_pct': 'wrongly_split_pct'
        })
        df_dest_region['has_data'] = True
    else:
        # Empty dataframe with correct columns
        df_dest_region = pd.DataFrame(columns=['planning_area_raw', 'wrongly_split_n', 'wrongly_split_pct', 'has_data'])
    
    # Left join all planning areas with simulation data
    # This ensures all areas appear on map, with has_data=False for missing areas
    df_merged = meta[['planning_area_raw', 'planning_area', 'region']].merge(
        df_dest_region,
        on='planning_area_raw',
        how='left'
    )
    
    # Fill missing data rows with NaN for values and has_data=False
    df_merged['wrongly_split_n'] = df_merged['wrongly_split_n'].fillna(0)
    
    # For areas with 0 pairs but NaN percentage, fill percentage with 0
    df_merged.loc[(df_merged['wrongly_split_n'] == 0) & (df_merged['wrongly_split_pct'].isna()), 'wrongly_split_pct'] = 0.0
    
    df_merged['wrongly_split_pct'] = df_merged['wrongly_split_pct'].fillna(np.nan)
    
    # Mark as has_data only if wrongly_split_pct is not NaN
    df_merged['has_data'] = df_merged['has_data'].fillna(False)
    df_merged.loc[df_merged['wrongly_split_pct'].isna(), 'has_data'] = False
    
    # Apply filters
    if region and region != "All Regions":
        df_merged = df_merged[df_merged["region"] == region]
    
    if planning_area and planning_area != "All Planning Areas":
        df_merged = df_merged[
            df_merged["planning_area"].str.strip().str.lower() == planning_area.strip().lower()
            ]
    
    return df_merged[['region', 'planning_area_raw', 'planning_area', 'wrongly_split_n', 'wrongly_split_pct', 'has_data']]


# ── Figure builders ───────────────────────────────────────────────────────────

def build_map_figure(region=None, time_of_day=None, delay_duration=None, transfer_window=45, planning_area=None):
    """
    Builds the Singapore map figure using real simulation data.
    
    The map shows the percentage of genuine transfers broken (wrongly_split_pct)
    for each destination planning area, colored by a blue intensity scale.
    Uncolored areas are those with no data (grey background with "No data" on hover).
    
    Behavior:
    - If no region/planning_area selected: show full Singapore with data areas colored, no-data areas grey
    - If region/planning_area selected: grey out unselected areas, highlight selection (with separate no-data handling)
    - Time-of-day filtering: Currently ignored (TODO)
    """
    sg_geojson = load_planning_area_geojson()
    
    # Get real map data (all planning areas for reference)
    df_all = get_real_map_data(
        region=None,
        planning_area=None,
        delay_duration=delay_duration,
        transfer_window=transfer_window,
        classifier_type="baseline",
        time_of_day=time_of_day
    )
    
    # Get filtered map data (based on region/planning_area selections)
    df_selected = get_real_map_data(
        region=region if region != "All Regions" else None,
        planning_area=planning_area if planning_area != "All Planning Areas" else None,
        delay_duration=delay_duration,
        transfer_window=transfer_window,
        classifier_type="baseline",
        time_of_day=time_of_day
    )

    has_filter = (region and region != "All Regions") or (
        planning_area and planning_area != "All Planning Areas"
    )

    fig = go.Figure()

    if not has_filter:
        # No filter: show all areas, separated into data and no-data regions
        df_with_data = df_all[df_all['has_data'] == True].copy()
        df_no_data = df_all[df_all['has_data'] == False].copy()
        
        # Trace 1: Areas with data (colored by value)
        if not df_with_data.empty:
            fig = px.choropleth_mapbox(
                df_with_data,
                geojson=sg_geojson,
                locations="planning_area_raw",
                featureidkey="properties.PLN_AREA_N",
                color="wrongly_split_pct",
                labels={"wrongly_split_pct": "% of genuine transfers broken in that town"},
                color_continuous_scale=[
                    "#eaf2ff",
                    "#bfd6ff",
                    "#7faeff",
                    "#1a56db"
                ],
                mapbox_style="carto-positron",
                center={"lat": 1.3521, "lon": 103.8198},
                zoom=9.7
            )
            fig.update_layout(coloraxis_showscale=False)
            
            fig.update_traces(
                marker_line_width=0.5,
                marker_line_color="grey",
                showscale=False,
                
            )

            fig.update_traces(
                customdata=df_with_data[["planning_area", "region", "wrongly_split_n", "wrongly_split_pct"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Region: %{customdata[1]}<br>"
                    "Transfers broken: %{customdata[2]}<br>"
                    "% of transfers: %{customdata[3]:.2f}%<extra></extra>"
                ),
                marker_line_width=0.5,
                marker_line_color="grey",
            )
        
        # Trace 2: Areas without data (grey)
        if not df_no_data.empty:
            fig.add_trace(
                go.Choroplethmapbox(
                    geojson=sg_geojson,
                    locations=df_no_data["planning_area_raw"],
                    z=[1] * len(df_no_data),
                    featureidkey="properties.PLN_AREA_N",
                    colorscale=[[0, "#9ca3af"], [1, "#9ca3af"]],
                    showscale=False,
                    name = '',
                    marker_line_width=0.5,
                    marker_line_color="grey",
                    customdata=df_no_data[["planning_area", "region"]].values,
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Region: %{customdata[1]}<br>"
                        "No data<extra></extra>"
                    ),
                )
            )

    else:
    # Filter active: use a single trace
    # selected area(s) = blue, everything else = grey

        selected_areas = set(df_selected["planning_area_raw"])

        df_display = df_all.copy()
        df_display["is_selected"] = df_display["planning_area_raw"].isin(selected_areas)
        df_display["fill_value"] = df_display["is_selected"].astype(int)

        fig.add_trace(
            go.Choroplethmapbox(
                geojson=sg_geojson,
                locations=df_display["planning_area_raw"],
                z=df_display["fill_value"],
                featureidkey="properties.PLN_AREA_N",
                colorscale=[
                    [0.0, "#e5e7eb"],
                    [0.499, "#e5e7eb"],
                    [0.5, "#1a56db"],
                    [1.0, "#1a56db"],
                ],
                zmin=0,
                zmax=1,
                showscale=False,
                name = '',
                marker_line_width=0.5,
                marker_line_color="grey",
                customdata=df_display[
                    ["planning_area", "region", "wrongly_split_n", "wrongly_split_pct"]
                ].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Region: %{customdata[1]}<br>"
                    "Transfers broken: %{customdata[2]}<br>"
                    "% of transfers: %{customdata[3]:.2f}%<br>"
                ),
            )
        )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center={"lat": 1.3521, "lon": 103.8198},
            zoom=9.7,
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Arial",
            font_color="#1f2937",
            bordercolor="#d1d5db"
        )
    )
    
    return fig


def get_patron_kpi_data(delay_duration=None, transfer_window=45):
    if DELAY_SIM_DF is None:
        return pd.DataFrame()

    if delay_duration:
        try:
            delay_mins = int(delay_duration.split()[0])
        except (ValueError, IndexError):
            delay_mins = 0
    else:
        delay_mins = 0

    try:
        result = query_delay_sim(
            delay_mins=delay_mins,
            bus_window=transfer_window,
            classifier_type="baseline",
            patron="all"
        )
    except Exception:
        return pd.DataFrame()

    df_patron = result["by_patron"].copy()

    if df_patron.empty:
        return pd.DataFrame()

    rows = []
    for _, row in df_patron.iterrows():
        ground_truth_transfer_n = row["ground_truth_transfer_n"]
        ground_truth_new_journey_n = row["ground_truth_new_journey_n"]
        wrongly_split_n = row["wrongly_split_n"]
        wrongly_merged_n = row["wrongly_merged_n"]

        correctly_kept_n = ground_truth_transfer_n - wrongly_split_n
        correctly_kept_pct = (
            correctly_kept_n / ground_truth_transfer_n * 100
            if ground_truth_transfer_n > 0 else 0.0
        )

        correctly_split_n = ground_truth_new_journey_n - wrongly_merged_n
        correctly_split_pct = (
            correctly_split_n / ground_truth_new_journey_n * 100
            if ground_truth_new_journey_n > 0 else 0.0
        )

        rows.append({
            "patron": row["patron"],
            "Correctly merged": correctly_kept_n,
            "Wrongly split": row["wrongly_split_n"],
            "Correctly split": correctly_split_n,
            "Wrongly merged": row["wrongly_merged_n"],
        })

    df = pd.DataFrame(rows)

    order = ["Adult", "Senior Citizen", "Student"]
    df["patron"] = pd.Categorical(df["patron"], categories=order, ordered=True)
    df = df.sort_values("patron")

    return df


def build_patron_chart(delay_duration=None, transfer_window=45):
    """
    Builds a grouped bar chart comparing 4 KPIs across patron types.
    Each patron has 4 bars side-by-side.
    """
    df = get_patron_kpi_data(delay_duration, transfer_window)
    
    if df.empty:
        return go.Figure().add_annotation(text="No patron data available")
    
    metrics = [
        'Correctly split',
        'Wrongly split',
        'Correctly merged',
        'Wrongly merged',
    ]
    colors = ["#0ea5e9", "#dc2626", "#10b981", "#f59e0b"]
    
    fig = go.Figure()
    
    for metric, color in zip(metrics, colors):
        fig.add_trace(go.Bar(
            x=df['patron'],
            y=df[metric],
            name=metric,
            marker_color=color,
            text=[f"{int(v):,}" for v in df[metric]],
            textposition="outside",
            textfont=dict(size=10, family=FONT_MONO),
            cliponaxis=False,
        ))
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode = False,
        font=dict(family=FONT_SANS, color=C["text"], size=12),
        margin=dict(l=48, r=24, t=80, b=48),
        xaxis=dict(
            **AXIS_STYLE,
            title="Patron Type",
            categoryorder="array",
            categoryarray=["Adult", "Senior Citizen", "Student"],
        ),
        yaxis=dict(**AXIS_STYLE, title="Number of Journeys"),
        barmode='group',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.3,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=C["border"],
            borderwidth=1,
            font=dict(size=10),
        ),
    )
    
    return fig


# ── Layout helpers ────────────────────────────────────

def section_label(text):
    return html.P(text, style={
        "fontSize":      "10px",
        "fontWeight":    "600",
        "letterSpacing": "0.1em",
        "textTransform": "uppercase",
        "color":         C["secondary"],
        "fontFamily":    FONT_MONO,
        "margin":        "0 0 6px 0",
    })

def tradeoff_kpi_card(title, count_value, pct_value, accent_color):
    return html.Div([
        html.Div(title, style={
            "fontSize": "12px",
            "fontWeight": "600",
            "color": C["secondary"],
            "fontFamily": FONT_SANS,
            "marginBottom": "6px",
        }),

        html.Div(count_value, style={
            "fontSize": "30px",
            "fontWeight": "700",
            "color": accent_color,
            "fontFamily": FONT_SANS,
            "lineHeight": "1.1",
        }),
    ], style={
        "background": C["bg"],
        "border": f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding": "14px 16px",
        "marginBottom": "10px",
    })
    
def card(title, subtitle, children):
    return html.Div([
        html.Div([
            html.H3(title, style={
                "margin":     0,
                "fontSize":   "15px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT_SANS,
            }),
            html.P(subtitle, style={
                "margin":     "3px 0 0",
                "fontSize":   "12px",
                "color":      C["secondary"],
                "fontFamily": FONT_SANS,
            }),
        ], style={
            "marginBottom":  "20px",
            "paddingBottom": "16px",
            "borderBottom":  f"1px solid {C['border_light']}",
        }),
        *children,
    ], style={
        "background":   C["surface"],
        "border":       f"1px solid {C['border']}",
        "borderRadius": "10px",
        "padding":      "24px 28px",
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


def color_legend(min_val=0, max_val=1.12):
    """Create a color legend showing light blue to dark blue for increasing % of transfers broken, plus no-data grey."""
    # Calculate 4 evenly spaced values across the range
    if max_val <= min_val:
        max_val = min_val + 0.01
    
    step = (max_val - min_val) / 3
    values = [min_val, min_val + step, min_val + 2*step, max_val]
    
    colors = ["#eaf2ff", "#bfd6ff", "#7faeff", "#1a56db", "#9ca3af"]
    labels = [f"{v:.1f}%" for v in values] + ["No data"]
    
    legend_items = []
    for i, (color, label) in enumerate(zip(colors, labels)):
        legend_items.append(
            html.Div([
                html.Div(style={
                    "width": "20px",
                    "height": "20px",
                    "backgroundColor": color,
                    "border": "1px solid #d1d5db",
                    "borderRadius": "3px",
                }),
                html.Span(label, style={
                    "fontSize": "12px",
                    "color": C["secondary"],
                    "fontFamily": FONT_SANS,
                }),
            ], style={
                "display": "flex",
                "alignItems": "center",
                "gap": "8px",
            })
        )
    
    return html.Div([
        html.P(
            "% of genuine transfers broken in that town",
            style={
                "fontSize": "11px",
                "fontWeight": "600",
                "color": C["muted"],
                "fontFamily": FONT_MONO,
                "margin": "0 0 8px 0",
                "letterSpacing": "0.05em",
                "textTransform": "uppercase",
            }
        ),
        html.Div(
            legend_items,
            style={
                "display": "flex",
                "gap": "12px",
                "flexWrap": "wrap",
            }
        ),
    ], style={
        "padding": "12px 0",
    })


# ── Page layout ───────────────────────────────────────────────────────────────

layout = html.Div([
    
    html.Div(id="top"),

    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap",
    ),

    # Page header
    html.Div([
        html.Div([
            html.H1("Delay Simulation", style={
                "margin":     0,
                "fontSize":   "20px",
                "fontWeight": "600",
                "color":      C["text"],
                "fontFamily": FONT_SANS,
            }),
            html.P(
                "Evaluate transfer window performance under different delay scenarios.",
                style={
                    "margin":     "4px 0 0",
                    "fontSize":   "13px",
                    "color":      C["secondary"],
                    "fontFamily": FONT_SANS,
                },
            ),
        ]),
    ], style={
        "display":        "flex",
        "justifyContent": "space-between",
        "alignItems":     "flex-start",
        "marginBottom":   "28px",
        "paddingBottom":  "20px",
        "borderBottom":   f"1px solid {C['border']}",
    }),
    
    info_box(
            "How to use this simulation",
            [
                html.Div(["1. "] + [html.Strong("Hover over the map")] + [" to view detailed metrics for each planning area."]),
                html.Div(["2. "] + [html.Strong("Select a region or planning area")] + [" to explore local impact."]),
                html.Div(["3. "] + [html.Strong("Choose a time of day and delay duration")] + [" to simulate disruption scenarios."]),
                html.Div(["4. "] + [html.Strong("Adjust the transfer window")] + [" to compare the trade-off between genuine transfers broken and wrongly merged journeys."]),
                html.Div(["5. "] + [html.Strong("Scroll down")] + [" to see how different patron types are affected by the transfer rules."]),
            ]
        ),
    html.Div([
    html.Span("Jump to: ", style={"fontWeight": "600", "marginRight": "10px"}),

    html.A(
        "Regional Impact Map",
        href="#regional-map",
        style={"marginRight": "15px", "textDecoration": "none", "color": C["accent"]}
    ),

    html.A(
        " Patron Impact Comparison",
        href="#patron-impact",
        style={"textDecoration": "none", "color": C["accent"]}
    ),
], style={"marginBottom": "20px"}),

    # ── Main card: Map + Controls ─────────────────────────────────────────────
    html.Div(card(
        "Regional Impact Map",
        "Genuine transfers broken by transfer window / delays, shown as % of all transfers in each town (hover over map for details)",
        [
            

            # Filter row
            html.Div([
                html.Div([
                    section_label("Region"),
                    dcc.Dropdown(
                        id="p4-region-dropdown",
                        options=[{"label": r, "value": r} for r in REGIONS],
                        value="All Regions",
                        clearable=False,
                        style={"fontSize": "13px", "width": "180px"},
                    ),
                ]),
                html.Div([
                    section_label("Planning Area (Town)"),
                    dcc.Dropdown(
                        id="p4-planning-area-dropdown",
                        options=[],
                        value="All Planning Areas",
                        clearable=False,
                        style={"fontSize": "13px", "width": "200px"},
                    ),
                ]),
                html.Div([
                    section_label("Time of Day"),
                    dcc.Dropdown(
                        id="p4-time-dropdown",
                        options=[{"label": t, "value": t} for t in TIMES_OF_DAY],
                        placeholder="All times",
                        clearable=True,
                        style={"fontSize": "13px", "width": "220px"},
                    )
                ]),
                html.Div([
                    section_label("Duration of Delay"),
                    dcc.Dropdown(
                        id="p4-delay-dropdown",
                        options=[{"label": d, "value": d} for d in DELAY_DURATIONS],
                        value="0 minutes",
                        clearable=False,
                        style={"fontSize": "13px", "width": "160px"},
                    ),
                ]),
            ], style={
                "display":      "flex",
                "flexWrap":     "wrap",
                "gap":          "32px",
                "padding":      "14px 18px",
                "background":   C["bg"],
                "borderRadius": "6px",
                "border":       f"1px solid {C['border']}",
                "marginBottom": "20px",
            }),

            # Map + right panel
            html.Div([

                # Map
                html.Div([
                    html.Div(
                        dcc.Graph(
                            id="p4-map-figure",
                            figure=build_map_figure(),
                            config={"displayModeBar": False},
                            style={"height": "400px"},
                        ),
                        style={
                            "borderRadius": "8px",
                            "overflow":     "hidden",
                            "border":       f"1px solid {C['border_light']}",
                        },
                    ),
                    html.Div(id="p4-color-legend"),
                ], style={
                    "flex": "1",
                }),

                # Right panel: slider + bar chart
                html.Div([

                    # Transfer window slider
                    html.Div([
                        section_label("Transfer Window (minutes)"),
                        dcc.Slider(
                            id="p4-transfer-window-slider",
                            min=30, max=60, step=5, value=45,
                            marks={
                                30: {"label": "30", "style": {"fontFamily": FONT_MONO, "fontSize": "11px"}},
                                45: {"label": "45", "style": {"fontFamily": FONT_MONO, "fontSize": "11px", "color": C["accent"]}},
                                60: {"label": "60", "style": {"fontFamily": FONT_MONO, "fontSize": "11px"}},
                            },
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ], style={
                        "background":   C["surface"],
                        "border":       f"1px solid {C['border']}",
                        "borderRadius": "8px",
                        "padding":      "16px 18px",
                        "marginBottom": "12px",
                    }),

                    # Bar chart
                    html.Div([
                        section_label("Tradeoff Analysis"),
                        html.Div(id="p4-tradeoff-kpis"),
                        
                    ], style={
                        "background":   C["surface"],
                        "border":       f"1px solid {C['border']}",
                        "borderRadius": "8px",
                        "padding":      "16px 18px",
                    }),

                ], style={"width": "260px", "display": "flex", "flexDirection": "column"}),

            ], style={"display": "flex", "gap": "20px", "alignItems": "stretch"}),

        ],
    ),
             id = 'regional-map'
    ),

    # ── Patron Comparison Card ─────────────────────────────────────────────
  html.Div(
    card(
        "Patron Impact Comparison",
        "How different patron types are affected by the transfer window setting",
        [
            html.Div(
                [
                    html.Div([
                        section_label("Duration of Delay"),
                        dcc.Dropdown(
                            id="p4-patron-delay-dropdown",
                            options=[{"label": d, "value": d} for d in DELAY_DURATIONS],
                            value="0 minutes",
                            clearable=False,
                            style={"fontSize": "13px", "width": "180px"},
                        ),
                    ]),

                    html.Div([
                        section_label("Transfer Window (minutes)"),
                        dcc.Slider(
                            id="p4-patron-transfer-slider",
                            min=30,
                            max=60,
                            step=5,
                            value=45,
                            marks={
                                30: {"label": "30", "style": {"fontFamily": FONT_MONO, "fontSize": "11px"}},
                                45: {"label": "45", "style": {"fontFamily": FONT_MONO, "fontSize": "11px", "color": C["accent"]}},
                                60: {"label": "60", "style": {"fontFamily": FONT_MONO, "fontSize": "11px"}},
                            },
                        ),
                    ], style={
                        "width": "260px",
                        "background": C["surface"],
                        "border": f"1px solid {C['border']}",
                        "borderRadius": "8px",
                        "padding": "14px 18px",
                    }),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "center",
                    "gap": "24px",
                    "alignItems": "flex-start",
                    "marginBottom": "20px",
                    "width": "100%",
                },
            ),

            html.Div(
                dcc.Graph(
                    id="p4-patron-chart",
                    figure=build_patron_chart(),
                    config={"displayModeBar": False},
                    style={"height": "300px"},
                ),
            ),
        ],
    ),
    id="patron-impact",
),

], style={
    "background":  C["bg"],
    "minHeight":   "100vh",
    "padding":     "36px 48px",
    "fontFamily":  FONT_SANS,
    "color":       C["text"],
    "maxWidth":    "1100px",
    "margin":      "0 auto",
})

# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output("p4-planning-area-dropdown", "options"),
    Output("p4-planning-area-dropdown", "value"),
    Input("p4-region-dropdown", "value"),
    State("p4-planning-area-dropdown", "value"),
)
def update_planning_areas(region, current_value):
    planning_areas = get_planning_areas_for_region(region)
    options = [{"label": pa, "value": pa} for pa in planning_areas]

    # keep current selection if still valid
    valid_values = [pa for pa in planning_areas]
    if current_value in valid_values:
        return options, current_value
    return options, "All Planning Areas"


@callback(
    Output("p4-map-figure", "figure"),
    Output("p4-tradeoff-kpis", "children"),
    Output("p4-color-legend", "children"),
    Input("p4-region-dropdown", "value"),
    Input("p4-planning-area-dropdown", "value"),
    Input("p4-time-dropdown", "value"),
    Input("p4-delay-dropdown", "value"),
    Input("p4-transfer-window-slider", "value"),
)


def update_figures(region, planning_area, time_of_day, delay_duration, transfer_window):
    map_fig = build_map_figure(region, time_of_day, delay_duration, transfer_window, planning_area)

    if DELAY_SIM_DF is None:
        return map_fig, html.Div("CSV not loaded"), color_legend()

    if delay_duration is None:
        delay_mins = 0
    else:
        try:
            delay_mins = int(delay_duration.split()[0])
        except (ValueError, IndexError):
            delay_mins = 0

    # Calculate min/max for legend
    df_all = get_real_map_data(
        region=None,
        planning_area=None,
        delay_duration=delay_duration,
        transfer_window=transfer_window,
        classifier_type="baseline",
        time_of_day=time_of_day
    )
    
    valid_pcts = df_all[df_all['has_data'] == True]['wrongly_split_pct'].dropna()
    if not valid_pcts.empty:
        legend_min = valid_pcts.min()
        legend_max = valid_pcts.max()
    else:
        legend_min = 0
        legend_max = 1.12
    
    legend = color_legend(legend_min, legend_max)

    try:
        result = query_delay_sim(
            delay_mins=delay_mins,
            bus_window=transfer_window,
            classifier_type="baseline",
            patron="all"
        )
        if (not region or region == "All Regions") and (not planning_area or planning_area == "All Planning Areas") and not time_of_day:
            correctly_kept_n = result["correctly_kept_n"]
            correctly_kept_pct = result["correctly_kept_pct"]
            correctly_split_n = result["correctly_split_n"]
            correctly_split_pct = result["correctly_split_pct"]
            wrongly_split_n = result["wrongly_split_n"]
            wrongly_merged_n = result["wrongly_merged_n"]
            wrongly_split_pct = result["wrongly_split_pct"]
            wrongly_merged_pct = result["wrongly_merged_pct"]

        else:
            df_region = result["by_hour_x_region"].copy()

            if time_of_day:
                df_region = df_region[
                    df_region["time_bucket"].astype(str).str.strip().str.lower()
                    == time_of_day.strip().lower()
                ]

            if planning_area and planning_area != "All Planning Areas":
                df_region = df_region[
                    df_region["dest_region"].astype(str).str.strip().str.lower()
                    == planning_area.strip().lower()
                ]
            elif region and region != "All Regions":
                meta = get_planning_area_metadata()[["planning_area_raw", "region"]].drop_duplicates()
                valid_areas = meta.loc[meta["region"] == region, "planning_area_raw"].tolist()
                df_region = df_region[df_region["dest_region"].isin(valid_areas)]

            if df_region.empty:
                correctly_kept_n = 0
                correctly_kept_pct = 0.0
                correctly_split_n = 0
                correctly_split_pct = 0.0
                wrongly_split_n = 0
                wrongly_merged_n = 0
                wrongly_split_pct = 0.0
                wrongly_merged_pct = 0.0
            else:
                ground_truth_transfer_n = df_region["ground_truth_transfer_n"].sum()
                ground_truth_new_journey_n = df_region["ground_truth_new_journey_n"].sum()
                wrongly_split_n = int(df_region["wrongly_split_n"].sum())
                wrongly_merged_n = int(df_region["wrongly_merged_n"].sum())

                correctly_kept_n = int(ground_truth_transfer_n) - wrongly_split_n
                correctly_kept_pct = (correctly_kept_n / ground_truth_transfer_n * 100) if ground_truth_transfer_n > 0 else 0.0

                correctly_split_n = int(ground_truth_new_journey_n) - wrongly_merged_n
                correctly_split_pct = (correctly_split_n / ground_truth_new_journey_n * 100) if ground_truth_new_journey_n > 0 else 0.0

                wrongly_split_pct = (wrongly_split_n / ground_truth_transfer_n * 100) if ground_truth_transfer_n > 0 else 0.0
                wrongly_merged_pct = (wrongly_merged_n / ground_truth_new_journey_n * 100) if ground_truth_new_journey_n > 0 else 0.0

        tradeoff_kpis = html.Div([
            tradeoff_kpi_card(
                "Correctly split",
                f"{correctly_split_n:,}",
                f"{correctly_split_pct:.2f}% of separate journeys",
                "#0ea5e9",
            ),
            tradeoff_kpi_card(
                "Wrongly split",
                f"{wrongly_split_n:,}",
                f"{wrongly_split_pct:.2f}% of genuine transfers",
                "#dc2626",
            ),
            tradeoff_kpi_card(
                "Correctly merged",
                f"{correctly_kept_n:,}",
                f"{correctly_kept_pct:.2f}% of genuine transfers",
                "#10b981",
            ),
            tradeoff_kpi_card(
                "Wrongly merged",
                f"{wrongly_merged_n:,}",
                f"{wrongly_merged_pct:.2f}% of separate journeys",
                "#f59e0b",
            ),
            ])

    except Exception as e:
        tradeoff_kpis = html.Div("Unable to load tradeoff metrics")

    return map_fig, tradeoff_kpis, legend

@callback(
    Output("p4-patron-chart", "figure"),
    Input("p4-patron-delay-dropdown", "value"),
    Input("p4-patron-transfer-slider", "value"),
)

def update_patron_chart(delay_duration, transfer_window):
    return build_patron_chart(delay_duration, transfer_window)