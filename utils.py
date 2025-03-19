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

#######################
# Page configuration
def setup_page_config():
    st.set_page_config(
        page_title="Häuser zum Leben",
        page_icon="img/logo.jpeg",
        layout="wide",
        initial_sidebar_state="expanded")
    alt.themes.enable("dark")

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
@st.cache_data
def load_data():
    residents = pd.read_csv('data/residents.csv')
    meal_orders = pd.read_csv('data/meal_orders.csv')
    health_monitoring = pd.read_csv('data/health_monitoring.csv')
    menu_items = pd.read_csv('data/menu_items.csv')
    weather_data = pd.read_csv('data/weather_data.csv')
    db_data = load_database_data()
    return residents, meal_orders, health_monitoring, menu_items, weather_data, db_data

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