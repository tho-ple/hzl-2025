import streamlit as st
from utils import setup_page_config, load_data, analyze_weather_correlation
import plotly.express as px
import pandas as pd

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Wetterkorrelation")

# Weather Correlation section
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