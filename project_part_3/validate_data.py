"""
validate_data.py
----------------
Automated pytest tests for the Maji Ndogo pipeline output DataFrames.

These tests read from two temporary CSV files that the main notebook
creates before running pytest:
    - sampled_weather_df.csv  (output of WeatherDataProcessor)
    - sampled_field_df.csv    (output of FieldDataProcessor)

Run with:
    pytest validate_data.py -v
"""

import pytest
import pandas as pd


# ---------------------------------------------------------------------------
# Load the CSVs once for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def weather_df():
    return pd.read_csv('sampled_weather_df.csv')


@pytest.fixture(scope="module")
def field_df():
    return pd.read_csv('sampled_field_df.csv')


# ---------------------------------------------------------------------------
# Shape tests
# ---------------------------------------------------------------------------

def test_read_weather_DataFrame_shape(weather_df):
    """Weather DataFrame must have exactly 2 original columns + 2 extracted."""
    assert weather_df.shape[1] == 4, (
        f"Expected 4 columns, got {weather_df.shape[1]}"
    )


def test_read_field_DataFrame_shape(field_df):
    """Field DataFrame should have 19 columns after the weather-station merge."""
    assert field_df.shape[1] == 19, (
        f"Expected 19 columns, got {field_df.shape[1]}"
    )


# ---------------------------------------------------------------------------
# Column presence tests
# ---------------------------------------------------------------------------

def test_weather_DataFrame_columns(weather_df):
    """Parsed weather DataFrame must have the Measurement and Value columns."""
    expected = {'Measurement', 'Value'}
    assert expected.issubset(set(weather_df.columns)), (
        f"Missing columns: {expected - set(weather_df.columns)}"
    )


def test_field_DataFrame_columns(field_df):
    """Field DataFrame must contain all core survey columns."""
    expected_columns = {
        'Field_ID', 'Elevation', 'Latitude', 'Longitude', 'Location', 'Slope',
        'Rainfall', 'Min_temperature_C', 'Max_temperature_C', 'Ave_temps',
        'Soil_fertility', 'Soil_type', 'pH',
        'Pollution_level', 'Plot_size', 'Crop_type', 'Annual_yield',
        'Standard_yield', 'Weather_station'
    }
    missing = expected_columns - set(field_df.columns)
    assert not missing, f"Missing columns: {missing}"


# ---------------------------------------------------------------------------
# Data quality tests
# ---------------------------------------------------------------------------

def test_field_DataFrame_non_negative_elevation(field_df):
    """All Elevation values must be non-negative after apply_corrections()."""
    assert (field_df['Elevation'] >= 0).all(), (
        "Negative Elevation values found — fix_elevation step may have failed."
    )


def test_crop_types_are_valid(field_df):
    """Crop_type column must contain only known, correctly spelled crop names."""
    valid_crops = {
        'cassava', 'wheat', 'tea', 'coffee', 'rice',
        'maize', 'banana', 'potato', 'beans', 'sugarcane'
    }
    actual_crops = set(field_df['Crop_type'].unique())
    invalid = actual_crops - valid_crops
    assert not invalid, f"Invalid crop types found: {invalid}"


def test_positive_rainfall_values(field_df):
    """All Rainfall values must be positive (rainfall cannot be negative)."""
    assert (field_df['Rainfall'] >= 0).all(), (
        "Negative Rainfall values found in field_df."
    )
