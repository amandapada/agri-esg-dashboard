import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------
# CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Farm ESG Analysis",
    layout="wide",
)

# Emission factors (simple placeholders – refine with experts later)
EF_N = 6.0          # kg CO2e per kg nitrogen fertilizer
EF_DIESEL = 2.7     # kg CO2e per litre diesel
EF_ELEC = 0.5       # kg CO2e per kWh electricity
EF_CATTLE_CO2E = 3000  # kg CO2e per head of cattle per year (rough placeholder)


# -----------------------------------
# HELPER FUNCTIONS
# -----------------------------------

def safe_div(a, b):
    """Avoid divide-by-zero."""
    if b is None or b == 0 or pd.isna(b):
        return np.nan
    return a / b


def to_bool(x):
    """Convert yes/no/True/False text to bool."""
    if isinstance(x, str):
        x = x.strip().lower()
        if x in ["yes", "y", "true", "1"]:
            return True
        if x in ["no", "n", "false", "0"]:
            return False
    return bool(x) if not pd.isna(x) else False


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Add KPI columns to the dataframe."""
    df = df.copy()

    # Make sure numeric columns are numeric
    numeric_cols = [
        "land_area_ha", "total_yield_tonnes", "nitrogen_kg", "phosphate_kg",
        "potash_kg", "organic_manure_kg", "pesticide_liters",
        "herbicide_liters", "fungicide_liters", "diesel_litres",
        "electricity_kwh", "irrigation_water_m3", "soil_organic_matter_pct",
        "soil_ph", "workers_total", "workers_female", "training_hours",
        "accidents_count", "cattle_headcount", "daily_milk_litres",
        "feed_kg_day", "manure_tonnes_year", "vet_visits_per_year"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Core productivity
    df["yield_per_ha"] = df.apply(
        lambda r: safe_div(r.get("total_yield_tonnes"), r.get("land_area_ha")),
        axis=1,
    )

    # Water & fertilizer efficiency
    df["water_per_tonne"] = df.apply(
        lambda r: safe_div(r.get("irrigation_water_m3"), r.get("total_yield_tonnes")),
        axis=1,
    )
    df["n_per_ha"] = df.apply(
        lambda r: safe_div(r.get("nitrogen_kg"), r.get("land_area_ha")),
        axis=1,
    )

    # Chemical intensity per ha
    for chem in ["pesticide_liters", "herbicide_liters", "fungicide_liters"]:
        if chem in df.columns:
            df[f"{chem}_per_ha"] = df.apply(
                lambda r: safe_div(r.get(chem), r.get("land_area_ha")),
                axis=1,
            )

    # Emissions: fertilizer, diesel, electricity, cattle
    fert_em = df.get("nitrogen_kg", 0) * EF_N
    diesel_em = df.get("diesel_litres", 0) * EF_DIESEL
    elec_em = df.get("electricity_kwh", 0) * EF_ELEC
    cattle_em = df.get("cattle_headcount", 0) * EF_CATTLE_CO2E if "cattle_headcount" in df.columns else 0

    df["emissions_fertilizer"] = fert_em
    df["emissions_diesel"] = diesel_em
    df["emissions_electricity"] = elec_em
    df["emissions_livestock"] = cattle_em
    df["total_emissions"] = fert_em + diesel_em + elec_em + cattle_em

    df["emissions_per_ha"] = df.apply(
        lambda r: safe_div(r.get("total_emissions"), r.get("land_area_ha")),
        axis=1,
    )
    df["emissions_per_tonne"] = df.apply(
        lambda r: safe_div(r.get("total_emissions"), r.get("total_yield_tonnes")),
        axis=1,
    )

    # Social metrics
    df["female_share"] = df.apply(
        lambda r: safe_div(r.get("workers_female"), r.get("workers_total")),
        axis=1,
    )
    df["accidents_per_100_workers"] = df.apply(
        lambda r: safe_div(r.get("accidents_count") * 100, r.get("workers_total")),
        axis=1,
    )
    df["training_hours_per_worker"] = df.apply(
        lambda r: safe_div(r.get("training_hours"), r.get("workers_total")),
        axis=1,
    )

    # Soil health score (0–100, simple rules)
    def soil_score(row):
        som = row.get("soil_organic_matter_pct")
        ph = row.get("soil_ph")
        score = 50.0

        # Soil organic matter
        if pd.notna(som):
            if som < 1.5:
                score -= 15
            elif som > 3:
                score += 10
            else:
                score += 5

        # pH
        if pd.notna(ph):
            if 6 <= ph <= 7.5:
                score += 10
            else:
                score -= 10

        return max(0, min(100, score))

    if "soil_organic_matter_pct" in df.columns:
        df["soil_health_score"] = df.apply(soil_score, axis=1)
    else:
        df["soil_health_score"] = np.nan

    # Regenerative practices score (0–100)
    def regen_score(row):
        score = 50

        if to_bool(row.get("crop_rotation")):
            score += 15
        if to_bool(row.get("cover_cropping")):
            score += 15
        if row.get("organic_manure_kg", 0) > 0:
            score += 10
        # ✅ fixed irrigation line
        if str(row.get("irrigation_method", "")).lower() == "drip":
            score += 10

        return max(0, min(100, score))

    df["regen_practice_score"] = df.apply(regen_score, axis=1)

    # Social score
    def social_score(row):
        score = 50
        female_share = row.get("female_share")
        if pd.notna(female_share):
            if female_share >= 0.4:
                score += 10
            elif female_share < 0.2:
                score -= 10
        if row.get("accidents_per_100_workers", 0) == 0:
            score += 15
        elif row.get("accidents_per_100_workers", 0) > 10:
            score -= 15
        if row.get("training_hours_per_worker", 0) >= 5:
            score += 10
        return max(0, min(100, score))

    df["social_score"] = df.apply(social_score, axis=1)

    # Governance score
    def gov_score(row):
        score = 50
        if to_bool(row.get("farm_safety_policy")):
            score += 10
        if to_bool(row.get("pesticide_handling_training")):
            score += 10
        if to_bool(row.get("grievance_mechanism")):
            score += 10
        cert = str(row.get("certification", "")).strip().lower()
        if cert not in ["", "none", "nan"]:
            score += 15
        return max(0, min(100, score))

    df["governance_score"] = df.apply(gov_score, axis=1)

    # Overall ESG score (simple average)
    df["esg_score"] = df[[
        "soil_health_score",
        "regen_practice_score",
        "social_score",
        "governance_score",
    ]].mean(axis=1)

    return df


def kpi_card(label, value, suffix="", precision=2):
    if value is None or pd.isna(value):
        txt = "N/A"
    else:
        txt = f"{value:.{precision}f}{suffix}"
    st.metric(label, txt)


def generate_insights(row: pd.Series):
    """Return a list of short text insights for a single farm."""
    insights = []

    # Emissions intensity
    if not pd.isna(row["emissions_per_tonne"]):
        if row["emissions_per_tonne"] > 500:
            insights.append(
                f"High emissions intensity ({row['emissions_per_tonne']:.0f} kg CO₂e per tonne of product). "
                "Consider reducing nitrogen fertilizer or diesel use."
            )
        else:
            insights.append(
                f"Emissions intensity ({row['emissions_per_tonne']:.0f} kg CO₂e per tonne) is moderate for a smallholder farm."
            )

    # Emissions source breakdown
    fert_share = safe_div(row["emissions_fertilizer"], row["total_emissions"])
    if fert_share and fert_share > 0.5:
        insights.append(
            f"Fertilizer is the main emissions source ({fert_share*100:.0f}% of total). "
            "Improving nitrogen use efficiency could significantly reduce emissions."
        )

    # Water
    if not pd.isna(row["water_per_tonne"]):
        if row["water_per_tonne"] > 150:
            insights.append(
                f"Water use per tonne ({row['water_per_tonne']:.1f} m³/t) is high. "
                "Upgrading irrigation or improving scheduling could reduce water demand."
            )
        else:
            insights.append(
                f"Water productivity ({row['water_per_tonne']:.1f} m³/t) is relatively efficient for irrigated crops."
            )

    # Soil health
    if not pd.isna(row["soil_health_score"]):
        if row["soil_health_score"] < 50:
            insights.append(
                "Soil health score is low. Increasing organic matter (manure/compost, cover crops) could improve soil function and resilience."
            )
        else:
            insights.append(
                "Soil health score is reasonably strong. Maintaining organic inputs and careful tillage will help keep soils productive."
            )

    # Regenerative practices
    if row["regen_practice_score"] < 50:
        insights.append(
            "Regenerative practices are limited. Crop rotation, cover cropping and organic inputs could strengthen long-term sustainability."
        )
    else:
        insights.append(
            "You already apply several regenerative practices, which supports long-term soil and ecosystem health."
        )

    # Social
    if not pd.isna(row["female_share"]):
        if row["female_share"] < 0.25:
            insights.append(
                f"Female participation in the workforce is low ({row['female_share']*100:.0f}%). "
                "Encouraging more inclusive hiring and training could improve social outcomes."
            )

    if row["accidents_per_100_workers"] > 0:
        insights.append(
            f"There were {row['accidents_count']} recorded accidents. "
            "Regular safety training and protective equipment could reduce this risk."
        )
    else:
        insights.append(
            "No accidents were reported, which is positive from a worker safety perspective."
        )

    # Governance / certification
    cert = str(row.get("certification", "")).strip()
    if cert in ["", "None", "none"]:
        insights.append(
            "No current certification recorded. If you plan to access premium markets, exploring schemes like Organic, GlobalG.A.P or Rainforest Alliance may be valuable."
        )
    else:
        insights.append(
            f"The farm holds a certification ({cert}), which can support market access and ESG credibility."
        )

    return insights


# -----------------------------------
# UI
# -----------------------------------

st.title("🌱 Farm-Level ESG Analysis")
st.write(
    "Upload your farm ESG dataset, then select a farm to see detailed sustainability analysis "
    "(environmental, social, and governance)."
)

with st.expander("Expected key columns (minimum)"):
    st.markdown(
        """
        **Required columns for this analysis:**

        - `farm_id`
        - `farm_name`
        - `country`
        - `year`
        - `crop_type`
        - `land_area_ha`
        - `total_yield_tonnes`
        - `nitrogen_kg`
        - `diesel_litres`
        - `electricity_kwh`
        - `irrigation_water_m3`
        - `workers_total`
        - `workers_female`
        - `accidents_count`

        **Optional (used if present):**

        - `phosphate_kg`, `potash_kg`, `organic_manure_kg`
        - `pesticide_liters`, `herbicide_liters`, `fungicide_liters`
        - `soil_organic_matter_pct`, `soil_ph`
        - `crop_rotation`, `cover_cropping`
        - `training_hours`, `living_wage_paid`
        - `certification`, `farm_safety_policy`, `pesticide_handling_training`, `grievance_mechanism`
        - `cattle_headcount`, `daily_milk_litres`, `feed_kg_day`, `manure_tonnes_year`, `vet_visits_per_year`
        """
    )

uploaded = st.file_uploader("Upload farm ESG CSV", type=["csv"])

if uploaded is None:
    st.info("Upload a CSV file to begin.")
    raise SystemExit

# Read CSV with encoding fallback
try:
    data = pd.read_csv(uploaded, encoding="utf-8")
except UnicodeDecodeError:
    uploaded.seek(0)
    data = pd.read_csv(uploaded, encoding="latin1")
except Exception as e:
    st.error(f"Error reading CSV: {e}")
    raise SystemExit

# Check required columns
required_cols = [
    "farm_id", "farm_name", "country", "year", "crop_type",
    "land_area_ha", "total_yield_tonnes", "nitrogen_kg",
    "diesel_litres", "electricity_kwh", "irrigation_water_m3",
    "workers_total", "workers_female", "accidents_count"
]

missing = [c for c in required_cols if c not in data.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}")
    raise SystemExit

# Compute KPIs for all farms
data_kpi = compute_kpis(data)

# Farm selection
data_kpi["farm_label"] = data_kpi["farm_name"].astype(str) + " (" + data_kpi["farm_id"].astype(str) + ")"
farm_options = data_kpi["farm_label"].tolist()
selected_label = st.selectbox("Select a farm to analyse", farm_options)

farm_row = data_kpi[data_kpi["farm_label"] == selected_label].iloc[0]

st.markdown(f"### 📍 Farm: **{farm_row['farm_name']}** — {farm_row['country']} ({farm_row['year']})")
st.caption(f"Crop type: {farm_row.get('crop_type', 'N/A')}")

# -----------------------------------
# KPI CARDS
# -----------------------------------
st.subheader("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Yield per ha (t/ha)", farm_row["yield_per_ha"])
with col2:
    kpi_card("Emissions per tonne (kg CO₂e/t)", farm_row["emissions_per_tonne"], precision=1)
with col3:
    kpi_card("Water per tonne (m³/t)", farm_row["water_per_tonne"], precision=1)
with col4:
    kpi_card(
        "Female workforce (%)",
        farm_row["female_share"] * 100 if not pd.isna(farm_row["female_share"]) else np.nan,
        suffix="%",
        precision=0,
    )

col5, col6, col7, col8 = st.columns(4)
with col5:
    kpi_card("Total emissions (kg CO₂e)", farm_row["total_emissions"], precision=0)
with col6:
    kpi_card("Land area (ha)", farm_row["land_area_ha"], precision=1)
with col7:
    kpi_card("Total workers", farm_row["workers_total"], precision=0)
with col8:
    kpi_card("Accidents per 100 workers", farm_row["accidents_per_100_workers"], precision=2)

# ESG scores
st.subheader("ESG Scores")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Soil health score", farm_row["soil_health_score"], suffix="/100", precision=0)
with c2:
    kpi_card("Regenerative practices", farm_row["regen_practice_score"], suffix="/100", precision=0)
with c3:
    kpi_card("Social score", farm_row["social_score"], suffix="/100", precision=0)
with c4:
    kpi_card("Governance score", farm_row["governance_score"], suffix="/100", precision=0)
with c5:
    kpi_card("Overall ESG score", farm_row["esg_score"], suffix="/100", precision=0)

# -----------------------------------
# EMISSIONS BREAKDOWN & EFFICIENCY
# -----------------------------------
st.markdown("---")
st.subheader("Emissions Breakdown & Efficiency")

left, right = st.columns(2)

with left:
    st.markdown("**Emissions by source (kg CO₂e)**")
    em_df = pd.DataFrame({
        "source": ["Fertilizer", "Diesel", "Electricity", "Livestock"],
        "emissions": [
            farm_row["emissions_fertilizer"],
            farm_row["emissions_diesel"],
            farm_row["emissions_electricity"],
            farm_row["emissions_livestock"],
        ],
    }).set_index("source")
    st.bar_chart(em_df)

with right:
    st.markdown("**Resource efficiency**")
    eff_df = pd.DataFrame({
        "metric": ["Yield per ha (t/ha)", "N per ha (kg/ha)", "Water per tonne (m³/t)"],
        "value": [
            farm_row["yield_per_ha"],
            farm_row["n_per_ha"],
            farm_row["water_per_tonne"],
        ],
    }).set_index("metric")
    st.bar_chart(eff_df)

# -----------------------------------
# INSIGHTS
# -----------------------------------
st.markdown("---")
st.subheader("Automatic ESG Insights for this Farm")

insights = generate_insights(farm_row)
for i in insights:
    st.markdown(f"- {i}")

# Raw data for this farm
with st.expander("See raw data for this farm"):
    st.write(farm_row.to_frame().T)
