"""
weather_data_processor.py
--------------------------
Provides the WeatherDataProcessor class, which downloads the raw IoT
weather-station sensor messages, extracts numeric measurements from the
free-text Message column using regular expressions, and computes per-station
averages for later comparison against the field survey data.

Typical usage
-------------
    from weather_data_processor import WeatherDataProcessor

    weather_processor = WeatherDataProcessor(config_params)
    weather_processor.process()
    weather_df = weather_processor.weather_df
"""

import re
import numpy as np
import pandas as pd
import logging
from data_ingestion import read_from_web_CSV


class WeatherDataProcessor:
    """
    Encapsulates the full download and parsing pipeline for the Maji Ndogo
    weather station sensor data.

    Raw sensor messages are free-text strings (in several languages and
    formats). This class applies regex patterns to extract the measurement
    type (Temperature, Rainfall, or Pollution_level) and its numeric value
    from each message.

    Attributes
    ----------
    weather_station_data : str
        URL (or path) to Weather_station_data.csv.
    patterns : dict
        Regex patterns keyed by measurement name.
    weather_df : pd.DataFrame or None
        The processed DataFrame; None until .process() is called.

    Parameters
    ----------
    config_params : dict
        Dictionary with keys: 'weather_csv_path', 'regex_patterns'.
    logging_level : str, optional
        One of "DEBUG", "INFO", or "NONE". Defaults to "INFO".
    """

    def __init__(self, config_params, logging_level="INFO"):
        self.weather_station_data = config_params['weather_csv_path']
        self.patterns             = config_params['regex_patterns']
        self.weather_df           = None  # Populated by .process()
        self.initialize_logging(logging_level)

    # ------------------------------------------------------------------
    # Logging setup
    # ------------------------------------------------------------------

    def initialize_logging(self, logging_level):
        """
        Configure a module-specific logger for this WeatherDataProcessor.

        Parameters
        ----------
        logging_level : str
            "DEBUG", "INFO", or "NONE".
        """
        logger_name = __name__ + ".WeatherDataProcessor"
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False

        if logging_level.upper() == "DEBUG":
            log_level = logging.DEBUG
        elif logging_level.upper() == "INFO":
            log_level = logging.INFO
        elif logging_level.upper() == "NONE":
            self.logger.disabled = True
            return
        else:
            log_level = logging.INFO

        self.logger.setLevel(log_level)

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

    def weather_station_mapping(self):
        """
        Download the raw weather station CSV and store it in self.weather_df.

        The CSV has two columns: Weather_station_ID (int) and Message (str).
        After loading, further methods parse the Message column to extract
        structured measurements.
        """
        self.weather_df = read_from_web_CSV(self.weather_station_data)
        self.logger.info("Successfully loaded weather station data from the web.")

    def extract_measurement(self, message):
        """
        Apply every regex pattern to a single message string.

        Iterates through self.patterns and returns the first match found as
        a (measurement_name, float_value) tuple. If no pattern matches,
        returns (None, None).

        Parameters
        ----------
        message : str
            A raw sensor message, e.g.
            "Temp. Reading [2023-05-23 09:41:36]: Current 14.53 C."

        Returns
        -------
        tuple : (str | None, float | None)
            e.g. ('Temperature', 14.53)
        """
        for key, pattern in self.patterns.items():
            match = re.search(pattern, message)
            if match:
                self.logger.debug(f"Measurement extracted: {key}")
                # Pull the first non-None capture group — that's the numeric value
                value = float(next(x for x in match.groups() if x is not None))
                return key, value
        self.logger.debug("No measurement match found.")
        return None, None

    def process_messages(self):
        """
        Apply extract_measurement to every row and store the results.

        Adds two new columns to self.weather_df:
        - Measurement : str  — the type ('Temperature', 'Rainfall', 'Pollution_level')
        - Value       : float — the extracted numeric value

        Returns
        -------
        pd.DataFrame
            The updated self.weather_df with Measurement and Value columns.
        """
        if self.weather_df is not None:
            result = self.weather_df['Message'].apply(self.extract_measurement)
            self.weather_df['Measurement'], self.weather_df['Value'] = zip(*result)
            self.logger.info("Messages processed and measurements extracted.")
        else:
            self.logger.warning("weather_df is not initialized, skipping message processing.")
        return self.weather_df

    def calculate_means(self):
        """
        Calculate the mean Value per weather station and measurement type.

        Returns
        -------
        pd.DataFrame or None
            A pivot table indexed by Weather_station_ID with one column per
            measurement type, or None if weather_df is not yet loaded.

        Example
        -------
        Measurement       Pollution_level    Rainfall  Temperature
        Weather_station_ID
        0                        0.352791  1575.953750    13.403900
        """
        if self.weather_df is not None:
            means = self.weather_df.groupby(
                by=['Weather_station_ID', 'Measurement']
            )['Value'].mean()
            self.logger.info("Mean values calculated.")
            return means.unstack()
        else:
            self.logger.warning("weather_df is not initialized, cannot calculate means.")
            return None

    def process(self):
        """
        Run the full download and parsing pipeline.

        Steps
        -----
        1. weather_station_mapping — download CSV into self.weather_df.
        2. process_messages        — parse Message column; add Measurement & Value.

        After calling this, self.weather_df is ready for analysis.
        """
        self.weather_station_mapping()
        self.process_messages()
        self.logger.info("Data processing completed.")
