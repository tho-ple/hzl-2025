import streamlit as st
from utils import setup_page_config, load_data
import plotly.express as px
import pandas as pd

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Gesundheitsmonitoring")

# Health Monitoring section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Vitalparameter Trends")
    health_data = health_monitoring.groupby('date').agg({
        'blood_pressure_systolic': 'mean',
        'heart_rate': 'mean'
    }).reset_index()
    
    fig = px.line(health_data, x='date', y=['blood_pressure_systolic', 'heart_rate'],
                  title='Durchschnittliche Vitalparameter über Zeit')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Gewichtsentwicklung")
    weight_data = health_monitoring.groupby('date')['weight'].mean().reset_index()
    fig = px.line(weight_data, x='date', y='weight',
                  title='Durchschnittliches Gewicht über Zeit')
    st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True) 