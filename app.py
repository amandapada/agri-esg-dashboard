import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("ESG Dashboard for Agricultural SMEs")

# Sample ESG data
data = {
    "Metric": ["Carbon Emissions", "Water Usage", "Waste Generated", "Labour Hours"],
    "Value": [120, 3500, 1200, 180],
    "Regional Avg": [140, 3200, 1000, 200]
}
df = pd.DataFrame(data)

# Bar chart
st.subheader("Current ESG Performance")
st.bar_chart(df.set_index("Metric")["Value"])

# Radar chart (placeholder)
st.subheader("Comparison to Regional Averages")
st.write("Radar chart coming soon...")

# Line chart
st.subheader("Carbon Emissions Over Time")
carbon_trend = pd.Series([160, 150, 135, 125, 120], index=[2021, 2022, 2023, 2024, 2025])
st.line_chart(carbon_trend)