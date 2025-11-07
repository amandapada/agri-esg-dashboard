import streamlit as st
import pandas as pd

# Load ESG data
df = pd.read_csv("esg_data.csv")

st.set_page_config(page_title="ESG Dashboard", layout="wide")
st.title("ESG Dashboard for Agricultural SMEs")
st.markdown("This dashboard visualizes sustainability performance across key metrics from 2021 to 2025.")

# Show raw data
with st.expander("View Raw ESG Data"):
    st.dataframe(df)

# Line chart: Carbon Emissions
st.subheader("Carbon Emissions Over Time")
st.line_chart(df.set_index("Year")["Carbon Emissions (tonnes CO2e)"])

# Line chart: Biodiversity Score (robust column handling)
st.subheader("Biodiversity Score Trend")
biodiversity_col = None
for col in df.columns:
    if "Biodiversity" in col:
        biodiversity_col = col
        break

if biodiversity_col:
    st.line_chart(df.set_index("Year")[biodiversity_col])
else:
    st.error("Biodiversity Score column not found. Please check your CSV file.")

# Bar chart: ESG Snapshot for 2025
st.subheader("2025 ESG Snapshot")
if 2025 in df["Year"].values:
    latest = df[df["Year"] == 2025].drop("Year", axis=1).T
    latest.columns = ["2025"]
    st.bar_chart(latest)
else:
    st.error("No data found for year 2025.")

# Insights
st.subheader("Key Insights")
st.markdown("- Carbon emissions reduced by 27% from 2021 to 2025.")
st.markdown("- Biodiversity score improved significantly, reflecting regenerative practices.")
st.markdown("- Energy consumption dropped by over 10%, showing efficiency gains.")
st.markdown("- Fertilizer usage decreased steadily, supporting soil health and sustainability.")

# Footer
st.markdown("---")
st.caption("Built with Streamlit | Data based on UK agricultural estimates | MVP for ESG innovation endorsement")