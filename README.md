# Häuser zum Leben - Intelligentes Pflegemanagement

Ein datengetriebenes Dashboard zur Analyse und Optimierung von Pflegeeinrichtungen.

## Features

- **Übersicht**: Wichtige Kennzahlen und Statistiken auf einen Blick
  - Gesamtbewohner
  - Altersstatistiken (Durchschnitt, Minimum, Maximum)
  - Pflegegrade
- **Ernährungsanalyse**: 
  - Verbrauchsanalyse pro Mahlzeit
  - Ernährungsgewohnheiten nach Pflegegrad
- **Gesundheitsmonitoring**:
  - Vitalparameter Trends
  - Gewichtsentwicklung
- **Waste Management**: Analyse nicht verzehrter Portionen
- **Anomalieerkennung**: Identifizierung ungewöhnlicher Muster
- **Wetterkorrelation**: Analyse des Wettereinflusses auf Ernährungsgewohnheiten
- **Berichtgenerierung**: Export von Excel-Berichten
  - Übersichtsbericht
  - Ernährungsbericht
  - Gesundheitsbericht
  - Wettereinflussbericht

## Installation

1. Klonen Sie das Repository
2. Installieren Sie die Abhängigkeiten:
```bash
pip install -r requirements.txt
```

## Verwendung

Starten Sie die Anwendung mit:
```bash
streamlit run app.py
```

## Datenstruktur

Die Anwendung verwendet folgende CSV-Dateien:
- `data/residents.csv`: Informationen über Bewohner
- `data/meal_orders.csv`: Bestell- und Verbrauchsdaten
- `data/health_monitoring.csv`: Gesundheitsüberwachungsdaten
- `data/menu_items.csv`: Menü- und Ernährungsinformationen
- `data/weather_data.csv`: Wetterdaten

Die Anwendung darpber hinaus eine Datenbank:
- hauszumleben.db welche strukturierte Daten zu Bewohnern und Essensgewohnheiten beinhaltet

## Berichte

Die Anwendung bietet die Möglichkeit, verschiedene Excel-Berichte zu generieren:
- **Übersichtsbericht**: Allgemeine Statistiken und Altersverteilung
- **Ernährungsbericht**: Verbrauchs- und Abfallanalyse
- **Gesundheitsbericht**: Vitalparameter und Gewichtsentwicklung
- **Wettereinflussbericht**: Korrelationen zwischen Wetter und Ernährungsgewohnheiten

Die generierten Berichte werden im `reports/` Verzeichnis gespeichert und können direkt aus der Anwendung heruntergeladen werden.

## Technologie-Stack

- Streamlit für das Frontend
- Pandas für Datenverarbeitung
- Plotly für interaktive Visualisierungen
- Altair für zusätzliche Visualisierungen
- Scikit-learn für Anomalieerkennung
- Scipy für statistische Analysen

## Datenschutz

Diese Demo-Version verwendet Beispieldaten. In der Produktionsversion müssen alle relevanten Datenschutzbestimmungen eingehalten werden.
