import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import setup_page_config, load_database_data, calculate_social_isolation_risk, calculate_fall_risk

# Setup page configuration
setup_page_config()

# Load database data
db_data = load_database_data()
patients = db_data.get('patient', pd.DataFrame())

# Berechnung des Alters aus dem Geburtsdatum
def calculate_age(birthdate):
    today = datetime.today()
    try:
        birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except:
        return None

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

# Add Logo
st.sidebar.image("./img/logo_lang.png", width=250)

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
    .st-emotion-cache-16txtl3 {
    padding: 6rem 1.5rem;
    padding-top: 50px;
    }
    .sidebar .radio label {
        font-size: 22px;  /* Increase font size */
        line-height: 2.2rem;  /* More space between options */
        padding: 10px; /* Add some padding around each item */
    }
    </style>
""", unsafe_allow_html=True)

# Show the patients as radio buttons in the sidebar
selected_patient_info = st.sidebar.radio("Patient auswählen:", patient_list, index=0 if patient_list else None)

messages = st.sidebar.container(height=300)
if prompt := st.sidebar.chat_input("Say something"):        
    messages.chat_message("user").write(prompt)
    messages.chat_message("assistant").write(f"Echo: {prompt}")

# Falls ein Patient ausgewählt wurde, entsprechende DetaiFls abrufen
if selected_patient_info:
    selected_patient_id = int(selected_patient_info.split("(ID: ")[1][:-1])
    selected_patient = patients[patients["pat_id"] == selected_patient_id].iloc[0]

    st.header(f"Patient: {selected_patient['vorname']} {selected_patient['nachname']}")

    # Calculate all status metrics
    isolation_risk, isolation_factors = calculate_social_isolation_risk(selected_patient_id)
    fall_risk, fall_factors = calculate_fall_risk(selected_patient_id)
    
    # Display four key metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Social Isolation Risk
        st.metric(
            "Soziale Isolation",
            f"{isolation_risk}%",
            delta="Risiko" if isolation_risk > 50 else "Normal",
            delta_color="inverse"
        )
        if isolation_risk > 50:
            st.markdown(f"""
            <div style='background-color: rgba(255, 0, 0, 0.1); padding: 10px; border-radius: 5px;'>
                <h6>Risikofaktoren:</h6>
                <ul>{''.join([f'<li>{factor}</li>' for factor in isolation_factors])}</ul>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        # Fall Risk
        st.metric(
            "Sturzrisiko",
            f"{fall_risk}%",
            delta="Erhöht" if fall_risk > 50 else "Gering",
            delta_color="inverse"
        )
        if fall_risk > 50:
            st.markdown(f"""
            <div style='background-color: rgba(255, 0, 0, 0.1); padding: 10px; border-radius: 5px;'>
                <h6>Risikofaktoren:</h6>
                <ul>{''.join([f'<li>{factor}</li>' for factor in fall_factors])}</ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Add a divider
    st.markdown("---")
    
    # Tabs für unterschiedliche Ansichten
    tab1, tab2, tab3 = st.tabs(["Patienten-Informationen", "Datenvisualisierung", "Sicherheitsdaten"])
    
    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Persönliche Informationen")
            st.write(f"**Alter:** {selected_patient['age']} Jahre")
            st.write(f"**Geschlecht:** {selected_patient['geschlecht']}")
            st.write(f"**Betreuer-ID:** {selected_patient['betreuer_id']}")
            
            # Finde zusätzliche Informationen aus health_vitals
            if 'health_vitals' in db_data:
                # Map patient ID to resident ID (if needed)
                # This is needed because health_vitals uses resident_id
                resident_id = selected_patient_id  # Assuming they match
                
                vitals = db_data['health_vitals']
                patient_vitals = vitals[vitals['resident_id'] == resident_id]
                
                if not patient_vitals.empty:
                    latest_vitals = patient_vitals.iloc[-1]
                    st.subheader("Neueste Vitalwerte")
                    st.write(f"**Herzfrequenz:** {latest_vitals['heart_rate']} bpm")
                    st.write(f"**Blutdruck:** {latest_vitals['blood_pressure_systolic']}/{latest_vitals['blood_pressure_diastolic']} mmHg")
                    st.write(f"**Gemessen am:** {latest_vitals['measurement_time']}")

        with col2:
            st.subheader("Zimmerdaten")
            # Get room information
            if 'raum' in db_data:
                rooms = db_data['raum']
                patient_room = rooms[rooms['pat_id'] == selected_patient_id]
                if not patient_room.empty:
                    room_info = patient_room.iloc[0]
                    st.write(f"**Zimmer-Nr:** {room_info['raum_nr']}")
                    st.write(f"**Belegt seit:** {room_info['belegt_seit']}")
            
            # Show allergies if available
            if 'allergies' in db_data:
                allergies = db_data['allergies']
                patient_allergies = allergies[allergies['resident_id'] == resident_id]
                if not patient_allergies.empty:
                    st.subheader("Allergien")
                    for _, allergy in patient_allergies.iterrows():
                        st.write(f"**{allergy['allergy_type']}:** {allergy['allergy_name']} ({allergy['severity']})")

        # Aktivitäten anzeigen
        if 'activity_participation' in db_data and 'activities' in db_data:
            st.subheader("Aktivitäten")
            activities = db_data['activities']
            participation = db_data['activity_participation']
            
            patient_activities = participation[participation['resident_id'] == resident_id]
            
            if not patient_activities.empty:
                # Join with activities to get names
                activity_data = []
                for _, part in patient_activities.iterrows():
                    act_id = part['activity_id']
                    act = activities[activities['id'] == act_id]
                    if not act.empty:
                        activity_data.append({
                            "Datum": part['date'],
                            "Aktivität": act.iloc[0]['name'],
                            "Teilgenommen": "Ja" if part['attended'] == 1 else "Nein",
                            "Notizen": part['notes']
                        })
                
                if activity_data:
                    st.dataframe(pd.DataFrame(activity_data))
            else:
                st.write("Keine Aktivitätsdaten verfügbar.")
    
    with tab2:
        st.subheader("Gesundheitsdaten-Visualisierung")
        
        # Health vitals visualization
        if 'health_vitals' in db_data:
            vitals = db_data['health_vitals']
            patient_vitals = vitals[vitals['resident_id'] == resident_id]
            
            if not patient_vitals.empty:
                # Data selection
                metric_options = {
                    "Herzfrequenz": "heart_rate",
                    "Blutdruck (systolisch)": "blood_pressure_systolic",
                    "Blutdruck (diastolisch)": "blood_pressure_diastolic"
                }
                
                selected_metric = st.selectbox(
                    "Metrik auswählen:", 
                    list(metric_options.keys())
                )
                
                # Convert measurement_time to datetime
                try:
                    patient_vitals['measurement_time'] = pd.to_datetime(patient_vitals['measurement_time'])
                    patient_vitals = patient_vitals.sort_values('measurement_time')
                except:
                    pass  # If conversion fails, use as is
                
                # Line chart for selected metric
                fig = px.line(
                    patient_vitals, 
                    x="measurement_time", 
                    y=metric_options[selected_metric],
                    title=f"{selected_metric} Trend",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                avg_value = patient_vitals[metric_options[selected_metric]].mean()
                max_value = patient_vitals[metric_options[selected_metric]].max()
                min_value = patient_vitals[metric_options[selected_metric]].min()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Durchschnitt", f"{avg_value:.1f}")
                col2.metric("Maximum", f"{max_value}")
                col3.metric("Minimum", f"{min_value}")
                
                # Add histogram
                fig2 = px.histogram(
                    patient_vitals, 
                    x=metric_options[selected_metric],
                    nbins=10,
                    title=f"{selected_metric} Verteilung"
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Export options
                st.subheader("Datenexport")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        "CSV-Daten exportieren",
                        data=patient_vitals.to_csv(index=False).encode('utf-8'),
                        file_name=f"{selected_patient['nachname']}_{selected_patient['vorname']}_vitalwerte.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Sleep data if available
                    if 'sleep_quality' in db_data:
                        sleep_data = db_data['sleep_quality']
                        patient_sleep = sleep_data[sleep_data['resident_id'] == resident_id]
                        
                        if not patient_sleep.empty:
                            st.download_button(
                                "Schlafqualitätsdaten exportieren",
                                data=patient_sleep.to_csv(index=False).encode('utf-8'),
                                file_name=f"{selected_patient['nachname']}_{selected_patient['vorname']}_schlaf.csv",
                                mime="text/csv"
                            )
            else:
                st.info("Keine Gesundheitsdaten für die Visualisierung verfügbar.")

            # Add doctor visits if available
            if 'doctor_visits' in db_data:
                visits = db_data['doctor_visits']
                patient_visits = visits[visits['resident_id'] == resident_id]
                
                if not patient_visits.empty:
                    st.subheader("Arztbesuche")
                    st.dataframe(
                        patient_visits[['visit_date', 'doctor_name', 'reason', 'follow_up_date']],
                        use_container_width=True
                    )
        else:
            st.info("Keine Gesundheitsdaten in der Datenbank gefunden.")

#tab3 Sicherheitsdaten 


    with tab3:
        st.subheader("Sicherheitsdaten")
        
        # Treuhand-Transaktionen
        if 'trust_account_transactions' in db_data:
            transactions = db_data['trust_account_transactions']
            patient_transactions = transactions[transactions['resident_id'] == selected_patient_id]
            
            if not patient_transactions.empty:
                # Convert transaction_date to datetime and sort chronologically
                try:
                    patient_transactions['transaction_date'] = pd.to_datetime(patient_transactions['transaction_date'])
                    patient_transactions = patient_transactions.sort_values('transaction_date')
                except:
                    pass  # If conversion fails, use as is
                    
                st.subheader("Treuhand-Transaktionen")
                st.dataframe(patient_transactions[['transaction_date', 'amount', 'description']], use_container_width=True)
                
                # Visualize transactions over time
                fig = px.line(patient_transactions, x='transaction_date', y='amount', title="Finanzielle Transaktionen", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Keine Transaktionsdaten verfügbar.")
        
        # Ausgehzeiten
        if 'Ein_aus' in db_data:
            exit_data = db_data['Ein_aus']
            # Filter for resident_id and where ausgang = 1 (indicating exit events)
            patient_exit_data = exit_data[
                (exit_data['pat_id'] == selected_patient_id) & 
                (exit_data['ausgang'] == 1)
            ]
            
            if not patient_exit_data.empty:
                # Convert zeitstempel to datetime format and sort by date
                try:
                    patient_exit_data['zeitstempel'] = pd.to_datetime(patient_exit_data['zeitstempel'])
                    patient_exit_data = patient_exit_data.sort_values('zeitstempel')
                except:
                    pass  # If conversion fails, use as is
                    
                st.subheader("Ausgehzeiten")
                st.dataframe(patient_exit_data[['zeitstempel']], use_container_width=True)
                
                # Visualization
                fig = px.histogram(patient_exit_data, x='zeitstempel', title="Verteilung der Ausgehzeiten", nbins=20)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Keine Ausgehzeiten-Daten verfügbar.")
        else:
            st.info("Keine Ausgehzeiten-Daten verfügbar.")
        
        # Smart-Home-Daten
        if 'smart_home' in db_data:
            smart_home_data = db_data['smart_home']
            patient_smart_home = smart_home_data[smart_home_data['resident_id'] == selected_patient_id]
            
            if not patient_smart_home.empty:
                st.subheader("Smart-Home Überwachung")
                st.dataframe(patient_smart_home[['device', 'status', 'timestamp']], use_container_width=True)
                
                # Visualization
                device_counts = patient_smart_home['device'].value_counts()
                fig = px.pie(device_counts, names=device_counts.index, values=device_counts.values, title="Gerätenutzung im Smart Home")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Keine Smart-Home-Daten verfügbar.")


# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Häuser zum Leben - Intelligentes Pflegemanagement System</p>
        <p>© 2025 - Demo Version</p>
    </div>
""", unsafe_allow_html=True)