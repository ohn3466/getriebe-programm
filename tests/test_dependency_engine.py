from pathlib import Path
import unittest

from core.calculations import calc_section_loads
from core.dependency_engine import load_bearings, load_materials, load_norm_module_rows, recalculate_all
from core.models import GearInputs


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def check_by_name(results, name):
    for check in results.checks:
        if check.name == name:
            return check
    raise AssertionError(f"Check nicht gefunden: {name}")


class DependencyEngineTests(unittest.TestCase):
    def setUp(self):
        self.norm_modules = load_norm_module_rows(DATA / "normmodule.csv")
        self.bearings = load_bearings(DATA / "lager.csv")

    def test_norm_modules_include_reihe_i_and_ii(self):
        modules_by_row = {(row["reihe"], row["modul"]) for row in self.norm_modules}

        self.assertIn(("I", 2.5), modules_by_row)
        self.assertIn(("I", 50.0), modules_by_row)
        self.assertIn(("II", 2.25), modules_by_row)
        self.assertIn(("II", 45.0), modules_by_row)

    def test_42crmo4_tau_t_zul_from_table(self):
        materials = load_materials(DATA / "werkstoffe.csv")
        material = next(row for row in materials if row["werkstoff"] == "42CrMo4")

        self.assertEqual(float(material["tau_t_zul"]), 55.0)

    def test_default_chain_recalculates_expected_values(self):
        inputs = GearInputs(selected_module=2.5, selected_bearing_left="6206", selected_bearing_right="6206")
        results = recalculate_all(inputs, self.norm_modules, self.bearings)

        self.assertAlmostEqual(results.i_target, 1850 / 410)
        self.assertAlmostEqual(results.i_deviation_percent, (results.i_real - results.i_target) / results.i_target * 100.0)
        self.assertAlmostEqual(results.alpha_transverse_deg, inputs.alpha_deg)
        self.assertAlmostEqual(results.m_theoretical_mm, 2.24, places=2)
        self.assertEqual(results.m_recommended_mm, 2.5)
        self.assertEqual(results.z2, 113)
        self.assertAlmostEqual(results.d1_mm, 62.5)
        self.assertAlmostEqual(results.d2_mm, 282.5)
        self.assertGreater(results.contact_ratio, 1.0)
        self.assertGreater(results.Ft_N, 0)
        self.assertGreater(results.bearing_load_left_N, 0)
        self.assertIsNotNone(results.bearing_life_left_h)
        self.assertIsNotNone(results.bearing_life_right_h)

    def test_dsh_change_updates_recommended_module_and_geometry(self):
        inputs = GearInputs(d_sh_pinion_mm=32, selected_module=3.0)
        results = recalculate_all(inputs, self.norm_modules, self.bearings)

        self.assertGreater(results.m_theoretical_mm, 2.5)
        self.assertEqual(results.m_recommended_mm, 3.0)
        self.assertAlmostEqual(results.d1_mm, 75.0)
        self.assertAlmostEqual(results.d2_mm, 339.0)

    def test_module_change_updates_complete_downstream_chain(self):
        base = recalculate_all(GearInputs(d_sh_pinion_mm=28, selected_module=2.5), self.norm_modules, self.bearings)
        changed = recalculate_all(GearInputs(d_sh_pinion_mm=32, selected_module=3.0), self.norm_modules, self.bearings)

        changed_fields = [
            "m_theoretical_mm",
            "m_recommended_mm",
            "m_selected_mm",
            "d1_mm",
            "db1_mm",
            "da1_mm",
            "df1_mm",
            "b1_mm",
            "d2_mm",
            "db2_mm",
            "da2_mm",
            "df2_mm",
            "b2_mm",
            "center_distance_mm",
            "pitch_mm",
            "base_pitch_mm",
            "path_contact_pinion_mm",
            "path_contact_wheel_mm",
            "path_contact_center_subtract_mm",
            "path_of_contact_mm",
            "Ft_N",
            "Fr_N",
            "tooth_force_resultant_N",
            "bearing_load_left_N",
            "bearing_load_right_N",
            "max_bending_resultant_Nmm",
        ]

        for field in changed_fields:
            with self.subTest(field=field):
                self.assertNotAlmostEqual(getattr(base, field), getattr(changed, field), places=9)

        self.assertAlmostEqual(base.path_of_contact_mm, 12.831019702359193)
        self.assertAlmostEqual(
            base.path_contact_pinion_mm + base.path_contact_wheel_mm - base.path_contact_center_subtract_mm,
            base.path_of_contact_mm,
        )
        self.assertAlmostEqual(base.contact_ratio, changed.contact_ratio)

    def test_beta_change_updates_complete_downstream_chain(self):
        spur = recalculate_all(GearInputs(selected_module=2.5, beta_deg=0), self.norm_modules, self.bearings)
        helical = recalculate_all(GearInputs(selected_module=2.5, beta_deg=20), self.norm_modules, self.bearings)

        self.assertGreater(helical.alpha_transverse_deg, 20.0)
        self.assertGreater(helical.d1_mm, spur.d1_mm)
        self.assertGreater(helical.pitch_mm, spur.pitch_mm)
        self.assertGreater(helical.Fa_N, 0.0)
        self.assertNotAlmostEqual(helical.db1_mm, spur.db1_mm)
        self.assertNotAlmostEqual(helical.path_of_contact_mm, spur.path_of_contact_mm)

        self.assertEqual(check_by_name(helical, "Schraegungswinkel beta").status, "OK")

    def test_too_small_manual_module_is_reported_as_error(self):
        inputs = GearInputs(d_sh_pinion_mm=32, selected_module=2.5)
        results = recalculate_all(inputs, self.norm_modules, self.bearings)
        module_check = check_by_name(results, "Normmodul")

        self.assertEqual(module_check.status, "FEHLER")

    def test_manual_z2_updates_ratio_geometry_and_g_alpha(self):
        automatic = recalculate_all(GearInputs(z1=26, selected_module=2.5), self.norm_modules, self.bearings)
        manual = recalculate_all(GearInputs(z1=26, z2_manual=112, selected_module=2.5), self.norm_modules, self.bearings)

        self.assertNotEqual(automatic.z2, manual.z2)
        self.assertEqual(manual.z2, 112)
        self.assertAlmostEqual(manual.i_real, 112 / 26)
        self.assertNotAlmostEqual(automatic.d2_mm, manual.d2_mm)
        self.assertNotAlmostEqual(automatic.path_of_contact_mm, manual.path_of_contact_mm)
        self.assertAlmostEqual(manual.path_of_contact_mm, 12.861794361585758)

    def test_bearing_selection_links_to_life_checks(self):
        inputs = GearInputs(selected_module=2.5, selected_bearing_left="6206", selected_bearing_right="6206")
        results = recalculate_all(inputs, self.norm_modules, self.bearings)

        self.assertEqual(check_by_name(results, "Lager links Bohrung").status, "OK")
        self.assertEqual(check_by_name(results, "Lager rechts Bohrung").status, "OK")
        self.assertEqual(check_by_name(results, "Lager links Lebensdauer").status, "OK")
        self.assertEqual(check_by_name(results, "Lager rechts Lebensdauer").status, "OK")

    def test_section_loads_have_zero_end_moments_and_maximum_at_force(self):
        rows = calc_section_loads(1000, 500, 60, 80, points=15)
        force_row = rows[6]

        self.assertAlmostEqual(rows[0]["M_res_Nmm"], 0.0)
        self.assertAlmostEqual(rows[-1]["M_res_Nmm"], 0.0)
        self.assertAlmostEqual(force_row["x_mm"], 60.0)
        self.assertAlmostEqual(force_row["M_t_Nmm"], 34285.714, places=3)
        self.assertEqual(max(row["M_res_Nmm"] for row in rows), force_row["M_res_Nmm"])


if __name__ == "__main__":
    unittest.main()
