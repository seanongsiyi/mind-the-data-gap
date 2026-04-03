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


def get_trf_region_pair(orig_region=None, dest_region=None, hour=None):
    """
    Returns transfer volume by origin-destination region pair and hour of day.

    Inputs:
    - orig_region: None (all), or filter by origin region string
    - dest_region: None (all), or filter by destination region string
    - hour:        None (all), or integer 0-23

    Returns: DataFrame with [orig_region, dest_region, hour_of_day, count]
    """
    df = pd.read_csv(os.path.join(_data_dir, 'trf_region_pair.csv'))

    if orig_region is not None:
        df = df[df['orig_region'] == orig_region]
    if dest_region is not None:
        df = df[df['dest_region'] == dest_region]
    if hour is not None:
        df = df[df['hour_of_day'] == hour]

    return df.reset_index(drop=True)

def get_trf_temporal_pattern(patron=None):
    """
    Returns avg transfer time by hour of day for the temporal pattern chart.

    Inputs:
    - patron: None (all), or one of 'Adult', 'Student', 'Senior Citizen'

    Returns: DataFrame with [hour_of_day, PATRON_CATG_DESC_TXT, avg_transfer_time_mins, count]
    """
    age_group_map = {
        '7-19':  'Student',
        '20-59': 'Adult',
        '60+':   'Senior Citizen'
    }

    df = pd.read_csv(os.path.join(_data_dir, 'trf_time_distribution.csv'))
    df['PATRON_CATG_DESC_TXT'] = df['age_group'].map(age_group_map)

    if patron is not None:
        df = df[df['PATRON_CATG_DESC_TXT'] == patron]

    return df[['hour_of_day', 'PATRON_CATG_DESC_TXT', 'avg_transfer_time_mins', 'count']].reset_index(drop=True)

## Delay Simulator Functions
def query_delay_sim(
    delay_mins:      int,
    bus_window:      int,
    classifier_type: str,
    patron:          str = 'all',
    df:              pd.DataFrame = None
):
    if df is None:
        raise ValueError("Please provide final_df")

    valid_delays  = [0, 5, 10, 15, 20]
    valid_windows = list(range(35, 65, 5))
    valid_specs   = ['baseline', 'lenient', 'strict']

    if delay_mins      not in valid_delays:  raise ValueError(f"delay_mins must be one of {valid_delays}")
    if bus_window      not in valid_windows: raise ValueError(f"bus_window must be one of {valid_windows}")
    if classifier_type not in valid_specs:   raise ValueError(f"classifier_type must be one of {valid_specs}")

    sub = df[
        (df['delay_mins']      == delay_mins)  &
        (df['bus_window_mins'] == bus_window)  &
        (df['spec']            == classifier_type)
    ].copy()

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

    def get_breakdown(breakdown_type, col_name):
        return (
            sub[sub['breakdown_type'] == breakdown_type][[
                'breakdown_value', 'n_pairs', 'n_cards',
                'classifier_journeys', 'window_journeys',
                'wrongly_split_n',       'wrongly_merged_n',
                'wrongly_split_pct',     'wrongly_merged_pct',
                'wrongly_split_pct_all', 'wrongly_merged_pct_all',
            ]]
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
        'wrongly_split_n':     int(main_row['wrongly_split_n']),
        'wrongly_merged_n':    int(main_row['wrongly_merged_n']),
        'wrongly_split_pct':   float(main_row['wrongly_split_pct']),
        'wrongly_merged_pct':  float(main_row['wrongly_merged_pct']),
        'by_patron':           get_breakdown('patron',          'patron'),
        'by_dest_region':      get_breakdown('dest_region',     'dest_region'),
        'by_orig_region':      get_breakdown('orig_region',     'orig_region'),
        'by_hour':             get_breakdown('next_entry_hour', 'hour'),
    }
    def get_hour_region_breakdown(region=None):
        sub_cross = sub[sub['breakdown_type'] == 'hour_x_dest_region'].copy()
        if region is not None:
            # frontend passes a specific region to filter
            sub_cross = sub_cross[sub_cross['dest_region'] == region]
        return (
            sub_cross[[
                'breakdown_value', 'dest_region', 'n_pairs',
                'wrongly_split_n',       'wrongly_merged_n',
                'wrongly_split_pct',     'wrongly_merged_pct',
            ]]
            .rename(columns={'breakdown_value': 'hour'})
            .sort_values(['dest_region', 'hour'])
            .reset_index(drop=True)
        )

    return {
        # existing keys unchanged
        'spec':                classifier_type,
        'delay_mins':          delay_mins,
        'bus_window_mins':     bus_window,
        'patron':              patron,
        'classifier_journeys': classifier_journeys,
        'window_journeys':     window_journeys,
        'journey_difference':  journey_difference,
        'wrongly_split_n':     int(main_row['wrongly_split_n']),
        'wrongly_merged_n':    int(main_row['wrongly_merged_n']),
        'wrongly_split_pct':   float(main_row['wrongly_split_pct']),
        'wrongly_merged_pct':  float(main_row['wrongly_merged_pct']),
        'by_patron':           get_breakdown('patron',          'patron'),
        'by_dest_region':      get_breakdown('dest_region',     'dest_region'),
        'by_orig_region':      get_breakdown('orig_region',     'orig_region'),
        'by_hour':             get_breakdown('next_entry_hour', 'hour'),

        'by_hour_dest_region': get_hour_region_breakdown(region=None),
    }

'''

def get_misclassified_transfers_region(region=None):
    """
    Returns number of actual transfers that were predicted to be new journeys (split error/'false negative') grouped by destination region
    """
    df = pd.read_csv(os.path.join(_data_dir, 'fn_by_region.csv'))

    if region is not None:
        df = df[df['dest_region'] == region]
    
    return df.reset_index(drop=True)

def get_misclassified_journeys_region(region=None):
    """
    Returns number of actual new journeys that were predicted to be transfers (merge error/'false positive') grouped by destination region
    """
    df = pd.read_csv(os.path.join(_data_dir, 'fp_by_region.csv'))

    if region is not None:
        df = df[df['dest_region'] == region]
    
    return df.reset_index(drop=True)

def get_misclassified_transfers_pairs(origin=None, next=None):
    """
    Returns exact station/stop transfer pair and the corresponding number of actual transfers that were predicted to be new journeys 
    (split error/'false negative')
    """
    df = pd.read_csv(os.path.join(_data_dir, 'fn_pair.csv'))

    if origin is not None:
        df = df[df['ORIG_STATION_NAME'] == origin]
    
    if next is not None:
        df = df[df['next_orig_station'] == next]
    
    return df.reset_index(drop=True)

def get_misclassified_journeys_pairs(origin=None, next=None):
    """
    Returns exact station/stop transfer pair and the corresponding number of actual new journeys that were predicted to be transfers 
    (merge error/'false positive')
    """
    df = pd.read_csv(os.path.join(_data_dir, 'fn_pair.csv'))

    if origin is not None:
        df = df[df['ORIG_STATION_NAME'] == origin]
    
    if next is not None:
        df = df[df['next_orig_station'] == next]
    
    return df.reset_index(drop=True)
'''