import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
import httpx

from app.core.exceptions import (
    AIModelOfflineException,
    InvalidResponseError,
    ModelNotFoundError,
    RequestTimeoutError,
)

logger = logging.getLogger(__name__)

# Load env từ thư mục gốc hoặc api/app để không bao giờ bị sót key
_root_env = Path(__file__).resolve().parents[3] / ".env"
_app_env = Path(__file__).resolve().parents[1] / ".env"
if _root_env.exists():
    load_dotenv(_root_env)
if _app_env.exists():
    load_dotenv(_app_env)
load_dotenv()

# GEMINI CONFIG
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# GROQ CONFIG
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# Khởi tạo Async Client cho Gemini
ai_client = genai.Client(api_key=GEMINI_API_KEY)


async def chat() -> None:
    """Check whether at least one AI service (Gemini or Groq) is reachable."""
    errors = []
    # Test Gemini
    try:
        await ai_client.aio.models.get(model=GEMINI_MODEL)
        return
    except Exception as exc:
        errors.append(f"Gemini: {exc}")

    # Fallback test Groq
    if GROQ_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                )
                if res.status_code == 200:
                    return
                errors.append(f"Groq status {res.status_code}")
        except Exception as exc:
            errors.append(f"Groq: {exc}")

    raise AIModelOfflineException(f"Tất cả AI services đều offline hoặc lỗi kết nối: {'; '.join(errors)}")


async def _call_gemini_once(
    prompt: str,
    response_mime_type: str,
    response_format: Optional[Any],
    timeout_seconds: float,
) -> str:
    """Gửi request tới Gemini API với timeout cụ thể."""
    config = types.GenerateContentConfig(
        temperature=0.4,
        response_mime_type=response_mime_type if response_mime_type else "text/plain",
        response_schema=response_format if response_format is not None else None,
    )
    # Dùng asyncio.wait_for để khống chế timeout chặt chẽ
    response = await asyncio.wait_for(
        ai_client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        ),
        timeout=timeout_seconds,
    )

    if not response or not response.text:
        raise InvalidResponseError("Gemini trả về rỗng")

    content = response.text.strip()
    if not content:
        raise InvalidResponseError("Gemini response không hợp lệ")

    return content


async def _call_groq_once(
    prompt: str,
    timeout_seconds: float,
    response_mime_type: str = "application/json",
) -> str:
    """Gửi request tới Groq API (OpenAI-compatible) với timeout cụ thể."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY chưa được cấu hình")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    if response_mime_type == "text/plain":
        messages = [
            {
                "role": "system",
                "content": "You are an expert Clinical AI Advisor. Provide empathetic, accurate medical guidance in standard Markdown format.",
            },
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800,
        }
    else:
        messages = [
            {
                "role": "system",
                "content": "You are a professional nutritionist API. Respond ONLY with valid raw JSON.",
            },
            {"role": "user", "content": prompt},
        ]
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800,
            "response_format": {"type": "json_object"},
        }

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        res = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        if res.status_code != 200:
            raise InvalidResponseError(f"Groq trả về HTTP {res.status_code}: {res.text[:200]}")

        data = res.json()
        content = data["choices"][0]["message"]["content"].strip()
        if not content:
            raise InvalidResponseError("Groq trả về content rỗng")
        return content


async def generate_chat(
    prompt: str,
    response_mime_type: str = "application/json",
    response_format: Optional[Any] = None,
) -> str:
    """
    Cơ chế dự phòng tự động (Failover Mechanism):
    - Ưu tiên gọi Gemini trước.
    - Nếu Gemini nghẽn/lỗi -> chuyển sang Groq.
    - Nếu Groq lỗi -> quay lại thử Gemini.
    - Luân phiên liên tục trong tối đa 30s.
    - Nếu quá 30s mà cả 2 đều không phản hồi -> raise error thông báo server API bị nghẽn.
    """
    TOTAL_TIMEOUT = 30.0
    start_time = time.monotonic()
    last_error = None
    step_timeout = 8.0  # Mỗi lượt thử tối đa 8s để kịp luân phiên

    while True:
        elapsed = time.monotonic() - start_time
        remaining = TOTAL_TIMEOUT - elapsed
        if remaining <= 1.0:
            break

        # 1. Thử Gemini
        gemini_timeout = min(step_timeout, remaining)
        try:
            logger.info("Đang gọi Gemini API...")
            content = await _call_gemini_once(
                prompt=prompt,
                response_mime_type=response_mime_type,
                response_format=response_format,
                timeout_seconds=gemini_timeout,
            )
            return content
        except Exception as exc:
            logger.warning(f"Gemini gặp sự cố/nghẽn: {exc}. Đang chuyển tiếp sang Groq...")
            last_error = exc

        # Kiểm tra thời gian còn lại trước khi gọi Groq
        elapsed = time.monotonic() - start_time
        remaining = TOTAL_TIMEOUT - elapsed
        if remaining <= 1.0:
            break

        # 2. Thử Groq
        if GROQ_API_KEY:
            groq_timeout = min(step_timeout, remaining)
            try:
                logger.info("Đang gọi Groq API dự phòng...")
                content = await _call_groq_once(
                    prompt=prompt,
                    timeout_seconds=groq_timeout,
                    response_mime_type=response_mime_type,
                )
                return content
            except Exception as exc:
                logger.warning(f"Groq gặp sự cố: {exc}. Đang chuyển ngược lại thử Gemini...")
                last_error = exc
        else:
            await asyncio.sleep(0.5)

    # Nếu sau 30s vẫn không có model nào phản hồi
    raise RequestTimeoutError(
        f"Server API đang bị nghẽn (Gemini và Groq không phản hồi sau 30s). Chi tiết lỗi: {last_error}"
    )
