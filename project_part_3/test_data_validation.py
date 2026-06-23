"""
test_data_validation.py
-----------------------
Automated data validation tests for the Maji Ndogo pipeline.

Run with:
    python test_data_validation.py

Each test prints PASS or FAIL and a short explanation so you always know
exactly what is wrong and where to look.
"""

import sys
import pandas as pd

# ── Import our three modules ──────────────────────────────────────────
from data_ingestion        import (create_db_engine, test_db_connection,
                                   load_farm_data, load_weather_station_data,
                                   load_weather_station_mapping)
from field_data_processor  import (clean_field_data,
                                   merge_with_weather_station_mapping,
                                   get_farm_weather_means)
from weather_data_processor import (parse_weather_messages,
                                    get_unparsed_messages,
                                    get_station_means)


# ──────────────────────────────────────────────
# Tiny test-runner helpers
# ──────────────────────────────────────────────

PASS = "✅ PASS"
FAIL = "❌ FAIL"
_results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status}  [{name}]"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    _results.append((name, condition))


def summary():
    total  = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed = total - passed
    print("\n" + "=" * 55)
    print(f"Results: {passed}/{total} passed  |  {failed} failed")
    print("=" * 55)
    if failed:
        sys.exit(1)   # non-zero exit so CI/CD pipelines detect failures


# ──────────────────────────────────────────────
# 1. Database connection & load
# ──────────────────────────────────────────────

print("\n── Section 1: Database ingestion ──────────────────────\n")

DB_PATH = "Maji_Ndogo_farm_survey_small.db"

engine = create_db_engine(DB_PATH)

check(
    "DB connection",
    test_db_connection(engine),
    "Could not connect to the database. Is the .db file in this directory?"
)

raw_df = load_farm_data(engine)

check(
    "Farm data not empty",
    len(raw_df) > 0,
    f"Expected rows > 0, got {len(raw_df)}"
)

EXPECTED_COLUMNS = {
    "Field_ID", "Elevation", "Latitude", "Longitude", "Location", "Slope",
    "Rainfall", "Min_temperature_C", "Max_temperature_C", "Ave_temps",
    "Soil_fertility", "Soil_type", "pH",
    "Pollution_level", "Plot_size", "Crop_type", "Annual_yield", "Standard_yield"
}

check(
    "Expected columns present in raw load",
    EXPECTED_COLUMNS.issubset(set(raw_df.columns)),
    f"Missing: {EXPECTED_COLUMNS - set(raw_df.columns)}"
)


# ──────────────────────────────────────────────
# 2. Weather station data load
# ──────────────────────────────────────────────

print("\n── Section 2: Weather station ingestion ───────────────\n")

weather_df  = load_weather_station_data()
mapping_df  = load_weather_station_mapping()

check(
    "Weather station data not empty",
    len(weather_df) > 0
)

check(
    "Weather station mapping not empty",
    len(mapping_df) > 0
)

check(
    "Mapping has Field_ID and Weather_station_ID columns",
    {"Field_ID", "Weather_station_ID"}.issubset(set(mapping_df.columns)),
    f"Columns found: {list(mapping_df.columns)}"
)


# ──────────────────────────────────────────────
# 3. Field data cleaning
# ──────────────────────────────────────────────

print("\n── Section 3: Field data cleaning ─────────────────────\n")

clean_df = clean_field_data(raw_df)

check(
    "No negative Elevation values after cleaning",
    (clean_df["Elevation"] >= 0).all(),
    "Elevation column still has negative values."
)

VALID_CROP_TYPES = {"cassava", "wheat", "tea", "coffee", "rice", "maize",
                    "banana", "potato", "beans", "sugarcane"}

invalid_crops = set(clean_df["Crop_type"].unique()) - VALID_CROP_TYPES
check(
    "No unknown crop types after cleaning",
    len(invalid_crops) == 0,
    f"Unknown crop types found: {invalid_crops}"
)

check(
    "Crop_type column has no leading/trailing spaces",
    clean_df["Crop_type"].apply(lambda x: x == x.strip()).all()
)

check(
    "No null Field_IDs",
    clean_df["Field_ID"].notna().all()
)

check(
    "No duplicate Field_IDs",
    clean_df["Field_ID"].nunique() == len(clean_df),
    f"Rows: {len(clean_df)}, unique Field_IDs: {clean_df['Field_ID'].nunique()}"
)

check(
    "Standard_yield values are between 0 and 1",
    clean_df["Standard_yield"].between(0, 1).all(),
    f"Min: {clean_df['Standard_yield'].min():.4f}, "
    f"Max: {clean_df['Standard_yield'].max():.4f}"
)

check(
    "Pollution_level values are between 0 and 1",
    clean_df["Pollution_level"].between(0, 1).all(),
    f"Min: {clean_df['Pollution_level'].min():.4f}, "
    f"Max: {clean_df['Pollution_level'].max():.4f}"
)


# ──────────────────────────────────────────────
# 4. Weather message parsing
# ──────────────────────────────────────────────

print("\n── Section 4: Weather message parsing ─────────────────\n")

parsed_weather_df = parse_weather_messages(weather_df)

check(
    "Measurement column created",
    "Measurement" in parsed_weather_df.columns
)

check(
    "Value column created",
    "Value" in parsed_weather_df.columns
)

parsed_pct = parsed_weather_df["Value"].notna().mean() * 100
check(
    "At least 95% of messages parsed successfully",
    parsed_pct >= 95,
    f"Only {parsed_pct:.1f}% parsed. Check PATTERNS in weather_data_processor.py"
)

check(
    "All three measurement types are present",
    {"Temperature", "Rainfall", "Pollution_level"}.issubset(
        set(parsed_weather_df["Measurement"].dropna().unique())
    ),
    f"Types found: {parsed_weather_df['Measurement'].dropna().unique()}"
)

check(
    "Temperature values are plausible (0 °C – 45 °C)",
    parsed_weather_df.loc[
        parsed_weather_df["Measurement"] == "Temperature", "Value"
    ].between(0, 45).all()
)

check(
    "Rainfall values are plausible (0 – 5000 mm)",
    parsed_weather_df.loc[
        parsed_weather_df["Measurement"] == "Rainfall", "Value"
    ].between(0, 5000).all()
)

check(
    "Pollution values are plausible (0 – 1)",
    parsed_weather_df.loc[
        parsed_weather_df["Measurement"] == "Pollution_level", "Value"
    ].between(0, 1).all()
)


# ──────────────────────────────────────────────
# 5. Station means vs farm means (tolerance check)
# ──────────────────────────────────────────────

print("\n── Section 5: Cross-dataset validation ─────────────────\n")

station_means = get_station_means(parsed_weather_df)

merged_df         = merge_with_weather_station_mapping(clean_df, mapping_df)
farm_station_means = get_farm_weather_means(merged_df)

TOLERANCE_PCT = 10   # % — Temperature usually agrees well; rainfall/pollution less so

def within_tolerance(extracted, original, tol_pct):
    if original == 0:
        return extracted == 0
    return abs((extracted - original) / original) * 100 <= tol_pct


for station_id in station_means.index:
    for measurement in ["Temperature", "Rainfall", "Pollution_level"]:
        try:
            extracted = station_means.loc[station_id, measurement]
            original  = farm_station_means.loc[station_id, measurement]
            ok        = within_tolerance(extracted, original, TOLERANCE_PCT)
            check(
                f"Station {station_id} – {measurement} within {TOLERANCE_PCT}%",
                ok,
                f"Station mean: {extracted:.4f}  |  Farm mean: {original:.4f}"
            )
        except KeyError as e:
            check(
                f"Station {station_id} – {measurement} lookup",
                False,
                f"KeyError: {e}"
            )


# ──────────────────────────────────────────────
# Final summary
# ──────────────────────────────────────────────

summary()
