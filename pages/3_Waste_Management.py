import streamlit as st
from utils import setup_page_config, load_data
import plotly.express as px
import pandas as pd

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Waste Management")

# Waste Management section
st.subheader("Nicht verzehrte Portionen nach Mahlzeitentyp")
waste_data = meal_orders.copy()
waste_data['waste'] = 1 - waste_data['actual_consumption']
waste_by_meal = waste_data.groupby('meal_type')['waste'].mean().reset_index()

fig = px.pie(waste_by_meal, values='waste', names='meal_type',
             title='Verteilung der nicht verzehrten Portionen')
st.plotly_chart(fig, use_container_width=True)

# Additional waste analysis
st.subheader("Detaillierte Abfallanalyse")
col1, col2 = st.columns(2)

with col1:
    # Waste trends over time
    waste_data['date'] = pd.to_datetime(waste_data['date'])
    daily_waste = waste_data.groupby('date')['waste'].mean().reset_index()
    fig = px.line(daily_waste, x='date', y='waste',
                  title='Tägliche Abfallmenge über Zeit')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Waste by care level
    waste_by_care = pd.merge(waste_data, residents, on='resident_id')
    waste_by_care = waste_by_care.groupby('care_level')['waste'].mean().reset_index()
    fig = px.bar(waste_by_care, x='care_level', y='waste',
                 title='Abfallmenge nach Pflegegrad')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True) 