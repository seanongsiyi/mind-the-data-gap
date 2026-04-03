# Mind the Data Gap

> DSE3101 · NUS · Evaluating Public Transfer Rules in Singapore

## Overview

Current public transfer rules enforce a 45-minute window for train-bus and bus-bus transfers. These policies leave certain demographics — particularly the elderly — in inequitable situations where reduced mobility results in higher fares.

This project investigates how the 45-minute bus transfer window can be made more equitable and efficient. It assesses demographic fairness of the existing policy, proposes dynamic transfer rules that vary by commuter type, region, and time-of-day, and evaluates the impact of real-world delays on transfer window performance.

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| **Home** | Project overview, transfer rules reference, and team directory |
| **Visualisation Suite** | Explore transfer time and volume trends by age group, region, and time of day |
| **Delay Simulator** | Evaluate transfer window performance under different delay scenarios |
| **Policy Simulator** | Simulate cost-benefit tradeoffs of proposed transfer window changes by patron type and region |


---

## Project Structure
```
mind-the-data-gap/
├── assets/              # Images and static files (commuter characters, icons)
├── callbacks/           # Shared callback logic
│   ├── __init__.py
│   └── predictions.py
├── data/                # Data files (see Data Dependencies below)
├── models/              # Jupyter notebooks for modelling and analysis
│   ├── classifier.ipynb
│   ├── classifier_lenient.ipynb
│   ├── classifier_strict.ipynb
│   ├── delay_simulation.ipynb
│   ├── functions.py
│   ├── welfare_analysis.ipynb
│   └── README.md
├── pages/               # Dash page modules
│   ├── home.py
│   ├── page1.py
│   ├── page2.py
│   ├── page3.py
│   ├── page4.py
│   └── README.md
├── test/                # Test scripts
├── app.py               # Main Dash app entry point
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Data Dependencies

The `data/` folder is not fully committed to this repository. Large CSV files must be sourced separately. The following files are required to run the app:

| File | Required By | Notes |
|------|-------------|-------|
| `trf_time_distribution.csv` | page1 | Transfer time by age group and hour |
| `trf_region_pair.csv` | page1 | Transfer volume by origin-destination pair and hour |
| `singapore_planning_areas.geojson` | page1, page4 | Singapore planning area boundaries |
| `welfare_marginal.csv` | page3 | Marginal welfare results by patron and spec |
| `welfare_results_regional.csv` | page3 | Regional welfare results |
| `spec_info.csv` | page3 | Model specification descriptions |
| `final_delays_updated.csv` | page4 | Raw delay simulation input |
| `final_cleaned_delay_sim_results.csv` | page4 | Auto-generated from above on app startup |

---

## Setup & Running

**1. Clone the repository**
```bash
git clone https://github.com/JingHerng12/mind-the-data-gap.git
cd mind-the-data-gap
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add data files**

Place the required CSV and GeoJSON files in the `data/` folder. Contact a backend team member for access.

**4. Run the app**
```bash
python app.py
```

The app will be available at `http://127.0.0.1:8050`.

---

## Team

**Front End**
| Name | Matric |
|------|--------|
| Christopher Goh | A0272921E |
| Keira Low | A0283298M |
| Neoh Jing Herng | A0272508A |
| Ryan Chong | A0272778L |
| Sean Ong | A0271830J |

**Back End**
| Name | Matric |
|------|--------|
| Calista Wong | A0283269R |
| Jeslyn Tan | A0282642A |
| Koh Lin Kiat | A0273180J |
| Tan Shao Gjin | A0281362H |

---

## Course

DSE3101 — Data Science for Decision Making  
National University of Singapore (NUS)
