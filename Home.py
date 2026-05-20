from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Getriebe Programm", page_icon="G", layout="wide")

st.markdown(
    """
    <style>
    .stApp { background: #f6f7fb; color: #111827; }
    [data-testid="stHeader"] { background: rgba(246, 247, 251, 0.9); }
    .block-container { padding-top: 1.6rem; max-width: 980px; }
    .block-container, .block-container h1, .block-container h2,
    .block-container h3, .block-container p, .block-container li,
    .block-container span { color: #111827; }
    div[data-testid="stButton"] > button,
    div[data-testid="stPageLink"] a {
        background: #075e2d !important;
        color: #ffffff !important;
        border: 1px solid #064d26 !important;
        border-radius: 0.45rem !important;
        font-weight: 650 !important;
        text-decoration: none !important;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stPageLink"] a:hover {
        background: #05431f !important;
        color: #ffffff !important;
        border-color: #043619 !important;
    }
    div[data-testid="stButton"] > button:focus,
    div[data-testid="stPageLink"] a:focus {
        color: #ffffff !important;
        border-color: #ffffff !important;
        box-shadow: 0 0 0 0.16rem rgba(7, 94, 45, 0.35) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Getriebe Programm")
st.caption("Online-Version mit Dashboard und gefuehrtem Assistenten.")

st.write(
    "Waehle links in der Seitenleiste eine Seite aus. "
    "Beide Oberflaechen verwenden denselben Rechenkern und dieselben Tabellen."
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
