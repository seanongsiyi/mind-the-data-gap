# Pages

This folder contains all page modules for the Mind the Data Gap dashboard. Each file registers a Dash page and is automatically loaded by `app.py`.

## Page Overview

| File | Path | Name | Description |
|------|------|------|-------------|
| `home.py` | `/` | Home | Project overview, transfer rules, team members |
| `page1.py` | `/page-1` | Visualisation Suite | Explore transfer time and volume trends by age group and region |
| `page2.py` | `/page-2` | Delay Simulator | Evaluate transfer window performance under different delay scenarios |
| `page3.py` | `/page-3` | Policy Simulator | Cost-benefit analysis of proposed transfer window changes by patron type and region |

## Data Dependencies

Each page reads from the `data/` folder at the project root. The required files are:

| File | Used By |
|------|---------|
| `trf_time_distribution.csv` | page1 |
| `trf_region_pair.csv` | page1 |
| `singapore_planning_areas.geojson` | page1, page2 |
| `final_cleaned_delay_sim_results.csv` | page2 |
| `welfare_marginal.csv` | page3 |
| `welfare_results.csv` | page3 |
| `welfare_results_regional.csv` | page3 |
| `spec_info.csv` | page3 |


## Adding a New Page

1. Create a new file `pageN.py` in this folder.
2. Register it at the top of the file:
```python
   import dash
   dash.register_page(__name__, path="/page-N", name="Your Page Name")
```
3. Define a `layout` variable.
4. Use unique component IDs to avoid conflicts with other pages.

## Notes

- Pages load their data at module import time, so missing CSV files will crash the app on startup.
- The data files in `data/` folder needs are not uploaded to this repo for privacy reasons.
