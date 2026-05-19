import math
import unittest

from core.calculations import (
    calc_contact_ratio,
    calc_forces,
    calc_gear_geometry,
    calc_max_bending_moment_single_force,
    calc_module_from_dsh,
    calc_path_of_contact,
    calc_pitch_diameter,
    calc_ratio,
    calc_transverse_pressure_angle,
    calc_torque,
    next_norm_module,
    next_preferred_norm_module,
)


class CalculationTests(unittest.TestCase):
    def test_ratio(self):
        self.assertAlmostEqual(calc_ratio(1850, 410), 4.512195, places=6)

    def test_torque(self):
        self.assertAlmostEqual(calc_torque(12, 1850), 61.94, places=2)

    def test_module_from_dsh(self):
        self.assertAlmostEqual(calc_module_from_dsh(28, 25, 0, "mounted"), 2.24, places=2)

    def test_next_norm_module(self):
        self.assertEqual(next_norm_module(2.24, [1.0, 1.25, 1.5, 2.0, 2.5, 3.0]), 2.5)

    def test_next_preferred_norm_module_uses_reihe_i_first(self):
        rows = [
            {"reihe": "I", "modul": 2.0},
            {"reihe": "I", "modul": 2.5},
            {"reihe": "II", "modul": 2.25},
        ]
        self.assertEqual(next_preferred_norm_module(2.24, rows), 2.5)

    def test_gear_diameter(self):
        geometry = calc_gear_geometry(2.5, 25, 20, "psi_d", 1.0, 12.0)
        self.assertAlmostEqual(geometry["d_mm"], 62.5)
        self.assertAlmostEqual(geometry["db_mm"], 62.5 * math.cos(math.radians(20)))

    def test_transverse_pressure_angle_equals_alpha_for_spur_gears(self):
        self.assertAlmostEqual(calc_transverse_pressure_angle(20, 0), 20.0)

    def test_helical_geometry_uses_transverse_plane(self):
        beta = 20.0
        alpha = 20.0
        alpha_t = calc_transverse_pressure_angle(alpha, beta)
        d = calc_pitch_diameter(2.5, 25, beta)
        geometry = calc_gear_geometry(2.5, 25, alpha, "psi_d", 1.0, 12.0, beta)

        self.assertGreater(alpha_t, alpha)
        self.assertAlmostEqual(d, 2.5 * 25 / math.cos(math.radians(beta)))
        self.assertAlmostEqual(geometry["d_mm"], d)
        self.assertAlmostEqual(geometry["db_mm"], d * math.cos(math.radians(alpha_t)))
        self.assertAlmostEqual(geometry["da_mm"], d + 2 * 2.5)
        self.assertAlmostEqual(geometry["df_mm"], d - 2.5 * 2.5)

    def test_contact_ratio_is_plausible(self):
        pinion = calc_gear_geometry(2.5, 25, 20, "psi_d", 1.0, 12.0)
        wheel = calc_gear_geometry(2.5, 113, 20, "psi_d", 1.0, 12.0)
        center_distance = (pinion["d_mm"] + wheel["d_mm"]) / 2
        path = calc_path_of_contact(
            pinion["da_mm"],
            pinion["db_mm"],
            wheel["da_mm"],
            wheel["db_mm"],
            center_distance,
            20,
        )
        epsilon = calc_contact_ratio(path, math.pi * 2.5 * math.cos(math.radians(20)))
        self.assertGreater(epsilon, 1.0)

    def test_forces(self):
        ft, fr, fa, resultant = calc_forces(61.94, 62.5, 20, 0)
        self.assertAlmostEqual(ft, 1982.08, places=1)
        self.assertAlmostEqual(fr, ft * math.tan(math.radians(20)), places=6)
        self.assertEqual(fa, 0)
        self.assertGreater(resultant, ft)

    def test_max_bending_moment_single_force(self):
        self.assertAlmostEqual(calc_max_bending_moment_single_force(1000, 60, 80), 34285.714, places=3)


if __name__ == "__main__":
    unittest.main()
