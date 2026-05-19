def kw_to_w(power_kw: float) -> float:
    return power_kw * 1000.0


def rpm_to_per_second(n_rpm: float) -> float:
    return n_rpm / 60.0


def nm_to_nmm(moment_nm: float) -> float:
    return moment_nm * 1000.0


def kn_to_n(force_kn: float) -> float:
    return force_kn * 1000.0

