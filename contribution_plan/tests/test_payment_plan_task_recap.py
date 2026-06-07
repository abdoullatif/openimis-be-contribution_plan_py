from django.test import SimpleTestCase

from contribution_plan.payment_plan_task_recap import (
    _normalize_plan_snapshot,
    _snapshot_periodicity,
    build_payment_plan_task_display,
    format_payment_plan_recap_text,
)


class PaymentPlanTaskRecapPeriodicityTest(SimpleTestCase):
    def test_snapshot_periodicity_from_api_field(self):
        self.assertEqual(_snapshot_periodicity({"periodicity": 12}), "Annuelle (12)")

    def test_normalize_plan_snapshot_includes_periodicite(self):
        snapshot = _normalize_plan_snapshot({
            "code": "PL001",
            "name": "Test",
            "periodicity": 1,
        })
        self.assertEqual(snapshot["periodicite"], "Mensuelle (1)")

    def test_build_display_includes_periodicite_in_incoming(self):
        display = build_payment_plan_task_display({
            "incoming_data": {
                "code": "PL001",
                "name": "Plan test",
                "periodicity": 6,
            },
        })
        self.assertEqual(display["incoming_data"]["periodicite"], "Semestrielle (6)")

    def test_recap_text_includes_periodicite(self):
        proposed = _normalize_plan_snapshot({"code": "PL001", "name": "X", "periodicity": 3})
        text = format_payment_plan_recap_text("Création", proposed)
        self.assertIn("Périodicité : Trimestrielle (3)", text)
