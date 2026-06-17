"""
data_ingestion.py
-----------------
Handles all database connections, SQL queries, and web-based CSV retrieval
for the Maji Ndogo agricultural pipeline.

Functions
---------
create_db_engine(db_path)
    Create a SQLAlchemy engine and verify the connection.

query_data(engine, sql_query)
    Execute a SQL query and return the results as a DataFrame.

read_from_web_CSV(URL)
    Download a CSV file from a URL and return it as a DataFrame.
"""

from sqlalchemy import create_engine, text
import logging
import pandas as pd

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------
# Naming the logger after this module means every log line shows
# "data_ingestion" as the source, which makes debugging across modules easy.
logger = logging.getLogger('data_ingestion')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------

def create_db_engine(db_path):
    """
    Create and return a SQLAlchemy engine for the given database path.

    The function tests the connection immediately after creation so any
    problems (wrong path, missing file, etc.) surface early rather than
    during a later query.

    Parameters
    ----------
    db_path : str
        SQLAlchemy-style connection string, e.g.
        'sqlite:///Maji_Ndogo_farm_survey_small.db'

    Returns
    -------
    sqlalchemy.engine.Engine
        A live engine object ready for querying.

    Raises
    ------
    ImportError
        If SQLAlchemy is not installed.
    Exception
        If the engine cannot be created or the connection test fails.
    """
    try:
        engine = create_engine(db_path)
        # Test connection immediately so we fail fast on bad paths
        with engine.connect() as conn:
            pass
        logger.info("Database engine created successfully.")
        return engine
    except ImportError:
        logger.error("SQLAlchemy is required to use this function. Please install it first.")
        raise
    except Exception as e:
        logger.error(f"Failed to create database engine. Error: {e}")
        raise


def query_data(engine, sql_query):
    """
    Execute a SQL query against the given engine and return the results.

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        An active engine (from create_db_engine).
    sql_query : str
        A valid SQL SELECT statement.

    Returns
    -------
    pd.DataFrame
        The query result as a Pandas DataFrame.

    Raises
    ------
    ValueError
        If the query returns an empty DataFrame (nothing matched).
    Exception
        If any other database error occurs.
    """
    try:
        with engine.connect() as connection:
            df = pd.read_sql_query(text(sql_query), connection)
        if df.empty:
            msg = "The query returned an empty DataFrame."
            logger.error(msg)
            raise ValueError(msg)
        logger.info("Query executed successfully.")
        return df
    except ValueError as e:
        logger.error(f"SQL query failed. Error: {e}")
        raise
    except Exception as e:
        logger.error(f"An error occurred while querying the database. Error: {e}")
        raise


def read_from_web_CSV(URL):
    """
    Download a CSV file from the given URL and return it as a DataFrame.

    Parameters
    ----------
    URL : str
        A publicly accessible URL pointing to a CSV file.

    Returns
    -------
    pd.DataFrame
        The CSV contents as a Pandas DataFrame.

    Raises
    ------
    pd.errors.EmptyDataError
        If the URL exists but points to an empty or non-CSV resource.
    Exception
        If any other network or parsing error occurs.
    """
    try:
        df = pd.read_csv(URL)
        logger.info("CSV file read successfully from the web.")
        return df
    except pd.errors.EmptyDataError as e:
        logger.error("The URL does not point to a valid CSV file. Please check the URL and try again.")
        raise
    except Exception as e:
        logger.error(f"Failed to read CSV from the web. Error: {e}")
        raise
