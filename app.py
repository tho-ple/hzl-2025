#######################
# Import libraries
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from scipy import stats
import sqlite3
import os
from utils import setup_page_config, load_data

#######################
# Page configuration
setup_page_config()

#######################
# Database Functions
@st.cache_data
def load_database_data():
    try:
        conn = sqlite3.connect('hauszumleben.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Load data from each table
        db_data = {}
        for table in tables:
            table_name = table[0]
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            db_data[table_name] = df
        
        conn.close()
        return db_data
    except Exception as e:
        st.error(f"Fehler beim Laden der Datenbank: {str(e)}")
        return None

#######################
# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

#######################
# Weather Correlation Functions
@st.cache_data
def analyze_weather_correlation(meal_orders, weather_data, menu_items):
    try:
        # Merge meal orders with weather data
        meal_orders['date'] = pd.to_datetime(meal_orders['date'])
        weather_data['date'] = pd.to_datetime(weather_data['date'])
        merged_data = pd.merge(meal_orders, weather_data, on='date', how='inner')
        
        if len(merged_data) == 0:
            st.warning("Keine übereinstimmenden Daten zwischen Mahlzeiten und Wetter gefunden.")
            return None, None
        
        # Calculate daily consumption by meal type
        daily_consumption = merged_data.groupby(['date', 'meal_type'])['actual_consumption'].mean().reset_index()
        
        # Merge with weather data
        weather_consumption = pd.merge(daily_consumption, weather_data, on='date')
        
        # Calculate correlations for each meal type
        correlations = []
        for meal_type in weather_consumption['meal_type'].unique():
            meal_data = weather_consumption[weather_consumption['meal_type'] == meal_type]
            
            if len(meal_data) < 2:
                continue
                
            # Calculate correlations with weather parameters
            temp_corr = stats.pearsonr(meal_data['temperature'], meal_data['actual_consumption'])[0]
            precip_corr = stats.pearsonr(meal_data['precipitation'], meal_data['actual_consumption'])[0]
            humidity_corr = stats.pearsonr(meal_data['humidity'], meal_data['actual_consumption'])[0]
            
            correlations.append({
                'meal_type': meal_type,
                'temperature_correlation': temp_corr,
                'precipitation_correlation': precip_corr,
                'humidity_correlation': humidity_corr
            })
        
        correlations_df = pd.DataFrame(correlations)
        return weather_consumption, correlations_df
    
    except Exception as e:
        st.error(f"Fehler bei der Wetterkorrelationsanalyse: {str(e)}")
        return None, None

#######################
# Anomaly Detection Functions
@st.cache_data
def detect_consumption_anomalies(meal_orders, residents):
    # Merge meal orders with resident data
    merged_data = pd.merge(meal_orders, residents, on='resident_id')
    
    # Calculate consumption statistics per resident
    resident_stats = merged_data.groupby('resident_id').agg({
        'actual_consumption': ['mean', 'std', 'count']
    }).reset_index()
    
    # Flatten column names
    resident_stats.columns = ['resident_id', 'mean_consumption', 'std_consumption', 'meal_count']
    
    # Prepare features for anomaly detection
    features = resident_stats[['mean_consumption', 'std_consumption']].values
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Apply Isolation Forest
    iso_forest = IsolationForest(contamination=0.1, random_state=42)
    predictions = iso_forest.fit_predict(features_scaled)
    
    # Add anomaly predictions to resident stats
    resident_stats['is_anomaly'] = predictions == -1
    
    # Merge back with resident data
    anomalies = pd.merge(resident_stats, residents, on='resident_id')
    return anomalies

@st.cache_data
def detect_meal_pattern_anomalies(meal_orders):
    # Calculate daily consumption patterns
    daily_patterns = meal_orders.groupby(['date', 'meal_type'])['actual_consumption'].mean().reset_index()
    
    # Calculate z-scores for each meal type
    meal_stats = daily_patterns.groupby('meal_type').agg({
        'actual_consumption': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    meal_stats.columns = ['meal_type', 'mean_consumption', 'std_consumption']
    
    # Calculate z-scores
    daily_patterns = pd.merge(daily_patterns, meal_stats, on='meal_type')
    daily_patterns['z_score'] = (daily_patterns['actual_consumption'] - daily_patterns['mean_consumption']) / daily_patterns['std_consumption']
    
    # Identify anomalies (z-score > 2 or < -2)
    daily_patterns['is_anomaly'] = abs(daily_patterns['z_score']) > 2
    
    return daily_patterns

#######################
# Main content
st.title("Häuser zum Leben - Intelligentes Pflegemanagement")

# Overview section
st.header("Übersicht")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Gesamtbewohner", len(residents))
    
with col2:
    avg_age = residents['age'].mean()
    min_age = residents['age'].min()
    max_age = residents['age'].max()
    st.metric("Durchschnittsalter", f"{avg_age:.1f} Jahre")
    st.metric("Jüngster Bewohner", f"{min_age} Jahre")
    st.metric("Ältester Bewohner", f"{max_age} Jahre")
    
with col3:
    care_levels = residents['care_level'].value_counts()
    st.metric("Durchschnittlicher Pflegegrad", f"{residents['care_level'].mean():.1f}")

# Quick Links
st.header("Schnellzugriff")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
        <a href="pages/1_Ernährungsanalyse.py" target="_self">
            <div style="text-align: center; padding: 20px; background-color: #1f1f1f; border-radius: 10px;">
                <h3>Ernährungsanalyse</h3>
                <p>Analyse der Mahlzeitenverbräuche</p>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <a href="pages/2_Gesundheitsmonitoring.py" target="_self">
            <div style="text-align: center; padding: 20px; background-color: #1f1f1f; border-width: 1px; border-color: #333; border-style: solid; border-radius: 10px;">
                <h3>Gesundheitsmonitoring</h3>
                <p>Überwachung der Vitalparameter</p>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <a href="pages/3_Waste_Management.py" target="_self">
            <div style="text-align: center; padding: 20px; background-color: #1f1f1f; border-width: 1px; border-color: #333; border-style: solid; border-radius: 10px;">
                <h3>Waste Management</h3>
                <p>Analyse der Lebensmittelabfälle</p>
            </div>
        </a>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
        <a href="pages/4_Anomalieerkennung.py" target="_self">
            <div style="text-align: center; padding: 20px; background-color: #1f1f1f; border-width: 1px; border-color: #333; border-style: solid; border-radius: 10px;">
                <h3>Anomalieerkennung</h3>
                <p>Erkennung von Auffälligkeiten</p>
            </div>
        </a>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True)


