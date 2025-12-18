Project Summary:
This capstone project explores UK road collision data (STATS19) to understand where, when, and why collisions become severe, and to assess whether collision severity can realistically be predicted using the available data.
The project combines exploratory data analysis, geospatial visualisation, and machine-learning classification to uncover key risk patterns and highlight the limitations of predictive modelling when critical variables are missing.

Contents:
Project Proposal – problem definition, objectives, and planned approach
Final Presentation (PDF) – key findings, visualisations, and modelling results
Streamlit App (app.py) – interactive dashboard for exploring collision patterns

Key Focus Areas:
Temporal trends and seasonality
Demographic differences in collision severity
Urban vs rural risk patterns
Speed limits, weather, and lighting conditions
Binary classification modelling for severe collisions

Key Takeaways:
Collision severity is inherently difficult to predict using STATS19 alone
Environmental conditions (visibility, weather, speed environment) strongly influence severity
Urban areas see more collisions, while rural roads are far more dangerous when collisions occur

Data:
This project uses the UK Department for Transport STATS19 Road Safety Dataset 
In particular the collisions dataset for the past 5 years (2024-2019)
Due to file size limits, raw data files are not included in this repository.
Data source:
https://www.gov.uk/government/statistics/road-safety-data

Technologies Used:
Python
Pandas, NumPy
Scikit-learn, XGBoost
Streamlit
