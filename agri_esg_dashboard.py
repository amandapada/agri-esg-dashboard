import streamlit as st
import pandas as pd
import numpy as np

# -----------------------
# CONFIG
# -----------------------

st.set_page_config(
    page_title="AgriESG Dashboard",
    layout="wide",
)

# Emission factors (placeholder values – adjust with ESG experts)
EF_N = 5.5      # kg CO2e per kg N fertilizer
EF_DIESEL = 2.7 # kg CO2e per litre diesel
EF_ELEC = 0.5   # kg CO2e per kWh electricity

# -----------------------
# HELPER FUNCTIONS
# -----------------------

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["area_ha"] = df["area_ha"].replace(0, np.nan)
    df["yield_tonnes"] = df["yield_tonnes"].replace(0, np.nan)
    df["workers_total"] = df["workers_total"].replace(0, np.nan)

    df["yield_per_ha"] = df["yield_tonnes"] / df["area_ha"]
    df["n_per_ha"] = df["fertilizer_n_kg"] / df["area_ha"]
    df["water_per_tonne"] = df["water_m3"] / df["yield_tonnes"]

    emissions_fertilizer = df["fertilizer_n_kg"] * EF_N
    emissions_diesel = df["diesel_litres"] * EF_DIESEL
    emissions_electric = df["electricity_kwh"] * EF_ELEC

    df["total_emissions"] = emissions_fertilizer + emissions_diesel + emissions_electric
    df["emissions_per_tonne"] = df["total_emissions"] / df["yield_tonnes"]
    df["emissions_per_ha"] = df["total_emissions"] / df["area_ha"]

    df["female_share"] = df["workers_female"] / df["workers_total"]
    df["accidents_per_100_workers"] = (df["accidents_count"] / df["workers_total"]) * 100

    return df


def kpi_card(label: str, value, suffix: str = "", precision: int = 2):
    if pd.isna(value):
        display_value = "N/A"
    else:
        display_value = f"{value:.{precision}f}{suffix}"
    st.metric(label=label, value=display_value)


# -----------------------
# UI LAYOUT
# -----------------------

st.title("🌱 AgriESG Dashboard (MVP)")
st.write("Upload your farm data CSV to generate ESG indicators and a simple dashboard.")

with st.expander("Click to see expected CSV format"):
    st.markdown(
        """
        **Required CSV columns:**

        - `organisation_name`
        - `farm_id`
        - `country`
        - `year`
        - `crop`
        - `area_ha`
        - `yield_tonnes`
        - `fertilizer_n_kg`
        - `diesel_litres`
        - `electricity_kwh`
        - `water_m3`
        - `workers_total`
        - `workers_female`
        - `accidents_count`
        """
    )

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV to see the dashboard.")
    st.stop()

# -----------------------
# READ CSV WITH FALLBACK ENCODINGS
# -----------------------

try:
    raw_df = pd.read_csv(uploaded_file, encoding="utf-8")
except UnicodeDecodeError:
    uploaded_file.seek(0)
    raw_df = pd.read_csv(uploaded_file, encoding="latin1")
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    st.stop()

# -----------------------
# VALIDATE REQUIRED COLUMNS
# -----------------------

required_cols = [
    "organisation_name","farm_id","country","year","crop","area_ha",
    "yield_tonnes","fertilizer_n_kg","diesel_litres","electricity_kwh",
    "water_m3","workers_total","workers_female","accidents_count"
]

missing = [c for c in required_cols if c not in raw_df.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

# -----------------------
# KPI CALCULATION
# -----------------------

df = compute_kpis(raw_df)

st.sidebar.header("Filters")

years = sorted(df["year"].dropna().unique().tolist())
crops = sorted(df["crop"].dropna().unique().tolist())
countries = sorted(df["country"].dropna().unique().tolist())

year_filter = st.sidebar.multiselect("Year", years, default=years)
crop_filter = st.sidebar.multiselect("Crop", crops, default=crops)
country_filter = st.sidebar.multiselect("Country", countries, default=countries)

filtered_df = df[
    df["year"].isin(year_filter)
    & df["crop"].isin(crop_filter)
    & df["country"].isin(country_filter)
]

if filtered_df.empty:
    st.warning("No data after applying filters.")
    st.stop()

# -----------------------
# KPI CARDS
# -----------------------

st.subheader("Key Indicators (filtered)")

agg = filtered_df.copy()

total_area = agg["area_ha"].sum()
total_yield = agg["yield_tonnes"].sum()
total_emissions = agg["total_emissions"].sum()
total_workers = agg["workers_total"].sum()
total_female_workers = agg["workers_female"].sum()
total_accidents = agg["accidents_count"].sum()

yield_per_ha = total_yield / total_area if total_area else np.nan
emissions_per_tonne = total_emissions / total_yield if total_yield else np.nan
water_per_tonne = agg["water_m3"].sum() / total_yield if total_yield else np.nan
female_share_overall = total_female_workers / total_workers if total_workers else np.nan
accidents_per_100_workers_overall = (total_accidents / total_workers * 100) if total_workers else np.nan

col1, col2, col3, col4 = st.columns(4)

with col1: kpi_card("Yield per ha (t/ha)", yield_per_ha)
with col2: kpi_card("Emissions per tonne (kg CO₂e/t)", emissions_per_tonne, precision=1)
with col3: kpi_card("Water per tonne (m³/t)", water_per_tonne, precision=1)
with col4: kpi_card("Female workforce (%)", female_share_overall*100 if not pd.isna(female_share_overall) else np.nan, suffix="%", precision=0)

col5, col6, col7, col8 = st.columns(4)

with col5: kpi_card("Total emissions (kg CO₂e)", total_emissions, precision=0)
with col6: kpi_card("Total area (ha)", total_area, precision=1)
with col7: kpi_card("Total workers", total_workers, precision=0)
with col8: kpi_card("Accidents per 100 workers", accidents_per_100_workers_overall, precision=2)

# -----------------------
# CHARTS
# -----------------------

st.markdown("---")
st.subheader("Emissions & Productivity by Farm")

emissions_farm = filtered_df.groupby("farm_id", as_index=False)["total_emissions"].sum()
yield_farm = filtered_df.groupby("farm_id", as_index=False)["yield_tonnes"].sum()

c1, c2 = st.columns(2)

with c1:
    st.markdown("**Emissions per farm (kg CO₂e)**")
    st.bar_chart(emissions_farm.set_index("farm_id")["total_emissions"])

with c2:
    st.markdown("**Yield per farm (tonnes)**")
    st.bar_chart(yield_farm.set_index("farm_id")["yield_tonnes"])

st.markdown("---")
st.subheader("Detailed data")
st.dataframe(filtered_df, use_container_width=True)
