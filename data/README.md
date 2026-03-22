## Description of variables created

1. `df2.pkl`
    - pt_ride, merge with bus stop and train stop coordinates
2. `df3.pkl`
    - df2, merge with walking distance, filtered for 11 Feb 2025
    - sorted by card number and entry time
3. `df5.pkl`
    - pt_jrny, cleaned the same way is df2


## Data Loading and Cleaning

1. Run `dataclean2.ipynb`
    - Prepare information on bus stops and MRT stations (e.g., ID, station names, latitude, longtitude)
    - Clean `pt_ride` and `pt_jrny` for data processing
    - (if needed) Choose a representative weekday, drop incomplete rows. 
    - Drop columns: 
        - For `pt_ride`:
            - `BIZ_DT` — filtered to one day already, redundant
            - `PAY_CD_21` — payment mode, not relevant to transfer logic
            - `RIDE_DISC_AMT` — can be derived from fare if needed
            - `RIDE_ID_NUM` — just a unique row ID, no analytical value
            - `SVC_GRADE_ID_NUM` — service grade, not relevant to transfer logic
            - `TKT_TYP_CD` — ticket type, not relevant to transfer logic
        - For `pt_jrny`:
            - `PAY_CD` — payment mode, not relevant to transfer logic
            - `SVC_GRADE_ID_NUM` — service grade, not relevant to transfer logic
            - `TKT_TYP_CD` — ticket type, not relevant to transfer logic
    - Choose only card types student, adult, senior citizens (ignoring concession, child, staff passes as we are
      unable to do any sort of fare analysis, also to reduce the dataset size)
    - Join the datasets with the bus and train dataframes to get information on the origin and destinations
    ** *.pkl is added into .gitignore so nobody on github can see it hehe

2. Go to the models folder and run the notebooks/scripts there.

** Note that the cleaned `pt_ride` and `pt_jrny` datasets are saved as pickle files for ease of access across all scripts/notebooks. Hence, `dataclean2.ipynb` only needs to be run ONCE. 


