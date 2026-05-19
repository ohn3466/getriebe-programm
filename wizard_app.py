from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from core.dependency_engine import load_bearings, load_norm_module_rows, recalculate_all
from core.models import GearInputs
from core.report import generate_calculation_report, generate_latex_report, generate_live_latex_blocks


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

STEPS = [
    "Grunddaten",
    "Werkstoff",
    "Welle und Zaehne",
    "Normmodul",
    "Geometrie",
    "Lager",
    "Ergebnis",
]

STATUS_COLORS = {
    "OK": "#147d3f",
    "WARNUNG": "#9a6700",
    "FEHLER": "#b42318",
    "NICHT BERECHNET": "#667085",
}


@st.cache_data
def load_materials() -> list[dict[str, Any]]:
    return pd.read_csv(DATA_DIR / "werkstoffe.csv").to_dict("records")


@st.cache_data
def load_norm_rows_cached() -> list[dict[str, Any]]:
    return load_norm_module_rows(DATA_DIR / "normmodule.csv")


@st.cache_data
def load_bearings_cached() -> list[dict[str, Any]]:
    return load_bearings(DATA_DIR / "lager.csv")


def find_material(materials: list[dict[str, Any]], name: str | None) -> dict[str, Any]:
    if name:
        for material in materials:
            if str(material["werkstoff"]) == name:
                return material
    return next((material for material in materials if str(material["werkstoff"]) == "C45E"), materials[0])


def find_bearing(bearings: list[dict[str, Any]], name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    for bearing in bearings:
        if str(bearing["lager"]) == str(name):
            return bearing
    return None


def fmt(value: float | None, digits: int = 3, unit: str = "") -> str:
    if value is None:
        return "-"
    text = f"{value:.{digits}f}"
    if unit:
        return f"{text} {unit}"
    return text


def init_state() -> None:
    defaults = {
        "step": 0,
        "project_name": "Getriebeauslegung",
        "power_kw": 12.0,
        "n1_rpm": 1850.0,
        "n2_target_rpm": 410.0,
        "alpha_deg": 20.0,
        "beta_deg": 0.0,
        "material_name": None,
        "shaft_design": "mounted",
        "d_sh_pinion_mm": 28.0,
        "z1": 25,
        "z2_auto": True,
        "z2_manual": 113,
        "selected_module": None,
        "width_rule": "psi_d",
        "psi_d": 1.0,
        "width_factor_m": 12.0,
        "b2_offset_mm": 0.0,
        "bearing_distance_left_mm": 60.0,
        "bearing_distance_right_mm": 80.0,
        "bearing_seat_left_mm": 30.0,
        "bearing_seat_right_mm": 30.0,
        "bearing_life_required_h": 10000.0,
        "selected_bearing_left": None,
        "selected_bearing_right": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(f"wizard_{key}", value)


def current_inputs(materials: list[dict[str, Any]]) -> GearInputs:
    material = find_material(materials, st.session_state.wizard_material_name)
    return GearInputs(
        project_name=st.session_state.wizard_project_name,
        power_kw=st.session_state.wizard_power_kw,
        n1_rpm=st.session_state.wizard_n1_rpm,
        n2_target_rpm=st.session_state.wizard_n2_target_rpm,
        alpha_deg=st.session_state.wizard_alpha_deg,
        beta_deg=st.session_state.wizard_beta_deg,
        z1=int(st.session_state.wizard_z1),
        z2_manual=None if st.session_state.wizard_z2_auto else int(st.session_state.wizard_z2_manual),
        shaft_material=str(material["werkstoff"]),
        tau_t_zul=float(material["tau_t_zul"]),
        sigma_b_zul=float(material["sigma_b_zul"]),
        shaft_design=st.session_state.wizard_shaft_design,
        d_sh_pinion_mm=st.session_state.wizard_d_sh_pinion_mm,
        selected_module=st.session_state.wizard_selected_module,
        width_rule=st.session_state.wizard_width_rule,
        psi_d=st.session_state.wizard_psi_d,
        width_factor_m=st.session_state.wizard_width_factor_m,
        b2_offset_mm=st.session_state.wizard_b2_offset_mm,
        bearing_distance_left_mm=st.session_state.wizard_bearing_distance_left_mm,
        bearing_distance_right_mm=st.session_state.wizard_bearing_distance_right_mm,
        bearing_seat_left_mm=st.session_state.wizard_bearing_seat_left_mm,
        bearing_seat_right_mm=st.session_state.wizard_bearing_seat_right_mm,
        bearing_life_required_h=st.session_state.wizard_bearing_life_required_h,
        selected_bearing_left=st.session_state.wizard_selected_bearing_left,
        selected_bearing_right=st.session_state.wizard_selected_bearing_right,
    )


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#667085")
    return f"<span class='status-badge' style='background:{color};'>{status}</span>"


def check_table(checks: list[Any]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Bereich": check.name,
                "Status": check.status,
                "Wert": check.value,
                "Grenze": check.limit,
                "Hinweis": check.message,
            }
            for check in checks
        ]
    )


def selected_module_text(results: Any) -> str:
    chosen = st.session_state.wizard_selected_module
    if chosen is None:
        return "Noch nicht fest gewaehlt"
    if chosen < results.m_theoretical_mm:
        return f"{chosen:g} mm, zu klein"
    return f"{chosen:g} mm"


def module_table(norm_modules: list[dict[str, Any]], results: Any) -> pd.DataFrame:
    rows = []
    for row in sorted(norm_modules, key=lambda item: (float(item["modul"]), str(item["reihe"]))):
        module = float(row["modul"])
        if module < results.m_theoretical_mm:
            status = "zu klein"
        elif module == results.m_recommended_mm:
            status = "empfohlen"
        else:
            status = "moeglich"
        if st.session_state.wizard_selected_module == module:
            status = f"{status}, gewaehlt"
        rows.append({"Reihe": row["reihe"], "m [mm]": module, "Status": status})
    return pd.DataFrame(rows)


def bearing_options(bearings: list[dict[str, Any]], seat_mm: float) -> list[dict[str, Any]]:
    exact = [bearing for bearing in bearings if float(bearing["d"]) == float(seat_mm)]
    if exact:
        return exact
    return [bearing for bearing in bearings if float(bearing["d"]) >= float(seat_mm)]


def bearing_table(bearings: list[dict[str, Any]], seat_mm: float, selected_name: str | None) -> pd.DataFrame:
    rows = []
    for bearing in bearing_options(bearings, seat_mm):
        status = "passt" if float(bearing["d"]) == float(seat_mm) else "Bohrung groesser"
        if selected_name and str(bearing["lager"]) == str(selected_name):
            status = f"{status}, gewaehlt"
        rows.append({**bearing, "Status": status})
    return pd.DataFrame(rows)


def result_export_json(inputs: GearInputs, results: Any) -> str:
    return json.dumps(
        {
            "inputs": asdict(inputs),
            "results": asdict(results),
        },
        indent=2,
        ensure_ascii=True,
    )


def render_live_latex(inputs: GearInputs, results: Any, bearings: list[dict[str, Any]]) -> None:
    st.divider()
    st.header("Live-Rechenweg")
    st.caption("Diese LaTeX-Formeln werden bei jeder Eingabeaenderung automatisch neu berechnet.")
    blocks = generate_live_latex_blocks(inputs, results, bearings)
    tabs = st.tabs([title for title, _ in blocks])
    for tab, (title, formulas) in zip(tabs, blocks):
        with tab:
            st.subheader(title)
            for formula in formulas:
                st.latex(formula)


def next_button(enabled: bool = True) -> None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.wizard_step > 0 and st.button("Zurueck", width="stretch"):
            st.session_state.wizard_step -= 1
            st.rerun()
    with col3:
        if st.session_state.wizard_step < len(STEPS) - 1:
            if st.button("Weiter", disabled=not enabled, width="stretch"):
                st.session_state.wizard_step += 1
                st.rerun()


@st.dialog("Werkstoff aus Tabelle waehlen")
def material_dialog(materials: list[dict[str, Any]]) -> None:
    df = pd.DataFrame(materials)
    st.dataframe(df, width="stretch", hide_index=True)

    names = [str(material["werkstoff"]) for material in materials]
    current = st.session_state.wizard_material_name or "C45E"
    index = names.index(current) if current in names else 0
    choice = st.selectbox("Werkstoff", names, index=index)
    material = find_material(materials, choice)
    st.write(f"Auswahl: {choice}, tau_t_zul = {material['tau_t_zul']} N/mm2")

    if st.button("Werkstoff uebernehmen", width="stretch"):
        st.session_state.wizard_material_name = choice
        st.rerun()


@st.dialog("Normmodul aus Tabelle waehlen")
def norm_module_dialog(norm_modules: list[dict[str, Any]], results: Any) -> None:
    st.write(f"Berechneter theoretischer Modul: m' = {results.m_theoretical_mm:.3f} mm")
    st.write(f"Empfohlener Normmodul: m = {results.m_recommended_mm:g} mm")
    st.dataframe(module_table(norm_modules, results), width="stretch", hide_index=True)

    modules = sorted(float(row["modul"]) for row in norm_modules)
    current = st.session_state.wizard_selected_module or results.m_recommended_mm
    index = modules.index(current) if current in modules else modules.index(results.m_recommended_mm)
    choice = st.selectbox("Normmodul m [mm]", modules, index=index, format_func=lambda value: f"{value:g} mm")

    if choice < results.m_theoretical_mm:
        st.error("Dieser Modul ist kleiner als m'. Waehle besser den empfohlenen oder einen groesseren Normmodul.")
    else:
        st.success("Dieser Modul ist fuer die aktuelle Vordimensionierung zulaessig.")

    if st.button("Normmodul uebernehmen", width="stretch"):
        st.session_state.wizard_selected_module = float(choice)
        st.rerun()


@st.dialog("Lager aus Tabelle waehlen")
def bearing_dialog(side: str, bearings: list[dict[str, Any]], seat_mm: float) -> None:
    state_key = f"wizard_selected_bearing_{side}"
    df = bearing_table(bearings, seat_mm, st.session_state.get(state_key))
    st.write(f"Erforderlicher Lagersitz: d = {seat_mm:g} mm")
    st.dataframe(df, width="stretch", hide_index=True)

    if df.empty:
        st.error("Keine passenden Lager in der Tabelle gefunden.")
        return

    names = [str(value) for value in df["lager"].tolist()]
    current = st.session_state.get(state_key)
    index = names.index(current) if current in names else 0
    choice = st.selectbox("Lager", names, index=index)
    bearing = find_bearing(bearings, choice)
    if bearing:
        st.write(f"Auswahl: {choice}, d = {bearing['d']:g} mm, C = {bearing['C']:g} kN, C0 = {bearing['C0']:g} kN")

    if st.button("Lager uebernehmen", width="stretch"):
        st.session_state[state_key] = choice
        st.rerun()


st.set_page_config(page_title="Getriebe Wizard", page_icon="W", layout="wide")
st.markdown(
    """
    <style>
    .stApp { background: #f6f7fb; color: #111827; }
    [data-testid="stHeader"] { background: rgba(246, 247, 251, 0.9); }
    .block-container { padding-top: 1.2rem; max-width: 1180px; }
    .block-container, .block-container h1, .block-container h2, .block-container h3,
    .block-container p, .block-container label, .block-container span { color: #111827; }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 0.65rem 0.8rem;
        border-radius: 0.5rem;
        color: #111827;
    }
    div[data-testid="stMetric"] * { color: #111827; }
    .wizard-panel {
        background: #ffffff;
        border: 1px solid #d0d5dd;
        border-radius: 0.5rem;
        padding: 0.85rem 1rem;
        margin: 0.5rem 0 1rem;
    }
    .wizard-panel strong { color: #111827; }
    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        background: #147d3f !important;
        color: #ffffff !important;
        border: 1px solid #0f6b35 !important;
        border-radius: 0.45rem !important;
        font-weight: 650 !important;
        box-shadow: none !important;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        background: #0f6b35 !important;
        color: #ffffff !important;
        border-color: #0b5a2c !important;
    }
    div[data-testid="stButton"] > button:focus,
    div[data-testid="stDownloadButton"] > button:focus {
        color: #ffffff !important;
        border-color: #054f31 !important;
        box-shadow: 0 0 0 0.14rem rgba(20, 125, 63, 0.22) !important;
    }
    div[data-testid="stButton"] > button:disabled,
    div[data-testid="stDownloadButton"] > button:disabled {
        background: #e5e7eb !important;
        color: #667085 !important;
        border-color: #d0d5dd !important;
    }
    .status-badge {
        display: inline-block;
        padding: 0.18rem 0.5rem;
        border-radius: 999px;
        color: #ffffff !important;
        font-size: 0.78rem;
        font-weight: 650;
        line-height: 1.25;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

init_state()
materials = load_materials()
norm_module_rows = load_norm_rows_cached()
bearings = load_bearings_cached()
inputs = current_inputs(materials)
results = recalculate_all(inputs, norm_module_rows, bearings)

st.title("Getriebe Wizard")
st.caption("Gefuehrte Eingabe mit Pflichtentscheidungen aus Tabellen und automatischer Neuberechnung.")

step = int(st.session_state.wizard_step)
st.progress((step + 1) / len(STEPS), text=f"Schritt {step + 1} von {len(STEPS)}: {STEPS[step]}")

with st.expander("Aktueller Rechenstand", expanded=False):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("m'", f"{results.m_theoretical_mm:.3f} mm")
    col2.metric("m gewaehlt", selected_module_text(results))
    col3.metric("z2", str(results.z2))
    col4.metric("g_alpha", f"{results.path_of_contact_mm:.3f} mm")

if step == 0:
    st.header("1. Grunddaten")
    st.markdown(
        "<div class='wizard-panel'><strong>Diese Werte bestimmen Uebersetzung, Drehmomente und alle weiteren Schritte.</strong></div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Projektname", key="wizard_project_name")
        st.number_input("Leistung P [kW]", min_value=0.01, step=0.5, key="wizard_power_kw")
        st.number_input("Antriebsdrehzahl n1 [1/min]", min_value=1.0, step=10.0, key="wizard_n1_rpm")
    with col2:
        st.number_input("Abtriebsdrehzahl n2 soll [1/min]", min_value=1.0, step=10.0, key="wizard_n2_target_rpm")
        st.number_input("Eingriffswinkel alpha [deg]", min_value=1.0, step=0.5, key="wizard_alpha_deg")
        st.number_input("Schraegungswinkel beta [deg]", min_value=0.0, step=0.5, key="wizard_beta_deg")

    col1, col2, col3 = st.columns(3)
    col1.metric("i soll", f"{results.i_target:.4g}")
    col2.metric("M1", f"{results.M1_Nm:.2f} Nm")
    col3.metric("M2 ideal", f"{results.M2_Nm:.2f} Nm")
    next_button()

elif step == 1:
    st.header("2. Werkstoff aus Tabelle waehlen")
    selected = st.session_state.wizard_material_name
    if selected is None:
        st.warning("Bitte einen Werkstoff aus der Tabelle uebernehmen, bevor du weitergehst.")
    else:
        material = find_material(materials, selected)
        st.success(f"Gewaehlt: {selected}, tau_t_zul = {material['tau_t_zul']} N/mm2")

    if st.button("Werkstoff-Tabelle oeffnen", width="stretch"):
        material_dialog(materials)

    st.dataframe(pd.DataFrame(materials), width="stretch", hide_index=True)
    next_button(enabled=selected is not None)

elif step == 2:
    st.header("3. Welle, d_sh und Zaehnezahlen")
    col1, col2 = st.columns(2)
    with col1:
        st.radio(
            "Ritzelbauart",
            ["mounted", "pinion_shaft"],
            format_func=lambda value: "Ritzel auf Welle" if value == "mounted" else "Ritzelwelle",
            horizontal=True,
            key="wizard_shaft_design",
        )
        st.number_input("d_sh Ritzel [mm]", min_value=1.0, step=1.0, key="wizard_d_sh_pinion_mm")
        st.number_input("Zaehnezahl Ritzel z1", min_value=6, step=1, key="wizard_z1")
    with col2:
        st.toggle("z2 automatisch aus i * z1 berechnen", key="wizard_z2_auto")
        if not st.session_state.wizard_z2_auto:
            st.number_input("Zaehnezahl Gegenrad z2", min_value=1, step=1, key="wizard_z2_manual")

        st.metric("m' aus d_sh", f"{results.m_theoretical_mm:.3f} mm")
        st.metric("empfohlener Normmodul", f"{results.m_recommended_mm:g} mm")
        st.metric("z2 aktuell", str(results.z2))

    next_button()

elif step == 3:
    st.header("4. Normmodul festlegen")
    st.markdown(
        "<div class='wizard-panel'><strong>Hier muss ein Normmodul aus der Tabelle bewusst uebernommen werden.</strong></div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns(3)
    col1.metric("m'", f"{results.m_theoretical_mm:.3f} mm")
    col2.metric("Empfehlung", f"{results.m_recommended_mm:g} mm")
    col3.metric("Gewaehlt", selected_module_text(results))

    if st.button("Normmodul-Tabelle oeffnen", width="stretch"):
        norm_module_dialog(norm_module_rows, results)

    st.dataframe(module_table(norm_module_rows, results), width="stretch", hide_index=True)
    valid_module = st.session_state.wizard_selected_module is not None and st.session_state.wizard_selected_module >= results.m_theoretical_mm
    if not valid_module:
        st.warning("Waehle einen Normmodul aus der Tabelle. Er muss mindestens so gross wie m' sein.")
    next_button(enabled=valid_module)

elif step == 4:
    st.header("5. Zahnradgeometrie und Zahneingriff")
    st.subheader("Geometrie")
    st.selectbox(
        "Breitenregel",
        ["psi_d", "factor_m"],
        format_func=lambda value: "b = psi_d * d1" if value == "psi_d" else "b = k_b * m",
        key="wizard_width_rule",
    )
    col1, col2, col3 = st.columns(3)
    col1.number_input("psi_d [-]", min_value=0.1, step=0.1, key="wizard_psi_d")
    col2.number_input("k_b [-]", min_value=1.0, step=1.0, key="wizard_width_factor_m")
    col3.number_input("b2-Versatz [mm]", step=1.0, key="wizard_b2_offset_mm")

    st.dataframe(
        pd.DataFrame(
            [
                {"Groesse": "z", "Ritzel": results.z1, "Gegenrad": results.z2, "Einheit": "-"},
                {"Groesse": "d", "Ritzel": results.d1_mm, "Gegenrad": results.d2_mm, "Einheit": "mm"},
                {"Groesse": "db", "Ritzel": results.db1_mm, "Gegenrad": results.db2_mm, "Einheit": "mm"},
                {"Groesse": "da", "Ritzel": results.da1_mm, "Gegenrad": results.da2_mm, "Einheit": "mm"},
                {"Groesse": "df", "Ritzel": results.df1_mm, "Gegenrad": results.df2_mm, "Einheit": "mm"},
                {"Groesse": "b", "Ritzel": results.b1_mm, "Gegenrad": results.b2_mm, "Einheit": "mm"},
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Zahneingriff")
    col0, col1, col2, col3, col4 = st.columns(5)
    col0.metric("alpha_t", f"{results.alpha_transverse_deg:.3f} deg")
    col1.metric("p", f"{results.pitch_mm:.3f} mm")
    col2.metric("pe", f"{results.base_pitch_mm:.3f} mm")
    col3.metric("g_alpha", f"{results.path_of_contact_mm:.3f} mm")
    col4.metric("epsilon_alpha", f"{results.contact_ratio:.3f}")
    st.dataframe(
        pd.DataFrame(
            [
                {"Term": "Ritzel", "Wert [mm]": results.path_contact_pinion_mm},
                {"Term": "Gegenrad", "Wert [mm]": results.path_contact_wheel_mm},
                {"Term": "- a * sin(alpha_t)", "Wert [mm]": -results.path_contact_center_subtract_mm},
                {"Term": "g_alpha", "Wert [mm]": results.path_of_contact_mm},
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    next_button()

elif step == 5:
    st.header("6. Lager, Lagerabstaende und Kraefte")
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Abstand linkes Lager bis Zahnrad [mm]", min_value=1.0, step=5.0, key="wizard_bearing_distance_left_mm")
        st.number_input("Lagersitz links [mm]", min_value=1.0, step=1.0, key="wizard_bearing_seat_left_mm")
        if st.button("Lager links aus Tabelle waehlen", width="stretch"):
            bearing_dialog("left", bearings, st.session_state.wizard_bearing_seat_left_mm)
    with col2:
        st.number_input("Abstand Zahnrad bis rechtes Lager [mm]", min_value=1.0, step=5.0, key="wizard_bearing_distance_right_mm")
        st.number_input("Lagersitz rechts [mm]", min_value=1.0, step=1.0, key="wizard_bearing_seat_right_mm")
        if st.button("Lager rechts aus Tabelle waehlen", width="stretch"):
            bearing_dialog("right", bearings, st.session_state.wizard_bearing_seat_right_mm)

    st.number_input("Mindestlebensdauer L10h [h]", min_value=1.0, step=1000.0, key="wizard_bearing_life_required_h")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ft", f"{results.Ft_N:.1f} N")
    col2.metric("Fr", f"{results.Fr_N:.1f} N")
    col3.metric("Lagerkraft links", f"{results.bearing_load_left_N:.1f} N")
    col4.metric("Lagerkraft rechts", f"{results.bearing_load_right_N:.1f} N")

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Lager": "links",
                    "Auswahl": st.session_state.wizard_selected_bearing_left or "-",
                    "R res [N]": results.bearing_load_left_N,
                    "L10h [h]": results.bearing_life_left_h,
                    "S0 [-]": results.bearing_static_safety_left,
                },
                {
                    "Lager": "rechts",
                    "Auswahl": st.session_state.wizard_selected_bearing_right or "-",
                    "R res [N]": results.bearing_load_right_N,
                    "L10h [h]": results.bearing_life_right_h,
                    "S0 [-]": results.bearing_static_safety_right,
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )
    next_button(enabled=st.session_state.wizard_selected_bearing_left is not None and st.session_state.wizard_selected_bearing_right is not None)

else:
    st.header("7. Ergebnis und Pruefungen")
    counts = {status: 0 for status in STATUS_COLORS}
    for check in results.checks:
        counts[check.status] = counts.get(check.status, 0) + 1
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("OK", counts["OK"])
    col2.metric("Warnungen", counts["WARNUNG"])
    col3.metric("Fehler", counts["FEHLER"])
    col4.metric("Offen", counts["NICHT BERECHNET"])

    for check in results.checks:
        if check.status in {"WARNUNG", "FEHLER", "NICHT BERECHNET"}:
            st.markdown(f"{status_badge(check.status)} **{check.name}:** {check.message}", unsafe_allow_html=True)

    st.dataframe(check_table(results.checks), width="stretch", hide_index=True)
    st.download_button(
        "Rechenweg als LaTeX exportieren",
        data=generate_latex_report(inputs, results, bearings),
        file_name="getriebe_rechenbericht.tex",
        mime="text/x-tex",
    )
    st.download_button(
        "Rechenweg als Markdown exportieren",
        data=generate_calculation_report(inputs, results, bearings),
        file_name="getriebe_rechenbericht.md",
        mime="text/markdown",
    )
    st.download_button(
        "Projekt als JSON exportieren",
        data=result_export_json(inputs, results),
        file_name="getriebe_wizard_projekt.json",
        mime="application/json",
    )
    next_button()

render_live_latex(inputs, results, bearings)
