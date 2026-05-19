import unittest

from core.table_views import build_norm_module_table


class TableViewTests(unittest.TestCase):
    def test_norm_module_recommendation_status_moves_with_calculation(self):
        rows = [
            {"reihe": "I", "modul": 2.0},
            {"reihe": "II", "modul": 2.25},
            {"reihe": "I", "modul": 2.5},
            {"reihe": "I", "modul": 3.0},
        ]

        first = build_norm_module_table(rows, 2.24, 2.5, 2.5)
        changed = build_norm_module_table(rows, 2.56, 3.0, 3.0)

        first_recommended = first[first["Status"].str.contains("empfohlen", regex=False)]["Normmodul [mm]"].tolist()
        changed_recommended = changed[changed["Status"].str.contains("empfohlen", regex=False)]["Normmodul [mm]"].tolist()

        self.assertEqual(first_recommended, [2.5])
        self.assertEqual(changed_recommended, [3.0])

    def test_norm_module_table_marks_manual_selection_separately(self):
        rows = [
            {"reihe": "I", "modul": 2.5},
            {"reihe": "I", "modul": 3.0},
        ]

        table = build_norm_module_table(rows, 2.24, 2.5, 3.0)

        status_by_module = dict(zip(table["Normmodul [mm]"], table["Status"], strict=True))
        self.assertEqual(status_by_module[2.5], "empfohlen")
        self.assertEqual(status_by_module[3.0], "gewaehlt")


if __name__ == "__main__":
    unittest.main()
