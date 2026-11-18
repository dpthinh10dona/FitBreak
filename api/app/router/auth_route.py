import hashlib
import os
import httpx

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

try:
    from app.core.database import supabase
    from app.core.rate_limiter import RateLimiter
    from app.core.rate_limiter import _limiter
    from app.core.audit import audit_event
    from app.core.database import SUPABASE_KEY, SUPABASE_URL
    from app.schemas.authResponse import authResponse
    from app.schemas.logIn import logIn
    from app.schemas.signUp import signUp
except ImportError:
    from app.core.database import supabase
    from app.core.rate_limiter import RateLimiter
    from app.core.rate_limiter import _limiter
    from app.core.audit import audit_event
    from app.core.database import SUPABASE_KEY, SUPABASE_URL
    from app.schemas.authResponse import authResponse
    from app.schemas.logIn import logIn
    from app.schemas.signUp import signUp

router = APIRouter()


@router.post(
    "/register",
    dependencies=[Depends(RateLimiter(times=5, seconds=60, scope="auth:register"))],
)
async def register(data: signUp, request: Request):
    try:
        auth_response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })
        if auth_response is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Register that bai")
        session_token = auth_response.session.access_token if auth_response.session else None
        msg = "Đăng ký thành công" if session_token else "Đăng ký thành công. Vui lòng xác nhận email trước khi đăng nhập."
        result = authResponse(
            success=True,
            message=msg,
            access_token=session_token,
            user=auth_response.user,
        )
        audit_event("auth.register", request, user_id=str(data.email), outcome="success")
        return result
    except HTTPException:
        audit_event("auth.register", request, user_id=str(data.email), outcome="failure")
        raise
    except Exception:
        audit_event("auth.register", request, user_id=str(data.email), outcome="failure")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể đăng ký tài khoản. Vui lòng kiểm tra thông tin hoặc thử lại sau.")


@router.post(
    "/login",
    dependencies=[Depends(RateLimiter(times=10, seconds=60, scope="auth:login"))],
)
async def logIn(request: Request, response: Response, data: logIn):
    # response dung de ghi cookie cho cac lan dang nhap sau
    try:
        account_key = hashlib.sha256(str(data.email).lower().encode()).hexdigest()[:20]
        allowed, retry_after = await _limiter.is_allowed(f"auth-account:{account_key}", 5, 300)
        if not allowed:
            audit_event("auth.login", request, user_id=str(data.email), outcome="rate_limited")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Đăng nhập tạm thời bị giới hạn. Vui lòng thử lại sau.",
                headers={"Retry-After": str(retry_after)},
            )
        auth_response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })
        if auth_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email hoặc mật khẩu không chính xác",
            )
        access_token = auth_response.session.access_token
        # Hỗ trợ cả dev localhost lẫn production cross-domain (Vercel -> Render)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            path="/",
            samesite=os.getenv("COOKIE_SAMESITE", "none"),
            secure=os.getenv("COOKIE_SECURE", "true").lower() == "true",
            max_age=int(os.getenv("SESSION_MAX_AGE_SECONDS", "3600")),
        )
        audit_event("auth.login", request, user_id=str(data.email), outcome="success")
        return authResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            user=auth_response.user,
        )
    except HTTPException:
        raise
    except Exception:
        audit_event("auth.login", request, user_id=str(data.email), outcome="failure")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác",
        )


@router.post("/logout")
async def logOut(request: Request, response: Response):
    raw_token = request.headers.get("authorization", "")
    if raw_token.lower().startswith("bearer "):
        access_token = raw_token.split(" ", 1)[1]
    else:
        access_token = request.cookies.get("access_token", "").replace("Bearer ", "").strip()
    if access_token:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{SUPABASE_URL.rstrip('/')}/auth/v1/logout",
                    headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {access_token}"},
                )
        except Exception:
            pass
    response.delete_cookie(
        key="access_token",
        path="/",
        samesite=os.getenv("COOKIE_SAMESITE", "none"),
        secure=os.getenv("COOKIE_SECURE", "true").lower() == "true",
    )
    audit_event("auth.logout", request, outcome="success")
    return authResponse(
        success=True,
        message="Đăng xuất thành công",
        access_token=None,
        user=None,
    )
