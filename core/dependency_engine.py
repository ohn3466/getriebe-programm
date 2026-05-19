from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from core.calculations import (
    calc_bearing_life_h,
    calc_bearing_reactions,
    calc_base_pitch,
    calc_contact_ratio,
    calc_forces,
    calc_gear_geometry,
    calc_max_bending_moment_single_force,
    calc_min_shaft_diameter,
    calc_module_from_dsh,
    calc_path_of_contact,
    calc_path_of_contact_terms,
    calc_pitch,
    calc_ratio,
    calc_static_safety,
    calc_teeth_numbers,
    calc_torque,
    calc_transverse_pressure_angle,
    next_preferred_norm_module,
)
from core.models import GearInputs, GearResults
from core.validators import run_all_checks


def load_norm_modules(path: str | Path) -> list[float]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [float(row["modul"]) for row in reader]


def load_norm_module_rows(path: str | Path) -> list[dict[str, Any]]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [{"reihe": str(row["reihe"]), "modul": float(row["modul"])} for row in reader]


def load_materials(path: str | Path) -> list[dict[str, Any]]:
    numeric_fields = {"tau_t_zul", "sigma_b_zul", "Rm", "Re"}
    materials: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed = dict(row)
            for field in numeric_fields:
                parsed[field] = float(parsed[field])
            materials.append(parsed)
    return materials


def load_bearings(path: str | Path) -> list[dict[str, Any]]:
    numeric_fields = {"d", "D", "B", "C", "C0"}
    bearings: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            parsed = dict(row)
            for field in numeric_fields:
                parsed[field] = float(parsed[field])
            bearings.append(parsed)
    return bearings


def find_bearing(bearings: list[dict[str, Any]], name: str | None) -> dict[str, Any] | None:
    if not name:
        return None
    for bearing in bearings:
        if str(bearing["lager"]) == str(name):
            return bearing
    return None


def normalize_norm_modules(norm_modules: list[Any]) -> tuple[list[float], list[dict[str, Any]]]:
    if not norm_modules:
        raise ValueError("Normmodul-Tabelle ist leer.")

    first = norm_modules[0]
    if isinstance(first, dict):
        rows = [{"reihe": str(row["reihe"]), "modul": float(row["modul"])} for row in norm_modules]
        modules = [row["modul"] for row in rows]
        return modules, rows

    modules = [float(module) for module in norm_modules]
    rows = [{"reihe": "I", "modul": module} for module in modules]
    return modules, rows


def recalculate_all(inputs: GearInputs, norm_modules: list[Any], bearings: list[dict[str, Any]]) -> GearResults:
    results = GearResults()
    _, norm_module_rows = normalize_norm_modules(norm_modules)

    results.i_target = calc_ratio(inputs.n1_rpm, inputs.n2_target_rpm)
    results.M1_Nm = calc_torque(inputs.power_kw, inputs.n1_rpm)
    results.M2_Nm = results.M1_Nm * results.i_target
    results.d_min_shaft_1_mm = calc_min_shaft_diameter(results.M1_Nm, inputs.tau_t_zul)
    results.d_min_shaft_2_mm = calc_min_shaft_diameter(results.M2_Nm, inputs.tau_t_zul)

    results.m_theoretical_mm = calc_module_from_dsh(
        inputs.d_sh_pinion_mm,
        inputs.z1,
        inputs.beta_deg,
        inputs.shaft_design,
    )
    results.m_recommended_mm = next_preferred_norm_module(results.m_theoretical_mm, norm_module_rows)
    results.m_selected_mm = float(inputs.selected_module or results.m_recommended_mm)

    results.z1 = inputs.z1
    results.z2, results.i_real, results.n2_real_rpm, results.n2_deviation_percent = calc_teeth_numbers(
        inputs.n1_rpm,
        inputs.n2_target_rpm,
        inputs.z1,
        inputs.z2_manual,
    )
    results.alpha_transverse_deg = calc_transverse_pressure_angle(inputs.alpha_deg, inputs.beta_deg)

    pinion = calc_gear_geometry(
        results.m_selected_mm,
        inputs.z1,
        inputs.alpha_deg,
        inputs.width_rule,
        inputs.psi_d,
        inputs.width_factor_m,
        inputs.beta_deg,
    )
    wheel = calc_gear_geometry(
        results.m_selected_mm,
        results.z2,
        inputs.alpha_deg,
        inputs.width_rule,
        inputs.psi_d,
        inputs.width_factor_m,
        inputs.beta_deg,
    )

    results.d1_mm = pinion["d_mm"]
    results.db1_mm = pinion["db_mm"]
    results.da1_mm = pinion["da_mm"]
    results.df1_mm = pinion["df_mm"]
    results.b1_mm = pinion["b_mm"]

    results.d2_mm = wheel["d_mm"]
    results.db2_mm = wheel["db_mm"]
    results.da2_mm = wheel["da_mm"]
    results.df2_mm = wheel["df_mm"]
    results.b2_mm = max(wheel["b_mm"] - inputs.b2_offset_mm, 0.0)
    results.center_distance_mm = (results.d1_mm + results.d2_mm) / 2.0

    results.pitch_mm = calc_pitch(results.m_selected_mm, inputs.beta_deg)
    results.base_pitch_mm = calc_base_pitch(results.m_selected_mm, inputs.alpha_deg, inputs.beta_deg)
    path_terms = calc_path_of_contact_terms(
        results.da1_mm,
        results.db1_mm,
        results.da2_mm,
        results.db2_mm,
        results.center_distance_mm,
        results.alpha_transverse_deg,
    )
    results.path_contact_pinion_mm = path_terms["pinion_mm"]
    results.path_contact_wheel_mm = path_terms["wheel_mm"]
    results.path_contact_center_subtract_mm = path_terms["center_subtract_mm"]
    results.path_of_contact_mm = calc_path_of_contact(
        results.da1_mm,
        results.db1_mm,
        results.da2_mm,
        results.db2_mm,
        results.center_distance_mm,
        results.alpha_transverse_deg,
    )
    results.contact_ratio = calc_contact_ratio(results.path_of_contact_mm, results.base_pitch_mm)

    results.Ft_N, results.Fr_N, results.Fa_N, results.tooth_force_resultant_N = calc_forces(
        results.M1_Nm,
        results.d1_mm,
        inputs.alpha_deg,
        inputs.beta_deg,
    )

    results.bearing_left_tangential_N, results.bearing_right_tangential_N = calc_bearing_reactions(
        results.Ft_N,
        inputs.bearing_distance_left_mm,
        inputs.bearing_distance_right_mm,
    )
    results.bearing_left_radial_N, results.bearing_right_radial_N = calc_bearing_reactions(
        results.Fr_N,
        inputs.bearing_distance_left_mm,
        inputs.bearing_distance_right_mm,
    )
    results.bearing_load_left_N = math.sqrt(results.bearing_left_tangential_N**2 + results.bearing_left_radial_N**2)
    results.bearing_load_right_N = math.sqrt(results.bearing_right_tangential_N**2 + results.bearing_right_radial_N**2)
    results.max_bending_tangential_Nmm = calc_max_bending_moment_single_force(
        results.Ft_N,
        inputs.bearing_distance_left_mm,
        inputs.bearing_distance_right_mm,
    )
    results.max_bending_radial_Nmm = calc_max_bending_moment_single_force(
        results.Fr_N,
        inputs.bearing_distance_left_mm,
        inputs.bearing_distance_right_mm,
    )
    results.max_bending_resultant_Nmm = math.sqrt(
        results.max_bending_tangential_Nmm**2 + results.max_bending_radial_Nmm**2
    )

    left_bearing = find_bearing(bearings, inputs.selected_bearing_left)
    right_bearing = find_bearing(bearings, inputs.selected_bearing_right)

    if left_bearing and results.bearing_load_left_N > 0:
        results.bearing_life_left_h = calc_bearing_life_h(
            float(left_bearing["C"]),
            results.bearing_load_left_N,
            inputs.n1_rpm,
        )
        results.bearing_static_safety_left = calc_static_safety(
            float(left_bearing["C0"]),
            results.bearing_load_left_N,
        )

    if right_bearing and results.bearing_load_right_N > 0:
        results.bearing_life_right_h = calc_bearing_life_h(
            float(right_bearing["C"]),
            results.bearing_load_right_N,
            inputs.n1_rpm,
        )
        results.bearing_static_safety_right = calc_static_safety(
            float(right_bearing["C0"]),
            results.bearing_load_right_N,
        )

    results.checks = run_all_checks(inputs, results, left_bearing, right_bearing)
    return results
