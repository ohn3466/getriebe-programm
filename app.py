from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from core.calculations import (
    calc_module_from_dsh,
    calc_section_loads,
    next_preferred_norm_module,
)
from core.dependency_engine import load_bearings, load_norm_module_rows, load_norm_modules, recalculate_all
from core.models import GearInputs
from core.report import generate_calculation_report, generate_latex_report, generate_live_latex_blocks


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


STATUS_COLORS = {
    "OK": "#147d3f",
    "WARNUNG": "#9a6700",
    "FEHLER": "#b42318",
    "NICHT BERECHNET": "#667085",
}


@st.cache_data
def load_materials() -> list[dict[str, Any]]:
    path = DATA_DIR / "werkstoffe.csv"
    return pd.read_csv(path).to_dict("records")


@st.cache_data
def load_norms_cached() -> list[float]:
    return load_norm_modules(DATA_DIR / "normmodule.csv")


@st.cache_data
def load_norm_rows_cached() -> list[dict[str, Any]]:
    return load_norm_module_rows(DATA_DIR / "normmodule.csv")


@st.cache_data
def load_bearings_cached() -> list[dict[str, Any]]:
    return load_bearings(DATA_DIR / "lager.csv")


def find_material(materials: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for material in materials:
        if str(material["werkstoff"]) == name:
            return material
    return materials[0]


def matching_bearings(bearings: list[dict[str, Any]], bore_mm: float) -> list[dict[str, Any]]:
    return [bearing for bearing in bearings if float(bearing["d"]) == float(bore_mm)]


def dataframe_from_checks(checks: list[Any]) -> pd.DataFrame:
    rows = []
    for check in checks:
        rows.append(
            {
                "Bereich": check.name,
                "Status": check.status,
                "Wert": check.value,
                "Grenze": check.limit,
                "Hinweis": check.message,
            }
        )
    return pd.DataFrame(rows)


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#667085")
    return (
        f"<span class='status-badge' style='background:{color};'>"
        f"{status}</span>"
    )


def render_check_summary(checks: list[Any]) -> None:
    counts = {status: 0 for status in STATUS_COLORS}
    for check in checks:
        counts[check.status] = counts.get(check.status, 0) + 1

    cols = st.columns(4)
    cols[0].metric("OK", counts["OK"])
    cols[1].metric("Warnungen", counts["WARNUNG"])
    cols[2].metric("Fehler", counts["FEHLER"])
    cols[3].metric("Offen", counts["NICHT BERECHNET"])


def export_json(inputs: GearInputs, results: Any) -> str:
    return json.dumps(
        {
            "inputs": asdict(inputs),
            "results": asdict(results),
        },
        indent=2,
        ensure_ascii=True,
    )


def export_csv(results: Any) -> str:
    data = asdict(results)
    data.pop("checks", None)
    rows = []
    for key, value in data.items():
        if isinstance(value, (int, float, str)) or value is None:
            rows.append({"name": key, "value": value})
    return pd.DataFrame(rows).to_csv(index=False)


def section_load_dataframe(inputs: GearInputs, results: Any, points: int = 101) -> pd.DataFrame:
    return pd.DataFrame(
        calc_section_loads(
            results.Ft_N,
            results.Fr_N,
            inputs.bearing_distance_left_mm,
            inputs.bearing_distance_right_mm,
            points=points,
        )
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


st.set_page_config(page_title="Getriebe Programm", page_icon="G", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background: #f6f7fb;
        color: #111827;
    }
    [data-testid="stHeader"] {
        background: rgba(246, 247, 251, 0.88);
    }
    .block-container { padding-top: 1.4rem; max-width: 1280px; }
    .block-container,
    .block-container h1,
    .block-container h2,
    .block-container h3,
    .block-container p,
    .block-container label,
    .block-container span {
        color: #111827;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 0.65rem 0.8rem;
        border-radius: 0.5rem;
        color: #111827;
    }
    div[data-testid="stMetric"] * {
        color: #111827;
    }
    div[data-testid="stCaptionContainer"],
    div[data-testid="stCaptionContainer"] * {
        color: #475467;
    }
    div[data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background: #f8fafc;
        color: #111827;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] small {
        color: #111827 !important;
    }
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] div[data-baseweb="base-input"] {
        background: #ffffff !important;
        color: #111827 !important;
        border-color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] input::placeholder {
        color: #667085 !important;
    }
    section[data-testid="stSidebar"] svg {
        color: #344054;
        fill: #344054;
    }
    .auto-recalc-banner {
        margin: 0.4rem 0 1.1rem;
        padding: 0.7rem 0.85rem;
        border: 1px solid #b7e4c7;
        background: #ecfdf3;
        border-radius: 0.5rem;
        color: #054f31;
        font-weight: 650;
    }
    .auto-recalc-banner span {
        color: #054f31;
        font-weight: 500;
    }
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

materials = load_materials()
norm_modules = load_norms_cached()
norm_module_rows = load_norm_rows_cached()
bearings = load_bearings_cached()

with st.sidebar:
    st.header("Eingaben")

    project_name = st.text_input("Projektname", value="Getriebeauslegung")

    st.subheader("Grunddaten")
    power_kw = st.number_input("Leistung P [kW]", min_value=0.01, value=12.0, step=0.5)
    n1_rpm = st.number_input("Antriebsdrehzahl n1 [1/min]", min_value=1.0, value=1850.0, step=10.0)
    n2_target_rpm = st.number_input(
        "Abtriebsdrehzahl n2 soll [1/min]", min_value=1.0, value=410.0, step=10.0
    )
    alpha_deg = st.number_input("Eingriffswinkel alpha [deg]", min_value=1.0, value=20.0, step=0.5)
    beta_deg = st.number_input("Schraegungswinkel beta [deg]", min_value=0.0, value=0.0, step=0.5)

    st.subheader("Werkstoff")
    material_names = [str(material["werkstoff"]) for material in materials]
    material_name = st.selectbox(
        "Werkstoff",
        material_names,
        index=material_names.index("C45E") if "C45E" in material_names else 0,
    )
    material = find_material(materials, material_name)

    st.subheader("Welle und Modul")
    shaft_label = st.radio(
        "Ritzelbauart",
        ["Ritzel auf Welle", "Ritzelwelle"],
        horizontal=True,
    )
    shaft_design = "mounted" if shaft_label == "Ritzel auf Welle" else "pinion_shaft"
    d_sh_pinion_mm = st.number_input("d_sh Ritzel [mm]", min_value=1.0, value=28.0, step=1.0)
    z1 = st.number_input("Zaehnezahl Ritzel z1", min_value=6, value=25, step=1)
    z2_auto = st.toggle("z2 automatisch aus i * z1 berechnen", value=True)
    z2_manual = None
    if not z2_auto:
        z2_manual = st.number_input("Zaehnezahl Gegenrad z2", min_value=1, value=113, step=1)

    preliminary_m = calc_module_from_dsh(d_sh_pinion_mm, int(z1), beta_deg, shaft_design)
    recommended_m = next_preferred_norm_module(preliminary_m, norm_module_rows)
    auto_module = st.toggle("Normmodul automatisch uebernehmen", value=True)
    module_values = sorted(float(value) for value in norm_modules)
    recommended_index = module_values.index(recommended_m)
    if auto_module:
        selected_module = recommended_m
        st.caption(f"Empfehlung aus Tabelle: m = {recommended_m:g} mm")
    else:
        selected_module = st.selectbox(
            "Normmodul m [mm]",
            module_values,
            index=recommended_index,
            format_func=lambda value: f"{value:g} mm",
        )

    st.subheader("Breite")
    width_rule_label = st.selectbox("Breitenregel", ["b = psi_d * d1", "b = k_b * m"])
    width_rule = "psi_d" if width_rule_label == "b = psi_d * d1" else "factor_m"
    psi_d = st.number_input("psi_d [-]", min_value=0.1, value=1.0, step=0.1)
    width_factor_m = st.number_input("k_b [-]", min_value=1.0, value=12.0, step=1.0)
    b2_offset_mm = st.number_input("b2-Versatz [mm]", value=0.0, step=1.0)

    st.subheader("Lager")
    bearing_distance_left_mm = st.number_input(
        "Abstand linkes Lager bis Zahnrad [mm]", min_value=1.0, value=60.0, step=5.0
    )
    bearing_distance_right_mm = st.number_input(
        "Abstand Zahnrad bis rechtes Lager [mm]", min_value=1.0, value=80.0, step=5.0
    )
    bearing_seat_left_mm = st.number_input("Lagersitz links [mm]", min_value=1.0, value=30.0, step=1.0)
    bearing_seat_right_mm = st.number_input("Lagersitz rechts [mm]", min_value=1.0, value=30.0, step=1.0)
    bearing_life_required_h = st.number_input(
        "Mindestlebensdauer L10h [h]", min_value=1.0, value=10000.0, step=1000.0
    )

left_options = matching_bearings(bearings, bearing_seat_left_mm)
right_options = matching_bearings(bearings, bearing_seat_right_mm)

with st.sidebar:
    left_names = ["Keine Auswahl"] + [str(bearing["lager"]) for bearing in left_options]
    right_names = ["Keine Auswahl"] + [str(bearing["lager"]) for bearing in right_options]
    selected_bearing_left = st.selectbox("Lager links", left_names)
    selected_bearing_right = st.selectbox("Lager rechts", right_names)
    selected_bearing_left = None if selected_bearing_left == "Keine Auswahl" else selected_bearing_left
    selected_bearing_right = None if selected_bearing_right == "Keine Auswahl" else selected_bearing_right

inputs = GearInputs(
    project_name=project_name,
    power_kw=power_kw,
    n1_rpm=n1_rpm,
    n2_target_rpm=n2_target_rpm,
    alpha_deg=alpha_deg,
    beta_deg=beta_deg,
    z1=int(z1),
    z2_manual=None if z2_manual is None else int(z2_manual),
    shaft_material=material_name,
    tau_t_zul=float(material["tau_t_zul"]),
    sigma_b_zul=float(material["sigma_b_zul"]),
    shaft_design=shaft_design,
    d_sh_pinion_mm=d_sh_pinion_mm,
    selected_module=float(selected_module),
    width_rule=width_rule,
    psi_d=psi_d,
    width_factor_m=width_factor_m,
    b2_offset_mm=b2_offset_mm,
    bearing_distance_left_mm=bearing_distance_left_mm,
    bearing_distance_right_mm=bearing_distance_right_mm,
    bearing_seat_left_mm=bearing_seat_left_mm,
    bearing_seat_right_mm=bearing_seat_right_mm,
    bearing_life_required_h=bearing_life_required_h,
    selected_bearing_left=selected_bearing_left,
    selected_bearing_right=selected_bearing_right,
)

results = recalculate_all(inputs, norm_module_rows, bearings)

st.title("Getriebe Programm")
st.caption("Interaktive Auslegung mit automatischer Neuberechnung aller abhaengigen Werte.")
st.markdown(
    "<div class='auto-recalc-banner'>Automatische Neuberechnung aktiv. "
    "<span>Jede geaenderte Eingabe aktualisiert sofort Modul, Geometrie, Kraefte, Lager und Pruefungen.</span></div>",
    unsafe_allow_html=True,
)

render_check_summary(results.checks)

basic_tab, module_tab, geometry_tab, meshing_tab, loads_tab, section_tab, checks_tab, export_tab = st.tabs(
    [
        "Grunddaten",
        "Modul",
        "Geometrie",
        "Zahneingriff",
        "Kraefte und Lager",
        "Schnittlasten",
        "Pruefungen",
        "Export",
    ]
)

with basic_tab:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("i soll", f"{results.i_target:.4g}")
    col2.metric("M1", f"{results.M1_Nm:.2f} Nm")
    col3.metric("M2 ideal", f"{results.M2_Nm:.2f} Nm")
    col4.metric("d_min Welle 1", f"{results.d_min_shaft_1_mm:.2f} mm")

    st.dataframe(
        pd.DataFrame(
            [
                {"Groesse": "Leistung P", "Wert": f"{inputs.power_kw:g}", "Einheit": "kW"},
                {"Groesse": "n1", "Wert": f"{inputs.n1_rpm:g}", "Einheit": "1/min"},
                {"Groesse": "n2 soll", "Wert": f"{inputs.n2_target_rpm:g}", "Einheit": "1/min"},
                {"Groesse": "Werkstoff", "Wert": inputs.shaft_material, "Einheit": ""},
                {"Groesse": "tau_t_zul", "Wert": f"{inputs.tau_t_zul:g}", "Einheit": "N/mm2"},
            ]
        ),
        width="stretch",
        hide_index=True,
    )

with module_tab:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("m theoretisch", f"{results.m_theoretical_mm:.3f} mm")
    col2.metric("m empfohlen", f"{results.m_recommended_mm:g} mm")
    col3.metric("m gewaehlt", f"{results.m_selected_mm:g} mm")
    col4.metric("z2", f"{results.z2}")

    col1, col2, col3 = st.columns(3)
    col1.metric("i real", f"{results.i_real:.4g}")
    col2.metric("n2 real", f"{results.n2_real_rpm:.2f} 1/min")
    col3.metric("Abweichung", f"{results.n2_deviation_percent:.2f} %")

    module_df = pd.DataFrame(norm_module_rows).rename(columns={"reihe": "Reihe", "modul": "Normmodul [mm]"})
    module_df = module_df.sort_values(["Normmodul [mm]", "Reihe"]).reset_index(drop=True)
    module_df["Empfohlen"] = module_df["Normmodul [mm]"].eq(results.m_recommended_mm)
    module_df["Gewaehlt"] = module_df["Normmodul [mm]"].eq(results.m_selected_mm)
    st.dataframe(module_df, width="stretch", hide_index=True)

with geometry_tab:
    st.subheader("Zahnradgeometrie")
    st.dataframe(
        pd.DataFrame(
            [
                {"Groesse": "z", "Ritzel": results.z1, "Gegenrad": results.z2, "Einheit": "-"},
                {"Groesse": "m", "Ritzel": results.m_selected_mm, "Gegenrad": results.m_selected_mm, "Einheit": "mm"},
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
    st.metric("Achsabstand a", f"{results.center_distance_mm:.2f} mm")

with meshing_tab:
    col0, col1, col2, col3, col4 = st.columns(5)
    col0.metric("alpha_t", f"{results.alpha_transverse_deg:.3f} deg")
    col1.metric("p", f"{results.pitch_mm:.3f} mm")
    col2.metric("pe", f"{results.base_pitch_mm:.3f} mm")
    col3.metric("g_alpha", f"{results.path_of_contact_mm:.3f} mm")
    col4.metric("epsilon_alpha", f"{results.contact_ratio:.3f}")

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Term": "Ritzel",
                    "Formel": "sqrt((da1/2)^2 - (db1/2)^2)",
                    "Wert [mm]": results.path_contact_pinion_mm,
                },
                {
                    "Term": "Gegenrad",
                    "Formel": "sqrt((da2/2)^2 - (db2/2)^2)",
                    "Wert [mm]": results.path_contact_wheel_mm,
                },
                {
                    "Term": "- a * sin(alpha_t)",
                    "Formel": "minus Achsabstand * sin(alpha_t)",
                    "Wert [mm]": -results.path_contact_center_subtract_mm,
                },
                {
                    "Term": "g_alpha",
                    "Formel": "Ritzel + Gegenrad - a * sin(alpha_t)",
                    "Wert [mm]": results.path_of_contact_mm,
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    meshing_checks = [check for check in results.checks if "Profilueberdeckung" in check.name]
    for check in meshing_checks:
        st.markdown(f"{status_badge(check.status)} {check.message}", unsafe_allow_html=True)

with loads_tab:
    st.subheader("Zahnkraefte")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ft", f"{results.Ft_N:.1f} N")
    col2.metric("Fr", f"{results.Fr_N:.1f} N")
    col3.metric("Fa", f"{results.Fa_N:.1f} N")
    col4.metric("F res", f"{results.tooth_force_resultant_N:.1f} N")

    st.subheader("Lagerreaktionen")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Lager": "links",
                    "Rt [N]": results.bearing_left_tangential_N,
                    "Rr [N]": results.bearing_left_radial_N,
                    "R res [N]": results.bearing_load_left_N,
                    "L10h [h]": results.bearing_life_left_h,
                    "S0 [-]": results.bearing_static_safety_left,
                },
                {
                    "Lager": "rechts",
                    "Rt [N]": results.bearing_right_tangential_N,
                    "Rr [N]": results.bearing_right_radial_N,
                    "R res [N]": results.bearing_load_right_N,
                    "L10h [h]": results.bearing_life_right_h,
                    "S0 [-]": results.bearing_static_safety_right,
                },
            ]
        ),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Verfuegbare Lager fuer aktuelle Sitze")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Links: d = {inputs.bearing_seat_left_mm:g} mm")
        st.dataframe(pd.DataFrame(left_options), width="stretch", hide_index=True)
    with col2:
        st.caption(f"Rechts: d = {inputs.bearing_seat_right_mm:g} mm")
        st.dataframe(pd.DataFrame(right_options), width="stretch", hide_index=True)

with section_tab:
    st.subheader("Schnittlasten")
    col1, col2, col3 = st.columns(3)
    col1.metric("M_b max tangential", f"{results.max_bending_tangential_Nmm / 1000:.2f} Nm")
    col2.metric("M_b max radial", f"{results.max_bending_radial_Nmm / 1000:.2f} Nm")
    col3.metric("M_b max resultierend", f"{results.max_bending_resultant_Nmm / 1000:.2f} Nm")

    section_df = section_load_dataframe(inputs, results)
    st.caption("Querkraftverlauf")
    st.line_chart(section_df.set_index("x_mm")[["V_t_N", "V_r_N"]])
    st.caption("Momentenverlauf")
    st.line_chart(section_df.set_index("x_mm")[["M_t_Nmm", "M_r_Nmm", "M_res_Nmm"]])
    st.dataframe(section_df, width="stretch", hide_index=True)

with checks_tab:
    checks_df = dataframe_from_checks(results.checks)
    st.dataframe(checks_df, width="stretch", hide_index=True)

    problems = [check for check in results.checks if check.status in {"WARNUNG", "FEHLER"}]
    if problems:
        st.subheader("Problemstellen")
        for check in problems:
            st.markdown(f"{status_badge(check.status)} **{check.name}:** {check.message}", unsafe_allow_html=True)
    else:
        st.success("Alle berechneten Pruefungen sind OK.")

with export_tab:
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
        "JSON-Projekt exportieren",
        data=export_json(inputs, results),
        file_name="getriebe_projekt.json",
        mime="application/json",
    )
    st.download_button(
        "Ergebnistabelle CSV exportieren",
        data=export_csv(results),
        file_name="getriebe_ergebnisse.csv",
        mime="text/csv",
    )

render_live_latex(inputs, results, bearings)
