import unittest

from streamlit.testing.v1 import AppTest


def metric_value(app, label):
    for metric in app.metric:
        if metric.label == label:
            return metric.value
    raise AssertionError(f"Metrik nicht gefunden: {label}")


def button_by_label(app, label):
    for button in app.button:
        if button.label == label:
            return button
    raise AssertionError(f"Button nicht gefunden: {label}")


class WizardAppSmokeTests(unittest.TestCase):
    def test_wizard_renders_first_step_without_exceptions(self):
        app = AppTest.from_file("wizard_app.py")
        app.run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.header[0].value, "1. Grunddaten")
        self.assertEqual(metric_value(app, "i soll"), "4.512")
        self.assertFalse(button_by_label(app, "Weiter").disabled)

    def test_wizard_step_requires_material_choice(self):
        app = AppTest.from_file("wizard_app.py")
        app.run(timeout=10)
        button_by_label(app, "Weiter").click().run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.header[0].value, "2. Werkstoff aus Tabelle waehlen")
        self.assertTrue(button_by_label(app, "Weiter").disabled)

        app.session_state["wizard_material_name"] = "C45E"
        app.run(timeout=10)

        self.assertFalse(button_by_label(app, "Weiter").disabled)

    def test_wizard_keeps_values_when_moving_back_and_forward(self):
        app = AppTest.from_file("wizard_app.py")
        app.run(timeout=10)

        app.number_input[0].set_value(15.0).run(timeout=10)
        button_by_label(app, "Weiter").click().run(timeout=10)
        app.session_state["wizard_material_name"] = "C45E"
        app.run(timeout=10)
        button_by_label(app, "Weiter").click().run(timeout=10)
        button_by_label(app, "Zurueck").click().run(timeout=10)
        button_by_label(app, "Zurueck").click().run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.header[0].value, "1. Grunddaten")
        self.assertEqual(app.number_input[0].value, 15.0)
        self.assertEqual(metric_value(app, "M1"), "77.43 Nm")

    def test_wizard_manual_z2_updates_visible_g_alpha(self):
        app = AppTest.from_file("wizard_app.py")
        app.session_state["wizard_step"] = 2
        app.session_state["wizard_material_name"] = "C45E"
        app.session_state["wizard_z2_auto"] = False
        app.session_state["wizard_z1"] = 26
        app.session_state["wizard_z2_manual"] = 112
        app.session_state["wizard_selected_module"] = 2.5
        app.run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.header[0].value, "3. Welle, d_sh und Zaehnezahlen")
        self.assertEqual(metric_value(app, "z2"), "112")
        self.assertEqual(metric_value(app, "g_alpha"), "12.862 mm")


if __name__ == "__main__":
    unittest.main()
