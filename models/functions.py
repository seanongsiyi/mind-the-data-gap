import os
import pandas as pd

_base_dir = os.path.dirname(os.path.abspath(__file__)) # This line is for py file
_data_dir = os.path.join(_base_dir, '..', 'data')
 
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