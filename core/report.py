from __future__ import annotations

from typing import Any

from core.dependency_engine import find_bearing
from core.models import GearInputs, GearResults


def de(value: float | int | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    if isinstance(value, int):
        return str(value)
    text = f"{value:.{digits}f}"
    text = text.rstrip("0").rstrip(".") if "." in text else text
    return text.replace(".", ",")


def tex_num(value: float | int | None, digits: int = 3) -> str:
    return de(value, digits).replace(",", "{,}")


def tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def formula_title(formula: str) -> str:
    key = formula.split("=")[0].strip()
    titles = {
        "i_soll": "Soll-Uebersetzung",
        "M": "Drehmoment",
        "M_2": "ideales Abtriebsdrehmoment",
        "d_min": "Mindestwellendurchmesser",
        "m'": "theoretisch erforderlicher Modul",
        "z_2": "Zaehnezahl Gegenrad",
        "i_real": "reale Uebersetzung",
        "Delta_i": "Abweichung der realen Uebersetzung von der Soll-Uebersetzung",
        "n_2,real": "reale Abtriebsdrehzahl",
        "Delta_n2": "Abweichung der realen Abtriebsdrehzahl von der Soll-Abtriebsdrehzahl",
        "d_1": "Teilkreisdurchmesser Ritzel",
        "d_b1": "Grundkreisdurchmesser Ritzel",
        "d_a1": "Kopfkreisdurchmesser Ritzel",
        "d_f1": "Fusskreisdurchmesser Ritzel",
        "b_1": "Zahnbreite Ritzel",
        "d_2": "Teilkreisdurchmesser Gegenrad",
        "d_b2": "Grundkreisdurchmesser Gegenrad",
        "d_a2": "Kopfkreisdurchmesser Gegenrad",
        "d_f2": "Fusskreisdurchmesser Gegenrad",
        "b_2": "Zahnbreite Gegenrad",
        "a": "Achsabstand",
        "p_t": "Stirnteilung",
        "p_e": "Eingriffsteilung",
        "g_alpha": "Eingriffsstrecke",
        "epsilon_alpha": "Profilueberdeckung",
        "F_t": "Tangentialkraft",
        "F_r": "Radialkraft",
        "F_a": "Axialkraft",
        "R_L,t": "tangentiale Lagerreaktion links",
        "R_R,t": "tangentiale Lagerreaktion rechts",
        "R_L": "resultierende Lagerkraft links",
        "R_R": "resultierende Lagerkraft rechts",
        "L_10h,links": "Lagerlebensdauer links",
        "S_0,links": "statische Lagersicherheit links",
        "L_10h,rechts": "Lagerlebensdauer rechts",
        "S_0,rechts": "statische Lagersicherheit rechts",
        "M_b,t,max": "maximales tangentiales Biegemoment",
        "M_b,r,max": "maximales radiales Biegemoment",
        "M_b,res": "resultierendes Biegemoment",
    }
    return titles.get(key, key)


def line_formula(formula: str, substitution: str, result: str) -> str:
    return f"- **Berechnet: {formula_title(formula)}**\n  - Formel: `{formula}`\n  - Einsetzen: `{substitution}`\n  - Ergebnis: **{result}**"


def bearing_label(bearing: dict[str, Any] | None) -> str:
    if bearing is None:
        return "nicht ausgewaehlt"
    return (
        f"{bearing['lager']} "
        f"(d = {de(float(bearing['d']), 0)} mm, "
        f"D = {de(float(bearing['D']), 0)} mm, "
        f"B = {de(float(bearing['B']), 0)} mm, "
        f"C = {de(float(bearing['C']), 2)} kN, "
        f"C_0 = {de(float(bearing['C0']), 2)} kN)"
    )


def module_design_name(value: str) -> str:
    if value == "mounted":
        return "Ritzel auf Welle"
    if value == "pinion_shaft":
        return "Ritzelwelle"
    return value


def module_design_name_latex(value: str) -> str:
    return tex_escape(module_design_name(value))


def width_rule_text(inputs: GearInputs, results: GearResults) -> tuple[str, str, str]:
    if inputs.width_rule == "psi_d":
        return (
            "b_1 = psi_d * d_1",
            f"b_1 = {de(inputs.psi_d)} * {de(results.d1_mm)} mm",
            f"b_1 = {de(results.b1_mm)} mm",
        )
    return (
        "b_1 = k_b * m",
        f"b_1 = {de(inputs.width_factor_m)} * {de(results.m_selected_mm)} mm",
        f"b_1 = {de(results.b1_mm)} mm",
    )


def generate_calculation_report(inputs: GearInputs, results: GearResults, bearings: list[dict[str, Any]]) -> str:
    left_bearing = find_bearing(bearings, inputs.selected_bearing_left)
    right_bearing = find_bearing(bearings, inputs.selected_bearing_right)
    b_formula, b_substitution, b_result = width_rule_text(inputs, results)

    lines: list[str] = [
        f"# Rechenbericht Getriebeauslegung: {inputs.project_name}",
        "",
        "Alle Werte sind mit den aktuell im Programm ausgewaehlten Eingaben berechnet.",
        "Dezimalzahlen werden mit Komma geschrieben; Formeln sind in technischer Schreibweise angegeben.",
        "",
        "## 1. Eingabedaten",
        "",
        f"- Leistung: `P = {de(inputs.power_kw)} kW`",
        f"- Antriebsdrehzahl: `n_1 = {de(inputs.n1_rpm, 0)} 1/min`",
        f"- Soll-Abtriebsdrehzahl: `n_2,soll = {de(inputs.n2_target_rpm, 0)} 1/min`",
        f"- Eingriffswinkel: `alpha = {de(inputs.alpha_deg)} deg`",
        f"- Schraegungswinkel: `beta = {de(inputs.beta_deg)} deg`",
        f"- Stirneingriffswinkel: `alpha_t = {de(results.alpha_transverse_deg)} deg`",
        f"- Werkstoff: `{inputs.shaft_material}`",
        f"- Zulaessige Torsionsspannung: `tau_t,zul = {de(inputs.tau_t_zul)} N/mm^2`",
        f"- Ritzelbauart: `{module_design_name(inputs.shaft_design)}`",
        f"- Durchmesser unter dem Ritzel: `d_sh = {de(inputs.d_sh_pinion_mm)} mm`",
        f"- Zaehnezahl Ritzel: `z_1 = {results.z1}`",
        f"- Zaehnezahl Gegenrad: `z_2 = {results.z2}`",
        "",
        "## 2. Grundrechnung",
        "",
        line_formula(
            "i_soll = n_1 / n_2,soll",
            f"i_soll = {de(inputs.n1_rpm, 0)} / {de(inputs.n2_target_rpm, 0)}",
            f"i_soll = {de(results.i_target, 4)}",
        ),
        "",
        line_formula(
            "M = P / (2 * pi * n)",
            f"M_1 = ({de(inputs.power_kw)} * 1000 W) / (2 * pi * ({de(inputs.n1_rpm, 0)} / 60) 1/s)",
            f"M_1 = {de(results.M1_Nm, 2)} Nm",
        ),
        "",
        line_formula(
            "M_2 = M_1 * i_soll",
            f"M_2 = {de(results.M1_Nm, 2)} Nm * {de(results.i_target, 4)}",
            f"M_2 = {de(results.M2_Nm, 2)} Nm",
        ),
        "",
        "## 3. Wellenvordimensionierung",
        "",
        line_formula(
            "d_min = ((16 * M) / (pi * tau_t,zul))^(1/3)",
            f"d_min,1 = ((16 * {de(results.M1_Nm * 1000, 1)} Nmm) / (pi * {de(inputs.tau_t_zul)} N/mm^2))^(1/3)",
            f"d_min,1 = {de(results.d_min_shaft_1_mm, 2)} mm",
        ),
        "",
        line_formula(
            "d_min = ((16 * M) / (pi * tau_t,zul))^(1/3)",
            f"d_min,2 = ((16 * {de(results.M2_Nm * 1000, 1)} Nmm) / (pi * {de(inputs.tau_t_zul)} N/mm^2))^(1/3)",
            f"d_min,2 = {de(results.d_min_shaft_2_mm, 2)} mm",
        ),
        "",
        "## 4. Modulbestimmung",
        "",
    ]

    if inputs.shaft_design == "mounted":
        module_formula = "m' = (1,8 * d_sh * cos(beta)) / (z_1 - 2,5)"
        module_factor = 1.8
    else:
        module_formula = "m' = (1,1 * d_sh * cos(beta)) / (z_1 - 2,5)"
        module_factor = 1.1

    lines.extend(
        [
            line_formula(
                module_formula,
                f"m' = ({de(module_factor, 1)} * {de(inputs.d_sh_pinion_mm)} mm * cos({de(inputs.beta_deg)} deg)) / ({results.z1} - 2,5)",
                f"m' = {de(results.m_theoretical_mm, 3)} mm",
            ),
            "",
            f"- Empfohlener Normmodul aus Tabelle: **`m = {de(results.m_recommended_mm)} mm`**",
            f"- Gewaehlter Normmodul: **`m = {de(results.m_selected_mm)} mm`**",
            "",
            "## 5. Zaehnezahlen und reale Uebersetzung",
            "",
            line_formula(
                "z_2 = round(i_soll * z_1)",
                f"z_2 = round({de(results.i_target, 4)} * {results.z1})",
                f"z_2 = {results.z2}",
            )
            if inputs.z2_manual is None
            else f"- `z_2` wurde manuell gewaehlt: **z_2 = {results.z2}**",
            "",
            line_formula(
                "i_real = z_2 / z_1",
                f"i_real = {results.z2} / {results.z1}",
            f"i_real = {de(results.i_real, 4)}",
        ),
        "",
        line_formula(
            "Delta_i = (i_real - i_soll) / i_soll * 100 %",
            f"Delta_i = ({de(results.i_real, 4)} - {de(results.i_target, 4)}) / {de(results.i_target, 4)} * 100 %",
            f"Delta_i = {de(results.i_deviation_percent, 2)} %",
        ),
        "",
        line_formula(
            "n_2,real = n_1 / i_real",
            f"n_2,real = {de(inputs.n1_rpm, 0)} / {de(results.i_real, 4)}",
            f"n_2,real = {de(results.n2_real_rpm, 2)} 1/min",
        ),
        "",
        line_formula(
            "Delta_n2 = (n_2,real - n_2,soll) / n_2,soll * 100 %",
            f"Delta_n2 = ({de(results.n2_real_rpm, 2)} - {de(inputs.n2_target_rpm, 0)}) / {de(inputs.n2_target_rpm, 0)} * 100 %",
            f"Delta_n2 = {de(results.n2_deviation_percent, 2)} %",
        ),
        "",
        "## 6. Zahnradgeometrie",
            "",
            "### Ritzel",
            "",
            line_formula(
                "d_1 = m_n * z_1 / cos(beta)",
                f"d_1 = {de(results.m_selected_mm)} mm * {results.z1} / cos({de(inputs.beta_deg)} deg)",
                f"d_1 = {de(results.d1_mm)} mm",
            ),
            "",
            line_formula(
                "d_b1 = d_1 * cos(alpha_t)",
                f"d_b1 = {de(results.d1_mm)} mm * cos({de(results.alpha_transverse_deg)} deg)",
                f"d_b1 = {de(results.db1_mm)} mm",
            ),
            "",
            line_formula(
                "d_a1 = d_1 + 2 * m_n",
                f"d_a1 = {de(results.d1_mm)} mm + 2 * {de(results.m_selected_mm)} mm",
                f"d_a1 = {de(results.da1_mm)} mm",
            ),
            "",
            line_formula(
                "d_f1 = d_1 - 2,5 * m_n",
                f"d_f1 = {de(results.d1_mm)} mm - 2,5 * {de(results.m_selected_mm)} mm",
                f"d_f1 = {de(results.df1_mm)} mm",
            ),
            "",
            line_formula(b_formula, b_substitution, b_result),
            "",
            "### Gegenrad",
            "",
            line_formula(
                "d_2 = m_n * z_2 / cos(beta)",
                f"d_2 = {de(results.m_selected_mm)} mm * {results.z2} / cos({de(inputs.beta_deg)} deg)",
                f"d_2 = {de(results.d2_mm)} mm",
            ),
            "",
            line_formula(
                "d_b2 = d_2 * cos(alpha_t)",
                f"d_b2 = {de(results.d2_mm)} mm * cos({de(results.alpha_transverse_deg)} deg)",
                f"d_b2 = {de(results.db2_mm)} mm",
            ),
            "",
            line_formula(
                "d_a2 = d_2 + 2 * m_n",
                f"d_a2 = {de(results.d2_mm)} mm + 2 * {de(results.m_selected_mm)} mm",
                f"d_a2 = {de(results.da2_mm)} mm",
            ),
            "",
            line_formula(
                "d_f2 = d_2 - 2,5 * m_n",
                f"d_f2 = {de(results.d2_mm)} mm - 2,5 * {de(results.m_selected_mm)} mm",
                f"d_f2 = {de(results.df2_mm)} mm",
            ),
            "",
            f"- Gegenradbreite: **`b_2 = {de(results.b2_mm)} mm`**",
            "",
            line_formula(
                "a = (d_1 + d_2) / 2",
                f"a = ({de(results.d1_mm)} mm + {de(results.d2_mm)} mm) / 2",
                f"a = {de(results.center_distance_mm)} mm",
            ),
            "",
            "## 7. Zahneingriff",
            "",
            line_formula(
                "alpha_t = arctan(tan(alpha) / cos(beta))",
                f"alpha_t = arctan(tan({de(inputs.alpha_deg)} deg) / cos({de(inputs.beta_deg)} deg))",
                f"alpha_t = {de(results.alpha_transverse_deg, 3)} deg",
            ),
            "",
            line_formula(
                "p_t = pi * m_n / cos(beta)",
                f"p_t = pi * {de(results.m_selected_mm)} mm / cos({de(inputs.beta_deg)} deg)",
                f"p = {de(results.pitch_mm, 3)} mm",
            ),
            "",
            line_formula(
                "p_e = p_t * cos(alpha_t)",
                f"p_e = {de(results.pitch_mm, 3)} mm * cos({de(results.alpha_transverse_deg)} deg)",
                f"p_e = {de(results.base_pitch_mm, 3)} mm",
            ),
            "",
            line_formula(
                "g_alpha = sqrt((d_a1/2)^2 - (d_b1/2)^2) + sqrt((d_a2/2)^2 - (d_b2/2)^2) - a * sin(alpha_t)",
                (
                    f"g_alpha = {de(results.path_contact_pinion_mm, 3)} mm "
                    f"+ {de(results.path_contact_wheel_mm, 3)} mm "
                    f"- {de(results.path_contact_center_subtract_mm, 3)} mm"
                ),
                f"g_alpha = {de(results.path_of_contact_mm, 3)} mm",
            ),
            "",
            line_formula(
                "epsilon_alpha = g_alpha / p_e",
                f"epsilon_alpha = {de(results.path_of_contact_mm, 3)} / {de(results.base_pitch_mm, 3)}",
                f"epsilon_alpha = {de(results.contact_ratio, 3)}",
            ),
            "",
            "## 8. Zahnkraefte",
            "",
            line_formula(
                "F_t = 2 * M_1 / d_1",
                f"F_t = 2 * {de(results.M1_Nm * 1000, 1)} Nmm / {de(results.d1_mm)} mm",
                f"F_t = {de(results.Ft_N, 1)} N",
            ),
            "",
            line_formula(
                "F_r = F_t * tan(alpha_t)",
                f"F_r = {de(results.Ft_N, 1)} N * tan({de(results.alpha_transverse_deg)} deg)",
                f"F_r = {de(results.Fr_N, 1)} N",
            ),
            "",
            line_formula(
                "F_a = F_t * tan(beta)",
                f"F_a = {de(results.Ft_N, 1)} N * tan({de(inputs.beta_deg)} deg)",
                f"F_a = {de(results.Fa_N, 1)} N",
            ),
            "",
            f"- Resultierende Zahnkraft: **`F_res = {de(results.tooth_force_resultant_N, 1)} N`**",
            "",
            "## 9. Lagerkraefte",
            "",
            f"- Abstand linkes Lager bis Zahnrad: `a_L = {de(inputs.bearing_distance_left_mm)} mm`",
            f"- Abstand Zahnrad bis rechtes Lager: `a_R = {de(inputs.bearing_distance_right_mm)} mm`",
            "",
            line_formula(
                "R_L = F * a_R / (a_L + a_R)",
                f"R_L,t = {de(results.Ft_N, 1)} N * {de(inputs.bearing_distance_right_mm)} / ({de(inputs.bearing_distance_left_mm)} + {de(inputs.bearing_distance_right_mm)})",
                f"R_L,t = {de(results.bearing_left_tangential_N, 1)} N",
            ),
            "",
            line_formula(
                "R_R = F * a_L / (a_L + a_R)",
                f"R_R,t = {de(results.Ft_N, 1)} N * {de(inputs.bearing_distance_left_mm)} / ({de(inputs.bearing_distance_left_mm)} + {de(inputs.bearing_distance_right_mm)})",
                f"R_R,t = {de(results.bearing_right_tangential_N, 1)} N",
            ),
            "",
            line_formula(
                "R = sqrt(R_t^2 + R_r^2)",
                f"R_links = sqrt({de(results.bearing_left_tangential_N, 1)}^2 + {de(results.bearing_left_radial_N, 1)}^2)",
                f"R_links = {de(results.bearing_load_left_N, 1)} N",
            ),
            "",
            line_formula(
                "R = sqrt(R_t^2 + R_r^2)",
                f"R_rechts = sqrt({de(results.bearing_right_tangential_N, 1)}^2 + {de(results.bearing_right_radial_N, 1)}^2)",
                f"R_rechts = {de(results.bearing_load_right_N, 1)} N",
            ),
            "",
            "## 10. Lagerauswahl und Lagerpruefung",
            "",
            f"- Lager links: **{bearing_label(left_bearing)}**",
            f"- Lager rechts: **{bearing_label(right_bearing)}**",
            "",
        ]
    )

    if left_bearing is not None:
        lines.extend(
            [
                line_formula(
                    "L_10h = 10^6 / (60 * n) * (C / P)^3",
                    f"L_10h,links = 10^6 / (60 * {de(inputs.n1_rpm, 0)}) * ({de(float(left_bearing['C']) * 1000, 0)} / {de(results.bearing_load_left_N, 1)})^3",
                    f"L_10h,links = {de(results.bearing_life_left_h, 0)} h",
                ),
                "",
                line_formula(
                    "S_0 = C_0 / P_0",
                    f"S_0,links = {de(float(left_bearing['C0']) * 1000, 0)} / {de(results.bearing_load_left_N, 1)}",
                    f"S_0,links = {de(results.bearing_static_safety_left, 2)}",
                ),
                "",
            ]
        )

    if right_bearing is not None:
        lines.extend(
            [
                line_formula(
                    "L_10h = 10^6 / (60 * n) * (C / P)^3",
                    f"L_10h,rechts = 10^6 / (60 * {de(inputs.n1_rpm, 0)}) * ({de(float(right_bearing['C']) * 1000, 0)} / {de(results.bearing_load_right_N, 1)})^3",
                    f"L_10h,rechts = {de(results.bearing_life_right_h, 0)} h",
                ),
                "",
                line_formula(
                    "S_0 = C_0 / P_0",
                    f"S_0,rechts = {de(float(right_bearing['C0']) * 1000, 0)} / {de(results.bearing_load_right_N, 1)}",
                    f"S_0,rechts = {de(results.bearing_static_safety_right, 2)}",
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## 11. Schnittlasten",
            "",
            line_formula(
                "M_b,t,max = R_L,t * a_L",
                f"M_b,t,max = {de(results.bearing_left_tangential_N, 1)} N * {de(inputs.bearing_distance_left_mm)} mm",
                f"M_b,t,max = {de(results.max_bending_tangential_Nmm / 1000, 2)} Nm",
            ),
            "",
            line_formula(
                "M_b,r,max = R_L,r * a_L",
                f"M_b,r,max = {de(results.bearing_left_radial_N, 1)} N * {de(inputs.bearing_distance_left_mm)} mm",
                f"M_b,r,max = {de(results.max_bending_radial_Nmm / 1000, 2)} Nm",
            ),
            "",
            line_formula(
                "M_b,res = sqrt(M_b,t^2 + M_b,r^2)",
                f"M_b,res = sqrt({de(results.max_bending_tangential_Nmm / 1000, 2)}^2 + {de(results.max_bending_radial_Nmm / 1000, 2)}^2)",
                f"M_b,res = {de(results.max_bending_resultant_Nmm / 1000, 2)} Nm",
            ),
            "",
            "## 12. Pruefungen",
            "",
        ]
    )

    for check in results.checks:
        lines.append(f"- **{check.status}** - {check.name}: {check.value} (Grenze: {check.limit})")
        lines.append(f"  - {check.message}")

    lines.append("")
    return "\n".join(lines)


def generate_latex_report(inputs: GearInputs, results: GearResults, bearings: list[dict[str, Any]]) -> str:
    left_bearing = find_bearing(bearings, inputs.selected_bearing_left)
    right_bearing = find_bearing(bearings, inputs.selected_bearing_right)

    if inputs.shaft_design == "mounted":
        module_factor = 1.8
        module_formula = r"m' &= \frac{1{,}8 \cdot d_{sh} \cdot \cos(\beta)}{z_1 - 2{,}5}"
    else:
        module_factor = 1.1
        module_formula = r"m' &= \frac{1{,}1 \cdot d_{sh} \cdot \cos(\beta)}{z_1 - 2{,}5}"

    if inputs.width_rule == "psi_d":
        width_formula = (
            r"b_1 &= \psi_d \cdot d_1 \\",
            rf"    &= {tex_num(inputs.psi_d)} \cdot {tex_num(results.d1_mm)}\,\mathrm{{mm}} \\",
            rf"    &= {tex_num(results.b1_mm)}\,\mathrm{{mm}}",
        )
    else:
        width_formula = (
            r"b_1 &= k_b \cdot m \\",
            rf"    &= {tex_num(inputs.width_factor_m)} \cdot {tex_num(results.m_selected_mm)}\,\mathrm{{mm}} \\",
            rf"    &= {tex_num(results.b1_mm)}\,\mathrm{{mm}}",
        )

    z2_lines = (
        [
            r"\begin{align*}",
            r"z_2 &= \operatorname{round}(i_\mathrm{soll} \cdot z_1) \\",
            rf"    &= \operatorname{{round}}({tex_num(results.i_target, 4)} \cdot {results.z1}) \\",
            rf"    &= {results.z2}",
            r"\end{align*}",
        ]
        if inputs.z2_manual is None
        else [rf"\[z_2 = {results.z2}\quad\text{{(manuell gewaehlt)}}\]"]
    )

    lines: list[str] = [
        r"\documentclass[12pt,a4paper]{article}",
        r"\usepackage[ngerman]{babel}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{amsmath,booktabs,geometry}",
        r"\geometry{margin=2.5cm}",
        r"\setlength{\parindent}{0pt}",
        r"\begin{document}",
        rf"\section*{{Rechenbericht Getriebeauslegung: {tex_escape(inputs.project_name)}}}",
        r"Alle Werte wurden mit den aktuell ausgewaehlten Eingaben berechnet.",
        "",
        r"\section{Eingabedaten}",
        r"\begin{tabular}{ll}",
        rf"Leistung & $P = {tex_num(inputs.power_kw)}\,\mathrm{{kW}}$ \\",
        rf"Antriebsdrehzahl & $n_1 = {tex_num(inputs.n1_rpm, 0)}\,\mathrm{{min^{{-1}}}}$ \\",
        rf"Soll-Abtriebsdrehzahl & $n_{{2,\mathrm{{soll}}}} = {tex_num(inputs.n2_target_rpm, 0)}\,\mathrm{{min^{{-1}}}}$ \\",
        rf"Eingriffswinkel & $\alpha = {tex_num(inputs.alpha_deg)}^\circ$ \\",
        rf"Schraegungswinkel & $\beta = {tex_num(inputs.beta_deg)}^\circ$ \\",
        rf"Stirneingriffswinkel & $\alpha_t = {tex_num(results.alpha_transverse_deg)}^\circ$ \\",
        rf"Werkstoff & {tex_escape(inputs.shaft_material)} \\",
        rf"Zulaessige Torsionsspannung & $\tau_{{t,\mathrm{{zul}}}} = {tex_num(inputs.tau_t_zul)}\,\mathrm{{N/mm^2}}$ \\",
        rf"Ritzelbauart & {module_design_name_latex(inputs.shaft_design)} \\",
        rf"Durchmesser unter dem Ritzel & $d_{{sh}} = {tex_num(inputs.d_sh_pinion_mm)}\,\mathrm{{mm}}$ \\",
        rf"Zaehnezahlen & $z_1 = {results.z1}$, $z_2 = {results.z2}$ \\",
        r"\end{tabular}",
        "",
        r"\section{Grundrechnung}",
        r"\textbf{Berechnet: Soll-Uebersetzung}",
        r"\begin{align*}",
        r"i_\mathrm{soll} &= \frac{n_1}{n_{2,\mathrm{soll}}} \\",
        rf"    &= \frac{{{tex_num(inputs.n1_rpm, 0)}}}{{{tex_num(inputs.n2_target_rpm, 0)}}} \\",
        rf"    &= {tex_num(results.i_target, 4)}",
        r"\end{align*}",
        r"\textbf{Berechnet: Antriebsdrehmoment}",
        r"\begin{align*}",
        r"M_1 &= \frac{P}{2\pi n_1} \\",
        rf"    &= \frac{{{tex_num(inputs.power_kw)} \cdot 1000\,\mathrm{{W}}}}{{2\pi \cdot ({tex_num(inputs.n1_rpm, 0)}/60)\,\mathrm{{s^{{-1}}}}}} \\",
        rf"    &= {tex_num(results.M1_Nm, 2)}\,\mathrm{{Nm}}",
        r"\end{align*}",
        r"\textbf{Berechnet: ideales Abtriebsdrehmoment}",
        r"\begin{align*}",
        r"M_2 &= M_1 \cdot i_\mathrm{soll} \\",
        rf"    &= {tex_num(results.M1_Nm, 2)} \cdot {tex_num(results.i_target, 4)} \\",
        rf"    &= {tex_num(results.M2_Nm, 2)}\,\mathrm{{Nm}}",
        r"\end{align*}",
        "",
        r"\section{Wellenvordimensionierung}",
        r"\textbf{Berechnet: Mindestwellendurchmesser}",
        r"\begin{align*}",
        r"d_\mathrm{min} &= \sqrt[3]{\frac{16M}{\pi \tau_{t,\mathrm{zul}}}} \\",
        rf"d_{{\mathrm{{min}},1}} &= \sqrt[3]{{\frac{{16 \cdot {tex_num(results.M1_Nm * 1000, 1)}\,\mathrm{{Nmm}}}}{{\pi \cdot {tex_num(inputs.tau_t_zul)}\,\mathrm{{N/mm^2}}}}}} \\",
        rf"    &= {tex_num(results.d_min_shaft_1_mm, 2)}\,\mathrm{{mm}} \\",
        rf"d_{{\mathrm{{min}},2}} &= \sqrt[3]{{\frac{{16 \cdot {tex_num(results.M2_Nm * 1000, 1)}\,\mathrm{{Nmm}}}}{{\pi \cdot {tex_num(inputs.tau_t_zul)}\,\mathrm{{N/mm^2}}}}}} \\",
        rf"    &= {tex_num(results.d_min_shaft_2_mm, 2)}\,\mathrm{{mm}}",
        r"\end{align*}",
        "",
        r"\section{Modulbestimmung}",
        r"\textbf{Berechnet: theoretisch erforderlicher Modul}",
        r"\begin{align*}",
        module_formula + r" \\",
        rf"    &= \frac{{{tex_num(module_factor, 1)} \cdot {tex_num(inputs.d_sh_pinion_mm)}\,\mathrm{{mm}} \cdot \cos({tex_num(inputs.beta_deg)}^\circ)}}{{{results.z1} - 2{{,}}5}} \\",
        rf"    &= {tex_num(results.m_theoretical_mm, 3)}\,\mathrm{{mm}}",
        r"\end{align*}",
        rf"Empfohlener Normmodul: $m = {tex_num(results.m_recommended_mm)}\,\mathrm{{mm}}$\\",
        rf"Gewaehlter Normmodul: $m = {tex_num(results.m_selected_mm)}\,\mathrm{{mm}}$",
        "",
        r"\section{Zaehnezahlen und reale Uebersetzung}",
        r"\textbf{Berechnet: Zaehnezahl Gegenrad}",
        *z2_lines,
        r"\textbf{Berechnet: reale Uebersetzung, Uebersetzungsabweichung und reale Abtriebsdrehzahl}",
        r"\begin{align*}",
        r"i_\mathrm{real} &= \frac{z_2}{z_1} \\",
        rf"    &= \frac{{{results.z2}}}{{{results.z1}}} \\",
        rf"    &= {tex_num(results.i_real, 4)} \\",
        r"\Delta_i &= \frac{i_\mathrm{real} - i_\mathrm{soll}}{i_\mathrm{soll}} \cdot 100\,\% \\",
        rf"    &= \frac{{{tex_num(results.i_real, 4)} - {tex_num(results.i_target, 4)}}}{{{tex_num(results.i_target, 4)}}} \cdot 100\,\% \\",
        rf"    &= {tex_num(results.i_deviation_percent, 2)}\,\% \\",
        r"n_{2,\mathrm{real}} &= \frac{n_1}{i_\mathrm{real}} \\",
        rf"    &= \frac{{{tex_num(inputs.n1_rpm, 0)}}}{{{tex_num(results.i_real, 4)}}} \\",
        rf"    &= {tex_num(results.n2_real_rpm, 2)}\,\mathrm{{min^{{-1}}}}",
        r"\end{align*}",
        r"\textbf{Berechnet: Drehzahlabweichung}",
        r"\begin{align*}",
        r"\Delta_{n2} &= \frac{n_{2,\mathrm{real}} - n_{2,\mathrm{soll}}}{n_{2,\mathrm{soll}}} \cdot 100\,\% \\",
        rf"    &= \frac{{{tex_num(results.n2_real_rpm, 2)} - {tex_num(inputs.n2_target_rpm, 0)}}}{{{tex_num(inputs.n2_target_rpm, 0)}}} \cdot 100\,\% \\",
        rf"    &= {tex_num(results.n2_deviation_percent, 2)}\,\%",
        r"\end{align*}",
        "",
        r"\section{Zahnradgeometrie}",
        r"\subsection{Ritzel}",
        r"\textbf{Berechnet: Ritzel-Durchmesser}",
        r"\begin{align*}",
        r"d_1 &= \frac{m_n \cdot z_1}{\cos(\beta)} \\",
        rf"    &= \frac{{{tex_num(results.m_selected_mm)} \cdot {results.z1}}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}} \\",
        rf"    &= {tex_num(results.d1_mm)}\,\mathrm{{mm}} \\",
        r"d_{b1} &= d_1 \cdot \cos(\alpha_t) \\",
        rf"    &= {tex_num(results.d1_mm)} \cdot \cos({tex_num(results.alpha_transverse_deg)}^\circ) \\",
        rf"    &= {tex_num(results.db1_mm)}\,\mathrm{{mm}} \\",
        r"d_{a1} &= d_1 + 2m_n \\",
        rf"    &= {tex_num(results.d1_mm)} + 2 \cdot {tex_num(results.m_selected_mm)} \\",
        rf"    &= {tex_num(results.da1_mm)}\,\mathrm{{mm}} \\",
        r"d_{f1} &= d_1 - 2{,}5m_n \\",
        rf"    &= {tex_num(results.d1_mm)} - 2{{,}}5 \cdot {tex_num(results.m_selected_mm)} \\",
        rf"    &= {tex_num(results.df1_mm)}\,\mathrm{{mm}}",
        r"\end{align*}",
        r"\textbf{Berechnet: Zahnbreite Ritzel}",
        r"\begin{align*}",
        *width_formula,
        r"\end{align*}",
        r"\subsection{Gegenrad}",
        r"\textbf{Berechnet: Gegenrad-Durchmesser}",
        r"\begin{align*}",
        r"d_2 &= \frac{m_n \cdot z_2}{\cos(\beta)} \\",
        rf"    &= \frac{{{tex_num(results.m_selected_mm)} \cdot {results.z2}}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}} \\",
        rf"    &= {tex_num(results.d2_mm)}\,\mathrm{{mm}} \\",
        r"d_{b2} &= d_2 \cdot \cos(\alpha_t) \\",
        rf"    &= {tex_num(results.d2_mm)} \cdot \cos({tex_num(results.alpha_transverse_deg)}^\circ) \\",
        rf"    &= {tex_num(results.db2_mm)}\,\mathrm{{mm}} \\",
        r"d_{a2} &= d_2 + 2m_n \\",
        rf"    &= {tex_num(results.d2_mm)} + 2 \cdot {tex_num(results.m_selected_mm)} \\",
        rf"    &= {tex_num(results.da2_mm)}\,\mathrm{{mm}} \\",
        r"d_{f2} &= d_2 - 2{,}5m_n \\",
        rf"    &= {tex_num(results.d2_mm)} - 2{{,}}5 \cdot {tex_num(results.m_selected_mm)} \\",
        rf"    &= {tex_num(results.df2_mm)}\,\mathrm{{mm}} \\",
        r"a &= \frac{d_1 + d_2}{2} \\",
        rf"    &= \frac{{{tex_num(results.d1_mm)} + {tex_num(results.d2_mm)}}}{{2}} \\",
        rf"    &= {tex_num(results.center_distance_mm)}\,\mathrm{{mm}}",
        r"\end{align*}",
        rf"Gegenradbreite: $b_2 = {tex_num(results.b2_mm)}\,\mathrm{{mm}}$",
        "",
        r"\section{Zahneingriff}",
        r"\begin{align*}",
        r"\alpha_t &= \arctan\left(\frac{\tan(\alpha)}{\cos(\beta)}\right) \\",
        rf"  &= \arctan\left(\frac{{\tan({tex_num(inputs.alpha_deg)}^\circ)}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}}\right) \\",
        rf"  &= {tex_num(results.alpha_transverse_deg, 3)}^\circ \\",
        r"p_t &= \frac{\pi \cdot m_n}{\cos(\beta)} \\",
        rf"  &= \frac{{\pi \cdot {tex_num(results.m_selected_mm)}}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}} \\",
        rf"  &= {tex_num(results.pitch_mm, 3)}\,\mathrm{{mm}} \\",
        r"p_e &= p_t \cdot \cos(\alpha_t) \\",
        rf"    &= {tex_num(results.pitch_mm, 3)} \cdot \cos({tex_num(results.alpha_transverse_deg)}^\circ) \\",
        rf"    &= {tex_num(results.base_pitch_mm, 3)}\,\mathrm{{mm}}",
        r"\end{align*}",
        r"\begin{align*}",
        r"g_\alpha &= \sqrt{\left(\frac{d_{a1}}{2}\right)^2 - \left(\frac{d_{b1}}{2}\right)^2}",
        r"+ \sqrt{\left(\frac{d_{a2}}{2}\right)^2 - \left(\frac{d_{b2}}{2}\right)^2} - a\sin(\alpha_t) \\",
        rf"    &= {tex_num(results.path_contact_pinion_mm, 3)} + {tex_num(results.path_contact_wheel_mm, 3)} - {tex_num(results.path_contact_center_subtract_mm, 3)} \\",
        rf"    &= {tex_num(results.path_of_contact_mm, 3)}\,\mathrm{{mm}} \\",
        r"\varepsilon_\alpha &= \frac{g_\alpha}{p_e} \\",
        rf"    &= \frac{{{tex_num(results.path_of_contact_mm, 3)}}}{{{tex_num(results.base_pitch_mm, 3)}}} \\",
        rf"    &= {tex_num(results.contact_ratio, 3)}",
        r"\end{align*}",
        "",
        r"\section{Zahnkraefte}",
        r"\begin{align*}",
        r"F_t &= \frac{2M_1}{d_1} \\",
        rf"    &= \frac{{2 \cdot {tex_num(results.M1_Nm * 1000, 1)}\,\mathrm{{Nmm}}}}{{{tex_num(results.d1_mm)}\,\mathrm{{mm}}}} \\",
        rf"    &= {tex_num(results.Ft_N, 1)}\,\mathrm{{N}} \\",
        r"F_r &= F_t \cdot \tan(\alpha_t) \\",
        rf"    &= {tex_num(results.Ft_N, 1)} \cdot \tan({tex_num(results.alpha_transverse_deg)}^\circ) \\",
        rf"    &= {tex_num(results.Fr_N, 1)}\,\mathrm{{N}} \\",
        r"F_a &= F_t \cdot \tan(\beta) \\",
        rf"    &= {tex_num(results.Ft_N, 1)} \cdot \tan({tex_num(inputs.beta_deg)}^\circ) \\",
        rf"    &= {tex_num(results.Fa_N, 1)}\,\mathrm{{N}}",
        r"\end{align*}",
        rf"Resultierende Zahnkraft: $F_\mathrm{{res}} = {tex_num(results.tooth_force_resultant_N, 1)}\,\mathrm{{N}}$",
        "",
        r"\section{Lagerkraefte}",
        r"\begin{align*}",
        r"R_L &= F \cdot \frac{a_R}{a_L + a_R} \\",
        rf"R_{{L,t}} &= {tex_num(results.Ft_N, 1)} \cdot \frac{{{tex_num(inputs.bearing_distance_right_mm)}}}{{{tex_num(inputs.bearing_distance_left_mm)} + {tex_num(inputs.bearing_distance_right_mm)}}} = {tex_num(results.bearing_left_tangential_N, 1)}\,\mathrm{{N}} \\",
        rf"R_{{R,t}} &= {tex_num(results.Ft_N, 1)} \cdot \frac{{{tex_num(inputs.bearing_distance_left_mm)}}}{{{tex_num(inputs.bearing_distance_left_mm)} + {tex_num(inputs.bearing_distance_right_mm)}}} = {tex_num(results.bearing_right_tangential_N, 1)}\,\mathrm{{N}} \\",
        rf"R_\mathrm{{links}} &= \sqrt{{R_{{L,t}}^2 + R_{{L,r}}^2}} = {tex_num(results.bearing_load_left_N, 1)}\,\mathrm{{N}} \\",
        rf"R_\mathrm{{rechts}} &= \sqrt{{R_{{R,t}}^2 + R_{{R,r}}^2}} = {tex_num(results.bearing_load_right_N, 1)}\,\mathrm{{N}}",
        r"\end{align*}",
        "",
        r"\section{Lagerauswahl und Lagerpruefung}",
        rf"Lager links: {tex_escape(bearing_label(left_bearing))}\\",
        rf"Lager rechts: {tex_escape(bearing_label(right_bearing))}",
        "",
    ]

    if left_bearing is not None:
        lines.extend(
            [
                r"\begin{align*}",
                r"L_{10h} &= \frac{10^6}{60n} \left(\frac{C}{P}\right)^3 \\",
                rf"L_{{10h,\mathrm{{links}}}} &= \frac{{10^6}}{{60 \cdot {tex_num(inputs.n1_rpm, 0)}}} \left(\frac{{{tex_num(float(left_bearing['C']) * 1000, 0)}}}{{{tex_num(results.bearing_load_left_N, 1)}}}\right)^3 \\",
                rf"    &= {tex_num(results.bearing_life_left_h, 0)}\,\mathrm{{h}} \\",
                rf"S_{{0,\mathrm{{links}}}} &= \frac{{C_0}}{{P_0}} = \frac{{{tex_num(float(left_bearing['C0']) * 1000, 0)}}}{{{tex_num(results.bearing_load_left_N, 1)}}} = {tex_num(results.bearing_static_safety_left, 2)}",
                r"\end{align*}",
            ]
        )

    if right_bearing is not None:
        lines.extend(
            [
                r"\begin{align*}",
                rf"L_{{10h,\mathrm{{rechts}}}} &= \frac{{10^6}}{{60 \cdot {tex_num(inputs.n1_rpm, 0)}}} \left(\frac{{{tex_num(float(right_bearing['C']) * 1000, 0)}}}{{{tex_num(results.bearing_load_right_N, 1)}}}\right)^3 \\",
                rf"    &= {tex_num(results.bearing_life_right_h, 0)}\,\mathrm{{h}} \\",
                rf"S_{{0,\mathrm{{rechts}}}} &= \frac{{C_0}}{{P_0}} = \frac{{{tex_num(float(right_bearing['C0']) * 1000, 0)}}}{{{tex_num(results.bearing_load_right_N, 1)}}} = {tex_num(results.bearing_static_safety_right, 2)}",
                r"\end{align*}",
            ]
        )

    lines.extend(
        [
            "",
            r"\section{Schnittlasten}",
            r"\begin{align*}",
            r"M_{b,t,\max} &= R_{L,t} \cdot a_L \\",
            rf"    &= {tex_num(results.bearing_left_tangential_N, 1)} \cdot {tex_num(inputs.bearing_distance_left_mm)} \\",
            rf"    &= {tex_num(results.max_bending_tangential_Nmm / 1000, 2)}\,\mathrm{{Nm}} \\",
            r"M_{b,r,\max} &= R_{L,r} \cdot a_L \\",
            rf"    &= {tex_num(results.bearing_left_radial_N, 1)} \cdot {tex_num(inputs.bearing_distance_left_mm)} \\",
            rf"    &= {tex_num(results.max_bending_radial_Nmm / 1000, 2)}\,\mathrm{{Nm}} \\",
            r"M_{b,\mathrm{res}} &= \sqrt{M_{b,t}^2 + M_{b,r}^2} \\",
            rf"    &= {tex_num(results.max_bending_resultant_Nmm / 1000, 2)}\,\mathrm{{Nm}}",
            r"\end{align*}",
            "",
            r"\section{Pruefungen}",
            r"\begin{itemize}",
        ]
    )

    for check in results.checks:
        lines.append(
            rf"\item \textbf{{{tex_escape(check.status)}}} -- {tex_escape(check.name)}: "
            rf"{tex_escape(check.value)} (Grenze: {tex_escape(check.limit)}). {tex_escape(check.message)}"
        )

    lines.extend([r"\end{itemize}", r"\end{document}", ""])
    return "\n".join(lines)


def generate_live_latex_blocks(inputs: GearInputs, results: GearResults, bearings: list[dict[str, Any]]) -> list[tuple[str, list[str]]]:
    left_bearing = find_bearing(bearings, inputs.selected_bearing_left)
    right_bearing = find_bearing(bearings, inputs.selected_bearing_right)

    module_factor = 1.8 if inputs.shaft_design == "mounted" else 1.1
    if inputs.shaft_design == "mounted":
        module_formula = r"m' = \frac{1{,}8 \cdot d_{sh} \cdot \cos(\beta)}{z_1 - 2{,}5}"
    else:
        module_formula = r"m' = \frac{1{,}1 \cdot d_{sh} \cdot \cos(\beta)}{z_1 - 2{,}5}"

    if inputs.width_rule == "psi_d":
        width_formula = (
            rf"\begin{{aligned}}"
            rf"\text{{Zahnbreite Ritzel:}}\quad b_1 &= \psi_d \cdot d_1 \\"
            rf"&= {tex_num(inputs.psi_d)} \cdot {tex_num(results.d1_mm)} \\"
            rf"&= {tex_num(results.b1_mm)}\,\mathrm{{mm}}"
            rf"\end{{aligned}}"
        )
    else:
        width_formula = (
            rf"\begin{{aligned}}"
            rf"\text{{Zahnbreite Ritzel:}}\quad b_1 &= k_b \cdot m \\"
            rf"&= {tex_num(inputs.width_factor_m)} \cdot {tex_num(results.m_selected_mm)} \\"
            rf"&= {tex_num(results.b1_mm)}\,\mathrm{{mm}}"
            rf"\end{{aligned}}"
        )

    z2_formula = (
        rf"\begin{{aligned}}"
        rf"\text{{Zaehnezahl Gegenrad:}}\quad z_2 &= \operatorname{{round}}(i_\mathrm{{soll}}\cdot z_1) \\"
        rf"&= \operatorname{{round}}({tex_num(results.i_target, 4)}\cdot {results.z1}) \\"
        rf"&= {results.z2}"
        rf"\end{{aligned}}"
        if inputs.z2_manual is None
        else rf"\text{{Zaehnezahl Gegenrad:}}\quad z_2 = {results.z2}\quad\text{{(manuell gewaehlt)}}"
    )

    bearing_life_blocks: list[str] = []
    if left_bearing is not None:
        bearing_life_blocks.append(
            rf"\begin{{aligned}}"
            rf"\text{{Lagerlebensdauer links:}}\quad L_{{10h,L}} &= \frac{{10^6}}{{60n}}\left(\frac{{C}}{{P}}\right)^3 \\"
            rf"&= \frac{{10^6}}{{60\cdot {tex_num(inputs.n1_rpm, 0)}}}"
            rf"\left(\frac{{{tex_num(float(left_bearing['C']) * 1000, 0)}}}{{{tex_num(results.bearing_load_left_N, 1)}}}\right)^3 \\"
            rf"&= {tex_num(results.bearing_life_left_h, 0)}\,\mathrm{{h}}"
            rf"\end{{aligned}}"
        )
    else:
        bearing_life_blocks.append(r"L_{10h,L}: \text{kein linkes Lager ausgewaehlt}")

    if right_bearing is not None:
        bearing_life_blocks.append(
            rf"\begin{{aligned}}"
            rf"\text{{Lagerlebensdauer rechts:}}\quad L_{{10h,R}} &= \frac{{10^6}}{{60n}}\left(\frac{{C}}{{P}}\right)^3 \\"
            rf"&= \frac{{10^6}}{{60\cdot {tex_num(inputs.n1_rpm, 0)}}}"
            rf"\left(\frac{{{tex_num(float(right_bearing['C']) * 1000, 0)}}}{{{tex_num(results.bearing_load_right_N, 1)}}}\right)^3 \\"
            rf"&= {tex_num(results.bearing_life_right_h, 0)}\,\mathrm{{h}}"
            rf"\end{{aligned}}"
        )
    else:
        bearing_life_blocks.append(r"L_{10h,R}: \text{kein rechtes Lager ausgewaehlt}")

    return [
        (
            "Grundrechnung",
            [
                rf"\begin{{aligned}}\text{{Soll-Uebersetzung:}}\quad i_\mathrm{{soll}} &= \frac{{n_1}}{{n_{{2,\mathrm{{soll}}}}}} = \frac{{{tex_num(inputs.n1_rpm, 0)}}}{{{tex_num(inputs.n2_target_rpm, 0)}}} = {tex_num(results.i_target, 4)}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Antriebsdrehmoment:}}\quad M_1 &= \frac{{P}}{{2\pi n_1}} = \frac{{{tex_num(inputs.power_kw)}\cdot1000}}{{2\pi\cdot({tex_num(inputs.n1_rpm, 0)}/60)}} = {tex_num(results.M1_Nm, 2)}\,\mathrm{{Nm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{ideales Abtriebsdrehmoment:}}\quad M_2 &= M_1\cdot i_\mathrm{{soll}} = {tex_num(results.M1_Nm, 2)}\cdot {tex_num(results.i_target, 4)} = {tex_num(results.M2_Nm, 2)}\,\mathrm{{Nm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Mindestwellendurchmesser:}}\quad d_{{\min,1}} &= \sqrt[3]{{\frac{{16M_1}}{{\pi\tau_{{t,\mathrm{{zul}}}}}}}} = {tex_num(results.d_min_shaft_1_mm, 2)}\,\mathrm{{mm}}\end{{aligned}}",
            ],
        ),
        (
            "Modul und Zaehne",
            [
                rf"\begin{{aligned}}\text{{theoretisch erforderlicher Modul:}}\quad {module_formula} &= \frac{{{tex_num(module_factor, 1)}\cdot {tex_num(inputs.d_sh_pinion_mm)}\cdot \cos({tex_num(inputs.beta_deg)}^\circ)}}{{{results.z1}-2{{,}}5}} = {tex_num(results.m_theoretical_mm, 3)}\,\mathrm{{mm}}\end{{aligned}}",
                rf"\text{{Normmodul:}}\quad m_\mathrm{{Norm,empfohlen}} = {tex_num(results.m_recommended_mm)}\,\mathrm{{mm}}\qquad m_\mathrm{{gewaehlt}} = {tex_num(results.m_selected_mm)}\,\mathrm{{mm}}",
                z2_formula,
                rf"\begin{{aligned}}\text{{reale Uebersetzung:}}\quad i_\mathrm{{real}} &= \frac{{z_2}}{{z_1}} = \frac{{{results.z2}}}{{{results.z1}}} = {tex_num(results.i_real, 4)}\\ \text{{Uebersetzungsabweichung:}}\quad \Delta_i &= \frac{{i_\mathrm{{real}}-i_\mathrm{{soll}}}}{{i_\mathrm{{soll}}}}\cdot 100\,\% = {tex_num(results.i_deviation_percent, 2)}\,\%\\ \text{{reale Abtriebsdrehzahl:}}\quad n_{{2,\mathrm{{real}}}} &= \frac{{n_1}}{{i_\mathrm{{real}}}} = {tex_num(results.n2_real_rpm, 2)}\,\mathrm{{min^{{-1}}}}\\ \text{{Drehzahlabweichung:}}\quad \Delta_{{n2}} &= \frac{{n_{{2,\mathrm{{real}}}}-n_{{2,\mathrm{{soll}}}}}}{{n_{{2,\mathrm{{soll}}}}}}\cdot 100\,\% = {tex_num(results.n2_deviation_percent, 2)}\,\%\end{{aligned}}",
            ],
        ),
        (
            "Geometrie",
            [
                rf"\begin{{aligned}}\text{{Stirneingriffswinkel:}}\quad \alpha_t &= \arctan\left(\frac{{\tan(\alpha)}}{{\cos(\beta)}}\right) = \arctan\left(\frac{{\tan({tex_num(inputs.alpha_deg)}^\circ)}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}}\right) = {tex_num(results.alpha_transverse_deg, 3)}^\circ\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Teilkreisdurchmesser:}}\quad d_1 &= \frac{{m_n z_1}}{{\cos(\beta)}} = \frac{{{tex_num(results.m_selected_mm)}\cdot {results.z1}}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}} = {tex_num(results.d1_mm)}\,\mathrm{{mm}}\\ d_2 &= \frac{{m_n z_2}}{{\cos(\beta)}} = \frac{{{tex_num(results.m_selected_mm)}\cdot {results.z2}}}{{\cos({tex_num(inputs.beta_deg)}^\circ)}} = {tex_num(results.d2_mm)}\,\mathrm{{mm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Grundkreisdurchmesser:}}\quad d_{{b1}} &= d_1\cos(\alpha_t) = {tex_num(results.db1_mm)}\,\mathrm{{mm}}\\ d_{{b2}} &= d_2\cos(\alpha_t) = {tex_num(results.db2_mm)}\,\mathrm{{mm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Kopf- und Fusskreisdurchmesser Ritzel:}}\quad d_{{a1}} &= d_1+2m_n = {tex_num(results.da1_mm)}\,\mathrm{{mm}}\\ d_{{f1}} &= d_1-2{{,}}5m_n = {tex_num(results.df1_mm)}\,\mathrm{{mm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Kopf- und Fusskreisdurchmesser Gegenrad:}}\quad d_{{a2}} &= d_2+2m_n = {tex_num(results.da2_mm)}\,\mathrm{{mm}}\\ d_{{f2}} &= d_2-2{{,}}5m_n = {tex_num(results.df2_mm)}\,\mathrm{{mm}}\end{{aligned}}",
                width_formula,
                rf"\begin{{aligned}}\text{{Achsabstand:}}\quad a &= \frac{{d_1+d_2}}{{2}} = \frac{{{tex_num(results.d1_mm)}+{tex_num(results.d2_mm)}}}{{2}} = {tex_num(results.center_distance_mm)}\,\mathrm{{mm}}\end{{aligned}}",
            ],
        ),
        (
            "Zahneingriff",
            [
                rf"\begin{{aligned}}\text{{Teilungen:}}\quad p_t &= \frac{{\pi m_n}}{{\cos(\beta)}} = {tex_num(results.pitch_mm, 3)}\,\mathrm{{mm}}\\ p_e &= p_t\cos(\alpha_t) = {tex_num(results.base_pitch_mm, 3)}\,\mathrm{{mm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Eingriffsstrecke:}}\quad g_\alpha &= \sqrt{{\left(\frac{{d_{{a1}}}}{{2}}\right)^2-\left(\frac{{d_{{b1}}}}{{2}}\right)^2}} + \sqrt{{\left(\frac{{d_{{a2}}}}{{2}}\right)^2-\left(\frac{{d_{{b2}}}}{{2}}\right)^2}} - a\sin(\alpha_t)\\ &= {tex_num(results.path_contact_pinion_mm, 3)} + {tex_num(results.path_contact_wheel_mm, 3)} - {tex_num(results.path_contact_center_subtract_mm, 3)}\\ &= {tex_num(results.path_of_contact_mm, 3)}\,\mathrm{{mm}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Profilueberdeckung:}}\quad \varepsilon_\alpha &= \frac{{g_\alpha}}{{p_e}} = \frac{{{tex_num(results.path_of_contact_mm, 3)}}}{{{tex_num(results.base_pitch_mm, 3)}}} = {tex_num(results.contact_ratio, 3)}\end{{aligned}}",
            ],
        ),
        (
            "Kraefte",
            [
                rf"\begin{{aligned}}\text{{Tangentialkraft:}}\quad F_t &= \frac{{2M_1}}{{d_1}} = \frac{{2\cdot {tex_num(results.M1_Nm * 1000, 1)}}}{{{tex_num(results.d1_mm)}}} = {tex_num(results.Ft_N, 1)}\,\mathrm{{N}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{Radial- und Axialkraft:}}\quad F_r &= F_t\tan(\alpha_t) = {tex_num(results.Ft_N, 1)}\tan({tex_num(results.alpha_transverse_deg)}^\circ) = {tex_num(results.Fr_N, 1)}\,\mathrm{{N}}\\ F_a &= F_t\tan(\beta) = {tex_num(results.Fa_N, 1)}\,\mathrm{{N}}\end{{aligned}}",
            ],
        ),
        (
            "Lager und Schnittlasten",
            [
                rf"\begin{{aligned}}\text{{Lagerreaktionen tangential:}}\quad R_{{L,t}} &= F_t\frac{{a_R}}{{a_L+a_R}} = {tex_num(results.bearing_left_tangential_N, 1)}\,\mathrm{{N}}\\ R_{{R,t}} &= F_t\frac{{a_L}}{{a_L+a_R}} = {tex_num(results.bearing_right_tangential_N, 1)}\,\mathrm{{N}}\end{{aligned}}",
                rf"\begin{{aligned}}\text{{resultierende Lagerkraefte:}}\quad R_L &= \sqrt{{R_{{L,t}}^2+R_{{L,r}}^2}} = {tex_num(results.bearing_load_left_N, 1)}\,\mathrm{{N}}\\ R_R &= \sqrt{{R_{{R,t}}^2+R_{{R,r}}^2}} = {tex_num(results.bearing_load_right_N, 1)}\,\mathrm{{N}}\end{{aligned}}",
                *bearing_life_blocks,
                rf"\begin{{aligned}}\text{{resultierendes Biegemoment:}}\quad M_{{b,\mathrm{{res}}}} &= \sqrt{{M_{{b,t}}^2+M_{{b,r}}^2}} = {tex_num(results.max_bending_resultant_Nmm / 1000, 2)}\,\mathrm{{Nm}}\end{{aligned}}",
            ],
        ),
    ]
