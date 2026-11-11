from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import AIModelOfflineException
from app.core.ollama_client import chat as check_ollama
from app.core.rate_limiter import RateLimitMiddleware
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

app = FastAPI(lifespan=lifespan)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route.router, tags=["Auth Routers"])
app.include_router(profile.router, tags=["Create Profile Routers"])
app.include_router(exercise.router, tags=["Exercise"])
app.include_router(foodSuggest.router, tags=["Food Suggest"])
app.include_router(team.router, tags=["Team"])
app.include_router(raid.router, tags=["Raid"])
app.include_router(schedule.router, tags=["Schedule"])
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