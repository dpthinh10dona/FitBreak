from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

try:
    from app.core.database import supabase
    from app.core.rate_limiter import RateLimiter
    from app.schemas.authResponse import authResponse
    from app.schemas.logIn import logIn
    from app.schemas.signUp import signUp
except ImportError:
    from app.core.database import supabase
    from app.core.rate_limiter import RateLimiter
    from app.schemas.authResponse import authResponse
    from app.schemas.logIn import logIn
    from app.schemas.signUp import signUp

router = APIRouter()


@router.get("/register")
async def registerForm(request: Request):
    return {"message": "success"}


@router.post(
    "/register",
    dependencies=[Depends(RateLimiter(times=5, seconds=60, scope="auth:register"))],
)
async def register(data: signUp):
    try:
        auth_response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })
        if auth_response is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Register that bai")
        session_token = auth_response.session.access_token if auth_response.session else None
        msg = "Đăng ký thành công" if session_token else "Đăng ký thành công. Vui lòng xác nhận email trước khi đăng nhập."
        return authResponse(
            success=True,
            message=msg,
            access_token=session_token,
            user=auth_response.user,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/login")
async def logInForm(request: Request):
    return {"message": "success"}


@router.post(
    "/login",
    dependencies=[Depends(RateLimiter(times=10, seconds=60, scope="auth:login"))],
)
async def logIn(response: Response, data: logIn):
    # response dung de ghi cookie cho cac lan dang nhap sau
    try:
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
            samesite="none",
            secure=True,
        )
        return authResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            user=auth_response.user,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/logout")
async def logOut(response: Response):
    response.delete_cookie(key="access_token")
    return authResponse(
        success=True,
        message="Đăng xuất thành công",
        access_token=None,
        user=None,
    )