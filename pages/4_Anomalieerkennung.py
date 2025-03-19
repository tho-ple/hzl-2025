import streamlit as st
from utils import setup_page_config, load_data, detect_consumption_anomalies, detect_meal_pattern_anomalies
import plotly.express as px
import pandas as pd

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Anomalieerkennung")

# Anomaly Detection section
tab1, tab2 = st.tabs(["Bewohner-spezifische Anomalien", "Mahlzeit-spezifische Anomalien"])

with tab1:
    st.subheader("Auffällige Ernährungsmuster bei Bewohnern")
    anomalies = detect_consumption_anomalies(meal_orders, residents)
    
    # Display anomaly summary
    anomaly_count = anomalies['is_anomaly'].sum()
    st.metric("Anzahl auffälliger Bewohner", anomaly_count)
    
    if anomaly_count > 0:
        st.subheader("Details zu auffälligen Bewohnern")
        anomaly_details = anomalies[anomalies['is_anomaly']].copy()
        anomaly_details['mean_consumption'] = anomaly_details['mean_consumption'].round(2)
        anomaly_details['std_consumption'] = anomaly_details['std_consumption'].round(2)
        
        # Create a more readable display
        for _, row in anomaly_details.iterrows():
            with st.expander(f"Bewohner ID: {row['resident_id']} (Alter: {row['age']}, Pflegegrad: {row['care_level']})"):
                st.write(f"**Durchschnittlicher Verbrauch:** {row['mean_consumption']:.2%}")
                st.write(f"**Standardabweichung:** {row['std_consumption']:.2%}")
                st.write(f"**Spezielle Ernährungsanforderungen:** {row['special_dietary_requirements']}")
    
    # Visualization of consumption patterns
    fig = px.scatter(anomalies, x='mean_consumption', y='std_consumption',
                     color='is_anomaly', size='meal_count',
                     title='Verbrauchsmuster der Bewohner (Anomalien hervorgehoben)',
                     labels={'mean_consumption': 'Durchschnittlicher Verbrauch',
                            'std_consumption': 'Standardabweichung',
                            'meal_count': 'Anzahl Mahlzeiten',
                            'is_anomaly': 'Anomalie'})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Auffällige Mahlzeitmuster")
    daily_patterns = detect_meal_pattern_anomalies(meal_orders)
    
    # Display anomaly summary
    anomaly_count = daily_patterns['is_anomaly'].sum()
    st.metric("Anzahl auffälliger Mahlzeiten", anomaly_count)
    
    if anomaly_count > 0:
        st.subheader("Details zu auffälligen Mahlzeiten")
        anomaly_details = daily_patterns[daily_patterns['is_anomaly']].copy()
        anomaly_details['actual_consumption'] = anomaly_details['actual_consumption'].round(2)
        anomaly_details['z_score'] = anomaly_details['z_score'].round(2)
        
        for _, row in anomaly_details.iterrows():
            with st.expander(f"Datum: {row['date']} - {row['meal_type']}"):
                st.write(f"**Tatsächlicher Verbrauch:** {row['actual_consumption']:.2%}")
                st.write(f"**Z-Score:** {row['z_score']:.2f}")
        
        # Visualization of daily patterns
        fig = px.line(daily_patterns, x='date', y='actual_consumption',
                      color='meal_type', markers=True,
                      title='Tägliche Verbrauchsmuster nach Mahlzeitentyp')
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True) 