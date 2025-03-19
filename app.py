import streamlit as st
import pandas as pd
from datetime import datetime
from utils import setup_page_config, load_database_data

# Setup page configuration
setup_page_config()

# Load patient data from database
db_data = load_database_data()
patients = db_data.get('patient', pd.DataFrame())

# Berechnung des Alters aus dem Geburtsdatum (`geb`)
def calculate_age(birthdate):
    today = datetime.today()
    birthdate = datetime.strptime(birthdate, "%Y-%m-%d")  # Falls Format anders, anpassen
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

if not patients.empty:
    patients["age"] = patients["geb"].apply(calculate_age)

# Back button in top left corner
st.markdown("""
    <div style="position: absolute; top: 0.5rem; left: 1rem; z-index: 1000;">
        <a href="/" style="text-decoration: none; color: white; font-size: 24px;">
            ← Zurück
        </a>
    </div>
""", unsafe_allow_html=True)

st.title("Patientenliste")

#Add Logo
st.sidebar.image("./img/logo_lang.png", width=300)

# Sidebar: Patientensuche
st.sidebar.header("Patienten")
search = st.sidebar.text_input("Suche nach Name oder ID")

# Filter Patienten basierend auf Suche
filtered_patients = patients.copy()
if search:
    filtered_patients = filtered_patients[
        (filtered_patients["pat_id"].astype(str).str.contains(search, case=False)) |
        (filtered_patients["vorname"].str.contains(search, case=False)) |
        (filtered_patients["nachname"].str.contains(search, case=False))
    ]

# Patientenliste in Sidebar als Radio-Buttons anzeigen
st.sidebar.subheader("Wähle einen Patienten")
patient_list = [
    f"{row['vorname']} {row['nachname']} (ID: {row['pat_id']})"
    for _, row in filtered_patients.iterrows()
]

# Add custom CSS for larger patient list items
st.markdown("""
    <style>
    /* Larger text for the patient list items */
    .sidebar .radio label {
        font-size: 22px;  /* Increase font size */
        line-height: 2.2rem;  /* More space between options */
        padding: 10px; /* Add some padding around each item */
    }
    </style>
""", unsafe_allow_html=True)

# Show the patients as radio buttons in the sidebar
selected_patient_info = st.sidebar.radio("Patient auswählen:", patient_list, index=0 if patient_list else None)

# Falls ein Patient ausgewählt wurde, entsprechende Details abrufen
if selected_patient_info:
    selected_patient_id = int(selected_patient_info.split("(ID: ")[1][:-1])
    selected_patient = patients[patients["pat_id"] == selected_patient_id].iloc[0]

    st.header(f"Patient: {selected_patient['vorname']} {selected_patient['nachname']}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Persönliche Informationen")
        st.write(f"**Alter:** {selected_patient['age']} Jahre")
        st.write(f"**Geschlecht:** {selected_patient['geschlecht']}")
        st.write(f"**Betreuer-ID:** {selected_patient['betreuer_id']}")

    with col2:
        st.subheader("Adresse")
        st.write(f"**Wohnort:** {selected_patient['adresse']}")

    # Gesundheitsdaten anzeigen
    st.subheader("Gesundheitshistorie")
    if 'health_monitoring' in db_data:
        health_data = db_data['health_monitoring']
        patient_health = health_data[health_data['pat_id'] == selected_patient['pat_id']]
        if not patient_health.empty:
            st.dataframe(patient_health)
        else:
            st.write("Keine Gesundheitsdaten verfügbar.")
    else:
        st.write("Keine Gesundheitsdaten verfügbar.")

else:
    st.info("Wähle einen Patienten aus der Seitenleiste.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2025 - Demo Version</p>
    </div>
""", unsafe_allow_html=True)
