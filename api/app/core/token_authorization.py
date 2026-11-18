import os
import jwt

from fastapi import HTTPException, Depends, status
from dataclasses import dataclass
from supabase import create_client, Client
from app.core.database import SUPABASE_URL, SUPABASE_KEY
from app.core.auth import get_current_user

@dataclass
class tokenAuthorization:
    client: Client
    user_id: str
    user_email: str
    is_admin: bool = False
    auth_level: str = "aal1"


def token_authorization(
    current_user: dict = Depends(get_current_user)
) -> tokenAuthorization:
    user = current_user.get("user")
    token = current_user.get("token")

    user_email = user.get("email")
    user_id = user.get("id")
    if not user_email or not user_id:
        raise HTTPException(status_code=401, detail="Email not found in token")

    app_metadata = user.get("app_metadata") or {}
    admin_emails = {email.strip().lower() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()}
    is_admin = app_metadata.get("role") == "admin" or user_email.lower() in admin_emails
    try:
        claims = jwt.decode(token, options={"verify_signature": False, "verify_aud": False})
        auth_level = claims.get("aal", "aal1")
    except Exception:
        auth_level = "aal1"

    user_supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    user_supabase.postgrest.auth(token)

    return tokenAuthorization(
        client = user_supabase,
        user_id = user_id,
        user_email = user_email,
        is_admin = is_admin,
        auth_level = auth_level,
    )


def require_admin(token: tokenAuthorization = Depends(token_authorization)) -> tokenAuthorization:
    if not token.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yêu cầu quyền quản trị viên")
    if os.getenv("REQUIRE_ADMIN_MFA", "true").lower() == "true" and token.auth_level != "aal2":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Quản trị viên phải xác thực đa yếu tố")
    return token
