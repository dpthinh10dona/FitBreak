"""Registration errors must not falsely claim an email is already in use."""

import asyncio
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from supabase_auth.errors import AuthApiError

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.router.auth_route import register
from app.schemas.signUp import signUp


class RegistrationErrorTests(unittest.TestCase):
    def _register_error(self, message, code):
        error = AuthApiError(message, 422, code)
        with (
            patch("app.router.auth_route.supabase") as provider,
            patch("app.router.auth_route.audit_event"),
        ):
            provider.auth.sign_up.side_effect = error
            with self.assertRaises(HTTPException) as caught:
                asyncio.run(register(signUp(email="new@example.com", password="test-password"), None))
        return caught.exception

    def test_duplicate_code_reports_conflict(self):
        result = self._register_error("User already registered", "user_already_exists")
        self.assertEqual(result.status_code, 409)
        self.assertIn("đã được đăng ký", result.detail)

    def test_unrelated_already_message_does_not_report_duplicate(self):
        result = self._register_error("Email already sent; try again later", "unexpected_failure")
        self.assertEqual(result.status_code, 400)
        self.assertNotIn("đã được đăng ký", result.detail)

    def test_rate_limit_has_its_own_message(self):
        result = self._register_error("Too many requests", "over_email_send_rate_limit")
        self.assertEqual(result.status_code, 429)


if __name__ == "__main__":
    unittest.main()
