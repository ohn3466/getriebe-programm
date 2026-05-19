from __future__ import annotations

import math

from core.units import kn_to_n, kw_to_w, nm_to_nmm, rpm_to_per_second


def require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} muss groesser 0 sein.")


def calc_ratio(n1_rpm: float, n2_rpm: float) -> float:
    require_positive("n1_rpm", n1_rpm)
    require_positive("n2_rpm", n2_rpm)
    return n1_rpm / n2_rpm


def calc_torque(power_kw: float, n_rpm: float) -> float:
    require_positive("power_kw", power_kw)
    require_positive("n_rpm", n_rpm)
    angular_speed = 2.0 * math.pi * rpm_to_per_second(n_rpm)
    return kw_to_w(power_kw) / angular_speed


def calc_min_shaft_diameter(moment_nm: float, tau_t_zul_n_per_mm2: float) -> float:
    require_positive("moment_nm", moment_nm)
    require_positive("tau_t_zul_n_per_mm2", tau_t_zul_n_per_mm2)
    return ((16.0 * nm_to_nmm(moment_nm)) / (math.pi * tau_t_zul_n_per_mm2)) ** (1.0 / 3.0)


def calc_module_from_dsh(d_sh_mm: float, z1: int, beta_deg: float, shaft_design: str) -> float:
    require_positive("d_sh_mm", d_sh_mm)
    if z1 <= 3:
        raise ValueError("z1 muss groesser 3 sein.")

    factor_by_design = {
        "mounted": 1.8,
        "pinion_shaft": 1.1,
    }
    factor = factor_by_design.get(shaft_design)
    if factor is None:
        raise ValueError(f"Unbekannte Ritzelbauart: {shaft_design}")

    denominator = z1 - 2.5
    if denominator <= 0:
        raise ValueError("z1 - 2.5 muss groesser 0 sein.")

    return factor * d_sh_mm * math.cos(math.radians(beta_deg)) / denominator


def next_norm_module(m_theoretical_mm: float, norm_modules: list[float]) -> float:
    require_positive("m_theoretical_mm", m_theoretical_mm)
    sorted_modules = sorted(float(module) for module in norm_modules)
    for module in sorted_modules:
        if module >= m_theoretical_mm:
            return module
    return sorted_modules[-1]


def next_preferred_norm_module(m_theoretical_mm: float, norm_module_rows: list[dict[str, float | str]]) -> float:
    require_positive("m_theoretical_mm", m_theoretical_mm)
    preferred_modules = sorted(float(row["modul"]) for row in norm_module_rows if str(row["reihe"]) == "I")
    all_modules = sorted(float(row["modul"]) for row in norm_module_rows)

    for module in preferred_modules:
        if module >= m_theoretical_mm:
            return module
    for module in all_modules:
        if module >= m_theoretical_mm:
            return module
    return all_modules[-1]


def calc_teeth_numbers(n1_rpm: float, n2_target_rpm: float, z1: int, z2_manual: int | None = None) -> tuple[int, float, float, float]:
    i_target = calc_ratio(n1_rpm, n2_target_rpm)
    z2 = max(1, int(z2_manual)) if z2_manual is not None else max(1, round(i_target * z1))
    i_real = z2 / z1
    n2_real = n1_rpm / i_real
    deviation_percent = (n2_real - n2_target_rpm) / n2_target_rpm * 100.0
    return z2, i_real, n2_real, deviation_percent


def calc_transverse_pressure_angle(alpha_deg: float, beta_deg: float) -> float:
    beta_cos = max(math.cos(math.radians(beta_deg)), 1e-9)
    alpha_t_rad = math.atan(math.tan(math.radians(alpha_deg)) / beta_cos)
    return math.degrees(alpha_t_rad)


def calc_pitch_diameter(module_mm: float, teeth: int, beta_deg: float = 0.0) -> float:
    require_positive("module_mm", module_mm)
    if teeth <= 0:
        raise ValueError("Zaehnezahl muss groesser 0 sein.")
    beta_cos = max(math.cos(math.radians(beta_deg)), 1e-9)
    return module_mm * teeth / beta_cos


def calc_base_diameter(pitch_diameter_mm: float, alpha_deg: float) -> float:
    return pitch_diameter_mm * math.cos(math.radians(alpha_deg))


def calc_tip_diameter(module_mm: float, teeth: int, beta_deg: float = 0.0) -> float:
    return calc_pitch_diameter(module_mm, teeth, beta_deg) + 2.0 * module_mm


def calc_root_diameter(module_mm: float, teeth: int, beta_deg: float = 0.0) -> float:
    return calc_pitch_diameter(module_mm, teeth, beta_deg) - 2.5 * module_mm


def calc_face_width(module_mm: float, pitch_diameter_mm: float, rule: str, psi_d: float, width_factor_m: float) -> float:
    if rule == "psi_d":
        return psi_d * pitch_diameter_mm
    if rule == "factor_m":
        return width_factor_m * module_mm
    raise ValueError(f"Unbekannte Breitenregel: {rule}")


def calc_gear_geometry(
    module_mm: float,
    teeth: int,
    alpha_deg: float,
    width_rule: str,
    psi_d: float,
    width_factor_m: float,
    beta_deg: float = 0.0,
) -> dict[str, float]:
    d_mm = calc_pitch_diameter(module_mm, teeth, beta_deg)
    alpha_t_deg = calc_transverse_pressure_angle(alpha_deg, beta_deg)
    return {
        "d_mm": d_mm,
        "db_mm": calc_base_diameter(d_mm, alpha_t_deg),
        "da_mm": calc_tip_diameter(module_mm, teeth, beta_deg),
        "df_mm": calc_root_diameter(module_mm, teeth, beta_deg),
        "b_mm": calc_face_width(module_mm, d_mm, width_rule, psi_d, width_factor_m),
    }


def calc_pitch(module_mm: float, beta_deg: float = 0.0) -> float:
    require_positive("module_mm", module_mm)
    beta_cos = max(math.cos(math.radians(beta_deg)), 1e-9)
    return math.pi * module_mm / beta_cos


def calc_base_pitch(module_mm: float, alpha_deg: float, beta_deg: float = 0.0) -> float:
    alpha_t_deg = calc_transverse_pressure_angle(alpha_deg, beta_deg)
    return calc_pitch(module_mm, beta_deg) * math.cos(math.radians(alpha_t_deg))


def calc_path_of_contact(da1_mm: float, db1_mm: float, da2_mm: float, db2_mm: float, center_distance_mm: float, alpha_deg: float) -> float:
    terms = calc_path_of_contact_terms(da1_mm, db1_mm, da2_mm, db2_mm, center_distance_mm, alpha_deg)
    return terms["pinion_mm"] + terms["wheel_mm"] - terms["center_subtract_mm"]


def calc_path_of_contact_terms(
    da1_mm: float,
    db1_mm: float,
    da2_mm: float,
    db2_mm: float,
    center_distance_mm: float,
    alpha_deg: float,
) -> dict[str, float]:
    alpha_rad = math.radians(alpha_deg)
    term1 = math.sqrt(max((da1_mm / 2.0) ** 2 - (db1_mm / 2.0) ** 2, 0.0))
    term2 = math.sqrt(max((da2_mm / 2.0) ** 2 - (db2_mm / 2.0) ** 2, 0.0))
    center_subtract = center_distance_mm * math.sin(alpha_rad)
    return {
        "pinion_mm": term1,
        "wheel_mm": term2,
        "center_subtract_mm": center_subtract,
    }


def calc_contact_ratio(path_of_contact_mm: float, base_pitch_mm: float) -> float:
    require_positive("base_pitch_mm", base_pitch_mm)
    return path_of_contact_mm / base_pitch_mm


def calc_forces(moment_nm: float, d1_mm: float, alpha_deg: float, beta_deg: float) -> tuple[float, float, float, float]:
    require_positive("d1_mm", d1_mm)
    ft_n = 2.0 * nm_to_nmm(moment_nm) / d1_mm
    alpha_t_deg = calc_transverse_pressure_angle(alpha_deg, beta_deg)
    fr_n = ft_n * math.tan(math.radians(alpha_t_deg))
    fa_n = ft_n * math.tan(math.radians(beta_deg))
    resultant_n = math.sqrt(ft_n**2 + fr_n**2 + fa_n**2)
    return ft_n, fr_n, fa_n, resultant_n


def calc_bearing_reactions(force_n: float, left_distance_mm: float, right_distance_mm: float) -> tuple[float, float]:
    require_positive("left_distance_mm", left_distance_mm)
    require_positive("right_distance_mm", right_distance_mm)
    total_distance = left_distance_mm + right_distance_mm
    left_reaction = force_n * right_distance_mm / total_distance
    right_reaction = force_n * left_distance_mm / total_distance
    return left_reaction, right_reaction


def calc_max_bending_moment_single_force(force_n: float, left_distance_mm: float, right_distance_mm: float) -> float:
    left_reaction, _ = calc_bearing_reactions(force_n, left_distance_mm, right_distance_mm)
    return left_reaction * left_distance_mm


def calc_section_loads(
    force_tangential_n: float,
    force_radial_n: float,
    left_distance_mm: float,
    right_distance_mm: float,
    points: int = 101,
) -> list[dict[str, float]]:
    if points < 2:
        raise ValueError("points muss mindestens 2 sein.")

    left_reaction_t, _ = calc_bearing_reactions(force_tangential_n, left_distance_mm, right_distance_mm)
    left_reaction_r, _ = calc_bearing_reactions(force_radial_n, left_distance_mm, right_distance_mm)
    total_length = left_distance_mm + right_distance_mm
    rows: list[dict[str, float]] = []

    for index in range(points):
        x_mm = total_length * index / (points - 1)

        if x_mm < left_distance_mm:
            v_t = left_reaction_t
            v_r = left_reaction_r
            m_t = left_reaction_t * x_mm
            m_r = left_reaction_r * x_mm
        else:
            v_t = left_reaction_t - force_tangential_n
            v_r = left_reaction_r - force_radial_n
            m_t = left_reaction_t * x_mm - force_tangential_n * (x_mm - left_distance_mm)
            m_r = left_reaction_r * x_mm - force_radial_n * (x_mm - left_distance_mm)

        rows.append(
            {
                "x_mm": x_mm,
                "V_t_N": v_t,
                "V_r_N": v_r,
                "M_t_Nmm": m_t,
                "M_r_Nmm": m_r,
                "M_res_Nmm": math.sqrt(m_t**2 + m_r**2),
            }
        )

    return rows


def calc_bearing_life_h(dynamic_rating_c_kn: float, equivalent_load_n: float, n_rpm: float, exponent: float = 3.0) -> float:
    require_positive("dynamic_rating_c_kn", dynamic_rating_c_kn)
    require_positive("equivalent_load_n", equivalent_load_n)
    require_positive("n_rpm", n_rpm)
    c_n = kn_to_n(dynamic_rating_c_kn)
    return (1_000_000.0 / (60.0 * n_rpm)) * (c_n / equivalent_load_n) ** exponent


def calc_static_safety(static_rating_c0_kn: float, static_load_n: float) -> float:
    require_positive("static_rating_c0_kn", static_rating_c0_kn)
    require_positive("static_load_n", static_load_n)
    return kn_to_n(static_rating_c0_kn) / static_load_n
