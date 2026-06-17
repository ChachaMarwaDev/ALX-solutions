"""
Integrated_Project_P3_submission.py
-------------------------------------
Complete solution for Part 3: Validating our data.

This file contains:
  1. config_params           — single dictionary for all pipeline settings
  2. FieldDataProcessor      — already in field_data_processor.py
  3. WeatherDataProcessor    — already in weather_data_processor.py
  4. filter_field_data()     — filter farm data by station & measurement
  5. filter_weather_data()   — filter weather data by station & measurement
  6. run_ttest()             — Welch's two-sample t-test
  7. print_ttest_results()   — interpret and print the result
  8. hypothesis_results()    — loop over all stations and measurements

Put this file, data_ingestion.py, field_data_processor.py, and
weather_data_processor.py in the same folder as your notebook and .db file.
"""

import re
import numpy as np
import pandas as pd
import logging
from scipy.stats import ttest_ind

from field_data_processor   import FieldDataProcessor
from weather_data_processor import WeatherDataProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ===========================================================================
# 1. Central configuration dictionary
#    One place to change any path, query, or pattern — no hunting through
#    multiple files.
# ===========================================================================

config_params = {
    # --- Database ---
    "db_path": "sqlite:///Maji_Ndogo_farm_survey_small.db",

    # --- SQL query that joins all four survey tables ---
    "sql_query": """
        SELECT *
        FROM geographic_features
        LEFT JOIN weather_features       USING (Field_ID)
        LEFT JOIN soil_and_crop_features USING (Field_ID)
        LEFT JOIN farm_management_features USING (Field_ID)
    """,

    # --- Column swap: the raw join has these two the wrong way round ---
    "columns_to_rename": {
        "Annual_yield": "Crop_type",
        "Crop_type":    "Annual_yield"
    },

    # --- Known crop-type misspellings → correct spelling ---
    "values_to_rename": {
        "cassaval": "cassava",
        "wheatn":   "wheat",
        "teaa":     "tea"
    },

    # --- CSV URLs ---
    "weather_csv_path": (
        "https://raw.githubusercontent.com/Explore-AI/PublicData/master/"
        "Maji_Ndogo/Weather_station_data.csv"
    ),
    "weather_mapping_csv": (
        "https://raw.githubusercontent.com/Explore-AI/PublicData/master/"
        "Maji_Ndogo/Weather_data_field_mapping.csv"
    ),

    # --- Regex patterns for parsing IoT sensor messages ---
    # Each pattern has at least one capturing group for the numeric value.
    "regex_patterns": {
        "Rainfall":       r"(\d+(\.\d+)?)\s?mm",
        "Temperature":    r"(\d+(\.\d+)?)\s?C",
        # Matches "= 0.45" or "Pollution at 0.45" (with optional spaces)
        "Pollution_level": r"=\s*(-?\d+(\.\d+)?)|Pollution at\s*(-?\d+(\.\d+)?)"
    },
}


# ===========================================================================
# 2. Run the pipeline
# ===========================================================================

field_processor = FieldDataProcessor(config_params)
field_processor.process()
field_df = field_processor.df

weather_processor = WeatherDataProcessor(config_params)
weather_processor.process()
weather_df = weather_processor.weather_df

# Rename Ave_temps → Temperature so both DataFrames share the same column name
field_df.rename(columns={'Ave_temps': 'Temperature'}, inplace=True)


# ===========================================================================
# 3. Hypothesis test functions
# ===========================================================================

def filter_field_data(df, station_id, measurement):
    """
    Return a single Series of field measurements for a given station.

    Filters the field DataFrame to rows that belong to `station_id` and
    returns only the column named `measurement`.

    Parameters
    ----------
    df           : pd.DataFrame  — the cleaned field DataFrame (field_df)
    station_id   : int           — weather station ID (0–4)
    measurement  : str           — column name, e.g. 'Temperature'

    Returns
    -------
    pd.Series  — the measurement values for that station

    Example
    -------
    >>> field_values = filter_field_data(field_df, 0, 'Temperature')
    >>> field_values.shape
    (1375,)
    """
    return df[df['Weather_station'] == station_id][measurement]


def filter_weather_data(df, station_id, measurement):
    """
    Return a single Series of weather-station readings for a given station.

    Filters the weather DataFrame to rows where Weather_station_ID matches
    `station_id` and Measurement matches `measurement`, then returns the
    Value column.

    Parameters
    ----------
    df           : pd.DataFrame  — the parsed weather DataFrame (weather_df)
    station_id   : int           — weather station ID (0–4)
    measurement  : str           — measurement type, e.g. 'Temperature'

    Returns
    -------
    pd.Series  — the Value column for the matching rows

    Example
    -------
    >>> weather_values = filter_weather_data(weather_df, 0, 'Temperature')
    >>> weather_values.shape
    (100,)
    """
    mask = (
        (df['Weather_station_ID'] == station_id) &
        (df['Measurement'] == measurement)
    )
    return df[mask]['Value']


def run_ttest(Column_A, Column_B):
    """
    Run a two-sample Welch's t-test between two data Series.

    Uses scipy.stats.ttest_ind with equal_var=False (Welch's t-test), which
    does NOT assume the two samples have equal variance — safer when sample
    sizes differ (e.g. 1375 field readings vs 100 weather readings).

    The alternative='two-sided' matches our hypothesis:
        H0: μ_field == μ_weather  (no significant difference)
        Ha: μ_field != μ_weather  (significant difference exists)

    Parameters
    ----------
    Column_A : pd.Series  — first sample (e.g. field temperature values)
    Column_B : pd.Series  — second sample (e.g. weather station temperature values)

    Returns
    -------
    tuple : (float, float)
        (t_statistic, p_value)

    Example
    -------
    >>> t_stat, p_val = run_ttest(field_values, weather_values)
    >>> print(f"T-stat: {t_stat:.5f}, p-value: {p_val:.5f}")
    T-stat: -0.11632, p-value: 0.90761
    """
    t_stat, p_val = ttest_ind(Column_A, Column_B, equal_var=False, alternative='two-sided')
    return t_stat, p_val


def print_ttest_results(station_id, measurement, p_val, alpha):
    """
    Interpret and print a t-test result in plain English.

    Compares the p-value against alpha:
    - p <= alpha → reject H0 (significant difference detected)
    - p >  alpha → fail to reject H0 (no significant difference found)

    Parameters
    ----------
    station_id  : int    — the weather station being tested
    measurement : str    — the measurement being compared
    p_val       : float  — the p-value from the t-test
    alpha       : float  — significance level (typically 0.05)

    Example output
    --------------
    No significant difference in Temperature detected at Station 0,
    (P-Value: 0.90761 > 0.05). Null hypothesis not rejected.
    """
    if p_val <= alpha:
        print(
            f"  Significant difference in {measurement} detected at Station "
            f"{station_id}, (P-Value: {p_val:.5f} < {alpha}). "
            f"Null hypothesis rejected."
        )
    else:
        print(
            f"  No significant difference in {measurement} detected at Station "
            f"{station_id}, (P-Value: {p_val:.5f} > {alpha}). "
            f"Null hypothesis not rejected."
        )


def hypothesis_results(field_df, weather_df, list_measurements_to_compare, alpha=0.05):
    """
    Run t-tests for every combination of weather station and measurement type.

    For each station ID found in field_df['Weather_station'] and for each
    measurement in list_measurements_to_compare, this function:
        1. Filters field data to that station + measurement.
        2. Filters weather data to that station + measurement.
        3. Runs a two-sample Welch's t-test.
        4. Prints an interpretation of the result.

    Parameters
    ----------
    field_df                    : pd.DataFrame — cleaned field survey data
    weather_df                  : pd.DataFrame — parsed weather station data
    list_measurements_to_compare: list[str]    — e.g. ['Temperature', 'Rainfall', 'Pollution_level']
    alpha                       : float, optional — significance level (default 0.05)

    Example
    -------
    >>> hypothesis_results(field_df, weather_df, measurements_to_compare, alpha=0.05)
    No significant difference in Temperature detected at Station 0 ...
    """
    station_ids = sorted(field_df['Weather_station'].dropna().unique())

    for station_id in station_ids:
        for measurement in list_measurements_to_compare:
            field_values   = filter_field_data(field_df, station_id, measurement)
            weather_values = filter_weather_data(weather_df, station_id, measurement)

            t_stat, p_val = run_ttest(field_values, weather_values)
            print_ttest_results(station_id, measurement, p_val, alpha)


# ===========================================================================
# 4. Run the hypothesis tests
# ===========================================================================

measurements_to_compare = ['Temperature', 'Rainfall', 'Pollution_level']
alpha = 0.05

hypothesis_results(field_df, weather_df, measurements_to_compare, alpha)
