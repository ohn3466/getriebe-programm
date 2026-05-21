from __future__ import annotations

import streamlit as st

from core.ui import apply_app_style


st.set_page_config(page_title="Getriebe Programm", page_icon="G", layout="wide")
apply_app_style(max_width_px=980, top_padding_rem=1.6)

st.title("Getriebe Programm")
st.caption("Online-Version mit Dashboard und gefuehrtem Assistenten.")

st.write(
    "Waehle links in der Seitenleiste eine Seite aus. "
    "Beide Oberflaechen verwenden denselben Rechenkern und dieselben Tabellen."
)
st.markdown(
    "<div class='home-note'><strong>Empfehlung:</strong> Nutze den Assistenten fuer den Beleg Schritt fuer Schritt. "
    "Das Dashboard ist gut zum schnellen Pruefen und Vergleichen.</div>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Dashboard")
    st.write("Alle Eingaben und Ergebnisse auf einer Oberflaeche.")
    st.page_link("pages/1_Dashboard.py", label="Dashboard oeffnen")

with col2:
    st.subheader("Assistent")
    st.write("Schritt-fuer-Schritt durch Eingaben, Tabellen und Pruefungen.")
    st.page_link("pages/2_Assistent.py", label="Assistent oeffnen")

st.divider()
st.subheader("Enthaltene Funktionen")
st.write(
    "- Modulwahl nach Reihe I und Reihe II\n"
    "- automatische Neuberechnung der gesamten Rechenkette\n"
    "- Werkstoff-, Normmodul- und Lagertabellen\n"
    "- Zahnradgeometrie, Zahneingriff, Kraefte, Lagerkraefte und Schnittlasten\n"
    "- Export als JSON, Markdown und LaTeX"
)
