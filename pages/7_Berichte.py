import streamlit as st
from utils import setup_page_config, load_data, analyze_weather_correlation
import pandas as pd
import os

# Setup page configuration
setup_page_config()

# Load data
residents, meal_orders, health_monitoring, menu_items, weather_data, db_data = load_data()

# Main content
st.title("Berichte")

# Create reports directory if it doesn't exist
if not os.path.exists('reports'):
    os.makedirs('reports')

# Report Generation section
st.header("Excel-Berichte generieren")
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

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2024 - Demo Version</p>
    </div>
""", unsafe_allow_html=True) 