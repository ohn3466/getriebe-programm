# Online bereitstellen

## Empfohlene Variante: Streamlit Community Cloud

1. GitHub-Repository erstellen, z. B. `getriebe-programm`.
2. Projektdateien in dieses Repository hochladen.
3. Auf Streamlit Community Cloud einloggen.
4. Neues App-Projekt erstellen.
5. Repository auswaehlen.
6. Als Hauptdatei `Home.py` eintragen.
7. Deploy starten.

Danach sind Dashboard und Assistent in einer Online-App ueber die Seitenleiste erreichbar.

## Lokal testen

```powershell
python -m pip install -r requirements.txt
python -m streamlit run Home.py
```

## Wichtige Dateien fuer GitHub

- `Home.py`: Online-Startseite fuer die Multipage-App
- `pages/1_Dashboard.py`: Dashboard-Seite
- `pages/2_Assistent.py`: Wizard-Seite
- `app.py`: Dashboard-App
- `wizard_app.py`: gefuehrter Assistent
- `core/`: Rechenkern
- `data/`: Tabellen
- `requirements.txt`: Python-Abhaengigkeiten
- `.github/workflows/tests.yml`: automatische Tests auf GitHub

## Nicht hochladen

Diese Ordner/Dateien gehoeren nicht ins Repository:

- `.venv/`
- `__pycache__/`
- heruntergeladene Exportdateien

