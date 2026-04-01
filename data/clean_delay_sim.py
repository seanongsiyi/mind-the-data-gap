from pathlib import Path
import pandas as pd

INPUT_PATH = Path("data/final_delays_updated.csv")
OUTPUT_PATH = Path("data/delay_sim_results.csv")

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

def main():
    df = pd.read_csv(INPUT_PATH, low_memory=False)

    df["time_bucket"] = None

    mask = df["breakdown_type"] == "hour_x_dest_region"

    df.loc[mask, "time_bucket"] = df.loc[mask, "breakdown_value"].apply(hour_to_bucket)

    print("Rows in hour_x_dest_region:", mask.sum())
    print("Assigned time buckets:")
    print(df.loc[mask, "time_bucket"].value_counts(dropna=False))

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved transformed CSV to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()