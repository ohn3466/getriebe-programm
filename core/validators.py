from __future__ import annotations

from typing import Any

from core.models import CheckResult, GearInputs, GearResults


def ok(name: str, value: str, limit: str, message: str) -> CheckResult:
    return CheckResult(name=name, status="OK", value=value, limit=limit, message=message)


def warning(name: str, value: str, limit: str, message: str) -> CheckResult:
    return CheckResult(name=name, status="WARNUNG", value=value, limit=limit, message=message)


def error(name: str, value: str, limit: str, message: str) -> CheckResult:
    return CheckResult(name=name, status="FEHLER", value=value, limit=limit, message=message)


def missing(name: str, value: str, limit: str, message: str) -> CheckResult:
    return CheckResult(name=name, status="NICHT BERECHNET", value=value, limit=limit, message=message)


def fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def check_positive(name: str, value: float, unit: str = "") -> CheckResult:
    value_text = f"{fmt(value)} {unit}".strip()
    if value > 0:
        return ok(name, value_text, "> 0", "Eingabewert ist positiv.")
    return error(name, value_text, "> 0", "Eingabewert muss groesser 0 sein.")


def check_angles(inputs: GearInputs, results: GearResults) -> list[CheckResult]:
    checks: list[CheckResult] = []

    if 14.0 <= inputs.alpha_deg <= 25.0:
        checks.append(
            ok(
                "Eingriffswinkel alpha",
                f"{fmt(inputs.alpha_deg)} deg",
                "14 deg bis 25 deg",
                "Eingriffswinkel liegt im ueblichen Bereich.",
            )
        )
    elif inputs.alpha_deg > 0:
        checks.append(
            warning(
                "Eingriffswinkel alpha",
                f"{fmt(inputs.alpha_deg)} deg",
                "14 deg bis 25 deg",
                "Eingriffswinkel ist unueblich. Pruefe die Vorgabe aus der Aufgabe.",
            )
        )
    else:
        checks.append(error("Eingriffswinkel alpha", f"{fmt(inputs.alpha_deg)} deg", "> 0 deg", "Eingriffswinkel muss positiv sein."))

    if 0.0 <= inputs.beta_deg <= 30.0:
        checks.append(
            ok(
                "Schraegungswinkel beta",
                f"{fmt(inputs.beta_deg)} deg",
                "0 deg bis 30 deg",
                f"Schraegungswinkel ist plausibel; Stirneingriffswinkel alpha_t = {fmt(results.alpha_transverse_deg)} deg.",
            )
        )
    elif inputs.beta_deg < 45.0:
        checks.append(
            warning(
                "Schraegungswinkel beta",
                f"{fmt(inputs.beta_deg)} deg",
                "0 deg bis 30 deg",
                f"Schraegungswinkel ist hoch. Rechenweg nutzt alpha_t = {fmt(results.alpha_transverse_deg)} deg.",
            )
        )
    else:
        checks.append(
            error(
                "Schraegungswinkel beta",
                f"{fmt(inputs.beta_deg)} deg",
                "< 45 deg",
                "Schraegungswinkel ist fuer diese einfache Auslegung nicht plausibel.",
            )
        )

    return checks


def check_bearing(
    side: str,
    bearing: dict[str, Any] | None,
    seat_mm: float,
    load_n: float,
    life_h: float | None,
    static_safety: float | None,
    required_life_h: float,
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    label = f"Lager {side}"
    if bearing is None:
        return [
            missing(
                f"{label} Auswahl",
                "-",
                "Lager gewaehlt",
                "Noch kein Lager gewaehlt. Waehle ein Lager mit passender Bohrung.",
            )
        ]

    bore = float(bearing["d"])
    bearing_name = str(bearing["lager"])
    if abs(bore - seat_mm) < 1e-9:
        checks.append(ok(f"{label} Bohrung", f"{bore:g} mm", f"{seat_mm:g} mm", f"{bearing_name} passt zum Lagersitz."))
    else:
        checks.append(
            error(
                f"{label} Bohrung",
                f"{bore:g} mm",
                f"{seat_mm:g} mm",
                f"{bearing_name} passt nicht zum aktuellen Lagersitz.",
            )
        )

    if life_h is None:
        checks.append(missing(f"{label} Lebensdauer", "-", f">= {required_life_h:g} h", "Lebensdauer nicht berechnet."))
    elif life_h >= required_life_h:
        checks.append(ok(f"{label} Lebensdauer", f"{life_h:.0f} h", f">= {required_life_h:g} h", "L10h ist ausreichend."))
    else:
        checks.append(
            error(
                f"{label} Lebensdauer",
                f"{life_h:.0f} h",
                f">= {required_life_h:g} h",
                "Lager ist dynamisch zu klein. Waehle ein Lager mit hoeherer Tragzahl C.",
            )
        )

    if static_safety is None:
        checks.append(missing(f"{label} statische Sicherheit", "-", ">= 1.0", "Statische Sicherheit nicht berechnet."))
    elif static_safety >= 1.0:
        checks.append(ok(f"{label} statische Sicherheit", fmt(static_safety), ">= 1.0", "Statische Sicherheit ist ausreichend."))
    else:
        checks.append(
            warning(
                f"{label} statische Sicherheit",
                fmt(static_safety),
                ">= 1.0",
                "Statische Sicherheit ist klein. Pruefe C0 oder waehle ein groesseres Lager.",
            )
        )

    if load_n <= 0:
        checks.append(error(f"{label} Lagerlast", fmt(load_n, 1), "> 0 N", "Lagerlast ist nicht plausibel."))

    return checks


def run_all_checks(
    inputs: GearInputs,
    results: GearResults,
    left_bearing: dict[str, Any] | None,
    right_bearing: dict[str, Any] | None,
) -> list[CheckResult]:
    checks: list[CheckResult] = [
        check_positive("Leistung P", inputs.power_kw, "kW"),
        check_positive("Antriebsdrehzahl n1", inputs.n1_rpm, "1/min"),
        check_positive("Abtriebsdrehzahl n2 soll", inputs.n2_target_rpm, "1/min"),
    ]
    checks.extend(check_angles(inputs, results))

    if inputs.z1 >= 17:
        checks.append(ok("Zaehnezahl z1", str(inputs.z1), ">= 17", "Zaehnezahl ist fuer Standardverzahnung plausibel."))
    else:
        checks.append(
            warning(
                "Zaehnezahl z1",
                str(inputs.z1),
                ">= 17",
                "Zaehnezahl ist klein. Unterschnitt oder Profilverschiebung pruefen.",
            )
        )

    if inputs.d_sh_pinion_mm >= results.d_min_shaft_1_mm:
        checks.append(
            ok(
                "d_sh gegen d_min",
                f"{inputs.d_sh_pinion_mm:g} mm",
                f">= {results.d_min_shaft_1_mm:.2f} mm",
                "Ritzel-/Nabendurchmesser ist groesser als der torsionale Mindestdurchmesser.",
            )
        )
    else:
        checks.append(
            error(
                "d_sh gegen d_min",
                f"{inputs.d_sh_pinion_mm:g} mm",
                f">= {results.d_min_shaft_1_mm:.2f} mm",
                "d_sh ist kleiner als der torsionale Mindestdurchmesser. Welle vergroessern oder Werkstoff pruefen.",
            )
        )

    if results.m_selected_mm >= results.m_theoretical_mm:
        checks.append(
            ok(
                "Normmodul",
                f"{results.m_selected_mm:g} mm",
                f">= {results.m_theoretical_mm:.3f} mm",
                "Das gewaehlte Modul deckt den theoretischen Modul ab.",
            )
        )
    else:
        checks.append(
            error(
                "Normmodul",
                f"{results.m_selected_mm:g} mm",
                f">= {results.m_theoretical_mm:.3f} mm",
                "Das gewaehlte Modul ist kleiner als der theoretisch erforderliche Modul.",
            )
        )

    abs_deviation = abs(results.n2_deviation_percent)
    if abs_deviation <= 5.0:
        checks.append(ok("Abtriebsdrehzahl", f"{results.n2_deviation_percent:.2f} %", "<= 5 %", "Drehzahlabweichung liegt im Zielbereich."))
    elif abs_deviation <= 10.0:
        checks.append(
            warning(
                "Abtriebsdrehzahl",
                f"{results.n2_deviation_percent:.2f} %",
                "<= 5 %",
                "Drehzahlabweichung ist erhoeht. z1 oder z2 pruefen.",
            )
        )
    else:
        checks.append(
            error(
                "Abtriebsdrehzahl",
                f"{results.n2_deviation_percent:.2f} %",
                "<= 5 %",
                "Drehzahlabweichung ist zu gross. Zaehnezahlen neu waehlen.",
            )
        )

    if results.contact_ratio >= 1.2:
        checks.append(ok("Profilueberdeckung", fmt(results.contact_ratio), ">= 1.2", "Profilueberdeckung ist gut."))
    elif results.contact_ratio >= 1.0:
        checks.append(
            warning(
                "Profilueberdeckung",
                fmt(results.contact_ratio),
                ">= 1.2",
                "Profilueberdeckung ist knapp. Modul, Zaehnezahlen oder Profilverschiebung pruefen.",
            )
        )
    else:
        checks.append(
            error(
                "Profilueberdeckung",
                fmt(results.contact_ratio),
                "> 1.0",
                "Profilueberdeckung ist nicht zulaessig. Geometrie neu auslegen.",
            )
        )

    checks.extend(
        check_bearing(
            "links",
            left_bearing,
            inputs.bearing_seat_left_mm,
            results.bearing_load_left_N,
            results.bearing_life_left_h,
            results.bearing_static_safety_left,
            inputs.bearing_life_required_h,
        )
    )
    checks.extend(
        check_bearing(
            "rechts",
            right_bearing,
            inputs.bearing_seat_right_mm,
            results.bearing_load_right_N,
            results.bearing_life_right_h,
            results.bearing_static_safety_right,
            inputs.bearing_life_required_h,
        )
    )

    return checks
