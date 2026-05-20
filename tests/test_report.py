from pathlib import Path
import unittest

from core.dependency_engine import load_bearings, load_norm_module_rows, recalculate_all
from core.models import GearInputs
from core.report import generate_calculation_report, generate_latex_report, generate_live_latex_blocks


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


class ReportTests(unittest.TestCase):
    def test_calculation_report_contains_formulas_values_and_checks(self):
        norm_modules = load_norm_module_rows(DATA / "normmodule.csv")
        bearings = load_bearings(DATA / "lager.csv")
        inputs = GearInputs(
            selected_module=2.5,
            selected_bearing_left="6206",
            selected_bearing_right="6206",
        )
        results = recalculate_all(inputs, norm_modules, bearings)

        report = generate_calculation_report(inputs, results, bearings)

        self.assertIn("# Rechenbericht Getriebeauslegung", report)
        self.assertNotIn("## Bezeichnungen der berechneten Werte", report)
        self.assertIn("**Berechnet: Soll-Uebersetzung**", report)
        self.assertIn("Formel: `i_soll = n_1 / n_2,soll`", report)
        self.assertIn("**Berechnet: Abweichung der realen Uebersetzung von der Soll-Uebersetzung**", report)
        self.assertIn("`Delta_i = (i_real - i_soll) / i_soll * 100 %`", report)
        self.assertIn("`m' = (1,8 * d_sh * cos(beta)) / (z_1 - 2,5)`", report)
        self.assertIn("`g_alpha = sqrt((d_a1/2)^2 - (d_b1/2)^2)", report)
        self.assertIn("g_alpha = 12,831 mm", report)
        self.assertIn("epsilon_alpha = 1,739", report)
        self.assertIn("Lager links: **6206", report)
        self.assertIn("L_10h,links", report)
        self.assertIn("## 12. Pruefungen", report)

    def test_report_uses_manual_z2_text(self):
        norm_modules = load_norm_module_rows(DATA / "normmodule.csv")
        bearings = load_bearings(DATA / "lager.csv")
        inputs = GearInputs(z1=26, z2_manual=112, selected_module=2.5)
        results = recalculate_all(inputs, norm_modules, bearings)

        report = generate_calculation_report(inputs, results, bearings)

        self.assertIn("`z_2` wurde manuell gewaehlt", report)
        self.assertIn("g_alpha = 12,862 mm", report)

    def test_latex_report_contains_latex_formulas(self):
        norm_modules = load_norm_module_rows(DATA / "normmodule.csv")
        bearings = load_bearings(DATA / "lager.csv")
        inputs = GearInputs(
            selected_module=2.5,
            selected_bearing_left="6206",
            selected_bearing_right="6206",
        )
        results = recalculate_all(inputs, norm_modules, bearings)

        report = generate_latex_report(inputs, results, bearings)

        self.assertIn(r"\documentclass", report)
        self.assertIn(r"\begin{align*}", report)
        self.assertIn(r"g_\alpha", report)
        self.assertIn(r"\varepsilon_\alpha", report)
        self.assertIn(r"L_{10h}", report)
        self.assertIn(r"12{,}831", report)
        self.assertTrue(report.strip().endswith(r"\end{document}"))

    def test_live_latex_blocks_are_generated(self):
        norm_modules = load_norm_module_rows(DATA / "normmodule.csv")
        bearings = load_bearings(DATA / "lager.csv")
        inputs = GearInputs(selected_module=2.5)
        results = recalculate_all(inputs, norm_modules, bearings)

        blocks = generate_live_latex_blocks(inputs, results, bearings)

        titles = [title for title, _ in blocks]
        rendered = "\n".join(formula for _, formulas in blocks for formula in formulas)
        self.assertNotIn("Bezeichnungen", titles)
        self.assertIn("Grundrechnung", titles)
        self.assertIn(r"\text{Soll-Uebersetzung", rendered)
        self.assertIn("Zahneingriff", titles)
        self.assertIn(r"g_\alpha", rendered)
        self.assertIn(r"\varepsilon_\alpha", rendered)
        self.assertIn(r"12{,}831", rendered)


if __name__ == "__main__":
    unittest.main()
