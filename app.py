import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import os

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Maji Ndogo · Agricultural Analysis",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f1117; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #21262d;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 16px;
    }

    /* Headers */
    h1, h2, h3 { color: #e6edf3; }

    /* Section divider */
    .section-header {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #7d8590;
        margin-bottom: 0.4rem;
    }

    /* Insight box */
    .insight-box {
        background: linear-gradient(135deg, #1a2332, #162032);
        border-left: 3px solid #238636;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 8px 0;
        color: #cdd9e5;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    /* Tab styling */
    button[data-baseweb="tab"] {
        font-size: 0.85rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ─── CROP EMOJI MAP ───────────────────────────────────────────────────────────
CROP_EMOJI = {
    "tea": "🍵", "wheat": "🌾", "potato": "🥔", "cassava": "🫚",
    "banana": "🍌", "coffee": "☕", "rice": "🍚", "maize": "🌽"
}

CROP_COLORS = {
    "tea": "#2ea043", "wheat": "#f0c33c", "potato": "#c97a2a",
    "cassava": "#8b5cf6", "banana": "#facc15", "coffee": "#92400e",
    "rice": "#38bdf8", "maize": "#fb923c"
}

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data(db_path: str) -> pd.DataFrame:
    engine = create_engine(f"sqlite:///{db_path}")
    sql_query = """
        SELECT
            g.Field_ID, g.Elevation, g.Latitude, g.Longitude, g.Location, g.Slope,
            w.Rainfall, w.Min_temperature_C, w.Max_temperature_C, w.Ave_temps,
            s.Soil_fertility, s.Soil_type, s.pH,
            f.Pollution_level, f.Plot_size, f.Crop_type, f.Annual_yield, f.Standard_yield
        FROM geographic_features g
        INNER JOIN weather_features w ON g.Field_ID = w.Field_ID
        INNER JOIN soil_and_crop_features s ON g.Field_ID = s.Field_ID
        INNER JOIN farm_management_features f ON g.Field_ID = f.Field_ID;
    """
    with engine.connect() as conn:
        df = pd.read_sql_query(text(sql_query), conn)

    # Clean
    df.drop(columns="Field_ID", inplace=True)
    df.rename(columns={"Crop_type": "Annual_yield", "Annual_yield": "Crop_type"}, inplace=True)
    df["Crop_type"] = (
        df["Crop_type"]
        .str.strip()
        .replace({"cassaval": "cassava", "wheatn": "wheat", "teaa": "tea"})
    )
    df["Annual_yield"] = pd.to_numeric(df["Annual_yield"], errors="coerce")
    df["Elevation"] = df["Elevation"].abs()
    return df


# ─── DB PATH RESOLUTION ───────────────────────────────────────────────────────
DB_FILENAME = "Maji_Ndogo_farm_survey_small.db"
CANDIDATE_PATHS = [
    DB_FILENAME,
    os.path.join(os.path.dirname(__file__), DB_FILENAME),
    os.path.join(os.path.dirname(__file__), "data", DB_FILENAME),
]


def find_db() -> str | None:
    for p in CANDIDATE_PATHS:
        if os.path.exists(p):
            return p
    return None


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌱 Maji Ndogo")
    st.markdown("**Agricultural Analysis Dashboard**")
    st.divider()

    db_path = find_db()
    if not db_path:
        st.error("Database not found. Upload it below.")
        uploaded = st.file_uploader("Upload .db file", type=["db"])
        if uploaded:
            tmp = f"/tmp/{DB_FILENAME}"
            with open(tmp, "wb") as f:
                f.write(uploaded.read())
            db_path = tmp
    else:
        st.success(f"Database connected")

    if db_path:
        df = load_data(db_path)
        all_crops = sorted(df["Crop_type"].unique())
        all_locations = sorted(df["Location"].unique())
        all_soils = sorted(df["Soil_type"].unique())

        st.divider()
        st.markdown('<p class="section-header">Filters</p>', unsafe_allow_html=True)

        selected_locations = st.multiselect(
            "Province", all_locations, default=all_locations,
            help="Filter all charts by province"
        )
        selected_crops = st.multiselect(
            "Crop type", all_crops, default=all_crops
        )
        selected_soils = st.multiselect(
            "Soil type", all_soils, default=all_soils
        )

        df_filtered = df[
            df["Location"].isin(selected_locations) &
            df["Crop_type"].isin(selected_crops) &
            df["Soil_type"].isin(selected_soils)
        ]

        st.divider()
        st.caption(f"Showing **{len(df_filtered):,}** of {len(df):,} fields")

    st.divider()
    page = st.radio(
        "Navigation",
        ["📊 Overview", "🌾 Crop Explorer", "🪨 Soil Fertility",
         "🌦️ Climate & Geography", "🏆 Top Performers", "🗺️ Field Map"],
        label_visibility="collapsed"
    )

# ─── GUARD ────────────────────────────────────────────────────────────────────
if not db_path:
    st.info("👈 Please upload the database file in the sidebar to get started.")
    st.stop()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Overview")
    st.caption("High-level snapshot of the Maji Ndogo farm survey dataset")

    # KPI row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Fields surveyed", f"{len(df_filtered):,}")
    c2.metric("Crop types", df_filtered["Crop_type"].nunique())
    c3.metric("Provinces", df_filtered["Location"].nunique())
    c4.metric("Avg Standard Yield", f"{df_filtered['Standard_yield'].mean():.3f}")
    c5.metric("Avg Rainfall (mm)", f"{df_filtered['Rainfall'].mean():,.0f}")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Fields per Crop")
        counts = df_filtered["Crop_type"].value_counts().reset_index()
        counts.columns = ["Crop", "Fields"]
        counts["emoji"] = counts["Crop"].map(CROP_EMOJI)
        counts["label"] = counts["emoji"] + " " + counts["Crop"]
        fig = px.bar(
            counts, x="Fields", y="label", orientation="h",
            color="Crop",
            color_discrete_map=CROP_COLORS,
            template="plotly_dark",
            labels={"label": ""},
        )
        fig.update_layout(
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Standard Yield Distribution")
        fig2 = px.histogram(
            df_filtered, x="Standard_yield", nbins=30,
            color="Crop_type", color_discrete_map=CROP_COLORS,
            template="plotly_dark",
            labels={"Standard_yield": "Standard Yield", "Crop_type": "Crop"},
        )
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            bargap=0.05
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Mean Yield per Crop")
    mean_yield = (
        df_filtered.groupby("Crop_type")["Standard_yield"]
        .mean()
        .reset_index()
        .sort_values("Standard_yield", ascending=False)
    )
    mean_yield["emoji"] = mean_yield["Crop_type"].map(CROP_EMOJI)
    mean_yield["label"] = mean_yield["emoji"] + " " + mean_yield["Crop_type"]
    fig3 = px.bar(
        mean_yield, x="label", y="Standard_yield",
        color="Crop_type", color_discrete_map=CROP_COLORS,
        template="plotly_dark",
        labels={"label": "Crop", "Standard_yield": "Mean Standard Yield"},
        text_auto=".3f",
    )
    fig3.update_layout(
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig3, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — CROP EXPLORER  (Challenge 1)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🌾 Crop Explorer":
    st.title("🌾 Crop Explorer")
    st.caption("Challenge 1 — explore rainfall and elevation conditions per crop")

    def explore_crop_distribution(df, crop_filter):
        filtered = df[df["Crop_type"] == crop_filter]
        return filtered["Rainfall"].mean(), filtered["Elevation"].mean()

    selected_crop = st.selectbox(
        "Select a crop to explore",
        all_crops,
        format_func=lambda c: f"{CROP_EMOJI.get(c, '')} {c.title()}"
    )

    rain, elev = explore_crop_distribution(df_filtered, selected_crop)
    crop_df = df_filtered[df_filtered["Crop_type"] == selected_crop]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mean Rainfall (mm)", f"{rain:,.1f}")
    c2.metric("Mean Elevation (m)", f"{elev:,.1f}")
    c3.metric("Fields", f"{len(crop_df):,}")
    c4.metric("Mean Std Yield", f"{crop_df['Standard_yield'].mean():.3f}")

    st.divider()
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Rainfall vs Elevation")
        fig = px.scatter(
            crop_df, x="Rainfall", y="Elevation",
            color="Standard_yield",
            color_continuous_scale="Greens",
            template="plotly_dark",
            labels={"Standard_yield": "Std Yield"},
            opacity=0.7,
            hover_data=["Location", "Soil_type"],
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Rainfall distribution")
        fig2 = px.histogram(
            crop_df, x="Rainfall", nbins=25,
            template="plotly_dark",
            color_discrete_sequence=[CROP_COLORS.get(selected_crop, "#2ea043")],
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Comparison across all crops")
    compare = (
        df_filtered.groupby("Crop_type")[["Rainfall", "Elevation"]]
        .mean()
        .reset_index()
        .sort_values("Rainfall", ascending=False)
    )
    compare["highlight"] = compare["Crop_type"] == selected_crop
    fig3 = px.scatter(
        compare, x="Elevation", y="Rainfall",
        color="Crop_type", color_discrete_map=CROP_COLORS,
        text="Crop_type", template="plotly_dark",
        size=[20] * len(compare),
        labels={"Elevation": "Mean Elevation (m)", "Rainfall": "Mean Rainfall (mm)"},
    )
    fig3.update_traces(textposition="top center")
    fig3.update_layout(
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown(
        f'<div class="insight-box">💡 <b>{selected_crop.title()}</b> fields average '
        f'<b>{rain:,.0f} mm</b> of rainfall and grow at a mean elevation of <b>{elev:,.0f} m</b>. '
        f'That places it among {"high" if rain > 1200 else "low"}-rainfall crops at '
        f'{"higher" if elev > 650 else "lower"} elevations.</div>',
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SOIL FERTILITY  (Challenge 2)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🪨 Soil Fertility":
    st.title("🪨 Soil Fertility")
    st.caption("Challenge 2 — mean soil fertility grouped by soil type")

    def analyse_soil_fertility(df):
        return df.groupby("Soil_type")["Soil_fertility"].mean().sort_values(ascending=False)

    fertility = analyse_soil_fertility(df_filtered).reset_index()
    fertility.columns = ["Soil_type", "Mean_fertility"]

    col_l, col_r = st.columns([1.2, 1])

    with col_l:
        st.subheader("Mean Fertility by Soil Type")
        fig = px.bar(
            fertility, x="Mean_fertility", y="Soil_type",
            orientation="h", template="plotly_dark",
            color="Mean_fertility", color_continuous_scale="Greens",
            text_auto=".4f",
            labels={"Mean_fertility": "Mean Soil Fertility (0–1)", "Soil_type": ""},
        )
        fig.update_layout(
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Fertility × pH")
        fig2 = px.scatter(
            df_filtered, x="pH", y="Soil_fertility",
            color="Soil_type", template="plotly_dark",
            opacity=0.5,
            labels={"Soil_fertility": "Soil Fertility", "pH": "Soil pH"},
        )
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Fertility breakdown by Province")
    by_prov = (
        df_filtered.groupby(["Location", "Soil_type"])["Soil_fertility"]
        .mean()
        .reset_index()
    )
    fig3 = px.bar(
        by_prov, x="Location", y="Soil_fertility",
        color="Soil_type", barmode="group", template="plotly_dark",
        labels={"Soil_fertility": "Mean Fertility", "Location": "Province"},
    )
    fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig3, use_container_width=True)

    best = fertility.iloc[0]
    st.markdown(
        f'<div class="insight-box">💡 <b>{best["Soil_type"]}</b> soil has the highest mean fertility '
        f'at <b>{best["Mean_fertility"]:.4f}</b>, making it the top candidate for high-value crop placement. '
        f'Rocky soil is the least fertile at {fertility.iloc[-1]["Mean_fertility"]:.4f}.</div>',
        unsafe_allow_html=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — CLIMATE & GEOGRAPHY  (Challenge 3)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🌦️ Climate & Geography":
    st.title("🌦️ Climate & Geography")
    st.caption("Challenge 3 — climate and geography statistics grouped by any column")

    def climate_geography_influence(df, column):
        return (
            df.groupby(column)[["Elevation", "Min_temperature_C", "Max_temperature_C", "Rainfall"]]
            .mean()
            .round(2)
        )

    group_by_col = st.radio(
        "Group by", ["Crop_type", "Location", "Soil_type"],
        horizontal=True,
        format_func=lambda x: x.replace("_", " ").title()
    )

    result = climate_geography_influence(df_filtered, group_by_col).reset_index()

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Elevation")
        fig1 = px.bar(
            result, x=group_by_col, y="Elevation",
            color=group_by_col,
            color_discrete_map=CROP_COLORS if group_by_col == "Crop_type" else None,
            template="plotly_dark", text_auto=".1f",
            labels={"Elevation": "Mean Elevation (m)"},
        )
        fig1.update_layout(
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_r:
        st.subheader("Rainfall")
        fig2 = px.bar(
            result, x=group_by_col, y="Rainfall",
            color=group_by_col,
            color_discrete_map=CROP_COLORS if group_by_col == "Crop_type" else None,
            template="plotly_dark", text_auto=".0f",
            labels={"Rainfall": "Mean Rainfall (mm)"},
        )
        fig2.update_layout(
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Temperature Range")
    fig3 = go.Figure()
    for _, row in result.iterrows():
        label = str(row[group_by_col])
        color = CROP_COLORS.get(label, "#7d8590")
        fig3.add_trace(go.Bar(
            name=label,
            x=[label],
            y=[row["Max_temperature_C"] - row["Min_temperature_C"]],
            base=row["Min_temperature_C"],
            marker_color=color,
            text=f'{row["Min_temperature_C"]:.1f}° – {row["Max_temperature_C"]:.1f}°',
            textposition="inside",
        ))
    fig3.update_layout(
        template="plotly_dark", showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Temperature (°C)", barmode="group"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Summary Table")
    st.dataframe(
        result.set_index(group_by_col).style.background_gradient(cmap="Greens", axis=0),
        use_container_width=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — TOP PERFORMERS  (Challenges 4 & 5)
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🏆 Top Performers":
    st.title("🏆 Top Performers")
    st.caption("Challenges 4 & 5 — finding the best crop and its ideal growing conditions")

    # Challenge 4
    def find_ideal_fields(df):
        avg_yield = df["Standard_yield"].mean()
        above_avg = df[df["Standard_yield"] > avg_yield]
        grouped = (
            above_avg.groupby("Crop_type")
            .count()
            .sort_values(by="Standard_yield", ascending=False)
        )
        return grouped.index[0], grouped["Standard_yield"]

    top_crop, top_counts = find_ideal_fields(df_filtered)
    avg_yield = df_filtered["Standard_yield"].mean()

    st.subheader("Challenge 4 — Fields with Above-Average Yield")

    col_l, col_r = st.columns([1.6, 1])

    with col_l:
        top_df = top_counts.reset_index()
        top_df.columns = ["Crop", "Above-avg fields"]
        top_df["emoji"] = top_df["Crop"].map(CROP_EMOJI)
        top_df["label"] = top_df["emoji"] + " " + top_df["Crop"]
        fig = px.bar(
            top_df, x="label", y="Above-avg fields",
            color="Crop", color_discrete_map=CROP_COLORS,
            template="plotly_dark", text_auto=True,
            labels={"label": ""},
        )
        fig.update_layout(
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown(f"### 🏆 Top crop: `{top_crop.title()}`")
        st.metric("Above-avg yield fields", f"{top_counts.iloc[0]:,}")
        st.metric("Overall avg Standard Yield", f"{avg_yield:.4f}")
        st.markdown(
            f'<div class="insight-box">💡 <b>{top_crop.title()}</b> has the most fields '
            f'exceeding the dataset average yield of {avg_yield:.3f}. It is Maji Ndogo\'s '
            f'most consistently high-performing crop.</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Challenge 5
    st.subheader("Challenge 5 — Ideal Growing Conditions")

    def find_good_conditions(df, crop_type, min_temp=12, max_temp=15, max_pollution=0.0001):
        avg = df["Standard_yield"].mean()
        return df[
            (df["Crop_type"] == crop_type) &
            (df["Standard_yield"] > avg) &
            (df["Ave_temps"] >= min_temp) &
            (df["Ave_temps"] <= max_temp) &
            (df["Pollution_level"] < max_pollution)
        ]

    c1, c2, c3 = st.columns(3)
    with c1:
        ch5_crop = st.selectbox(
            "Crop", all_crops,
            index=all_crops.index(top_crop) if top_crop in all_crops else 0,
            format_func=lambda c: f"{CROP_EMOJI.get(c,'')} {c.title()}"
        )
    with c2:
        temp_range = st.slider("Ave temperature range (°C)", 10.0, 18.0, (12.0, 15.0), 0.5)
    with c3:
        max_poll = st.number_input(
            "Max pollution level", min_value=0.0, max_value=1.0,
            value=0.0001, step=0.0001, format="%.4f"
        )

    ideal = find_good_conditions(df_filtered, ch5_crop, temp_range[0], temp_range[1], max_poll)

    st.metric("Fields meeting all conditions", f"{len(ideal):,}")

    if len(ideal) > 0:
        col_l, col_r = st.columns(2)
        with col_l:
            fig2 = px.scatter(
                ideal, x="Rainfall", y="Elevation",
                color="Standard_yield", color_continuous_scale="Greens",
                template="plotly_dark", size="Plot_size",
                hover_data=["Location", "Soil_type", "Ave_temps", "Pollution_level"],
                labels={"Standard_yield": "Std Yield"},
            )
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)

        with col_r:
            by_prov = ideal["Location"].value_counts().reset_index()
            by_prov.columns = ["Province", "Fields"]
            fig3 = px.pie(
                by_prov, names="Province", values="Fields",
                template="plotly_dark", hole=0.45,
                color_discrete_sequence=px.colors.sequential.Greens[::-1],
            )
            fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Ideal fields — data table")
        st.dataframe(
            ideal[["Location", "Soil_type", "Elevation", "Rainfall",
                   "Ave_temps", "Pollution_level", "Standard_yield", "Plot_size"]]
            .reset_index(drop=True)
            .style.background_gradient(subset=["Standard_yield"], cmap="Greens"),
            use_container_width=True,
        )
    else:
        st.warning("No fields match the current filter conditions. Try widening the temperature range or pollution threshold.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — FIELD MAP
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "🗺️ Field Map":
    st.title("🗺️ Field Map")
    st.caption("Geographic distribution of fields by crop type")

    color_by = st.radio(
        "Colour points by",
        ["Crop_type", "Standard_yield", "Rainfall", "Soil_fertility"],
        horizontal=True,
        format_func=lambda x: x.replace("_", " ").title()
    )

    sample = df_filtered.sample(min(2000, len(df_filtered)), random_state=42)

    if color_by == "Crop_type":
        fig = px.scatter_mapbox(
            sample, lat="Latitude", lon="Longitude",
            color="Crop_type", color_discrete_map=CROP_COLORS,
            hover_data=["Location", "Soil_type", "Elevation", "Standard_yield"],
            zoom=5, height=600, template="plotly_dark",
        )
    else:
        fig = px.scatter_mapbox(
            sample, lat="Latitude", lon="Longitude",
            color=color_by, color_continuous_scale="Greens",
            hover_data=["Crop_type", "Location", "Soil_type"],
            zoom=5, height=600, template="plotly_dark",
        )

    fig.update_layout(
        mapbox_style="carto-darkmatter",
        paper_bgcolor="rgba(0,0,0,0)",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Showing a random sample of {len(sample):,} fields. Change sidebar filters to narrow down.")