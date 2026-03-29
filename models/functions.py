import os
import pandas as pd

_base_dir = os.path.dirname(os.path.abspath(__file__)) # This line is for py file
_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
 

 ## Welfare functions

def get_welfare_summary(patron, window, spec):
    """
    Look up welfare results for a given patron category, transfer window, and classifier spec.
 
    Inputs:
    - patron: 'Overall', 'Adult', 'Student', 'Senior Citizen'
    - window: integer, one of 20, 25, 30, 35, 40, 45, 50, 55
    - spec: 'strict', 'baseline', 'lenient'
 
    Returns:
    - dict with split/merge error counts, unconditional rates, and conditional rates
    """
    final_results_df = pd.read_csv(os.path.join(_data_dir, 'welfare_results.csv'))
 
    row = final_results_df[
        (final_results_df['patron'] == patron) &
        (final_results_df['window_mins'] == window) &
        (final_results_df['spec'] == spec)
    ]
 
    if row.empty:
        return f"No data found for patron='{patron}', window={window}, spec='{spec}'"
 
    row = row.iloc[0]
 
    return {
        'spec':                     spec,
        'patron':                   patron,
        'window_mins':              window,
        'classifier_transfer_n':    row['classifier_transfer_n'],
        'classifier_new_journey_n': row['classifier_new_journey_n'],
        'window_transfer_n':        row['window_transfer_n'],
        'window_new_journey_n':     row['window_new_journey_n'],
        # split error: window too strict, breaks classifier-valid transfers → commuter overcharged
        'split_error_n':            row['wrongly_split_n'],
        'split_error_pct':          row['wrongly_split_pct'],          # % of all pairs
        'split_error_cond_pct':     row['wrongly_split_cond_pct'],     # % of classifier-said transfers
        # merge error: window too lenient, links classifier-separate journeys → fare undercharged
        'merge_error_n':            row['wrongly_merged_n'],
        'merge_error_pct':          row['wrongly_merged_pct'],         # % of all pairs
        'merge_error_cond_pct':     row['wrongly_merged_cond_pct'],    # % of classifier-said new journeys
    }
 
 
def get_marginal_summary(patron, spec, window_from):
    """
    Look up the marginal welfare effect of increasing the transfer window by 5 minutes.
 
    Inputs:
    - patron: 'Overall', 'Adult', 'Student', 'Senior Citizen'
    - spec: 'strict', 'baseline', 'lenient'
    - window_from: integer, one of 20, 25, 30, 35, 40, 45, 50
                   (returns the effect of moving from window_from to window_from + 5)
 
    Returns:
    - dict with newly linked pairs, marginal benefit (legitimate transfers rescued),
      and marginal cost (illegitimate links added)
    """
    marginal_df = pd.read_csv(os.path.join(_data_dir, 'welfare_marginal.csv'))
 
    window_to = window_from + 5
 
    row = marginal_df[
        (marginal_df['patron'] == patron) &
        (marginal_df['spec'] == spec) &
        (marginal_df['window_from'] == window_from) &
        (marginal_df['window_to'] == window_to)
    ]
 
    if row.empty:
        return f"No data found for patron='{patron}', spec='{spec}', window_from={window_from}"
 
    row = row.iloc[0]
 
    return {
        'spec':               spec,
        'patron':             patron,
        'window_from':        window_from,
        'window_to':          window_to,
        'newly_linked_n':     row['newly_linked_n'],       # total pairs newly linked by the larger window
        'marginal_benefit_n': row['marginal_benefit_n'],   # newly linked where classifier says transfer → legitimate rescue
        'marginal_cost_n':    row['marginal_cost_n'],      # newly linked where classifier says new journey → illegitimate link
    }

## Visualisation Suite functions
# Frontend query functions (read from pre-computed CSVs)

def get_trf_time_distribution(age_group=None, hour=None):
    """
    Returns avg transfer time distribution by age group and hour of day.

    Inputs:
    - age_group: None (all), or one of '7-19', '20-59', '60+'
    - hour:      None (all), or int 0-23

    Returns: DataFrame with [age_group, hour_of_day, avg_transfer_time_mins]
    """
    df = pd.read_csv(os.path.join(_data_dir, 'trf_time_distribution.csv'))

    if age_group is not None:
        df = df[df['age_group'] == age_group]
    if hour is not None:
        df = df[df['hour_of_day'] == hour]

    return df.reset_index(drop=True)


def get_trf_pair_distribution(orig_station=None, dest_station=None):
    """
    Returns top transfer station pairs by count.

    Inputs:
    - orig_station: None (all), or filter by origin station name string
    - dest_station: None (all), or filter by destination station name string

    Returns: DataFrame with [ORIG_STATION_NAME, DEST_STATION_NAME, count]
    """
    df = pd.read_csv(os.path.join(_data_dir, 'trf_pair_dist.csv'))

    if orig_station is not None:
        df = df[df['ORIG_STATION_NAME'] == orig_station]
    if dest_station is not None:
        df = df[df['DEST_STATION_NAME'] == dest_station]

    return df.reset_index(drop=True)


def get_trf_temporal_pattern(patron=None):
    """
    Returns avg transfer time by hour of day for the temporal pattern chart.

    Inputs:
    - patron: None (all), or one of 'Adult', 'Student', 'Senior Citizen'

    Returns: DataFrame with [hour_of_day, PATRON_CATG_DESC_TXT, avg_transfer_time_mins]
    """
    df = pd.read_csv(os.path.join(_data_dir, 'trf_pattern_distribution.csv'))

    if patron is not None:
        df = df[df['PATRON_CATG_DESC_TXT'] == patron]

    return df.reset_index(drop=True)