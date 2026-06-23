"""
field_data_processor.py
-----------------------
Handles all cleaning, transformation, and merging of the farm field data
(geographic, weather features, soil, crop, and farm management tables).
"""

import pandas as pd


# ──────────────────────────────────────────────
# Column renaming
# ──────────────────────────────────────────────

def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix the swapped Annual_yield / Crop_type columns that exist in the
    raw database join result.

    The raw join has the columns in the wrong order, so we swap them back
    using a temporary column name.

    Parameters
    ----------
    df : pd.DataFrame  (raw joined DataFrame from load_farm_data)

    Returns
    -------
    pd.DataFrame  with correctly named columns
    """
    df = df.rename(columns={
        "Annual_yield": "Crop_type_Temp",
        "Crop_type":    "Annual_yield"
    })
    df = df.rename(columns={"Crop_type_Temp": "Crop_type"})
    print("✅ Columns renamed: Annual_yield and Crop_type corrected.")
    return df


# ──────────────────────────────────────────────
# Value corrections
# ──────────────────────────────────────────────

def fix_elevation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Elevation values should never be negative — take the absolute value.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    df["Elevation"] = df["Elevation"].abs()
    print("✅ Elevation: negative values corrected to absolute values.")
    return df


# Lookup table for known typos in Crop_type
CROP_TYPE_CORRECTIONS = {
    "cassaval": "cassava",
    "wheatn":   "wheat",
    "teaa":     "tea",
}


def correct_crop_type(crop: str) -> str:
    """
    Strip whitespace and fix known typos in a single crop type string.

    Parameters
    ----------
    crop : str

    Returns
    -------
    str  corrected crop type
    """
    crop = crop.strip()
    return CROP_TYPE_CORRECTIONS.get(crop, crop)


def fix_crop_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply crop type corrections across the whole DataFrame.

    Parameters
    ----------
    df : pd.DataFrame

    Returns
    -------
    pd.DataFrame
    """
    before = df["Crop_type"].nunique()
    df["Crop_type"] = df["Crop_type"].apply(correct_crop_type)
    after = df["Crop_type"].nunique()
    print(f"✅ Crop types cleaned. Unique values before: {before}, after: {after}")
    return df


# ──────────────────────────────────────────────
# Master cleaning function
# ──────────────────────────────────────────────

def clean_field_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all cleaning steps on the raw farm survey DataFrame in the
    correct order.

    Steps applied:
        1. rename_columns  – fix swapped Annual_yield / Crop_type
        2. fix_elevation   – make Elevation always positive
        3. fix_crop_types  – correct known Crop_type typos

    Parameters
    ----------
    df : pd.DataFrame  (raw output of load_farm_data)

    Returns
    -------
    pd.DataFrame  fully cleaned farm data
    """
    df = rename_columns(df)
    df = fix_elevation(df)
    df = fix_crop_types(df)
    print(f"✅ Field data cleaning complete. Shape: {df.shape}")
    return df


# ──────────────────────────────────────────────
# Merging with weather station mapping
# ──────────────────────────────────────────────

def merge_with_weather_station_mapping(
    farm_df: pd.DataFrame,
    mapping_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Left-join the farm survey DataFrame with the field-to-weather-station
    mapping so each row knows which weather station it belongs to.

    Parameters
    ----------
    farm_df     : pd.DataFrame  cleaned farm data (from clean_field_data)
    mapping_df  : pd.DataFrame  mapping data (from load_weather_station_mapping)

    Returns
    -------
    pd.DataFrame  farm data with a Weather_station_ID column added
    """
    merged = farm_df.merge(mapping_df, on="Field_ID", how="left")

    missing = merged["Weather_station_ID"].isna().sum()
    if missing > 0:
        print(f"⚠️  {missing} rows have no matching weather station.")
    else:
        print("✅ All fields matched to a weather station.")

    print(f"✅ Merge complete. Shape: {merged.shape}")
    return merged


# ──────────────────────────────────────────────
# Compute per-station averages from farm data
# ──────────────────────────────────────────────

def get_farm_weather_means(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the mean Pollution_level, Rainfall, and Ave_temps per
    weather station from the farm survey data.

    The Ave_temps column is renamed to Temperature so it can be compared
    directly against the weather station means.

    Parameters
    ----------
    merged_df : pd.DataFrame  output of merge_with_weather_station_mapping

    Returns
    -------
    pd.DataFrame  indexed by Weather_station_ID with columns:
                  Pollution_level, Rainfall, Temperature
    """
    means = (
        merged_df
        .groupby("Weather_station_ID")
        .mean(numeric_only=True)[["Pollution_level", "Rainfall", "Ave_temps"]]
        .rename(columns={"Ave_temps": "Temperature"})
    )
    print("✅ Farm weather means calculated per station.")
    return means
