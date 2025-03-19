import streamlit as st
from utils import setup_page_config, load_data
import plotly.express as px
import pandas as pd
import numpy as np

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Datenbankanalyse")

if db_data is not None:
    # Display available tables
    st.subheader("Verfügbare Datenbanktabellen")
    for table_name in db_data.keys():
        with st.expander(f"Tabelle: {table_name}"):
            st.write(f"Anzahl Einträge: {len(db_data[table_name])}")
            st.write("Beispieldaten:")
            st.dataframe(db_data[table_name].head())
            
            # Basic statistics for numeric columns
            numeric_cols = db_data[table_name].select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                st.write("Statistiken für numerische Spalten:")
                st.dataframe(db_data[table_name][numeric_cols].describe())
            
            # Visualizations for numeric columns
            if len(numeric_cols) > 0:
                st.write("Visualisierungen:")
                for col in numeric_cols:
                    fig = px.histogram(db_data[table_name], x=col,
                                     title=f'Verteilung von {col}')
                    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Keine Datenbankdaten verfügbar.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True) 