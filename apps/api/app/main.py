import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth.routes import router as auth_router
from app.core.config import DEFAULT_CORS_ORIGINS, get_settings
from app.db.base import Base
from app.db.session import engine
from app.v1.endpoints import admin_test
from app.v1.endpoints import announcements
from app.v1.endpoints import auth_internal
from app.v1.endpoints import recruits_admin
from app.v1.endpoints import recruits_public
from app.v1.endpoints import roster
from app.v1.endpoints import schedule
from app.v1.endpoints import users

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)

app.include_router(recruits_public.router, prefix="/api/v1")
app.include_router(auth_internal.router, prefix="/api/v1")
app.include_router(admin_test.router, prefix="/api/v1")
app.include_router(recruits_admin.router, prefix="/api/v1")
app.include_router(announcements.router, prefix="/api/v1")
app.include_router(schedule.router, prefix="/api/v1")
app.include_router(roster.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

if settings.auto_create_tables:
    logger.warning("AUTO_CREATE_TABLES is enabled; prefer Alembic migrations in production.")
    Base.metadata.create_all(bind=engine)

origins = settings.cors_origins_list
if not origins:
    origins = [origin.strip() for origin in DEFAULT_CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep local static upload serving for local development and legacy records.
uploads_dir = settings.uploads_root_path
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

if settings.enable_debug_routes:
    @app.get("/debug/env")
    def debug_env():
        return {
            "tenant": os.getenv("AZURE_TENANT_ID"),
            "client": os.getenv("AZURE_CLIENT_ID"),
            "secret_exists": os.getenv("AZURE_CLIENT_SECRET") is not None,
        }

    @app.get("/debug/token")
    async def debug_token():
        from app.auth.graph import get_graph_token

        return await get_graph_token()

    @app.get("/debug/calendar")
    async def debug_calendar():
        from app.auth.graph import get_calendar_events

        try:
            return await get_calendar_events()
        except Exception as exc:  # pragma: no cover
            return {"error": str(exc)}


@app.get("/health")
@app.get("/healthz")
def health():
    return {"status": "ok"}
