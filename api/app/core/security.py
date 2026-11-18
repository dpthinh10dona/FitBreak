"""Production security configuration and HTTP middleware for FitBreak."""

from __future__ import annotations

import os

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, RedirectResponse


def env_flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def csv_env(name: str, default: str = "") -> list[str]:
    return [value.strip().rstrip("/") for value in os.getenv(name, default).split(",") if value.strip()]


IS_PRODUCTION = os.getenv("APP_ENV", "development").lower() == "production"
ALLOWED_ORIGINS = csv_env(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
ALLOWED_HOSTS = csv_env("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")
MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", str(10 * 1024 * 1024)))


def _origin_allowed(origin: str) -> bool:
    return origin.rstrip("/") in ALLOWED_ORIGINS


class SecurityMiddleware(BaseHTTPMiddleware):
    """Apply HTTPS policy, request limits, CSRF origin checks and security headers."""

    async def dispatch(self, request: Request, call_next):
        forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
        is_https = request.url.scheme == "https" or forwarded_proto == "https"

        if env_flag("FORCE_HTTPS", IS_PRODUCTION) and not is_https:
            https_url = request.url.replace(scheme="https")
            return RedirectResponse(str(https_url), status_code=status.HTTP_308_PERMANENT_REDIRECT)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_BYTES:
                    return JSONResponse(status_code=413, content={"detail": "Request quá lớn."})
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Content-Length không hợp lệ."})

        # Bearer requests are not CSRF-prone. Cookie-authenticated state changes must
        # originate from an explicitly allowed frontend.
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            uses_auth_cookie = "access_token" in request.cookies
            has_bearer = request.headers.get("authorization", "").lower().startswith("bearer ")
            if uses_auth_cookie and not has_bearer:
                origin = request.headers.get("origin", "")
                if not origin or not _origin_allowed(origin):
                    return JSONResponse(status_code=403, content={"detail": "Nguồn request không được phép."})

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; "
            "object-src 'none'; form-action 'self'; script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            "font-src 'self' data:; connect-src 'self' https: http://localhost:* ws://localhost:*"
        )
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith(("/login", "/register", "/profiles")) else response.headers.get("Cache-Control", "no-cache")
        if is_https or IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

