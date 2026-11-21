from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

API_DIR = Path(__file__).resolve().parents[1]
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from pydantic import ValidationError
from app.schemas.chatbot import ChatBotRequest
from app.router.chatbot import ask_health_chatbot
from app.services.chatbot_agent import analyze_and_chat, is_health_related_message


class ChatbotScopeTests(unittest.TestCase):
    def test_unrelated_messages_are_rejected_locally(self):
        unrelated = [
            "Viết code Python cho tôi",
            "Thủ đô của Pháp là gì?",
            "Kể một câu chuyện cười",
            "Dự báo giá Bitcoin ngày mai",
            "Giải phương trình bậc hai",
            "Soạn email xin nghỉ phép",
            "Ai vô địch bóng đá?",
            "Dịch câu này sang tiếng Anh",
            "Gợi ý laptop chơi game",
            "Viết bài thơ về mùa thu",
            "Bài tập toán này làm thế nào?",
            "Bạn đang ở đâu?",
            "Quốc gia này thuộc châu nào?",
        ]
        for message in unrelated:
            with self.subTest(message=message):
                self.assertFalse(is_health_related_message(message))

                with patch(
                    "app.services.chatbot_agent.run_clinical_advisor",
                    new=AsyncMock(side_effect=AssertionError("AI must not be called")),
                ):
                    result = asyncio.run(analyze_and_chat(message, {}))

                self.assertEqual(result["status"], "OUT_OF_SCOPE")
                self.assertFalse(result["allow_ai_generation"])
                self.assertIn("chỉ hỗ trợ", result["reply"].lower())

    def test_api_does_not_query_profile_or_consume_quota_for_unrelated_message(self):
        class ExplodingClient:
            def table(self, *_args, **_kwargs):
                raise AssertionError("profile database must not be queried")

        quota_get = AsyncMock(return_value=1)
        quota_increment = AsyncMock(side_effect=AssertionError("quota must not be consumed"))
        auth = SimpleNamespace(user_id="scope-test-user", client=ExplodingClient())
        with (
            patch("app.router.chatbot.daily_chatbot_quota.get", quota_get),
            patch("app.router.chatbot.daily_chatbot_quota.increment", quota_increment),
        ):
            response = asyncio.run(
                ask_health_chatbot(ChatBotRequest(message="Viết code Python cho tôi"), auth)
            )

        self.assertEqual(response.status, "OUT_OF_SCOPE")
        self.assertFalse(response.allow_ai_generation)
        self.assertEqual(response.remaining_questions_today, 2)
        quota_increment.assert_not_awaited()

    def test_health_messages_remain_in_scope(self):
        related = [
            "Tôi bị đau ngực",
            "Cách tập thể dục an toàn?",
            "Tôi khó thở khi vận động",
            "Chế độ dinh dưỡng giảm cân",
            "Huyết áp cao cần lưu ý gì?",
            "Tôi bị mất ngủ",
            "Tôi đang stress và lo âu",
            "Đau khớp gối sau khi chạy",
            "Tôi bị dị ứng thực phẩm",
            "BMI của tôi có bình thường không?",
            "Tôi đau đầu và buồn nôn",
            "Tôi bị tiêu chảy",
        ]
        for message in related:
            with self.subTest(message=message):
                self.assertTrue(is_health_related_message(message))


class ChatbotCharacterLimitTests(unittest.TestCase):
    def test_exactly_100_characters_is_accepted(self):
        request = ChatBotRequest(message="a" * 100)
        self.assertEqual(len(request.message), 100)

    def test_101_characters_is_rejected(self):
        with self.assertRaises(ValidationError):
            ChatBotRequest(message="a" * 101)

    def test_single_spam_word_cannot_bypass_limit(self):
        with self.assertRaises(ValidationError):
            ChatBotRequest(message="a" * 500)


if __name__ == "__main__":
    unittest.main()
