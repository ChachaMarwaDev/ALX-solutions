"""
field_data_processor.py
-----------------------
Provides the FieldDataProcessor class, which ingests the raw farm survey
data from a SQLite database, applies all necessary cleaning and renaming
steps, and merges the weather-station mapping so each field row knows
which station it belongs to.

Typical usage
-------------
    from field_data_processor import FieldDataProcessor

    field_processor = FieldDataProcessor(config_params)
    field_processor.process()
    field_df = field_processor.df
"""

import pandas as pd
from data_ingestion import create_db_engine, query_data, read_from_web_CSV
import logging


class FieldDataProcessor:
    """
    Encapsulates the full ingestion and cleaning pipeline for the Maji Ndogo
    field survey data.

    All pipeline configuration (database path, SQL query, column/value
    corrections, and the weather-mapping CSV URL) is supplied via a single
    config_params dictionary so there is one central place to change settings.

    Attributes
    ----------
    db_path : str
        SQLAlchemy connection string for the SQLite database.
    sql_query : str
        SQL SELECT statement that joins all four survey tables.
    columns_to_rename : dict
        Maps the wrongly-named column to the correct name.
        e.g. {'Annual_yield': 'Crop_type', 'Crop_type': 'Annual_yield'}
    values_to_rename : dict
        Maps known misspelled crop strings to their correct values.
        e.g. {'cassaval': 'cassava', 'wheatn': 'wheat', 'teaa': 'tea'}
    weather_map_data : str
        URL (or path) to the Weather_data_field_mapping CSV.
    df : pd.DataFrame or None
        The processed DataFrame; None until .process() is called.
    engine : sqlalchemy.engine.Engine or None
        The active database engine; None until .ingest_sql_data() is called.

    Parameters
    ----------
    config_params : dict
        Dictionary with keys: 'db_path', 'sql_query', 'columns_to_rename',
        'values_to_rename', 'weather_mapping_csv'.
    logging_level : str, optional
        One of "DEBUG", "INFO", or "NONE". Defaults to "INFO".
    """

    def __init__(self, config_params, logging_level="INFO"):
        # Pull every config value from the shared dictionary
        self.db_path           = config_params['db_path']
        self.sql_query         = config_params['sql_query']
        self.columns_to_rename = config_params['columns_to_rename']
        self.values_to_rename  = config_params['values_to_rename']
        self.weather_map_data  = config_params['weather_mapping_csv']

        self.initialize_logging(logging_level)

        # Placeholders — populated once the relevant method runs
        self.df     = None
        self.engine = None

    # ------------------------------------------------------------------
    # Logging setup
    # ------------------------------------------------------------------

    def initialize_logging(self, logging_level):
        """
        Configure a module-specific logger for this FieldDataProcessor instance.

        Using a named logger (rather than the root logger) means log messages
        from this class are clearly labelled as coming from
        'field_data_processor.FieldDataProcessor', not from data_ingestion or
        any other module.

        Parameters
        ----------
        logging_level : str
            "DEBUG" for verbose output, "INFO" for standard progress messages,
            or "NONE" to silence all logging from this class.
        """
        logger_name  = __name__ + ".FieldDataProcessor"
        self.logger  = logging.getLogger(logger_name)
        self.logger.propagate = False  # Don't bubble up to the root logger

        if logging_level.upper() == "DEBUG":
            log_level = logging.DEBUG
        elif logging_level.upper() == "INFO":
            log_level = logging.INFO
        elif logging_level.upper() == "NONE":
            self.logger.disabled = True
            return
        else:
            log_level = logging.INFO  # Safe default

        self.logger.setLevel(log_level)

        # Guard against duplicate handlers when the class is re-instantiated
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    # ------------------------------------------------------------------
    # Pipeline methods
    # ------------------------------------------------------------------

    def ingest_sql_data(self):
        """
        Connect to the SQLite database and load the joined survey table.

        Creates a database engine using self.db_path, runs self.sql_query,
        and stores the result in self.df.

        Returns
        -------
        pd.DataFrame
            The raw joined DataFrame (also stored as self.df).
        """
        self.engine = create_db_engine(self.db_path)
        self.df     = query_data(self.engine, self.sql_query)
        self.logger.info("Sucessfully loaded data.")  # note: matches expected log exactly
        return self.df

    def rename_columns(self):
        """
        Swap the two misnamed columns Annual_yield and Crop_type.

        The raw database join has these two columns in the wrong order.
        A direct rename would cause a collision (both would momentarily share
        the same name), so we use a temporary placeholder name to do the swap
        safely.

        The column pair to swap is read from self.columns_to_rename so the
        logic is driven by config, not hard-coded strings.
        """
        # Read the swap pair from config
        column1, column2 = (
            list(self.columns_to_rename.keys())[0],
            list(self.columns_to_rename.values())[0]
        )

        # Pick a placeholder that definitely isn't already a column name
        temp_name = "__temp_name_for_swap__"
        while temp_name in self.df.columns:
            temp_name += "_"

        # Two-step rename to avoid collision
        self.df = self.df.rename(columns={column1: temp_name, column2: column1})
        self.df = self.df.rename(columns={temp_name: column2})

        self.logger.info(f"Swapped columns: {column1} with {column2}")

    def apply_corrections(self, column_name='Crop_type', abs_column='Elevation'):
        """
        Apply value-level corrections to the DataFrame.

        Two corrections are made:
        1. Elevation — takes the absolute value so negative entries are fixed.
        2. Crop_type — maps known misspellings to their correct values using
           self.values_to_rename (e.g. 'cassaval' → 'cassava').

        Parameters
        ----------
        column_name : str, optional
            Name of the crop-type column. Defaults to 'Crop_type'.
        abs_column : str, optional
            Name of the elevation column. Defaults to 'Elevation'.
        """
        self.df[abs_column]   = self.df[abs_column].abs()
        self.df[column_name]  = self.df[column_name].apply(
            lambda crop: self.values_to_rename.get(crop, crop)
        )

    def weather_station_mapping(self):
        """
        Download the field-to-weather-station mapping CSV from the web.

        Returns
        -------
        pd.DataFrame
            Mapping table with columns Field_ID and Weather_station_ID.
        """
        return read_from_web_CSV(self.weather_map_data)

    def process(self):
        """
        Run the full ingestion and cleaning pipeline in the correct order.

        Steps
        -----
        1. ingest_sql_data      — connect to DB and load the raw join.
        2. rename_columns       — fix the swapped Annual_yield / Crop_type.
        3. apply_corrections    — fix Elevation sign and crop-type spelling.
        4. weather_station_mapping — download the field→station mapping.
        5. Merge the mapping into self.df so each row has a Weather_station column.
        6. Drop the 'Unnamed: 0' index column that comes in from the CSV.

        After calling this method, the cleaned DataFrame is available at
        self.df.
        """
        self.ingest_sql_data()
        self.rename_columns()
        self.apply_corrections()

        weather_map_df = self.weather_station_mapping()

        self.df = self.df.merge(weather_map_df, on='Field_ID', how='left')

        # The mapping CSV has an extra index column — drop it if present
        if 'Unnamed: 0' in self.df.columns:
            self.df = self.df.drop(columns='Unnamed: 0')
