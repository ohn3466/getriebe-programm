from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    value: str
    limit: str
    message: str


@dataclass(frozen=True)
class GearInputs:
    project_name: str = "Getriebeauslegung"
    power_kw: float = 12.0
    n1_rpm: float = 1850.0
    n2_target_rpm: float = 410.0
    alpha_deg: float = 20.0
    beta_deg: float = 0.0
    z1: int = 25
    z2_manual: int | None = None
    shaft_material: str = "C45E"
    tau_t_zul: float = 32.0
    sigma_b_zul: float = 64.0
    shaft_design: str = "mounted"
    d_sh_pinion_mm: float = 28.0
    d_sh_wheel_mm: float = 45.0
    selected_module: float | None = None
    width_rule: str = "psi_d"
    psi_d: float = 1.0
    width_factor_m: float = 12.0
    b2_offset_mm: float = 0.0
    bearing_distance_left_mm: float = 60.0
    bearing_distance_right_mm: float = 80.0
    bearing_seat_left_mm: float = 30.0
    bearing_seat_right_mm: float = 30.0
    bearing_life_required_h: float = 10000.0
    selected_bearing_left: str | None = None
    selected_bearing_right: str | None = None


@dataclass
class GearResults:
    i_target: float = 0.0
    M1_Nm: float = 0.0
    M2_Nm: float = 0.0
    d_min_shaft_1_mm: float = 0.0
    d_min_shaft_2_mm: float = 0.0
    m_theoretical_mm: float = 0.0
    m_recommended_mm: float = 0.0
    m_selected_mm: float = 0.0
    z1: int = 0
    z2: int = 0
    i_real: float = 0.0
    i_deviation_percent: float = 0.0
    n2_real_rpm: float = 0.0
    n2_deviation_percent: float = 0.0
    alpha_transverse_deg: float = 0.0
    d1_mm: float = 0.0
    db1_mm: float = 0.0
    da1_mm: float = 0.0
    df1_mm: float = 0.0
    b1_mm: float = 0.0
    d2_mm: float = 0.0
    db2_mm: float = 0.0
    da2_mm: float = 0.0
    df2_mm: float = 0.0
    b2_mm: float = 0.0
    center_distance_mm: float = 0.0
    pitch_mm: float = 0.0
    base_pitch_mm: float = 0.0
    path_contact_pinion_mm: float = 0.0
    path_contact_wheel_mm: float = 0.0
    path_contact_center_subtract_mm: float = 0.0
    path_of_contact_mm: float = 0.0
    contact_ratio: float = 0.0
    Ft_N: float = 0.0
    Fr_N: float = 0.0
    Fa_N: float = 0.0
    tooth_force_resultant_N: float = 0.0
    bearing_left_tangential_N: float = 0.0
    bearing_right_tangential_N: float = 0.0
    bearing_left_radial_N: float = 0.0
    bearing_right_radial_N: float = 0.0
    bearing_load_left_N: float = 0.0
    bearing_load_right_N: float = 0.0
    max_bending_tangential_Nmm: float = 0.0
    max_bending_radial_Nmm: float = 0.0
    max_bending_resultant_Nmm: float = 0.0
    bearing_life_left_h: float | None = None
    bearing_life_right_h: float | None = None
    bearing_static_safety_left: float | None = None
    bearing_static_safety_right: float | None = None
    checks: list[CheckResult] = field(default_factory=list)
