import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.safety_guardrail import apply_youth_safety_guardrail


class YouthSafetyGuardrailTests(unittest.TestCase):
    def test_youth_rapid_weight_loss_overridden(self):
        res = apply_youth_safety_guardrail(
            age=15,
            tdee=2100,
            goal="giảm cân cấp tốc",
            target_calories=1200,
        )
        self.assertTrue(res["is_youth_mode"])
        self.assertEqual(
            res["safe_goal"],
            "Cân bằng năng lượng & hỗ trợ phát triển thể chất",
        )
        self.assertGreaterEqual(res["safe_target_calories"], 2100 * 0.90)
        self.assertIsNotNone(res["adjusted_reason"])

    def test_youth_deep_deficit_clamped(self):
        res = apply_youth_safety_guardrail(
            age=16,
            tdee=2000,
            goal="Giảm cân",
            target_calories=1400,
        )
        self.assertTrue(res["is_youth_mode"])
        self.assertGreaterEqual(res["safe_target_calories"], 1800)
        self.assertIsNotNone(res["adjusted_reason"])

    def test_adult_unchanged(self):
        res = apply_youth_safety_guardrail(
            age=22,
            tdee=2200,
            goal="Giảm cân",
            target_calories=1700,
        )
        self.assertFalse(res["is_youth_mode"])
        self.assertEqual(res["safe_goal"], "Giảm cân")
        self.assertEqual(res["safe_target_calories"], 1700)
        self.assertIsNone(res["adjusted_reason"])


if __name__ == "__main__":
    unittest.main()
