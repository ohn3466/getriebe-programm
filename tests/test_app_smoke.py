import unittest

from streamlit.testing.v1 import AppTest


def metric_value(app, label):
    for metric in app.metric:
        if metric.label == label:
            return metric.value
    raise AssertionError(f"Metrik nicht gefunden: {label}")


def number_input_by_label(app, label):
    for number_input in app.number_input:
        if number_input.label == label:
            return number_input
    raise AssertionError(f"Zahleneingabe nicht gefunden: {label}")


class AppSmokeTests(unittest.TestCase):
    def test_app_renders_without_exceptions(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertGreaterEqual(len(app.tabs), 8)
        self.assertGreaterEqual(len(app.number_input), 15)
        self.assertGreaterEqual(len(app.selectbox), 4)
        self.assertTrue(any(header.value == "Live-Rechenweg" for header in app.header))

    def test_dsh_change_updates_module_metrics_automatically(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=10)

        self.assertEqual(app.metric[8].label, "m theoretisch")
        self.assertEqual(app.metric[9].label, "m empfohlen")
        self.assertEqual(app.metric[10].label, "m gewaehlt")
        self.assertEqual(app.metric[9].value, "2.5 mm")

        number_input_by_label(app, "d_sh Ritzel [mm]").set_value(32).run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[8].value, "2.560 mm")
        self.assertEqual(app.metric[9].value, "3 mm")
        self.assertEqual(app.metric[10].value, "3 mm")

    def test_dsh_change_updates_visible_downstream_metrics(self):
        app = AppTest.from_file("app.py")
        app.run(timeout=10)

        self.assertEqual(metric_value(app, "g_alpha"), "12.831 mm")
        self.assertEqual(metric_value(app, "Ft"), "1982.1 N")
        self.assertEqual(metric_value(app, "M_b max resultierend"), "72.32 Nm")

        number_input_by_label(app, "d_sh Ritzel [mm]").set_value(32).run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(metric_value(app, "g_alpha"), "15.397 mm")
        self.assertEqual(metric_value(app, "Ft"), "1651.8 N")
        self.assertEqual(metric_value(app, "M_b max resultierend"), "60.27 Nm")


if __name__ == "__main__":
    unittest.main()
