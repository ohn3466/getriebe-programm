from __future__ import annotations

from typing import Any

import pandas as pd


def same_module(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return False
    return abs(float(left) - float(right)) < 1e-9


def norm_module_status(module: float, m_theoretical: float, m_recommended: float, m_selected: float | None) -> str:
    is_recommended = same_module(module, m_recommended)
    is_selected = same_module(module, m_selected)

    if is_recommended and is_selected:
        return "empfohlen und gewaehlt"
    if is_recommended:
        return "empfohlen"
    if is_selected:
        return "gewaehlt"
    if module < m_theoretical - 1e-9:
        return "zu klein"
    return "moeglich"


def build_norm_module_table(
    norm_module_rows: list[dict[str, Any]],
    m_theoretical: float,
    m_recommended: float,
    m_selected: float | None,
) -> pd.DataFrame:
    rows = []
    for row in sorted(norm_module_rows, key=lambda item: (float(item["modul"]), str(item["reihe"]))):
        module = float(row["modul"])
        rows.append(
            {
                "Reihe": str(row["reihe"]),
                "Normmodul [mm]": module,
                "Status": norm_module_status(module, m_theoretical, m_recommended, m_selected),
                "Abstand zu m' [mm]": module - m_theoretical,
            }
        )
    return pd.DataFrame(rows)
