from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

# Import routes
from app.api.routes import (
    users,
    sessions,
    object_memory,
    circle_search,
    calculation_recall,
    shape_recognition,
    activities,
    progress,
    admin
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from local frontend during dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(sessions.router, prefix=f"{settings.API_V1_STR}/sessions", tags=["sessions"])
app.include_router(object_memory.router, prefix=f"{settings.API_V1_STR}", tags=["object-memory"])
app.include_router(circle_search.router, prefix=f"{settings.API_V1_STR}", tags=["circle-search"])
app.include_router(calculation_recall.router, prefix=f"{settings.API_V1_STR}", tags=["calculation-recall"])
app.include_router(shape_recognition.router, prefix=f"{settings.API_V1_STR}", tags=["shape-recognition"])
app.include_router(activities.router, prefix=f"{settings.API_V1_STR}/activities", tags=["activities"])
app.include_router(progress.router, prefix=f"{settings.API_V1_STR}", tags=["progress"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])


@app.get("/")
def root():
    return {
        "message": "Cognitive Gaming and Memory Assistance Platform API",
        "docs": f"{settings.API_V1_STR}/docs",
        "disclaimer": (
            "These activities are experimental cognitive games and not validated clinical diagnostic instruments. "
            "Do not label their scores as dementia scores or use them to diagnose Alzheimer's disease."
        )
    }
