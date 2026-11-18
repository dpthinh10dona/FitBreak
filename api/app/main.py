from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from app.core.exceptions import AIModelOfflineException
from app.core.ollama_client import chat as check_ollama
from app.core.rate_limiter import RateLimitMiddleware
from app.core.security import ALLOWED_HOSTS, ALLOWED_ORIGINS, IS_PRODUCTION, SecurityMiddleware
from app.router import auth_route, exercise, profile, foodSuggest, team, raid, schedule, stats, shop, chatbot

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await check_ollama()
        print("[OK] Ollama connection OK")
    except AIModelOfflineException as e:
        print(f"[WARN] Ollama chưa sẵn sàng: {e}")
    except Exception as e:
        print(f"[WARN] Không thể kiểm tra Ollama lúc khởi động: {e}")
    yield

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
app.add_middleware(SecurityMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Do not expose stack traces, SQL errors, provider errors or versions.
    return JSONResponse(status_code=500, content={"detail": "Hệ thống gặp lỗi nội bộ. Vui lòng thử lại sau."})

app.include_router(auth_route.router, tags=["Auth Routers"])
app.include_router(profile.router, tags=["Create Profile Routers"])
app.include_router(exercise.router, tags=["Exercise"])
app.include_router(foodSuggest.router, tags=["Food Suggest"])
app.include_router(team.router, tags=["Team"])
app.include_router(raid.router, tags=["Raid"])
app.include_router(schedule.router, tags=["Schedule"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])
app.include_router(stats.router, tags=["Stats"])
app.include_router(shop.router, tags=["Shop"])
app.include_router(chatbot.router, tags=["AI Health ChatBot"])

@app.get("/health", tags=["Health"])
@app.get("/ping", tags=["Health"])
async def lightweight_health():
    """
    Endpoint siêu nhẹ (Zero Dependency / No AI call / No DB query)
    Dành riêng cho uptime bot (UptimeRobot, Cron-job.org, BetterUptime) ping định kỳ
    để ngăn server ngủ đông trên Render, Railway, Koyeb, Fly.io. Phản hồi < 1ms.
    """
    return {
        "status": "healthy",
        "service": "FitBreak API",
        "message": "Server is awake and active"
    }

@app.get("/api/health", tags=["Health"])
async def health_check():
    try:
        await check_ollama()
        return {"status": "ok", "ollama": "connected"}
    except Exception as e:
        return {"status": "degraded", "ollama": str(e)}

@app.get("/")
async def root():
    return {"message": "Welcome to FitBreak API! Go to /docs for API documentation."}
