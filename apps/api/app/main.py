import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import config  # noqa: F401
from app.db.base import Base
from app.db.session import engine

from app.v1.endpoints import recruits_public
from app.v1.endpoints import auth_internal
from app.v1.endpoints import admin_test

app = FastAPI(title="AU Esports Platform API")

app.include_router(recruits_public.router, prefix="/api/v1")
app.include_router(auth_internal.router, prefix="/api/v1")
app.include_router(admin_test.router, prefix="/api/v1")

Base.metadata.create_all(bind=engine)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
