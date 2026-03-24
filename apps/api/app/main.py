import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core import config  # noqa: F401
from app.db.base import Base
from app.db.session import engine

# Routers
from app.v1.endpoints import recruits_public
from app.v1.endpoints import auth_internal
from app.v1.endpoints import admin_test
from app.v1.endpoints import recruits_admin
from app.auth.routes import router as auth_router

# Load environment variables
load_dotenv()

app = FastAPI(title="AU Esports Platform API")

# Include routers
app.include_router(recruits_public.router, prefix="/api/v1")
app.include_router(auth_internal.router, prefix="/api/v1")
app.include_router(admin_test.router, prefix="/api/v1")
app.include_router(recruits_admin.router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

# Database
Base.metadata.create_all(bind=engine)

# CORS
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug routes
@app.get("/debug/env")
def debug_env():
    return {
        "tenant": os.getenv("AZURE_TENANT_ID"),
        "client": os.getenv("AZURE_CLIENT_ID"),
        "secret_exists": os.getenv("AZURE_CLIENT_SECRET") is not None
    }

@app.get("/debug/token")
async def debug_token():
    from app.auth.graph import get_graph_token
    return await get_graph_token()

@app.get("/debug/calendar")
async def debug_calendar():
    from app.auth.graph import get_calendar_events
    

    try:
        events = await get_calendar_events()
        return events
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

from app.v1.endpoints import roster

app.include_router(roster.router, prefix="/api/v1")