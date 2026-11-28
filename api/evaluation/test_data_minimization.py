import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.pii_scrubber import anonymous_health_payload, scrub_pii, scrub_symptom
from app.schemas.chatbot import ChatBotRequest, ConfirmProposalRequest
from app.schemas.createProfile import createProfile
from pydantic import ValidationError


class DataMinimizationTests(unittest.TestCase):
    def test_email_phone_and_vietnamese_name(self):
        value = scrub_pii("Tôi tên là Nguyễn Văn An, email an@example.com, SĐT +84 912 345 678")
        self.assertIn("[NAME]", value)
        self.assertIn("[EMAIL]", value)
        self.assertIn("[PHONE]", value)
        self.assertNotIn("Nguyễn Văn An", value)
        self.assertEqual(scrub_pii("Trần Thị Bình đau đầu, gọi 0912345678"), "[NAME] đau đầu, gọi [PHONE]")
        self.assertEqual(scrub_pii("NGUYỄN VĂN AN bị đau"), "[NAME] bị đau")

    def test_strict_length(self):
        self.assertEqual(len(scrub_symptom("a" * 99)), 99)
        with self.assertRaises(ValueError):
            scrub_symptom("a" * 100)
        with self.assertRaises(ValidationError):
            ChatBotRequest(message="a" * 100)

    def test_payload_allowlist_and_no_history(self):
        payload = anonymous_health_payload(
            {"id": "secret", "nickname": "An", "email": "an@example.com",
             "bmi": 22.4, "tdee": 1900, "allergies": ["Đậu phộng"]},
            "Em là Nguyễn Văn An, đau đầu",
        )
        self.assertEqual(set(payload), {"bmi", "tdee", "allergies", "symptom"})
        self.assertNotIn("Nguyễn Văn An", str(payload))
        with self.assertRaises(ValidationError):
            ConfirmProposalRequest(status_flag="Tôi bị đau đầu")

    def test_profile_rejects_removed_pii(self):
        minimal = dict(nickname="Chiến binh", birth_year=2000, gender=True,
                       height=170, weight=65, goal="duy trì", activity_frequency=2)
        self.assertEqual(createProfile(**minimal).nickname, "Chiến binh")
        for field in ("name", "email", "phone", "address", "school", "workplace"):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                createProfile(**minimal, **{field: "private"})


if __name__ == "__main__":
    unittest.main()
