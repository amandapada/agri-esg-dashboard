import streamlit as st
import pandas as pd

# Load ESG data
df = pd.read_csv("esg_data.csv")

st.set_page_config(page_title="ESG Dashboard", layout="wide")
st.title("🌿 ESG Dashboard for Agricultural SMEs")
st.markdown("This dashboard visualizes sustainability performance across key metrics from 2021 to 2025.")

# Show raw data
with st.expander("📄 View Raw ESG Data"):
    st.dataframe(df)

# Line chart: Carbon Emissions
st.subheader("📉 Carbon Emissions Over Time")
st.line_chart(df.set_index("Year")["Carbon Emissions (tonnes CO2e)"])

# Line chart: Biodiversity Score
st.subheader("🌱 Biodiversity Score Trend")
st.line_chart(df.set_index("Year")["Biodiversity Score (0–100)"])

# Bar chart: ESG Snapshot for 2025
st.subheader("📊 ESG Snapshot for 2025")
latest = df[df["Year"] == 2025].drop("Year", axis=1).T
latest.columns = ["2025"]
st.bar_chart(latest)

# Insights
st.subheader("🧠 Key Insights")
st.markdown("- ✅ **Carbon emissions reduced by 27%** from 2021 to 2025.")
st.markdown("- 🌿 **Biodiversity score improved from 58.2 to 77.5**, reflecting regenerative practices.")
st.markdown("- ⚡ **Energy consumption dropped by 10%**, showing efficiency gains.")
st.markdown("- 🧪 **Fertilizer usage decreased steadily**, supporting soil health and sustainability.")

# Footer
st.markdown("---")
st.caption("Built with Streamlit • Data based on UK agricultural estimates • MVP for ESG innovation endorsement")