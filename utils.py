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

def calculate_social_isolation_risk(resident_id):
    """
    Calculate social isolation risk based on:
    - Activity participation trend
    - Number of family visits
    - Upcoming holidays
    Returns: (risk_score, risk_factors)
    """
    conn = sqlite3.connect('hauszumleben.db')
    
    # Get activity participation for last 30 days
    activity_query = """
    SELECT date, COUNT(*) as participation_count 
    FROM activity_participation
    WHERE resident_id = ? 
    AND date >= date('now', '-30 days')
    GROUP BY date
    """
    
    # Get visits for last 30 days
    visits_query = """
    SELECT departure_time, COUNT(*) as visit_count 
    FROM outings 
    WHERE resident_id = ? 
    AND departure_time >= datetime('now', '-30 days')
    GROUP BY departure_time
    """
    
    activities_df = pd.read_sql_query(activity_query, conn, params=(resident_id,))
    visits_df = pd.read_sql_query(visits_query, conn, params=(resident_id,))
    
    risk_factors = []
    risk_score = 0
    
    # Check activity participation trend
    if not activities_df.empty:
        recent_activities = activities_df.sort_values('date')
        if len(recent_activities) >= 7:
            week_avg = recent_activities['participation_count'].rolling(7).mean()
            if week_avg.iloc[-1] < week_avg.iloc[-7]:
                risk_score += 30
                risk_factors.append("Abnehmende Aktivitätsteilnahme")
    else:
        risk_score += 40
        risk_factors.append("Keine Aktivitätsteilnahme registriert")
    
    # Check visit frequency
    if not visits_df.empty:
        avg_visits = visits_df['visit_count'].mean()
        if avg_visits < 0.5:  # Less than one visit every 2 days
            risk_score += 30
            risk_factors.append("Wenige Besuche")
    else:
        risk_score += 30
        risk_factors.append("Keine Besuche registriert")
    
    # Check upcoming holidays (simplified example)
    holidays = [
        ('01-01', 'Neujahr'),
        ('05-01', 'Staatsfeiertag'),
        ('12-25', 'Weihnachten'),
        # Add more Austrian holidays
    ]
    
    today = datetime.now()
    for holiday_date, holiday_name in holidays:
        holiday = datetime.strptime(f"{today.year}-{holiday_date}", "%Y-%m-%d")
        if 0 <= (holiday - today).days <= 7:  # Holiday within next 7 days
            risk_score += 20
            risk_factors.append(f"Bevorstehender Feiertag: {holiday_name}")
    
    conn.close()
    
    return min(100, risk_score), risk_factors


def calculate_fall_risk(resident_id):
    """
    Calculate fall risk based on mobility status and fall history
    Returns: (risk_score, risk_factors)
    """
    conn = sqlite3.connect('hauszumleben.db')
    
    # Get mobility status
    mobility_query = """
    SELECT mobility_status FROM residents
    WHERE id = ?
    """
    
    # Get recent falls
    falls_query = """
    SELECT * FROM residents 
    WHERE id = ? 
    AND last_fall_date >= date('now', '-90 days')
    """
    
    mobility = pd.read_sql_query(mobility_query, conn, params=(resident_id,))
    falls = pd.read_sql_query(falls_query, conn, params=(resident_id,))
    
    risk_score = 0
    risk_factors = []
    
    if not mobility.empty:
        mobility_status = mobility['mobility_status'].iloc[0]
        if mobility_status in ['eingeschränkt', 'Hilfsmittel benötigt']:
            risk_score += 30
            risk_factors.append("Eingeschränkte Mobilität")
    
    # Check fall history
    if not falls.empty:
        recent_falls = len(falls)
        if recent_falls > 0:
            risk_score += min(40, recent_falls * 20)
            risk_factors.append(f"{recent_falls} Stürze in den letzten 90 Tagen")
    
    conn.close()
    return min(100, risk_score), risk_factors 



