# Welfare function

def get_welfare_summary(patron, window, spec):
    """
    Look up welfare results for a given patron category, transfer window, and classifier spec.
    
    Inputs:
    - patron: 'Overall', 'Adult', 'Student', 'Senior Citizen'
    - window: integer, one of 20, 25, 30, 35, 40, 45, 50, 55
    - spec: 'strict', 'baseline', 'lenient'
    
    Returns:
    - dict with benefit (wrongly split) and cost (wrongly merged) counts and rates
    """
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
        'classifier_transfer_n':    row['classifier_transfer_n'],    # how many pairs classifier says are transfers
        'classifier_new_journey_n': row['classifier_new_journey_n'], # how many pairs classifier says are new journeys
        'window_transfer_n':        row['window_transfer_n'],        # how many pairs window says are transfers
        'window_new_journey_n':     row['window_new_journey_n'],     # how many pairs window says are new journeys
        # benefit: window too strict, splits legitimate transfers → commuter overcharged
        'benefit_n':                row['wrongly_split_n'],
        'benefit_pct':              row['wrongly_split_pct'],
        # cost: window too lenient, merges separate journeys → fare undercharged
        'cost_n':                   row['wrongly_merged_n'],
        'cost_pct':                 row['wrongly_merged_pct'],
    }
