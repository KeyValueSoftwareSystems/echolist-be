from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.connections import router as connections_router
from app.api.sections import router as sections_router
from app.api.items import router as items_router
from app.api.home import router as home_router
from app.api.ai import router as ai_router
from app.db.database import engine
from app.models import models

# Tables are created by Alembic migrations

app = FastAPI(
    title="EchoList API",
    description="API for EchoList - A voice-first productivity and personal memory assistant",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(users_router.router, prefix="/api")
app.include_router(connections_router.router, prefix="/api")
app.include_router(sections_router.router, prefix="/api")
app.include_router(items_router.router, prefix="/api")
app.include_router(home_router.router, prefix="/api")
app.include_router(ai_router.router, prefix="/api")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to EchoList API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
