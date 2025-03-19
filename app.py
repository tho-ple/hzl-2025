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

#######################
# Page configuration
st.set_page_config(
    page_title="Häuser zum Leben",
    page_icon="img/logo.jpeg",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

#######################
# Load data
@st.cache_data
def load_data():
    residents = pd.read_csv('data/residents.csv')
    meal_orders = pd.read_csv('data/meal_orders.csv')
    health_monitoring = pd.read_csv('data/health_monitoring.csv')
    menu_items = pd.read_csv('data/menu_items.csv')
    weather_data = pd.read_csv('data/weather_data.csv')
    return residents, meal_orders, health_monitoring, menu_items, weather_data

residents, meal_orders, health_monitoring, menu_items, weather_data = load_data()

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
# Sidebar
with st.sidebar:
    st.title('Häuser zum Leben - Demo')
    st.markdown("""
    ### Dashboard Navigation
    - [Übersicht](#übersicht)
    - [Ernährungsanalyse](#ernährungsanalyse)
    - [Gesundheitsmonitoring](#gesundheitsmonitoring)
    - [Waste Management](#waste-management)
    - [Anomalieerkennung](#anomalieerkennung)
    - [Wetterkorrelation](#wetterkorrelation)
    """)

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

# Add Excel Report Generation
st.header("Berichte")
with st.expander("Excel-Berichte generieren"):
    st.subheader("Berichte exportieren")
    
    # Create report options
    report_type = st.selectbox(
        "Wählen Sie den Berichtstyp",
        ["Übersichtsbericht", "Ernährungsbericht", "Gesundheitsbericht", "Wettereinflussbericht"]
    )
    
    if report_type == "Übersichtsbericht":
        # Create overview report
        overview_data = {
            'Gesamtbewohner': [len(residents)],
            'Durchschnittsalter': [residents['age'].mean()],
            'Minimales Alter': [residents['age'].min()],
            'Maximales Alter': [residents['age'].max()],
            'Durchschnittlicher Pflegegrad': [residents['care_level'].mean()]
        }
        overview_df = pd.DataFrame(overview_data)
        
        # Add age distribution
        age_distribution = residents['age'].value_counts().sort_index()
        age_distribution_df = pd.DataFrame({
            'Alter': age_distribution.index,
            'Anzahl Bewohner': age_distribution.values
        })
        
        # Create Excel writer
        with pd.ExcelWriter('reports/uebersichtsbericht.xlsx') as writer:
            overview_df.to_excel(writer, sheet_name='Übersicht', index=False)
            age_distribution_df.to_excel(writer, sheet_name='Altersverteilung', index=False)
            residents.to_excel(writer, sheet_name='Bewohnerdetails', index=False)
        
        st.success("Übersichtsbericht wurde erstellt!")
        with open('reports/uebersichtsbericht.xlsx', 'rb') as f:
            st.download_button(
                label="Übersichtsbericht herunterladen",
                data=f,
                file_name="uebersichtsbericht.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif report_type == "Ernährungsbericht":
        # Create nutrition report
        nutrition_data = meal_orders.groupby('meal_type').agg({
            'actual_consumption': ['mean', 'std', 'count']
        }).reset_index()
        
        nutrition_data.columns = ['Mahlzeitentyp', 'Durchschnittlicher Verbrauch', 'Standardabweichung', 'Anzahl']
        
        # Add waste analysis
        waste_data = meal_orders.copy()
        waste_data['waste'] = 1 - waste_data['actual_consumption']
        waste_by_meal = waste_data.groupby('meal_type')['waste'].mean().reset_index()
        waste_by_meal.columns = ['Mahlzeitentyp', 'Durchschnittlicher Abfall']
        
        # Create Excel writer
        with pd.ExcelWriter('reports/ernaehrungsbericht.xlsx') as writer:
            nutrition_data.to_excel(writer, sheet_name='Verbrauchsanalyse', index=False)
            waste_by_meal.to_excel(writer, sheet_name='Abfallanalyse', index=False)
            meal_orders.to_excel(writer, sheet_name='Rohdaten', index=False)
        
        st.success("Ernährungsbericht wurde erstellt!")
        with open('reports/ernaehrungsbericht.xlsx', 'rb') as f:
            st.download_button(
                label="Ernährungsbericht herunterladen",
                data=f,
                file_name="ernaehrungsbericht.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif report_type == "Gesundheitsbericht":
        # Create health report
        health_summary = health_monitoring.groupby('date').agg({
            'blood_pressure_systolic': ['mean', 'std'],
            'heart_rate': ['mean', 'std'],
            'weight': ['mean', 'std']
        }).reset_index()
        
        health_summary.columns = ['Datum', 'Durchschnittlicher systolischer Blutdruck', 
                                'Std. Abw. systolischer Blutdruck', 'Durchschnittliche Herzfrequenz',
                                'Std. Abw. Herzfrequenz', 'Durchschnittliches Gewicht', 
                                'Std. Abw. Gewicht']
        
        # Create Excel writer
        with pd.ExcelWriter('reports/gesundheitsbericht.xlsx') as writer:
            health_summary.to_excel(writer, sheet_name='Gesundheitszusammenfassung', index=False)
            health_monitoring.to_excel(writer, sheet_name='Rohdaten', index=False)
        
        st.success("Gesundheitsbericht wurde erstellt!")
        with open('reports/gesundheitsbericht.xlsx', 'rb') as f:
            st.download_button(
                label="Gesundheitsbericht herunterladen",
                data=f,
                file_name="gesundheitsbericht.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    elif report_type == "Wettereinflussbericht":
        # Create weather impact report
        weather_consumption, correlations_df = analyze_weather_correlation(meal_orders, weather_data, menu_items)
        
        if weather_consumption is not None and correlations_df is not None:
            # Create Excel writer
            with pd.ExcelWriter('reports/wettereinflussbericht.xlsx') as writer:
                correlations_df.to_excel(writer, sheet_name='Korrelationen', index=False)
                weather_consumption.to_excel(writer, sheet_name='Wettereinfluss', index=False)
                weather_data.to_excel(writer, sheet_name='Wetterdaten', index=False)
            
            st.success("Wettereinflussbericht wurde erstellt!")
            with open('reports/wettereinflussbericht.xlsx', 'rb') as f:
                st.download_button(
                    label="Wettereinflussbericht herunterladen",
                    data=f,
                    file_name="wettereinflussbericht.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("Keine Daten für den Wettereinflussbericht verfügbar.")

# Nutrition Analysis section
st.header("Ernährungsanalyse")
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

# Health Monitoring section
st.header("Gesundheitsmonitoring")
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

# Waste Management section
st.header("Waste Management")
st.subheader("Nicht verzehrte Portionen nach Mahlzeitentyp")
waste_data = meal_orders.copy()
waste_data['waste'] = 1 - waste_data['actual_consumption']
waste_by_meal = waste_data.groupby('meal_type')['waste'].mean().reset_index()

fig = px.pie(waste_by_meal, values='waste', names='meal_type',
             title='Verteilung der nicht verzehrten Portionen')
st.plotly_chart(fig, use_container_width=True)

# Anomaly Detection section
st.header("Anomalieerkennung")
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

# Weather Correlation section
st.header("Wetterkorrelation")
tab1, tab2 = st.tabs(["Wettereinfluss", "Korrelationsanalyse"])

with tab1:
    st.subheader("Wettereinfluss auf Mahlzeitenverbrauch")
    weather_consumption, correlations_df = analyze_weather_correlation(meal_orders, weather_data, menu_items)
    
    if weather_consumption is not None and correlations_df is not None:
        # Weather trends
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(weather_consumption, x='date', y=['temperature', 'actual_consumption'],
                          title='Temperatur und Mahlzeitenverbrauch über Zeit',
                          labels={'value': 'Wert', 'variable': 'Parameter'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(weather_consumption, x='temperature', y='actual_consumption',
                            color='meal_type',
                            title='Temperatur vs. Mahlzeitenverbrauch',
                            labels={'temperature': 'Temperatur (°C)',
                                   'actual_consumption': 'Verbrauch'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Weather conditions impact
        st.subheader("Einfluss der Wetterbedingungen")
        weather_impact = weather_consumption.groupby('weather_condition')['actual_consumption'].mean().reset_index()
        fig = px.bar(weather_impact, x='weather_condition', y='actual_consumption',
                     title='Durchschnittlicher Verbrauch nach Wetterbedingungen')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Keine Daten für die Wetterkorrelationsanalyse verfügbar.")

with tab2:
    st.subheader("Korrelationsanalyse")
    
    if correlations_df is not None and not correlations_df.empty:
        # Display correlation matrix
        correlation_matrix = correlations_df.set_index('meal_type')
        fig = px.imshow(correlation_matrix,
                        title='Korrelationsmatrix: Wetter vs. Mahlzeitenverbrauch',
                        labels={'x': 'Wetterparameter', 'y': 'Mahlzeitentyp'},
                        color_continuous_scale='RdBu')
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed correlations
        st.subheader("Detaillierte Korrelationen")
        for _, row in correlations_df.iterrows():
            with st.expander(f"Mahlzeitentyp: {row['meal_type']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Temperatur-Korrelation", f"{row['temperature_correlation']:.2f}")
                with col2:
                    st.metric("Niederschlag-Korrelation", f"{row['precipitation_correlation']:.2f}")
                with col3:
                    st.metric("Luftfeuchtigkeit-Korrelation", f"{row['humidity_correlation']:.2f}")
                
                # Interpretation
                st.markdown("**Interpretation:**")
                if abs(row['temperature_correlation']) > 0.5:
                    direction = "positiv" if row['temperature_correlation'] > 0 else "negativ"
                    st.write(f"- Starker {direction}er Einfluss der Temperatur")
                if abs(row['precipitation_correlation']) > 0.5:
                    direction = "positiv" if row['precipitation_correlation'] > 0 else "negativ"
                    st.write(f"- Starker {direction}er Einfluss des Niederschlags")
                if abs(row['humidity_correlation']) > 0.5:
                    direction = "positiv" if row['humidity_correlation'] > 0 else "negativ"
                    st.write(f"- Starker {direction}er Einfluss der Luftfeuchtigkeit")
    else:
        st.warning("Keine Korrelationsdaten verfügbar.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True)


