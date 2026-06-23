"""
data_ingestion.py
-----------------
Handles all database connections, SQL queries, and web-based data retrieval
for the Maji Ndogo agricultural pipeline.
"""

import pandas as pd
from sqlalchemy import create_engine, text


# ──────────────────────────────────────────────
# Database connection
# ──────────────────────────────────────────────

def create_db_engine(db_path: str):
    """
    Create and return a SQLAlchemy engine for the given SQLite database path.

    Parameters
    ----------
    db_path : str
        Path to the .db file, e.g. 'Maji_Ndogo_farm_survey_small.db'

    Returns
    -------
    sqlalchemy.engine.Engine
    """
    engine = create_engine(f"sqlite:///{db_path}")
    return engine


def test_db_connection(engine) -> bool:
    """
    Test that the database connection works by listing all tables.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine

    Returns
    -------
    bool : True if connection succeeded, False otherwise.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table';")
            )
            tables = [row[0] for row in result]
            print("✅ Connection successful. Tables found:")
            for t in tables:
                print(f"   - {t}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


# ──────────────────────────────────────────────
# SQL data loading
# ──────────────────────────────────────────────

def load_farm_data(engine) -> pd.DataFrame:
    """
    Load and join all four tables from the farm survey database into
    a single DataFrame, avoiding duplicate Field_ID columns.

    Tables joined:
        geographic_features
        weather_features
        soil_and_crop_features
        farm_management_features

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine

    Returns
    -------
    pd.DataFrame
    """
    sql_query = """
        SELECT *
        FROM geographic_features
        LEFT JOIN weather_features       USING (Field_ID)
        LEFT JOIN soil_and_crop_features USING (Field_ID)
        LEFT JOIN farm_management_features USING (Field_ID)
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql_query), conn)

    print(f"✅ Farm data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


# ──────────────────────────────────────────────
# Web-based CSV retrieval
# ──────────────────────────────────────────────

WEATHER_STATION_DATA_URL = (
    "https://raw.githubusercontent.com/Explore-AI/PublicData/master/"
    "Maji_Ndogo/Weather_station_data.csv"
)

WEATHER_STATION_MAPPING_URL = (
    "https://raw.githubusercontent.com/Explore-AI/PublicData/master/"
    "Maji_Ndogo/Weather_data_field_mapping.csv"
)


def load_weather_station_data(url: str = WEATHER_STATION_DATA_URL) -> pd.DataFrame:
    """
    Download the raw weather station sensor messages from GitHub (or a local path).

    Parameters
    ----------
    url : str
        URL or file path to Weather_station_data.csv

    Returns
    -------
    pd.DataFrame  with columns: Weather_station_ID, Message
    """
    df = pd.read_csv(url)
    print(f"✅ Weather station data loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    return df


def load_weather_station_mapping(url: str = WEATHER_STATION_MAPPING_URL) -> pd.DataFrame:
    """
    Download the field-to-weather-station mapping data.

    Parameters
    ----------
    url : str
        URL or file path to Weather_data_field_mapping.csv

    Returns
    -------
    pd.DataFrame  with columns: Field_ID, Weather_station_ID
    """
    df = pd.read_csv(url)
    print(f"✅ Weather station mapping loaded: {df.shape[0]} rows × {df.shape[1]} columns")
    return df
