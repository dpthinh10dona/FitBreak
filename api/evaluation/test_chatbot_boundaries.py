from __future__ import annotations

import asyncio
import json
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
from app.router.chatbot import ask_health_chatbot, get_approved_medical_source
from app.services.chatbot_agent import analyze_and_chat, is_health_related_message, run_clinical_advisor, contains_unsafe_medical_claim
from app.services.clinical_rag import InsufficientMedicalEvidenceError, retrieve_medical_docs, _approved_source_is_usable
from app.services.knowledge_ingestor import DEFAULT_KNOWLEDGE_DIR, load_source_catalog


class ChatbotScopeTests(unittest.TestCase):
    def test_warning_cases_use_deterministic_triage(self):
        suite = json.loads((Path(__file__).parent / "clinical_cases_80.json").read_text(encoding="utf-8"))
        warning_cases = next(group["cases"] for group in suite["groups"] if group["id"] == "WARNING")
        for case in warning_cases:
            with self.subTest(case=case["id"]):
                with patch("app.services.chatbot_agent.run_clinical_advisor", new=AsyncMock(side_effect=AssertionError("AI must not be called"))):
                    response = asyncio.run(analyze_and_chat(case["input"], {}))
                self.assertEqual(response["status"], "MEDICAL_WARNING")
                self.assertFalse(response["allow_ai_generation"])

    def test_emergency_is_flagged_without_model(self):
        message = "Tôi đau ngực dữ dội và khó thở"
        with patch("app.services.chatbot_agent.run_clinical_advisor", new=AsyncMock(side_effect=AssertionError("AI must not be called"))):
            result = asyncio.run(analyze_and_chat(message, {}))
        self.assertEqual(result["status"], "MEDICAL_WARNING")
        self.assertFalse(result["allow_ai_generation"])
        self.assertIn("115", result["reply"])

    def test_emergency_is_available_after_daily_quota(self):
        class ExplodingClient:
            def table(self, *_args, **_kwargs):
                raise AssertionError("profile database must not be queried")

        quota_increment = AsyncMock(side_effect=AssertionError("quota must not be consumed"))
        auth = SimpleNamespace(user_id="warning-test-user", client=ExplodingClient())
        with (
            patch("app.router.chatbot.daily_chatbot_quota.get", new=AsyncMock(return_value=3)),
            patch("app.router.chatbot.daily_chatbot_quota.increment", quota_increment),
        ):
            response = asyncio.run(ask_health_chatbot(
                ChatBotRequest(message="Tôi đau ngực dữ dội và khó thở"), auth
            ))
        self.assertEqual(response.status, "MEDICAL_WARNING")
        self.assertEqual(response.remaining_questions_today, 0)
        self.assertIn("115", response.reply)
        quota_increment.assert_not_awaited()

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
            "Tiền đái tháo đường là gì?",
            "Ung thư dạ dày điều trị thế nào?",
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


class VerifiedSourceTests(unittest.TestCase):
    def test_internal_source_urls_match_catalog_source_ids(self):
        catalog = load_source_catalog(DEFAULT_KNOWLEDGE_DIR)
        prefix = "/chatbot/sources/"
        for source in catalog.values():
            source_url = source.get("source_url", "")
            if source_url.startswith(prefix):
                with self.subTest(source_id=source.get("source_id")):
                    self.assertEqual(source_url.removeprefix(prefix), source["source_id"])

    def test_all_owner_approved_pdfs_are_cached_and_retrievable(self):
        catalog = load_source_catalog(DEFAULT_KNOWLEDGE_DIR)
        self.assertEqual(len(catalog), 16)
        self.assertTrue(all(_approved_source_is_usable(item) for item in catalog.values()))
        cache = json.loads((DEFAULT_KNOWLEDGE_DIR / "chunks_cache.json").read_text(encoding="utf-8"))
        cached_files = {chunk["source"] for chunk in cache}
        self.assertEqual(cached_files, set(catalog))
        for record in catalog.values():
            response = asyncio.run(get_approved_medical_source(record["source_id"]))
            self.assertEqual(response.media_type, "application/pdf")

    def test_newly_approved_source_can_be_used_offline(self):
        with patch("app.services.supabase_rag_chat.search_medical_knowledge_pgvector", return_value=[]):
            result = retrieve_medical_docs("Ung thư vú điều trị ra sao?")
        self.assertIn("Mã nguồn: BYT-3128-2020", result)

    def test_unsafe_medication_claim_is_blocked_without_blocking_negation(self):
        self.assertTrue(contains_unsafe_medical_claim("Tự tăng liều thuốc."))
        self.assertFalse(contains_unsafe_medical_claim("Không tự tăng liều thuốc."))

    def test_missing_source_marker_is_rejected(self):
        with (
            patch("app.services.chatbot_agent.retrieve_medical_docs", return_value=(
                "Nguồn tài liệu: Tài liệu thử\nMã nguồn: FIXTURE-1\nNội dung: hướng dẫn"
            )),
            patch("app.services.chatbot_agent.generate_chat", new=AsyncMock(
                return_value="Nội dung tư vấn không có mã nguồn."
            )),
        ):
            with self.assertRaises(InsufficientMedicalEvidenceError):
                asyncio.run(run_clinical_advisor("Tôi bị đau", {}))

    def test_model_source_section_is_replaced_by_retrieved_source(self):
        with (
            patch("app.services.chatbot_agent.retrieve_medical_docs", return_value=(
                "Nguồn tài liệu: Tài liệu đã duyệt (1/QĐ; hiệu lực: 2020-01-01)\n"
                "Mã nguồn: FIXTURE-1\n"
                "Giới hạn: Cần bác sĩ đánh giá\nNội dung: hướng dẫn"
            )),
            patch("app.services.chatbot_agent.generate_chat", new=AsyncMock(
                return_value="Nội dung tư vấn. [SOURCE:FIXTURE-1]\n\nNguồn tài liệu tham khảo:\n- Blog bịa"
            )),
        ):
            reply = asyncio.run(run_clinical_advisor("Tôi bị đau", {}))
        self.assertIn("Tài liệu đã duyệt (1/QĐ; hiệu lực: 2020-01-01)", reply)
        self.assertIn("Giới hạn: Cần bác sĩ đánh giá", reply)
        self.assertNotIn("Blog bịa", reply)

    def test_unapproved_source_cannot_authorize_medical_answer(self):
        with (
            patch("app.services.clinical_rag.load_source_catalog", return_value={}),
            patch("app.services.supabase_rag_chat.search_medical_knowledge_pgvector",
                  return_value=[{"source_id": "BYT-3087-2020", "content": "Thông tin y khoa", "similarity": 0.9}]),
        ):
            with self.assertRaises(InsufficientMedicalEvidenceError):
                retrieve_medical_docs("Tôi bị tiền đái tháo đường")

    def test_approved_source_includes_effective_date_and_limit(self):
        approved = {
            "file": "fixture.pdf", "source_id": "FIXTURE-1", "title": "Hướng dẫn đau ngực",
            "decision": "1/QĐ", "effective_at": "2020-01-01", "limitations": "Cần bác sĩ đánh giá",
            "source_url": "https://example.org/fixture.pdf",
            "verification_status": "APPROVED",
        }
        with (
            patch("app.services.clinical_rag.load_source_catalog", return_value={"fixture.pdf": approved}),
            patch("app.services.supabase_rag_chat.search_medical_knowledge_pgvector", return_value=[
                {"source_id": "FIXTURE-1", "content": "Hướng dẫn đánh giá đau ngực", "similarity": 0.9}
            ]),
        ):
            result = retrieve_medical_docs("Tôi bị đau ngực")
        self.assertIn("1/QĐ", result)
        self.assertIn("2020-01-01", result)
        self.assertIn("Cần bác sĩ đánh giá", result)

    def test_approved_source_requires_url_and_current_date(self):
        source = {
            "source_id": "FIXTURE-1", "file": "fixture.pdf", "title": "Hướng dẫn đau ngực", "decision": "1/QĐ",
            "effective_at": "2020-01-01", "limitations": "Cần bác sĩ đánh giá",
            "source_url": "https://example.org/fixture.pdf", "verification_status": "APPROVED",
        }
        self.assertTrue(_approved_source_is_usable(source))
        self.assertTrue(_approved_source_is_usable({**source, "effective_at": None}))
        self.assertFalse(_approved_source_is_usable({**source, "source_url": ""}))
        self.assertFalse(_approved_source_is_usable({**source, "effective_at": "2099-01-01"}))
        self.assertFalse(_approved_source_is_usable({**source, "expires_at": "2020-12-31"}))


if __name__ == "__main__":
    unittest.main()
