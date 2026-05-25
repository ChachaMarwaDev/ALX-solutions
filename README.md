# 🌱 Maji Ndogo Agricultural Analysis
### Integrated Project — ALX Data Analytics Programme

> Exploratory data analysis to identify optimal crop-growing conditions across five provinces of Maji Ndogo, as groundwork for an agricultural automation initiative.

---

## 📌 Project Overview

Maji Ndogo is an ambitious farming automation project. Before any technology can be deployed, the right decisions need to be made about **where** to plant **what**. This analysis answers exactly that — using survey data from 5,654 fields across five provinces, covering geography, weather, soil chemistry, and crop performance.

The work involves loading data from a multi-table SQLite database, cleaning it, and running structured analyses to surface the conditions under which each crop performs best.

---

## 📁 Repository Structure

```
maji-ndogo-agric-analysis/
│
├── Maji_Ndogo_farm_survey_small.db     # SQLite database (4 tables, 5,654 fields)
├── Code_challenge_Integrated_Project_P1_student_version.ipynb   # Main analysis notebook
└── README.md
```

---

## 🗄️ Database Schema

The database contains four tables, all joined on `Field_ID`:

| Table | Key Columns | Description |
|---|---|---|
| `geographic_features` | Elevation, Latitude, Longitude, Location, Slope | Where each field is located |
| `weather_features` | Rainfall, Min/Max/Ave temperature | Climate conditions per field |
| `soil_and_crop_features` | Soil_fertility, Soil_type, pH | Soil composition data |
| `farm_management_features` | Pollution_level, Plot_size, Crop_type, Annual_yield, Standard_yield | Crop and yield data |

All four tables are merged using a single SQL `INNER JOIN` query into one working DataFrame of **5,654 rows × 17 columns**.

---

## 🧹 Data Cleaning

Three data quality issues were identified and corrected before analysis:

**1. Swapped column names**
`Crop_type` and `Annual_yield` were stored in each other's columns in the database. They were renamed back to their correct positions.

**2. Spelling errors in crop names**
Several crop entries contained typos (e.g. `cassaval`, `wheatn`, `teaa`, trailing spaces). These were standardised to the 8 correct crop names using `.str.strip()` and `.replace()`.

**3. Negative elevation values**
Some fields had physically impossible negative elevations. All values were converted to their absolute equivalent using `.abs()`.

After cleaning, the three expected data integrity checks all pass:
- `len(MD_agric_df['Crop_type'].unique())` → `8`
- `MD_agric_df['Elevation'].min()` → `35.91`
- `MD_agric_df['Annual_yield'].dtype` → `float64`

---

## 📊 Dataset at a Glance

| Attribute | Detail |
|---|---|
| **Total fields surveyed** | 5,654 |
| **Provinces** | Rural_Akatsi, Rural_Amanzi, Rural_Hawassa, Rural_Kilimani, Rural_Sokoto |
| **Crops** | Banana, Cassava, Coffee, Maize, Potato, Rice, Tea, Wheat |
| **Soil types** | Loamy, Peaty, Rocky, Sandy, Silt, Volcanic |
| **Elevation range** | 35.9m – 1,122.3m |
| **Rainfall range** | 103.1mm – 2,470.9mm |
| **Plot sizes** | 0.5 Ha – 15.0 Ha |

---

## 🔍 Analysis Challenges

### Challenge 1 — Crop Distribution (`explore_crop_distribution`)
Filters the dataset by crop type and returns the mean **Rainfall** and **Elevation** as a tuple.

Key findings:
| Crop | Mean Rainfall (mm) | Mean Elevation (m) |
|---|---|---|
| Tea | 1,534.5 | 775.2 |
| Coffee | 1,527.3 | 647.0 |
| Rice | 1,632.4 | 352.9 |
| Wheat | 1,010.3 | 595.8 |
| Maize | 681.0 | 680.6 |
| Potato | 660.3 | 696.3 |

---

### Challenge 2 — Soil Fertility Analysis (`analyse_soil_fertility`)
Groups data by `Soil_type` and returns the mean `Soil_fertility` score (0 = infertile, 1 = very fertile).

| Soil Type | Mean Fertility |
|---|---|
| Silt | **0.653** ✅ Most fertile |
| Volcanic | 0.649 |
| Peaty | 0.605 |
| Sandy | 0.596 |
| Loamy | 0.586 |
| Rocky | 0.582 |

Silt and Volcanic soils are the most fertile in Maji Ndogo — prime candidates for high-value crop deployment.

---

### Challenge 3 — Climate & Geography by Crop (`climate_geography_influence`)
Groups by any column and aggregates mean Elevation, Min temperature, Max temperature, and Rainfall.

When grouped by `Crop_type`, the output reveals distinct climate niches per crop:
- **Banana and Rice** prefer lower elevations with very high rainfall
- **Tea** grows at the highest elevations with cooler average temperatures
- **Maize and Potato** are low-rainfall crops at mid-range elevations

---

### Challenge 4 — Finding the Top Performer (`find_ideal_fields`)
Filters fields with **above-average Standard_yield**, groups by crop type, and counts. Returns the crop name with the highest count of high-performing fields.

**Result: `tea`**

Tea has 682 above-average-yield fields — more than any other crop — making it Maji Ndogo's most consistently high-performing crop.

| Crop | Above-Avg Yield Fields |
|---|---|
| Tea | **682** |
| Potato | 663 |
| Wheat | 517 |
| Rice | 200 |
| Maize | 178 |

---

### Challenge 5 — Ideal Tea Growing Conditions (`find_good_conditions`)
Filters the top crop (tea) by four strict conditions simultaneously:
- Above-average `Standard_yield`
- `Ave_temps` between 12°C and 15°C (inclusive)
- `Pollution_level` below 0.0001

**Result:** 14 fields meet all four criteria (`shape: (14, 17)`).

These 14 fields represent the gold standard — the specific locations in Maji Ndogo where tea cultivation is most likely to succeed under automation.

---

## 💡 Key Insights

1. **Tea is the star crop.** It dominates above-average yield counts and has the most well-defined growing conditions — high elevation, heavy rainfall, cool temperatures, and near-zero pollution.

2. **Soil type matters.** Silt and Volcanic soils outperform the others on fertility. Future field selection should weigh soil type as a primary filter.

3. **Rainfall is the biggest differentiator between crops.** There is a clear split between high-rainfall crops (banana, rice, coffee, tea) and low-rainfall crops (maize, potato, wheat), which maps neatly onto provincial geography.

4. **Only 14 fields tick every box for ideal tea conditions** — pointing to very specific geographic pockets worth prioritising for the first wave of agricultural automation.

---

## 🛠️ Tools & Libraries

| Tool | Purpose |
|---|---|
| `Python 3` | Core language |
| `Pandas` | Data manipulation and analysis |
| `NumPy` | Numerical operations |
| `SQLAlchemy` | SQLite database connection |
| `SQLite` | Database storage (4-table schema) |
| `Matplotlib` (via `df.plot`) | Quick exploratory visualisations |

---

## 🚀 How to Run

1. Clone the repository and ensure `Maji_Ndogo_farm_survey_small.db` is in the same directory as the notebook.
2. Install dependencies:
   ```bash
   pip install pandas numpy sqlalchemy
   ```
3. Open the notebook:
   ```bash
   jupyter notebook Code_challenge_Integrated_Project_P1_student_version.ipynb
   ```
4. Run all cells from top to bottom. The data loading, cleaning, and all five challenge functions are self-contained.

---

## 👤 Author

**Chacha Marwa**
ALX Data Analytics Programme — Integrated Project Part 1
- GitHub: [ChachaMarwaDev](https://github.com/ChachaMarwaDev)
- Portfolio: [chachamarwadev.com](https://chachamarwadev.com)