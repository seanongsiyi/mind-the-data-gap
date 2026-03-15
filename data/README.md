To load the dataset and clean, go in this order

1. Run dataloader.ipynb 
    - install DBbeaver to view SQL tables if you want. Otherwise just trust that I cleaned it.
    - change the datapath to your local path to the datasets. ensure all 6 csv sheets are in a folder named 'data' for convenience
    - Wait (~3 min) while loading the tables. Don't anyhow click.
    - MUST run the con.close() otherwise cannot move on
    ** data.duckdb is added into .gitignore so nobody on github can see it hehe

2. Run dataclean.ipynb
    - Cleaning ride_all for data processing
    - Choose a representative weekday, drop incomplete rows. 
    - Drop columns: 
            BIZ_DT — filtered to one day already, redundant
            PAY_CD_21 — payment mode, not relevant to transfer logic
            RIDE_DISC_AMT — can be derived from fare if needed
            RIDE_ID_NUM — just a unique row ID, no analytical value
            SVC_GRADE_ID_NUM — service grade, not relevant to transfer logic
            TKT_TYP_CD — ticket type, not relevant to transfer logic
    - Choose only card types student, adult, senior citizens (ignoring concession, child, staff passes as we are unable to do any sort of fare analysis
      also to reduce the dataset size)
    - Join the dataset with the respective mappings for convenience (can directly filter by mapped value instead of manually checking the code)

** Note that we are unable to save variables in duckDB table (SQL?) format, and refer to them across code files. Which is why in steps 1 and 2 I am cleaning in duckDB to reduce the dataset size, then in step 3 I will convert it back to a python dataframe to further process the data. 

3. Run dataprocessor.ipynb