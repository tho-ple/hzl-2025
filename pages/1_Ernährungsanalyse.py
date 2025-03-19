import streamlit as st
from utils import setup_page_config, load_data
import plotly.express as px
import pandas as pd

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Ernährungsanalyse")

# Nutrition Analysis section
tab1, tab2 = st.tabs(["Verbrauchsanalyse", "Ernährungsgewohnheiten"])

with tab1:
    st.subheader("Durchschnittlicher Verbrauch pro Mahlzeit")
    consumption_data = meal_orders.groupby('meal_type')['actual_consumption'].mean().reset_index()
    fig = px.bar(consumption_data, x='meal_type', y='actual_consumption',
                 title='Durchschnittlicher Verbrauch nach Mahlzeitentyp')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Ernährungsgewohnheiten nach Pflegegrad")
    merged_data = pd.merge(meal_orders, residents, on='resident_id')
    consumption_by_care = merged_data.groupby('care_level')['actual_consumption'].mean().reset_index()
    fig = px.line(consumption_by_care, x='care_level', y='actual_consumption',
                  title='Durchschnittlicher Verbrauch nach Pflegegrad')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True) 