# =======================================
# 🌱 AgriESG — Farm-Level ESG Dashboard
# =======================================

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---------------------------------------------------
# Streamlit Page Config (white, wide)
# ---------------------------------------------------
st.set_page_config(
    page_title="AgriESG — Farm ESG Analysis",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------
# Global styling (white background + cards)
# ---------------------------------------------------
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: #ffffff !important;
        color: #111827;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
    }
    .kpi-card {
        padding: 1.0rem 1.1rem;
        border-radius: 18px;
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }
    .kpi-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #6b7280;
        margin-bottom: 0.25rem;
    }
    .kpi-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #111827;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.15rem;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #111827;
        margin-top: 1.3rem;
        margin-bottom: 0.6rem;
    }
    .gov-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        background: #ecfdf3;
        color: #15803d;
        font-size: 0.78rem;
        font-weight: 500;
        border: 1px solid #bbf7d0;
    }
    .gov-pill-none {
        background: #fef2f2;
        color: #b91c1c;
        border-color: #fecaca;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# Altair light theme (nice on white background)
# ---------------------------------------------------
light_theme = {
    "config": {
        "view": {
            "continuousWidth": 380,
            "continuousHeight": 260,
            "stroke": "transparent",
        },
        "background": "white",
        "axis": {
            "labelColor": "#374151",
            "titleColor": "#111827",
            "gridColor": "#e5e7eb",
            "domainColor": "#9ca3af",
        },
        "legend": {
            "labelColor": "#374151",
            "titleColor": "#111827",
        },
    }
}

alt.themes.register("agriesg_light", lambda: light_theme)
alt.themes.enable("agriesg_light")

# ---------------------------------------------------
# Emission factors (placeholder – tune with experts)
# ---------------------------------------------------
EF_N = 5.5      # kg CO2e per kg N fertiliser
EF_DIESEL = 2.7 # kg CO2e per litre diesel
EF_ELEC = 0.5   # kg CO2e per kWh electricity


# ---------------------------------------------------
# Helper functions
# ---------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Add agronomic, emissions & social KPIs."""
    df = df.copy()

    df["area_ha"] = df["area_ha"].replace(0, np.nan)
    df["yield_tonnes"] = df["yield_tonnes"].replace(0, np.nan)
    df["workers_total"] = df["workers_total"].replace(0, np.nan)

    # Productivity & resource intensity
    df["yield_per_ha"] = df["yield_tonnes"] / df["area_ha"]
    df["water_per_tonne"] = df["water_m3"] / df["yield_tonnes"]

    # Emissions (kg CO2e)
    df["emissions_fertilizer"] = df["fertilizer_n_kg"] * EF_N
    df["emissions_diesel"] = df["diesel_litres"] * EF_DIESEL
    df["emissions_electric"] = df["electricity_kwh"] * EF_ELEC

    df["total_emissions"] = (
        df["emissions_fertilizer"] +
        df["emissions_diesel"] +
        df["emissions_electric"]
    )

    df["emissions_per_ha"] = df["total_emissions"] / df["area_ha"]
    df["emissions_per_tonne"] = df["total_emissions"] / df["yield_tonnes"]

    # Social
    df["female_share"] = df["workers_female"] / df["workers_total"]
    df["accidents_per_100_workers"] = (
        df["accidents_count"] / df["workers_total"] * 100
    )

    return df


def safe(x, unit=""):
    return f"{x:.2f}{unit}" if pd.notna(x) else "N/A"


def kpi_card(label: str, value, sub: str = "", unit: str = "", precision: int = 2):
    if pd.isna(value):
        disp = "N/A"
    else:
        disp = f"{value:.{precision}f}{unit}"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{disp}</div>
            <div class="kpi-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_esg_report(row: pd.Series, df_all: pd.DataFrame) -> str:
    """
    ESG narrative for one farm.
    Suggested improvement areas are generated dynamically
    by comparing the farm with the portfolio in df_all.
    """
    r = row

    # ---------- Portfolio benchmarks ----------
    # Use sums to avoid weirdness with NaNs
    total_yield_all = df_all["yield_tonnes"].sum()
    total_emissions_all = df_all["total_emissions"].sum()
    total_water_all = df_all["water_m3"].sum()

    avg_emissions_per_tonne = (
        total_emissions_all / total_yield_all
        if total_yield_all else np.nan
    )
    avg_water_per_tonne = (
        total_water_all / total_yield_all
        if total_yield_all else np.nan
    )

    total_workers_all = df_all["workers_total"].sum()
    total_female_all = df_all["workers_female"].sum()
    avg_female_share = (
        total_female_all / total_workers_all
        if total_workers_all else np.nan
    )

    # Accident rate average (weighted)
    total_accidents_all = df_all["accidents_count"].sum()
    avg_accidents_rate = (
        (total_accidents_all / total_workers_all) * 100
        if total_workers_all else np.nan
    )

    # ---------- Dynamic suggestions ----------
    suggestions = []
    highlights = []

    # Emissions intensity
    if pd.notna(r["emissions_per_tonne"]) and pd.notna(avg_emissions_per_tonne):
        if r["emissions_per_tonne"] > avg_emissions_per_tonne * 1.1:
            suggestions.append(
                f"- Emissions intensity is **high** "
                f"({r['emissions_per_tonne']:.1f} kg CO₂e/t vs portfolio average "
                f"{avg_emissions_per_tonne:.1f}). Explore optimising N rates, "
                "field operations and electricity sources."
            )
        elif r["emissions_per_tonne"] < avg_emissions_per_tonne * 0.9:
            highlights.append(
                f"- Emissions intensity is **better than the portfolio average** "
                f"({r['emissions_per_tonne']:.1f} vs {avg_emissions_per_tonne:.1f} kg CO₂e/t)."
            )

    # Water use
    if pd.notna(r["water_per_tonne"]) and pd.notna(avg_water_per_tonne):
        if r["water_per_tonne"] > avg_water_per_tonne * 1.1:
            suggestions.append(
                f"- Water use per tonne is **above peers** "
                f"({r['water_per_tonne']:.1f} m³/t vs {avg_water_per_tonne:.1f} m³/t). "
                "Consider more efficient irrigation or scheduling."
            )
        elif r["water_per_tonne"] < avg_water_per_tonne * 0.9:
            highlights.append(
                f"- Water efficiency is **strong**, with "
                f"{r['water_per_tonne']:.1f} m³/t compared to a portfolio "
                f"average of {avg_water_per_tonne:.1f} m³/t."
            )

    # Gender inclusion
    if pd.notna(r["female_share"]) and pd.notna(avg_female_share):
        if r["female_share"] < max(avg_female_share - 0.05, 0.30):
            suggestions.append(
                f"- Female participation is **relatively low** "
                f"({r['female_share']*100:.0f}% vs portfolio average "
                f"{avg_female_share*100:.0f}%). Explore ways to attract, "
                "retain and support more women in the workforce."
            )
        elif r["female_share"] >= avg_female_share:
            highlights.append(
                f"- Female workforce share is **at or above peers** "
                f"({r['female_share']*100:.0f}%)."
            )

    # Safety
    if pd.notna(r["accidents_per_100_workers"]) and pd.notna(avg_accidents_rate):
        if r["accidents_per_100_workers"] > 0:
            if r["accidents_per_100_workers"] > avg_accidents_rate * 1.1:
                suggestions.append(
                    f"- Accident rate is **higher than the portfolio average** "
                    f"({r['accidents_per_100_workers']:.1f} vs "
                    f"{avg_accidents_rate:.1f} accidents per 100 workers). "
                    "Review safety training and risk controls."
                )
            else:
                suggestions.append(
                    f"- There were **{r['accidents_count']} accident(s)** in the year. "
                    "Aim for zero incidents through regular safety checks and training."
                )
        elif r["accidents_per_100_workers"] == 0:
            highlights.append(
                "- No workplace accidents were reported in the year – maintain this standard."
            )

    # Certification / governance
    cert = r.get("certification_scheme", "None")
    if isinstance(cert, float) and pd.isna(cert):
        cert = "None"

    if cert.lower() == "none":
        suggestions.append(
            "- No formal certification recorded. Consider schemes such as "
            "Red Tractor, LEAF or Soil Association to strengthen market access "
            "and demonstrate good governance."
        )
    else:
        highlights.append(
            f"- Farm is certified under **{cert}**, which supports governance and market trust."
        )

    if not suggestions:
        suggestions.append(
            "- Overall performance is close to or better than the portfolio average. "
            "Use future ESG cycles to set more ambitious, farm-specific targets."
        )

    # ---------- Build report text ----------
    report_lines = []

    report_lines.append(
        f"### 🌱 ESG Narrative — {r['organisation_name']} ({r['farm_id']})"
    )
    report_lines.append("")
    report_lines.append("**Location & enterprise**")
    report_lines.append(
        f"- Country: **{r['country']}**  \n"
        f"- Main enterprise: **{r['crop']}**  \n"
        f"- Reporting year: **{int(r['year'])}**  \n"
        f"- Farmed area: **{safe(r['area_ha'], ' ha')}**  \n"
        f"- Total output: **{safe(r['yield_tonnes'], ' tonnes')}**"
    )
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("#### 🌍 Environment")
    report_lines.append(
        f"- Total emissions: **{safe(r['total_emissions'], ' kg CO₂e')}**  \n"
        f"- Emissions intensity: **{safe(r['emissions_per_tonne'], ' kg CO₂e / tonne')}**  \n"
        f"- Emissions per hectare: **{safe(r['emissions_per_ha'], ' kg CO₂e / ha')}**  \n"
        f"- Nitrogen fertiliser: **{safe(r['fertilizer_n_kg'], ' kg N')}**  \n"
        f"- Water use per tonne: **{safe(r['water_per_tonne'], ' m³ / tonne')}**"
    )
    report_lines.append("")
    report_lines.append("#### 👩‍🌾 Social")
    report_lines.append(
        f"- Workers: **{int(r['workers_total'])}**  \n"
        f"- Female workers: **{int(r['workers_female'])}**  \n"
        f"- Female share: **{safe(r['female_share']*100, '%')}**  \n"
        f"- Accident rate: **{safe(r['accidents_per_100_workers'], ' accidents / 100 workers')}**"
    )
    report_lines.append("")
    report_lines.append("#### 📑 Governance")
    report_lines.append(f"- Certification scheme: **{cert}**")
    report_lines.append("")
    report_lines.append("#### ⭐ Strengths")
    if highlights:
        for h in highlights:
            report_lines.append(h)
    else:
        report_lines.append("- Data does not show clear strengths relative to the portfolio yet.")
    report_lines.append("")
    report_lines.append("#### 🎯 Suggested improvement areas")
    for sline in suggestions:
        report_lines.append(sline)
    report_lines.append("")
    report_lines.append(
        "*This narrative was auto-generated by the AgriESG farm ESG tool, "
        "using comparisons against all farms in the uploaded dataset.*"
    )

    return "\n".join(report_lines)


# ---------------------------------------------------
# Layout — title & upload
# ---------------------------------------------------
st.title("🌱 AgriESG — Farm-Level ESG Dashboard")

st.write(
    "Upload your farm dataset (same structure used for the multi-farm dashboard) "
    "and explore detailed ESG indicators farm-by-farm."
)

with st.expander("Expected CSV structure (minimum)"):
    st.markdown(
        """
**Required columns**

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

**Optional**

- `certification_scheme` (e.g. Red Tractor, LEAF, Soil Association)
        """
    )

uploaded = st.file_uploader("Upload CSV", type=["csv"])

if uploaded is None:
    st.info("Upload a CSV to see the dashboard.")
    st.stop()

try:
    raw = pd.read_csv(uploaded)
except UnicodeDecodeError:
    uploaded.seek(0)
    raw = pd.read_csv(uploaded, encoding="latin1")

required_cols = [
    "organisation_name",
    "farm_id",
    "country",
    "year",
    "crop",
    "area_ha",
    "yield_tonnes",
    "fertilizer_n_kg",
    "diesel_litres",
    "electricity_kwh",
    "water_m3",
    "workers_total",
    "workers_female",
    "accidents_count",
]

missing = [c for c in required_cols if c not in raw.columns]
if missing:
    st.error("Missing required columns: " + ", ".join(missing))
    st.stop()

df = compute_kpis(raw)

# ---------------------------------------------------
# Sidebar farm selection
# ---------------------------------------------------
st.sidebar.header("Farm selection")
farm_id = st.sidebar.selectbox("Choose a farm", df["farm_id"].unique())

row = df[df["farm_id"] == farm_id].iloc[0]

st.markdown(
    f"""
### 📍 {row['organisation_name']} — {row['crop']} ({row['country']}, {int(row['year'])})
Area: **{safe(row['area_ha'], ' ha')}** · Output: **{safe(row['yield_tonnes'], ' tonnes')}**
"""
)

# ---------------------------------------------------
# KPI cards
# ---------------------------------------------------
st.markdown('<div class="section-title">Key performance indicators</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("Yield per ha", row["yield_per_ha"], "Productivity", " t/ha", 2)
with c2:
    kpi_card("Emissions per tonne", row["emissions_per_tonne"], "Carbon intensity", " kg CO₂e/t", 1)
with c3:
    kpi_card("Water per tonne", row["water_per_tonne"], "Water use efficiency", " m³/t", 1)
with c4:
    kpi_card("Female workforce", row["female_share"] * 100, "Share of total workforce", " %", 0)

c5, c6, c7, c8 = st.columns(4)
with c5:
    kpi_card("Total emissions", row["total_emissions"], "Farm-level footprint", " kg CO₂e", 0)
with c6:
    kpi_card("Total area", row["area_ha"], "Utilised agricultural area", " ha", 1)
with c7:
    kpi_card("Workers", row["workers_total"], "Total people employed", "", 0)
with c8:
    kpi_card("Accidents rate", row["accidents_per_100_workers"], "Per 100 workers", "", 2)

# ---------------------------------------------------
# Main charts row
# ---------------------------------------------------
st.markdown('<div class="section-title">Environmental indicators</div>', unsafe_allow_html=True)

cc1, cc2 = st.columns(2)

# Emissions breakdown donut
with cc1:
    emis_parts = pd.Series(
        {
            "Fertiliser N": row["emissions_fertilizer"],
            "Diesel": row["emissions_diesel"],
            "Electricity": row["emissions_electric"],
        }
    )
    emis_df = emis_parts.rename_axis("Source").reset_index(name="kg_co2e")

    donut = (
        alt.Chart(emis_df)
        .mark_arc(innerRadius=60)
        .encode(
            theta=alt.Theta("kg_co2e:Q", title=None),
            color=alt.Color("Source:N", title="Source"),
            tooltip=[
                "Source",
                alt.Tooltip("kg_co2e:Q", title="Emissions (kg CO₂e)", format=".0f"),
            ],
        )
    )

    st.altair_chart(donut, use_container_width=True)

# Environmental comparison scatter
with cc2:
    compare_df = df[["farm_id", "yield_per_ha", "emissions_per_ha"]].copy()
    compare_df["Farm"] = np.where(compare_df["farm_id"] == farm_id, "Selected farm", "Other farms")

    scatter = (
        alt.Chart(compare_df)
        .mark_circle(size=90)
        .encode(
            x=alt.X("yield_per_ha:Q", title="Yield (t/ha)"),
            y=alt.Y("emissions_per_ha:Q", title="Emissions (kg CO₂e/ha)"),
            color=alt.Color("Farm:N", title=""),
            tooltip=[
                "farm_id",
                alt.Tooltip("yield_per_ha:Q", format=".2f", title="Yield t/ha"),
                alt.Tooltip("emissions_per_ha:Q", format=".1f", title="Emissions kg CO₂e/ha"),
            ],
        )
    )

    st.altair_chart(scatter, use_container_width=True)

# ---------------------------------------------------
# Social indicators chart
# ---------------------------------------------------
st.markdown('<div class="section-title">Social indicators</div>', unsafe_allow_html=True)

soc_df = pd.DataFrame(
    {
        "Indicator": ["Female workforce (%)", "Accidents per 100 workers"],
        "Value": [row["female_share"] * 100, row["accidents_per_100_workers"]],
    }
)

soc_chart = (
    alt.Chart(soc_df)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("Indicator:N", title=""),
        y=alt.Y("Value:Q", title="Value"),
        color=alt.Color("Indicator:N", legend=None),
        tooltip=["Indicator", alt.Tooltip("Value:Q", format=".1f")],
    )
)

st.altair_chart(soc_chart, use_container_width=True)

# ---------------------------------------------------
# Governance
# ---------------------------------------------------
st.markdown('<div class="section-title">Governance</div>', unsafe_allow_html=True)

cert = row.get("certification_scheme", "None")
if isinstance(cert, float) and pd.isna(cert):
    cert = "None"

if cert.lower() == "none":
    pill_class = "gov-pill gov-pill-none"
else:
    pill_class = "gov-pill"

st.markdown(
    f"""
    <span class="{pill_class}">
        Certification: {cert}
    </span>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------
# ESG Narrative / Report
# ---------------------------------------------------
st.markdown('<div class="section-title">ESG narrative report</div>', unsafe_allow_html=True)

with st.expander("Open auto-generated ESG report"):
    st.markdown(generate_esg_report(row, df))
