# Getriebe Programm

Interaktive Streamlit-App fuer eine erste Getriebeauslegung. Die App trennt
Oberflaeche, Rechenkern, Tabellen und Validierung, damit eine geaenderte
Eingabe automatisch alle abhaengigen Werte neu berechnet.

## Start

```powershell
python -m pip install -r requirements.txt
python -m streamlit run Home.py
```

Falls `python` unter Windows nicht verfuegbar ist, zuerst Python installieren
oder den im System vorhandenen Python-Launcher verwenden.

## Programme

Online-/Multipage-App:

```powershell
python -m streamlit run Home.py
```

Dashboard-App:

```powershell
python -m streamlit run app.py
```

Gefuehrter Assistent:

```powershell
python -m streamlit run wizard_app.py
```

## Pruefen

```powershell
python -m unittest discover -s tests -v
```

Die Tests pruefen einzelne Formeln, die automatische Rechenkette, Lagerauswahl,
Schnittlasten und einen Streamlit-Smoke-Test der Oberflaeche.

## Aktueller Umfang

- Grunddaten: Leistung, Drehzahlen, Uebersetzung und Drehmomente
- Werkstoffwahl aus CSV-Tabelle
- Wellenvordimensionierung aus Torsion
- Modulbestimmung aus `d_sh`, `z1` und Bauart
- Normmodul-Empfehlung aus DIN-780-Tabelle
- Manuelle oder automatische Modulwahl
- Automatische oder manuelle Wahl von `z2`
- Zahnradgeometrie fuer Ritzel und Gegenrad
- Zahneingriff mit Profilueberdeckung
- Zahnkraefte fuer Stirnradverzahnung
- Lagerreaktionen aus Zahnkraft und Lagerabstaenden
- Lagerauswahl aus CSV-Tabelle mit Lebensdauer- und Bohrungspruefung
- Export der aktuellen Ergebnisse als JSON und CSV
- Export eines Markdown-Rechenberichts mit Rechenweg, eingesetzten Werten und Pruefungen
- Export eines LaTeX-Rechenberichts mit sauber gesetzten Formeln

## Online Deployment

Fuer Streamlit Community Cloud als Hauptdatei `Home.py` angeben.
Eine genauere Anleitung steht in `DEPLOYMENT.md`.

## Struktur

```text
Home.py
app.py
wizard_app.py
pages/
  1_Dashboard.py
  2_Assistent.py
core/
  calculations.py
  dependency_engine.py
  models.py
  report.py
  units.py
  validators.py
data/
  lager.csv
  normmodule.csv
  werkstoffe.csv
  zahnrad_defaults.csv
tests/
  test_calculations.py
```
